# Booker UK Product Scraper

A Scrapy-based scraper for collecting product information from the Booker UK website. The spider logs into an account, navigates product categories, extracts product details, pricing, promotions, and descriptions, then exports the data to a CSV file.

## Features

* Login with Booker account credentials
* Automatically discover product categories
* Extract:

  * Product Name
  * Product ID
  * Barcode
  * Category
  * Description
  * Wholesale Price
  * RSP
  * Packet Format
  * VAT
  * Promotional Price
  * Price Marked
  * Direct Delivery Status
* Export data to a CSV file

## Requirements

* Python 3.9+
* Scrapy
* pandas
* json5

Install dependencies:

```bash
pip install scrapy pandas json5
```

## Configuration

Open the script and update the following variables with your Booker account details:

```python
CUST_NO = ""
EMAIL = ""
PASS = ""
```

## Usage

Run the scraper with:

```bash
scrapy runspider scraper.py
```

## Output

The scraper creates an `Output` folder and saves the extracted data as:

```
Output/booker_eastleigh_YYYYMMDD.csv
```

## Notes

* A valid Booker account is required.
* The scraper extracts data from product listings and individual product pages.
* Output is saved in CSV format for easy analysis or import into other systems.


