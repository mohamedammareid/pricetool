# Price Comparison Tool

## Overview
The **Price Comparison Tool** is a Python-based application designed to help users search for products, compare prices across multiple online platforms, and view the price history of products. It supports scraping data from Amazon and eBay, allowing users to find the best deals easily.

## Features
- **Product Search**: Search for products on Amazon and eBay using a single query.
- **Price Comparison**: Display a sorted list of products based on their prices.
- **Best Deals**: Highlight the top 5 best deals and optionally open them in the browser.
- **Price History**: View the price history of products to make informed purchasing decisions.
- **Database Storage**: Save product details and their prices for future reference.

## Requirements
### Software
- Python 3.7 or higher

### Libraries
Install the required Python libraries using:
```bash
pip install -r requirements.txt
```
**Dependencies:**
- `requests`
- `beautifulsoup4`
- `sqlite3` (built-in)
- `dataclasses` (for Python < 3.7)

### Other Tools
- A modern web browser to view product links.

## Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```bash
   cd price-comparison-tool
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Run the program:
   ```bash
   python PriceComparisonTool.py
   ```
2. Choose from the following options in the menu:
   - **Search for products**: Enter a product name to search and compare prices.
   - **View price history**: Check the price trends of a specific product.
   - **Exit**: Exit the application.

3. Follow the on-screen instructions to explore product details and open links in the browser.

## File Structure
- `PriceComparisonTool.py`: Main application file.
- `requirements.txt`: List of required libraries.
- `price_tracker.log`: Log file for tracking errors and activities.
- `product_prices.db`: SQLite database to store product details.

## Example
Search for "headphones":
- View products from Amazon and eBay.
- Compare prices and choose the best deal.
- Open product links directly in the browser.

## Contributing
Contributions are welcome! If you'd like to contribute:
1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes and push:
   ```bash
   git push origin feature-name
   ```
4. Submit a pull request.


## Acknowledgments
- Python community for amazing libraries and tools.
- Amazon and eBay for providing accessible product data.

