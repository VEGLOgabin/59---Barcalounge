# Web Scraper for Barcalounger

## Overview
This project is a web scraper designed to extract product information from the Barcalounger website. It leverages Scrapy, Playwright, and BeautifulSoup to collect product links and details efficiently.

## Features
- Extracts product categories and subcategories
- Retrieves product links from all collections
- Scrolls dynamically to load more products
- Saves extracted data in CSV format
- Uses Scrapy for structured data extraction
- Implements Playwright for handling dynamic content

## Installation
### Prerequisites
Ensure you have Python installed (>=3.7). Then, install the required dependencies:

```sh
pip install scrapy playwright beautifulsoup4 requests twisted
playwright install
```

## Usage
### Extracting Product Links
To scrape product links and store them in `utilities/products-links.csv`:

```sh
python -c 'import your_script; your_script.get_collections_products()'
```

### Running Scrapy Spider
After obtaining the product links, run the Scrapy spider to extract detailed product information:

```sh
scrapy crawl product_spider
```

## Output
- `utilities/products-links.csv`: Contains product categories and links
- `output/`: Directory containing extracted product details

## Notes
- The scraper uses Playwright to handle infinite scrolling
- Ensure JavaScript is enabled in Playwright for dynamic content loading

## License
This project is licensed under the MIT License.
