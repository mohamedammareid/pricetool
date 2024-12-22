import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import os
import sys
import webbrowser
from typing import List, Tuple, Dict, Optional
import logging
from dataclasses import dataclass
from urllib.parse import quote_plus
import time
import random

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.write("\033[H")

@dataclass
class Product:
    name: str
    price: Optional[float]  # Changed to Optional[float] to handle None values
    website: str
    url: str
    timestamp: datetime
    description: str = ''
    rating: float = 0.0
    num_reviews: int = 0
    availability: str = ''

    def __post_init__(self):
        # Ensure price is either float or None
        if self.price is not None:
            try:
                self.price = float(self.price)
            except (ValueError, TypeError):
                self.price = None

class DatabaseManager:
    def __init__(self, db_name: str = 'product_prices.db'):
        self.db_name = db_name
        self.setup_database()

    def setup_database(self) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    price REAL,
                    website TEXT,
                    url TEXT,
                    timestamp DATETIME,
                    description TEXT,
                    rating REAL,
                    num_reviews INTEGER,
                    availability TEXT,
                    UNIQUE(name, website, timestamp)
                )
            ''')
            conn.commit()

    def save_product(self, product: Product) -> None:
        if not product.name or product.price is None:  # Skip invalid products
            return
            
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO products 
                (name, price, website, url, timestamp, description, 
                rating, num_reviews, availability)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product.name, product.price, product.website, product.url,
                product.timestamp, product.description, product.rating,
                product.num_reviews, product.availability
            ))
            conn.commit()

    def get_price_history(self, product_name: str) -> List[Tuple]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT website, price, timestamp, url
                FROM products 
                WHERE name LIKE ? AND price IS NOT NULL
                ORDER BY timestamp DESC
            ''', (f'%{product_name}%',))
            return cursor.fetchall()

class WebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        try:
            time.sleep(random.uniform(2, 4))
            response = self.session.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()  # Raise exception for bad status codes
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def _extract_price(self, price_text: str) -> Optional[float]:
        if not price_text:
            return None
        try:
            # Remove currency symbols and whitespace
            cleaned = ''.join(c for c in price_text if c.isdigit() or c == '.' or c == ',')
            # Remove thousands separator
            cleaned = cleaned.replace(',', '')
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def _scrape_amazon(self, soup: BeautifulSoup, base_url: str) -> List[Product]:
        products = []
        if not soup:
            return products

        items = soup.select('div[data-component-type="s-search-result"]')
        for item in items:
            try:
                name_elem = item.select_one('h2 a span')
                price_elem = item.select_one('span.a-price > span.a-offscreen')
                rating_elem = item.select_one('span.a-icon-alt')
                reviews_elem = item.select_one('span.a-size-base.s-underline-text')

                if not name_elem:
                    continue

                name = name_elem.text.strip()
                price = self._extract_price(price_elem.text) if price_elem else None
                rating = float(rating_elem.text.split()[0]) if rating_elem else 0.0
                reviews = int(reviews_elem.text.replace(',', '')) if reviews_elem else 0

                url_elem = item.select_one('h2 a')
                url = 'https://www.amazon.com' + url_elem['href'] if url_elem and 'href' in url_elem.attrs else base_url

                if name and url:  # Only add if we have at least name and URL
                    products.append(Product(
                        name=name,
                        price=price,
                        website='Amazon',
                        url=url,
                        timestamp=datetime.now(),
                        rating=rating,
                        num_reviews=reviews
                    ))
            except Exception as e:
                self.logger.error(f"Error parsing Amazon product: {str(e)}")
                continue

        return products

    def _scrape_ebay(self, soup: BeautifulSoup, base_url: str) -> List[Product]:
        products = []
        if not soup:
            return products

        items = soup.select('li.s-item')
        for item in items:
            try:
                name_elem = item.select_one('div.s-item__title')
                price_elem = item.select_one('span.s-item__price')
                condition_elem = item.select_one('span.SECONDARY_INFO')

                if not name_elem:
                    continue

                name = name_elem.text.strip()
                if name.lower() == 'shop on ebay':
                    continue

                price = self._extract_price(price_elem.text) if price_elem else None
                availability = condition_elem.text.strip() if condition_elem else ''

                url_elem = item.select_one('a.s-item__link')
                url = url_elem['href'] if url_elem and 'href' in url_elem.attrs else base_url

                if name and url:  # Only add if we have at least name and URL
                    products.append(Product(
                        name=name,
                        price=price,
                        website='eBay',
                        url=url,
                        timestamp=datetime.now(),
                        availability=availability
                    ))
            except Exception as e:
                self.logger.error(f"Error parsing eBay product: {str(e)}")
                continue

        return products

    def scrape_site(self, url: str, site_name: str) -> List[Product]:
        soup = self.get_soup(url)
        if not soup:
            return []

        if site_name == 'amazon':
            return self._scrape_amazon(soup, url)
        elif site_name == 'ebay':
            return self._scrape_ebay(soup, url)
        return []

class PriceComparisonTool:
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = WebScraper()
        self.setup_logging()
        self.site_urls = {
            'amazon': 'https://www.amazon.com/s?k={}',
            'ebay': 'https://www.ebay.com/sch/i.html?_nkw={}'
        }

    def setup_logging(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('price_tracker.log'),
                logging.StreamHandler()
            ]
        )

    def search_products(self, query: str) -> List[Product]:
        products = []
        encoded_query = quote_plus(query)

        print("\n🔍 Searching for products across multiple sites...")
        for site_name, url_template in self.site_urls.items():
            try:
                url = url_template.format(encoded_query)
                print(f"\n⏳ Searching on {site_name.title()}...")
                site_products = self.scraper.scrape_site(url, site_name)
                products.extend(site_products)
            except Exception as e:
                print(f"Error searching {site_name}: {str(e)}")
                continue

        return products

    def display_results(self, products: List[Product]) -> None:
        if not products:
            print("❌ No products found.")
            return

        # Filter out products with no price before sorting
        valid_products = [p for p in products if p.price is not None]
        
        if not valid_products:
            print("❌ No products found with valid prices.")
            return

        print("\n🎯 Search Results:")
        print("-" * 80)
        
        sorted_products = sorted(valid_products, key=lambda x: x.price or float('inf'))
        for i, product in enumerate(sorted_products, 1):
            print(f"{i}. {product.name}")
            print(f"   💰 Price: ${product.price:.2f}" if product.price else "   💰 Price: Not available")
            print(f"   🏪 Website: {product.website}")
            if product.rating > 0:
                print(f"   ⭐ Rating: {product.rating:.1f} ({product.num_reviews} reviews)")
            if product.availability:
                print(f"   📦 Status: {product.availability}")
            print(f"   🔗 URL: {product.url}")
            print("-" * 80)

        self.offer_best_deals(sorted_products)

    def offer_best_deals(self, products: List[Product]) -> None:
        if not products:
            return

        try:
            choice = input("\n🎁 Would you like to see the top 5 best deals? (y/n): ").lower()
            if choice == 'y':
                clear_terminal()
                print("\n🏆 Top 5 Best Deals:")
                print("-" * 80)
                
                for i, product in enumerate(products[:5], 1):
                    print(f"{i}. {product.name}")
                    print(f"   💰 Price: ${product.price:.2f}" if product.price else "   💰 Price: Not available")
                    print(f"   🏪 Website: {product.website}")
                    print(f"   🔗 URL: {product.url}")
                    print("-" * 80)

                choice = input("\n🌐 Would you like to open these deals in your browser? (y/n): ").lower()
                if choice == 'y':
                    for product in products[:5]:
                        webbrowser.open(product.url)
        except Exception as e:
            print(f"Error displaying deals: {str(e)}")

    def show_price_history(self, product_name: str) -> None:
        try:
            history = self.db.get_price_history(product_name)
            if not history:
                print(f"❌ No price history found for '{product_name}'")
                return

            print(f"\n📊 Price History for '{product_name}':")
            print("-" * 80)
            for website, price, timestamp, url in history:
                print(f"🏪 Website: {website}")
                print(f"💰 Price: ${price:.2f}" if price else "💰 Price: Not available")
                print(f"📅 Date: {timestamp}")
                print(f"🔗 URL: {url}")
                print("-" * 80)
        except Exception as e:
            print(f"Error displaying price history: {str(e)}")

def main():
    tool = PriceComparisonTool()
    
    while True:
        try:
            clear_terminal()
            print("🛍️  US Price Comparison Tool 🛍️")
            print("\n1. 🔍 Search for products")
            print("2. 📊 View price history")
            print("3. 🚪 Exit")
            
            choice = input("\n✨ Enter your choice (1-3): ").strip()
            
            if choice == '1':
                clear_terminal()
                query = input("🔍 Enter product name to search: ").strip()
                if not query:
                    print("❌ Please enter a valid product name.")
                    time.sleep(2)
                    continue
                    
                products = tool.search_products(query)
                tool.display_results(products)
                
                # Save valid products to database
                for product in products:
                    if product.price is not None:
                        tool.db.save_product(product)
                
                input("\n⏎ Press Enter to continue...")
                
            elif choice == '2':
                clear_terminal()
                product_name = input("🔍 Enter product name to view history: ").strip()
                if not product_name:
                    print("❌ Please enter a valid product name.")
                    time.sleep(2)
                    continue
                    
                tool.show_price_history(product_name)
                input("\n⏎ Press Enter to continue...")
                
            elif choice == '3':
                clear_terminal()
                print("👋 Goodbye! Thank you for using Price Comparison Tool!")
                break
                
            else:
                print("❌ Invalid choice. Please try again.")
                time.sleep(2)
                
        except KeyboardInterrupt:
            clear_terminal()
            print("\n👋 Program terminated by user.")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            input("\n⏎ Press Enter to continue...")

if __name__ == "__main__":
    main()