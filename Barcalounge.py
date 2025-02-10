from twisted.internet import asyncioreactor
asyncioreactor.install()
import re
import scrapy
import os
from scrapy.crawler import CrawlerProcess
import requests
from bs4 import BeautifulSoup
import csv
from playwright.sync_api import sync_playwright


def process_collection_products(page, collection, all_products):
    print(f"Processing  collection : {collection[2]}")
    page.goto(collection[2])


    previous_count = 0

    while True:
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        products = soup.find_all("div", class_ = "card loop-card")
        current_count = len(products)

        if current_count == previous_count:
            break  

        previous_count = current_count

        # Scroll to the bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for new content to load
        page.wait_for_timeout(2000)

    print(f"Total products found: {current_count}")

    products = soup.find_all("div", class_ = "card loop-card")

    if products:
        for item in products:
            link = item.find("a").get("href")
            all_products.append([collection[0], collection[1], link])

        
def get_collections_products():
    output_file = 'utilities/products-links.csv'
    all_products = []  
    url = "https://www.barcalounger.com/"
    req = requests.get(url)
    soup = BeautifulSoup(req.content, "html.parser")

    menu = soup.find("ul", id = "menu-primary")
    menu_items = menu.find_all('li', recursive=False)
    collections_link = []
    for item in menu_items:
        category = item.find("a").text.strip()
        if category not in ["Shop All Products", "Browse by Covers"]:
            if not item.find('ul'):
                link = item.find("a").get("href")
                collections_link.append([category, "", link])
                # print([category, "", link])
            else:
                # print("Extract")
                sub_categories = item.find("ul")
                sub_categories = sub_categories.find_all("li")
                for categ2 in sub_categories:
                    category2 = categ2.find("a").text.strip()
                    if category2 != "All Recliners":
                        # print(category2)
                        link = categ2.find("a").get("href")
                        collections_link.append([category, category2, link])
                        # print([category, category2, link])
    
    collections = collections_link
    if collections:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            for collection in collections:
                process_collection_products(
                    page, 
                    collection, 
                    all_products
                )
            browser.close()
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["category1","category2",'product_link']) 
        for product_link in all_products:
            writer.writerow([product_link[0], product_link[1], product_link[2]]) 

    print("Scraping completed and data saved to CSV.")







# ----------------------------------------    Get product page html  ----------------------------------------------------------------


def get_prod_html():
    # url = 'https://www.barcalounger.com/view-all-options/anaheim-power-recline?attribute_pa_covers=dobbs-saddle'
    url = "https://www.barcalounger.com/view-all-options/langston-power-lift-recline?attribute_pa_covers=venzia-blue"
    # url = "https://www.barcalounger.com/view-all-options/monico?attribute_pa_covers=ashland-granite"
    # url = "https://www.barcalounger.com/view-all-options/byron"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url)
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        with open("product.html", "w", encoding="utf-8") as file:
            file.write(soup.prettify())


        scraped_data = {}
        tables = soup.find_all('table', class_='shop_attributes product_meta')
        for table in tables:
            rows = table.find_all('tr')
            for row_ in rows:
                header = row_.find('th').get_text(strip=True) if row_.find('th') else None
                data_ = row_.find('td').get_text(strip=True) if row_.find('td') else None
                if header and data_:
                    scraped_data[header] = data_
        dimensions = scraped_data.pop('Dimensions', None)
        width = ""
        height = ""
        depth = ""
        if dimensions:
            dimensions = dimensions.replace("in", "").split('"')
            for unit in dimensions:
                if "D" in unit:
                    depth = unit.replace("D", "")
                if "W" in unit:
                    width = unit.replace("W", "")
                if "H" in unit:
                    height = unit.replace("H", "")

        sku = scraped_data.pop('SKU', None) 
        scraped_data.pop('Price', None)
        remaining_data_str= ",   ".join([f"{k}: {v}" for k, v in scraped_data.items()])
        specifications_str = remaining_data_str




        weight = scraped_data.pop("Weight", None)
        if weight:
            weight = weight.replace('bs', "")

        arm_height = scraped_data.pop("Arm Height", None)

        seat_dimensions = scraped_data.pop("Seat Dimensions", None)
        seat_width = ""
        seat_height = ""
        seat_depth = ""
        if seat_dimensions:
            seat_dimensions = dimensions.replace("in", "").split('"')
            for unit in seat_dimensions:
                if "D" in unit:
                    seat_depth = unit.replace("D", "")
                if "W" in unit:
                    seat_width = unit.replace("W", "")
                if "H" in unit:
                    seat_heightt = unit.replace("H", "")



        print("-------------------------------------")
        print(scraped_data)


        

# --------------------------------------------------------------------------------------------------------------------------------------------

class ProductSpider(scrapy.Spider):
    name = "product_spider"
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'timeout': 100000,
        },
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',
        'CONCURRENT_REQUESTS': 1,
        'LOG_LEVEL': 'INFO',
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 429],
        'HTTPERROR_ALLOW_ALL': True,
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' \
                        'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                        'Chrome/115.0.0.0 Safari/537.36',
            'Accept-Language': 'en',
        },
    }
    

    columns = [
        "SKU", "START_DATE", "END_DATE", "DATE_QUALIFIER", "DISCONTINUED", "BRAND", "PRODUCT_GROUP1",
        "PRODUCT_GROUP2", "PRODUCT_GROUP3", "PRODUCT_GROUP4", "PRODUCT_GROUP1_QTY", "PRODUCT_GROUP2_QTY",
        "PRODUCT_GROUP3_QTY", "PRODUCT_GROUP4_QTY", "DEPARTMENT1", "ROOM1", "ROOM2", "ROOM3", "ROOM4",
        "ROOM5", "ROOM6", "CATEGORY1", "CATEGORY2", "CATEGORY3", "CATEGORY4", "CATEGORY5", "CATEGORY6",
        "COLLECTION", "FINISH1", "FINISH2", "FINISH3", "MATERIAL", "MOTION_TYPE1", "MOTION_TYPE2",
        "SECTIONAL", "TYPE1", "SUBTYPE1A", "SUBTYPE1B", "TYPE2", "SUBTYPE2A", "SUBTYPE2B",
        "TYPE3", "SUBTYPE3A", "SUBTYPE3B", "STYLE", "SUITE", "COUNTRY_OF_ORIGIN", "MADE_IN_USA",
        "BED_SIZE1", "FEATURES1", "TABLE_TYPE", "SEAT_TYPE", "WIDTH", "DEPTH", "HEIGHT", "LENGTH",
        "INSIDE_WIDTH", "INSIDE_DEPTH", "INSIDE_HEIGHT", "WEIGHT", "VOLUME", "DIAMETER", "ARM_HEIGHT",
        "SEAT_DEPTH", "SEAT_HEIGHT", "SEAT_WIDTH", "HEADBOARD_HEIGHT", "FOOTBOARD_HEIGHT",
        "NUMBER_OF_DRAWERS", "NUMBER_OF_LEAVES", "NUMBER_OF_SHELVES", "CARTON_WIDTH", "CARTON_DEPTH",
        "CARTON_HEIGHT", "CARTON_WEIGHT", "CARTON_VOLUME", "CARTON_LENGTH", "PHOTO1", "PHOTO2",
        "PHOTO3", "PHOTO4", "PHOTO5", "PHOTO6", "PHOTO7", "PHOTO8", "PHOTO9", "PHOTO10", "INFO1",
        "INFO2", "INFO3", "INFO4", "INFO5", "DESCRIPTION", "PRODUCT_DESCRIPTION",
        "SPECIFICATIONS", "CONSTRUCTION", "COLLECTION_FEATURES", "WARRANTY", "ADDITIONAL_INFORMATION",
        "DISCLAIMER", "VIEWTYPE", "ITEM_URL", "CATALOG_PDF",
    ]

    def __init__(self, input_file='utilities/products-links.csv', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_file = input_file
        os.makedirs('output', exist_ok=True)
        self.barcalounge_file = open('output/barcalounge.csv', 'w', newline='', encoding='utf-8')

        self.barcalounge_writer = csv.DictWriter(self.barcalounge_file, fieldnames=self.columns)

        self.barcalounge_writer.writeheader()


    def start_requests(self):
        self.logger.info("Spider started. Reading product links from CSV file.")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield scrapy.Request(
                    url=row['product_link'],
                    meta={
                        'playwright': True,
                        'playwright_include_page': True,
                        'product': row
                    },
                    callback=self.parse,
                    errback=self.handle_error
                )
    async def parse(self, response):
        product = response.meta['product']
        self.logger.info(f"Parsing product: {product['product_link']}")
        sku = ""
        width = ""
        depth = ""
        height = ""
        product_images = []
        product_description = ""
        specifications_str = ""
        assembly_pdf = ""
        collection = ""
        disclamer = ""
        limited_warranty = ""
        try:
            page = response.meta['playwright_page']
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            data = {col: "" for col in self.columns} 

            product_description_div = soup.find("div",  class_ = 'woocommerce-product-details__short-description')
            if product_description_div:
                product_description = product_description_div.find("p").text.strip()
            else:
                product_description=""

            try:
                scraped_data = {}
                tables = soup.find_all('table', class_='shop_attributes product_meta')
                for table in tables:
                    rows = table.find_all('tr')
                    for row_ in rows:
                        header = row_.find('th').get_text(strip=True) if row_.find('th') else None
                        data_ = row_.find('td').get_text(strip=True) if row_.find('td') else None
                        if header and data_:
                            scraped_data[header] = data_
                dimensions = scraped_data.pop('Dimensions', None)
                width = ""
                height = ""
                depth = ""
                if dimensions:
                    dimensions = dimensions.replace("in", "").split('"')
                    for unit in dimensions:
                        if "D" in unit:
                            depth = unit.replace("D", "")
                        if "W" in unit:
                            width = unit.replace("W", "")
                        if "H" in unit:
                            height = unit.replace("H", "")
                    if width == height == depth == "":
                        dimensions__ul =  product_description_div.find("ul")
                        if dimensions__ul:
                            dimensions__li = dimensions__ul.find_all("li")
                            if dimensions__li:
                                width = []
                                height = []
                                depth = []
                                for li in dimensions__li:
                                    text = li.get_text(strip=True)
                                    
                                    if ":" in text:
                                        name, dims = text.split(":", 1)
                                        dims = dims.strip().split(" x ")
                                        
                                        if len(dims) == 3:
                                            width.append(dims[0])
                                            depth.append(dims[1])
                                            height.append(dims[2])
                                width = "; ".join(width)
                                depth = "; ".join(depth)
                                height = "; ".join(height)
                        else:
                            pass
                
            


                sku = scraped_data.pop('SKU', None) 
                scraped_data.pop('Price', None)


                weight = scraped_data.pop("Weight", None)
                if weight:
                    weight = weight.replace("lbs", "")

                arm_height = scraped_data.pop("Arm Height", None)

                seat_dimensions = scraped_data.pop("Seat Dimensions", None)
                seat_width = ""
                seat_height = ""
                seat_depth = ""
                if seat_dimensions:
                    seat_dimensions = seat_dimensions.replace("in", "").split('"')
                    for unit in seat_dimensions:
                        if "D" in unit:
                            seat_depth = unit.replace("D", "")
                        if "W" in unit:
                            seat_width = unit.replace("W", "")
                        if "H" in unit:
                            seat_heightt = unit.replace("H", "")



     



                remaining_data_str= ",   ".join([f"{k}: {v}" for k, v in scraped_data.items()])
                specifications_str = remaining_data_str
            except Exception as e:
                print("An error occurred while extracting SKU:", str(e))


            try:
                collection = soup.find("h1", class_ = "product_title entry-title")
                collection = collection.text.strip()
            except AttributeError:
                collection = ""

            assembly_pdf = soup.find("a", class_ = "assembly-instructions")
            if assembly_pdf:
                assembly_pdf = assembly_pdf.get("href")
            else:
                assembly_pdf = ""


            p_dsiclamer = soup.select(".disclaimer p")
            if p_dsiclamer:
                disclamer = p_dsiclamer[-1].get_text(strip=True) if p_dsiclamer else None
            else:
                disclamer = ""
               
            limited_warranty = """
                BarcaLounger conveys the following Limited Warranty to the original retail purchaser under normal residential use and does not cover any type of commercial, industrial, institutional, or rental use. This warranty does not cover “floor samples” sold or products designated “as is” at the time of purchase. This warranty does not apply to furniture intentionally misused, or to damage resulting from negligence, exposure, pet damage, chemical treatment, improper cleaning, or when heavy soiling or abuse is evident. This warranty does not cover damage caused by improper transportation.  This warranty is not transferable. This warranty supersedes and replaces all implied warranties of merchantability and use for a particular purpose.
            """

            data.update({
                "CATEGORY1": product["category1"],
                "CATEGORY2": product["category2"],
                "COLLECTION": collection,
                "ITEM_URL": product['product_link'],
                "SKU": sku,
                "DESCRIPTION": collection,
                "PRODUCT_DESCRIPTION": product_description,
                "WIDTH": width,
                "DEPTH": depth,
                "HEIGHT": height,
                "ADDITIONAL_INFORMATION": specifications_str,
                "CONSTRUCTION": "", 
                "SPECIFICATIONS": specifications_str,
                "BRAND": "Barcalounge",
                "VIEWTYPE": "Normal",  
                "INFO1" : assembly_pdf, 
                "WARRANTY" : limited_warranty,
                "DISCLAIMER" : disclamer,
                "SEAT_DEPTH" : seat_depth, 
                "SEAT_HEIGHT" : seat_height, 
                "SEAT_WIDTH" : seat_width, 
                "WEIGHT" : weight,
                "ARM_HEIGHT" : arm_height,
            })

            product_images = soup.select("img.iconic-woothumbs-thumbnails__image.no-lazyload.skip-lazy")
            if product_images:                  
                product_images = [
                    (img.replace("180x180", "500x500") if "500x500" in item.get("data-srcset", "") else img)
                    for item in product_images
                    if (img := item.get("data-lazy") or item.get("src"))
                ]
            else:
                product_images = []

            if len(product_images) == 0:
                
                img_url = soup.find("img", class_ = "iconic-woothumbs-images__image no-lazyload skip-lazy")
                if img_url:
                    product_images.append(img_url.get("src"))
            for i in range(1, 11):
                data[f"PHOTO{i}"] = ""
            for idx, img_url in enumerate(product_images):
                if idx > 9:
                    continue
                else:
                    data[f"PHOTO{idx + 1}"] = img_url
            if len(product_images) < 10:
                self.logger.info(f"Only {len(product_images)} images found for {product['product_link']}. Remaining PHOTO columns will be ''.")
            elif len(product_images) > 10:
                self.logger.warning(f"More than 10 images found for {product['product_link']}. Only the first 10 will be saved.")

            if len(product_images) == 0:
                data.update({
                    "VIEWTYPE": "Limited",
                })

            if sku:
                self.barcalounge_writer.writerow(data)
                self.logger.info(f"Successfully scraped and categorized product: {product['product_link']}")
            else:
                self.barcalounge_writer.writerow(data)
                # self.logger.info(f"Successfully scraped and categorized product: {product['product_link']}")
                self.logger.info("############################ Missing SKU Detected  ###########################################")
                self.logger.info(f"Product link : {product['product_link']} ")
                self.logger.info("############################ Ending of the warning  ###########################################")
        except Exception as e:
            self.logger.error(f"Error parsing {response.url}: {e}")
        finally:
            await page.close()
    
    def handle_error(self, failure):
        self.logger.error(f"Request failed: {failure.request.url}")
        self.logger.error(repr(failure))
    
    def closed(self, reason):
        self.barcalounge_file.close()
        self.logger.info("Spider closed: %s", reason)
 


# ----------------------------------------    RUN THE CODE   --------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    output_dir = 'utilities'
    os.makedirs(output_dir, exist_ok=True)
    # get_collections_products()
    # get_prod_html()
    process = CrawlerProcess()
    process.crawl(ProductSpider)
    process.start()