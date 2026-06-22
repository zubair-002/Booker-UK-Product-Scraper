CUST_NO = ''
EMAIL = ''
PASS = ''

import scrapy
from scrapy.crawler import CrawlerProcess
import re
import json
import json5  
from urllib.parse import urljoin, quote
import scrapy
from urllib.parse import parse_qs, quote, urlsplit
import pandas as pd
from datetime import datetime
import os
import random
import scrapy.resolver
import pandas as pd
from datetime import datetime
import os
import random

def clean_category(text: str) -> str:
    return text.encode("utf-8").decode("unicode_escape").strip()



class ProductsSpider(scrapy.Spider):
    name = "products"
    headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'priority': 'u=0, i',
    'referer': 'https://www.booker.co.uk/en/My-Booker',
    'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
}
    count=1
    cmp = []
    prs = {}
    def start_requests(self):
        json_data = {
            'customerNumber': CUST_NO,
            'emailAddress': EMAIL,
            'password': PASS,
        }
        yield scrapy.http.JsonRequest(
            url="https://www.booker.co.uk/api/2.0/account/signin",
            data=json_data,
            headers=self.headers,
            callback=self.after_login,dont_filter=True
            
        )

    def after_login(self, response):
        yield scrapy.Request('https://www.booker.co.uk/en/Products/Categories',headers=self.headers,callback=self.parse,dont_filter=True)
    def parse(self, response):
        scripts = response.xpath("//script/text()").getall()
        for script in scripts:
            pattern = re.compile(
                r'"label":"([^"]+)".+?"href":"(/products/category\?[^"]+)"',
                re.DOTALL
            )

            for match in pattern.findall(script):
                label, href = match
                clean_href = href.encode("utf-8").decode("unicode_escape")
                abs_url = urljoin(response.url, clean_href)
                yield scrapy.Request("https://www.booker.co.uk/api/2.0/account/signin", callback=self.login_for_mainCategory, meta={'label': label,'Referer':abs_url}, headers=self.headers,dont_filter=True)
    def login_for_mainCategory(self, response):
        json_data = {
            'customerNumber': CUST_NO,
            'emailAddress': EMAIL,
            'password': PASS,
        }
        yield scrapy.http.JsonRequest(
            url="https://www.booker.co.uk/api/2.0/account/signin",
            data=json_data,
            headers=self.headers,
            callback=self.login_again_for_mainCategory,dont_filter=True,meta=response.meta
            
        )
    def login_again_for_mainCategory(self, response):
        yield scrapy.Request(response.meta['Referer'], callback=self.parse_sub_category, meta=response.meta,headers=self.headers,dont_filter=True)
    
    def parse_sub_category(self, response):
        scripts = response.xpath("//script/text()").getall()
        for script in scripts:
            pattern = re.compile(
                r'"label":"([^"]+)".+?"href":"(/products/category\?[^"]+)"',
                re.DOTALL
            )

            for label, href in pattern.findall(script):
                clean_href = href.encode("utf-8").decode("unicode_escape")
                abs_url = urljoin(response.url, clean_href)
                returnUrl = clean_href  
                encoded = quote(returnUrl, safe="/?=&|,‘'") 
                print_url = f"https://www.booker.co.uk/products/print-product-listing?returnUrl={abs_url}"
                yield scrapy.Request("https://www.booker.co.uk/api/2.0/account/signin", callback=self.login_for_subCategory, meta={'label': response.meta['label'],'Referer':print_url,"cookiejar":self.count,'ctgry':abs_url}, headers=self.headers,dont_filter=True)
                self.count += 1
    def login_for_subCategory(self, response):
        json_data = {
            'customerNumber': CUST_NO,
            'emailAddress': EMAIL,
            'password': PASS,
        }
        yield scrapy.http.JsonRequest(
            url="https://www.booker.co.uk/api/2.0/account/signin",
            data=json_data,
            headers=self.headers,
            callback=self.login_again_for_subCategory,dont_filter=True,meta=response.meta)
    def login_again_for_subCategory(self, response):
        yield scrapy.Request(response.meta['ctgry'], callback=self.to_print_list, meta=response.meta,headers=self.headers,dont_filter=True)
    def to_print_list(self, response):
        yield response.follow(response.meta['Referer'], meta=response.meta,callback=self.parse_print_listing,headers=self.headers,dont_filter=True)

    def parse_print_listing(self, response):
        scripts = response.xpath("//script/text()").getall()
        for script in scripts:
            if "PrintProductListing" in script and "products" in script:
                match = re.search(r'products:\s*(\[.*\])', script, re.DOTALL)
                if match:
                    products_json = match.group(1)

                    try:
                        products = json.loads(products_json)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"JSON parse failed: {e}")
                        continue

                    for p in products:
                        pro_code = p.get("productCode")
                        barcode = p.get("barcode")
                        wholesale = p.get("wsp") 
                        pack_format = p.get("packSize")
                        vat = p.get("vat")
                        yield scrapy.Request(f"https://www.booker.co.uk/products/product?Code={pro_code}", callback=self.parse_product, meta=response.meta,headers=self.headers,dont_filter=True)
                        self.prs[pro_code] = {
                            "name": p.get("description"),
                            "Barcode": "\t"+str(barcode),
                            "Product ID": pro_code,
                            "Wholesale Price": wholesale,
                            "Packet Format": pack_format,
                            "RSP": p.get("rsp"),
                            "Vat": vat,
                        }
    def parse_product(self, response):

        scripts = response.xpath("//script/text()").getall()
        product_data = None
        for script in scripts:
            if "const args" in script and '"discountText"' in script:
                match = re.search(r'\.\.\.({.*?})\s*,\s*onclick:', script, re.DOTALL)
                if match:
                    try:
                        promo_data = json5.loads(match.group(1))
                    except Exception as e:
                        self.logger.error(f"Failed to parse promo JSON: {e}")
                break
        if promo_data:
            discount_text = promo_data.get('standardPricing', {}).get('offer', {}).get('discountText')
            on_promo = "Yes" if discount_text else "No"
            pricerpp = promo_data.get("pricerpp", {}).get("value", "")
        for script in scripts:
            if "ProductTabs" in script and '"product":' in script:
                match = re.search(r'"product":(\{.*?\})\s*,\s*"midasCode"', script, re.DOTALL)
                if match:
                    try:
                        product_data = json5.loads(match.group(1))
                    except Exception as e:
                        self.logger.error(f"Failed to parse product JSON: {e}")

        if not product_data:
            self.logger.warning(f"No product data found for {response.url}")
            return
        id_ = response.url.split("=")[-1]
        name = product_data.get("description")
        direct_del = "Yes" if product_data.get("isDirectDelivery") else "No"
        description_lines = []

        for part in product_data.get("parts", []):
            for item_type in part.get("itemTypes", []):
                base_id = item_type.get("baseTypeId")
                type_id = item_type.get("id")

                for item in item_type.get("itemData", []):
                    value = item.get("value", "").strip()
                    if not value:
                        continue

                    if base_id == 4 and type_id == 159:
                        description_lines.append(value)

                    if base_id == 5 and type_id == 32:
                        description_lines.append(value)
                    if base_id == 4 and type_id == 35:
                        description_lines.append(value)

                    if base_id == 3 and type_id == 74:
                        if item.get("id") == 930:
                            description_lines.append(f"Alcohol By Volume: {value}")
                        else: 
                            description_lines.append(f"Tasting Notes: {value}")

        full_description = "\n".join(description_lines)

        product = self.prs[id_]
        item = {
            "Barcode": product['Barcode'],
            "Product ID": id_,
            "Product Name": product['name'],
            "Category": clean_category(response.meta['label']),
            "Description": full_description,
            "Wholesale Price": product['Wholesale Price'],
            "RSP": product['RSP'],
            "Packet Format": product['Packet Format'],
            "Vat": product['Vat'],
            "On Promo": on_promo,
            "Promotional Price": discount_text,
            "Price Marked": pricerpp,
            "Direct Delivered": direct_del,
        }
        self.cmp.append(item)
        self.logger.info(f"Scraped: {product['name']}")
    
    def closed(self, reason):
        filenm = datetime.now().strftime("%Y%m%d")
        if not os.path.exists("Output"):
            os.mkdir("Output")
        df = pd.DataFrame(self.cmp)
        df.to_csv(f"Output/booker_eastleigh_{filenm}.csv",  index=False)
