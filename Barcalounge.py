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
    # url = "https://www.barcalounger.com/view-all-options/langston-power-lift-recline?attribute_pa_covers=venzia-blue"
    url = "https://www.barcalounger.com/view-all-options/monico?attribute_pa_covers=ashland-granite"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url)
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        with open("product.html", "w", encoding="utf-8") as file:
            file.write(soup.prettify())



        product_description_div = soup.find("div",  class_ = 'woocommerce-product-details__short-description')
        if product_description_div:
            product_description = product_description_div.find("p").text.strip()

        else:
            product_description=""

        print("------------")
        print(product_description)



        scraped_data = {}
        tables = soup.find_all('table', class_='shop_attributes product_meta')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                header = row.find('th').get_text(strip=True) if row.find('th') else None
                data = row.find('td').get_text(strip=True) if row.find('td') else None
                if header and data:
                    scraped_data[header] = data

        print(scraped_data)
        print("----------")
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
                dimensions__li = dimensions__ul.find_all("li")
                if dimensions__li:
                    width = []
                    height = []
                    depth = []
                    for li in dimensions__li:
                        text = li.get_text(strip=True)
                        # print(text)
                        if ":" in text:
                            name, dims = text.split(":", 1)
                            dims = dims.strip().split(" x ")
                            # print(dims)
                            
                            if len(dims) == 3:
                                width.append(dims[0])
                                # print(width)
                                depth.append(dims[1])
                                height.append(dims[2])
                    width = "; ".join(width)
                    depth = "; ".join(depth)
                    height = "; ".join(height)
        print("------------------------------------")
        print("Width", width)
        print("Depth", depth)
        print("Height", height)
    


        sku = scraped_data.pop('SKU', None) 
        scraped_data.pop('Price', None)
        remaining_data_str= ",   ".join([f"{k}: {v}" for k, v in scraped_data.items()])

        print("-------------------------")
        print("SKU:", sku)
        print("---------------------------")
        print("Remaining Data:", remaining_data_str)
        p_dsiclamer = soup.select(".disclaimer p")
        disclamer = p_dsiclamer[-1].get_text(strip=True) if p_dsiclamer else None
        print("---------------------------------------------")
        print(disclamer)





        product_images = soup.select("img.iconic-woothumbs-thumbnails__image.no-lazyload.skip-lazy")
        if product_images:                  
            product_images = [
                (img.replace("180x180", "500x500") if "500x500" in item.get("data-srcset", "") else img)
                for item in product_images
                if (img := item.get("data-lazy") or item.get("src"))
            ]
            print("--------------------------------------------")
            print(len(product_images))
            print(product_images)





        collection = soup.find("h1", class_ = "product_title entry-title")
        collection = collection.text.strip()

        print("--------------")
        print(collection)


        assembly_pdf = soup.find("a", class_ = "assembly-instructions")
        if assembly_pdf:
            assembly_pdf = assembly_pdf.get("href")
        else:
            assembly_pdf = ""

        print("---------------")
        print(assembly_pdf)


# --------------------------------------------------------------------------------------------------------------------------------------------

class ProductSpider(scrapy.Spider):
    name = "product_spider"
    custom_settings = {
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
        self.bassett_mirror_company_file = open('output/bassett_mirror_companye.csv', 'w', newline='', encoding='utf-8')

        self.bassett_mirror_company_writer = csv.DictWriter(self.bassett_mirror_company_file, fieldnames=self.columns)

        self.bassett_mirror_company_writer.writeheader()


    def start_requests(self):
        self.logger.info("Spider started. Reading product links from CSV file.")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield scrapy.Request(
                    url=row['product_link'],
                    callback=self.parse,
                    meta={
                        'product_link': row['product_link']
                    }
                )
    def parse(self, response):
        self.logger.info(f"Parsing product: {response.url}")
        sku = ""
        product_title = ""
        width = ""
        depth = ""
        height = ""
        description = ""
        material = ""
        finish = ""
        category1 = ""
        category2 = ""
        category3 = ""
        collection = ''
        products_images = []
        product_description = ""
        specifications = ""
        specifications_str = ""
        catalog_pdf = ""
        try:
            meta = response.meta
            soup = BeautifulSoup(response.text, 'html.parser')

            data = {col: "" for col in self.columns} 


            try:
                spec = soup.find('div', class_="spec").get_text().strip()
                clean_spec = spec.replace('\xa0', ' ')
                if "|" in clean_spec:
                    sku, dim = clean_spec.split("|")
                    sku = sku.strip()
                    dim = dim.strip()
                    dims = dim.split("x")
                    if len(dims)==3:
                        width, depth, height = dims
                    elif len(dims)==2:
                        width, height = dims
                else:
                    sku = clean_spec
                    width, depth, height = ""
 
            except Exception as e:
                print("An error occurred while extracting SKU:", str(e))


            try:
                product_title = soup.find("span", class_ = "pageTitle")
                if product_title:
                    product_title = product_title.text.strip()
            except AttributeError:
                product_title = ""

            try:
                description_container = soup.find("div", class_="col span_1_of_3")
                if description_container:
                    description_paragraph = description_container.find("p")
                    if description_paragraph:
                        product_description = description_paragraph.get_text(strip=True)
            except AttributeError:
                product_description = ""

            try:
                specifiation_div = soup.find("div", class_ = "panel" )
                specifications = {}
                if specifiation_div:
                    items = specifiation_div.find_all('li')
                    if items:
                        for item in items:
                            key, value = item.get_text().split(":", 1)
                            specifications[key] = value

                if specifications:
                    style = specifications.get("Style", None)
                    material = specifications.get("Material", None)
                    finish = specifications.get("Color/Finish", None)
                specifications_str = "; ".join([f"{k}: {v}" for k, v in specifications.items()])
            except AttributeError:
                specifications_str = ""

            paths_div = soup.find("div", class_ = "master-width breadcrumbs")
            if paths_div:
                paths_span = paths_div.find("span", class_ = "breadcrumbs")
                if paths_span:
                    paths = paths_span.get_text(strip = True).split("/")

                    if len(paths) ==4:
                        category1 = paths[0]
                        category2 = paths[1]
                        category3 = paths[2]
                        collection = paths[3]
                    elif len(paths)==3:
                        category1 = paths[0]
                        category2 = paths[1]
                        collection = paths[2]

            try:
                description_div = soup.find('div', class_ = 'spec spec_desc')
                description = []
                if description_div:
                    description_items = description_div.find_all("td")
                    if description_items:
                        for item in description_items:
                            description.append(item.get_text(strip = True))
            except AttributeError:
                description = ""
               
            try:
                catalog_pdf = soup.find('a', class_ = "btn-tearsheet")
                if catalog_pdf:
                    catalog_pdf = catalog_pdf.get("href")
            except:
                catalog_pdf = ""

            data.update({
                "CATEGORY1": category1,
                "CATEGORY2": category2,
                "CATEGORY3": category3,
                "COLLECTION": collection,
                "ITEM_URL": meta['product_link'],
                "SKU": sku,
                "DESCRIPTION": ", ".join(description) if isinstance(description, list) else description,
                "PRODUCT_DESCRIPTION": product_description,
                "WIDTH": width,
                "DEPTH": depth,
                "HEIGHT": height,
                "STYLE": style,
                "ADDITIONAL_INFORMATION": material,
                "FINISH1": finish,
                "CONSTRUCTION": "", 
                "SPECIFICATIONS": specifications_str,
                "BRAND": "Bassett Mirror",
                "VIEWTYPE": "Normal",  
                "CATALOG_PDF" : catalog_pdf, 
            })

            try:
                image_urls = []
                gallery_div = soup.find("div", id="gallery")
                if gallery_div:
                    image_divs = gallery_div.find_all("div", class_="tn")
                    for div in image_divs:
                        st = div.get("style")
                        if st:
                            url_match = re.search(r'background-image:url\((.*?)\);', st)
                            if url_match:
                                image_urls.append(url_match.group(1))
                                products_images = image_urls
            except AttributeError:
                products_images = []

            if len(products_images) == 0:
                img_url = soup.find("div", id = "main-image")
                if img_url:
                    img_url = img_url.get("style")
                    img_url = re.search(r'background-image:url\((.*?)\);', img_url)
                    img_url = img_url.group(1)
                    products_images.append(img_url)
                
            for i in range(1, 11):
                data[f"PHOTO{i}"] = ""
            for idx, img_url in enumerate(products_images):
                if idx > 9:
                    continue
                else:
                    data[f"PHOTO{idx + 1}"] = img_url
            if len(products_images) < 10:
                self.logger.info(f"Only {len(products_images)} images found for {meta['product_link']}. Remaining PHOTO columns will be ''.")
            elif len(products_images) > 10:
                self.logger.warning(f"More than 10 images found for {meta['product_link']}. Only the first 10 will be saved.")

            if len(products_images) == 0:
                data.update({
                    "VIEWTYPE": "Limited",
                })

            if sku:
                self.bassett_mirror_company_writer.writerow(data)
                self.logger.info(f"Successfully scraped and categorized product: {meta['product_link']}")
            else:
                self.logger.info("############################ Missing SKU Detected  ###########################################")
                self.logger.info(soup.find('div', class_="spec").get_text().strip())
                self.logger.info("Product link : ", meta['product_link'])
                self.logger.info("############################ Missing SKU Detected  ###########################################")
        except Exception as e:
            self.logger.error(f"Error parsing product: {response.url}, {e}")

    def closed(self, reason):
        self.bassett_mirror_company_file.close()
        self.logger.info("Spider closed. Files saved.")
 


# ----------------------------------------    RUN THE CODE   --------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    output_dir = 'utilities'
    os.makedirs(output_dir, exist_ok=True)
    # get_collections_products()
    get_prod_html()
    # process = CrawlerProcess()
    # process.crawl(ProductSpider)
    # process.start()