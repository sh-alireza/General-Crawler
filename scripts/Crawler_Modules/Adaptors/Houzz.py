import logging
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import yaml
from inquirer import errors
from inquirer.themes import GreenPassion
import inquirer
import sqlite3
from datetime import datetime
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from BaseCrawler import BaseCrawler


class Houzz(BaseCrawler):

    def __init__(self, config_path=None):
        super(Houzz, self).__init__()

        self.all_departments = {
            'bed': [
                'panel-beds',
                'sleigh-beds',
                'canopy-beds',
            ],

            'chair': [
                'armchairs-and-accent-chairs',
                'recliner-chairs',
                'rocking-chairs',
                'dining-chairs',
                'vanity-stools-and-benches',
                'bar-stools-and-counter-stools',
                'office-chairs',
                'outdoor-lounge-chairs',
                'outdoor-bar-stools',
                'outdoor-dining-chairs',
                'outdoor-rocking-chairs'
            ],

            'dresser': [
                'accent-chests-and-cabinets',
                'dressers',
                'nightstands-and-bedside-tables'
            ],

            'lamp': [
                'table-lamps',
                'floor-lamps',
                'desk-lamps',
                'lamp-sets',
                'chandeliers',
                'pendant-lighting',
                'flush-mount-ceiling-lighting',
                'kitchen-island-lighting',
                'track-lighting-kits',
                'pool-table-lights',
                'wall-sconces',
                'bathroom-lighting-and-vanity-lighting',
                'swing-arm-wall-lamps',
                'outdoor-wall-lights-and-sconces',
                'outdoor-hanging-lights'
            ],

            'sofa': [
                'sofas',
                'sectional-sofas',
                'love-seats',
                'futons',
                'sleeper-sofas',
                'outdoor-love-seats',
                'outdoor-sofas'
            ],

            'table': [
                'coffee-tables',
                'side-tables-and-accent-tables',
                'coffee-table-sets',
                'dining-tables',
                'desks',
                'outdoor-coffee-tables',
                'outdoor-side-tables',
                'outdoor-dining-tables'
            ]
        }
        deps = []
        # loop through all the departments and add them to the list
        for key in list(self.all_departments.keys()):
            deps += self.all_departments[key]
        self.all_styles = ['asian', 'contemporary', 'modern', 'transitional', 'craftsman', 'farmhouse', 'rustic',
                      'southwestern', 'midcentury', 'scandinavian', 'victorian', 'traditional', 'mediterranean', 'industrial', 'tropical']
        # if a config file is provided, read the data from it
        if config_path:
            file = open(config_path)
            data = yaml.load(file, Loader=yaml.loader.SafeLoader)
            file.close()
            self.limit = data["Limit"] or 1
            self.departments = data["Departments"] or ['panel-beds']
            self.styles = data["Styles"] or ['transitional']
            self.canada_shipment_filter = data["Canada_Shipment_Filter"] or "True"
        # if no config file is provided, ask the user for the data
        else:
            questions = [
                inquirer.Text('limit',
                              message='What do you prefer for the minimum number of objects per each class?',
                              default='1',
                              validate=self._limit_validate),
                inquirer.Checkbox('departments',
                                  message='Which departments do you want to crawl?',
                                  choices=deps,
                                  default=['panel-beds']
                                  ),
                inquirer.Checkbox('styles',
                                  message='Which styles do you want to crawl?',
                                  choices=self.all_styles,
                                  default=['transitional']
                                  ),
                inquirer.List('canada',
                              message='Do you want to filter your data by ship to canada?',
                              choices=[('yes', 'True'), ('no', 'False')],
                              default='yes'
                              )
            ]

            answers = inquirer.prompt(questions, theme=GreenPassion())
            self.limit = eval(answers["limit"])
            self.departments = answers["departments"]
            self.styles = answers["styles"]
            self.canada_shipment_filter = answers["canada"]

        self.database_path = os.path.join(os.getcwd(),"data/databases/database_houzz.db")
        
        self.values = list(self.all_departments.values())
        self.words = list(self.all_departments.keys())
        self.connection = sqlite3.connect(self.database_path)
        self.cursor = self.connection.cursor()

        self.cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY,product_title TEXT,\
            images TEXT,url VARCHAR(100),style VARCHAR(50),product_type VARCHAR(50),description TEXT,\
            rate FLOAT,review_count INT,price DOUBLE,shipping_canada INT,department TEXT,time timestamp)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS failed (id INTEGER PRIMARY KEY,main_link VARCHAR(100) NOT NULL,\
            error TEXT,time timestamp)")
        self.driver = webdriver.Chrome(
            self.chromedriver_path, options=self.options)
    # validate the limit input
    def _limit_validate(self, _, limit):

        try:
            if eval(limit) < 1:
                raise errors.ValidationError(
                    '', reason='your number is lower than 1')
        except:
            raise errors.ValidationError('', reason='it\'s not a number')
        return True
    # get the links of all the products in the page 
    def get_cards_from_site(self, link):
        self.logger.info(f"Houzz: Getting cards from {link}")
        self.driver.get(link)
        self.driver.refresh()

        time.sleep(5)

        try:
            self.driver.find_element(
                By.CLASS_NAME, "hz-take-consents__success-button").click()
            time.sleep(1)
        except:
            pass

        try:
            self.driver.find_element(
                By.CLASS_NAME, "hz-universal-search-header-tip__dismiss").click()
            time.sleep(1)
        except:
            pass

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'hz-product-card--medium')))

        cards = self.driver.find_elements(
            By.CLASS_NAME, "hz-product-card--medium")

        return cards
    # get the specifications of the product
    def get_card_specifications(self, card_link):
        self.logger.info(
            f"Houzz: Getting Specifications from this product: {card_link}")
        self.driver.get(card_link)
        self.driver.refresh

        try:
            velems = self.driver.find_elements(
                By.CLASS_NAME, "alt-video__thumb")
            
            if len(velems) == 0:
                raise Exception
            
            for velem in velems:
                self.driver.execute_script(
                    "arguments[0].setAttribute('style',arguments[1])", velem, "display:none;")

            velem_flag = True
            self.logger.info(
                f"Houzz: Found Video Elements in this product: {card_link}")
        except:
            velem_flag = False

            pass

        time.sleep(3)
        try:
            card_description = self.driver.find_element(
                By.CLASS_NAME, "hzui-tabs__content").find_element(By.CLASS_NAME, "slide-toggle").get_attribute("innerHTML")
            card_description = card_description.replace('"', "")
            card_description = card_description.replace("'", "")
            card_description = card_description.replace("}", "")
            card_description = card_description.replace("{", "")

            card_description = f"'{card_description}'"
        except:
            card_description = "NULL"

        tabs = self.driver.find_element(
            By.CLASS_NAME, "hzui-tabs__labels").find_elements(By.CLASS_NAME, "hzui-tabs__label")
        specs = tabs[1]
        specs.click()
        spec_items = self.driver.find_element(
            By.CLASS_NAME, "hzui-tabs__content").find_elements(By.CLASS_NAME, "product-spec-item")

        for spec_item in spec_items:
            if spec_item.find_element(By.CLASS_NAME, "product-spec-item-label").get_attribute("innerHTML").strip().lower() == "style":
                try:
                    style = spec_item.find_element(By.CLASS_NAME, "product-spec-item-value").find_element(
                        By.XPATH, "./*").get_attribute("innerHTML").strip().lower()
                except:
                    style = spec_item.find_element(
                        By.CLASS_NAME, "product-spec-item-value").get_attribute("innerHTML").strip().lower()
            else:
                style = "none"

            if style in self.all_styles:
                break
            
        if style == "none":
            return "continue"

        br_crumbs = self.driver.find_elements(
            By.CLASS_NAME, "hz-breadcrumb__link")
        dep = os.path.basename(br_crumbs[-1].get_attribute("href"))

        word = "none"

        for i, val in enumerate(self.values):
            if dep in val:
                word = self.words[i]
                break

        if word == "none":
            return "err"

        try:
            price = self.driver.find_element(
                By.CLASS_NAME, "pricing-info__original-price").get_attribute("innerHTML")
            price = price.replace(",", "")
            price = float(price.replace("$", ""))
        except:
            price = self.driver.find_element(
                By.CLASS_NAME, "pricing-info__price").get_attribute("innerHTML")
            price = price.replace(",", "")
            price = float(price.replace("$", ""))

        try:

            shipment_text = self.driver.find_element(
                By.CLASS_NAME, "unshippable-text--tertiary-text-grey").get_attribute("innerHTML")
            if "canada" in shipment_text.strip().lower():

                shipment_status = 0
            else:
                shipment_status = 1
        except:
            shipment_status = 1

        card_title = self.driver.find_element(
            By.CLASS_NAME, "view-product-title").get_attribute("innerHTML").strip()
        card_title = card_title.replace("'", "")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'carousel-alt-images__container--vertical')))
            small_pics = self.driver.find_element(
                By.CLASS_NAME, "carousel-alt-images__container--vertical").find_elements(By.CLASS_NAME, "alt-images__thumb")
        except:
            small_pics = []

        img_links = []
        for small_pic in small_pics:
            if velem_flag:
                if small_pic.get_attribute("style") == 'display: none;':
                    continue

            actions = ActionChains(self.driver)
            actions.move_to_element(small_pic)
            actions.perform()
            time.sleep(1)
            try:
                img_links.append(self.driver.find_element(By.CLASS_NAME, "carousel-alt-images__container--vertical").find_element(
                    By.XPATH, "..").find_element(By.CLASS_NAME, "view-product-image-print").get_attribute("src"))
            except:
                continue

        img_links = list(dict.fromkeys(img_links))

        if len(small_pics) == 0:
            sub_img_link = self.driver.find_element(
                By.CLASS_NAME, "zoom-pane-image").get_attribute("style")
            sub_img_link = sub_img_link[sub_img_link.find(
                "https"):sub_img_link.find('")')]
            img_links.append(sub_img_link)

        try:
            product_reviews = self.driver.find_element(By.ID, "productReviews")
            rate = float(product_reviews.find_element(
                By.CLASS_NAME, "reviews-summary__rating").get_attribute("innerHTML"))
            review_count_text = product_reviews.find_element(
                By.CLASS_NAME, "reviews-summary__total").get_attribute("innerHTML")
            review_count = [int(s)
                            for s in review_count_text.split() if s.isdigit()][0]
        except:
            rate = 'NULL'
            review_count = 'NULL'

        return [dep, word, card_title, shipment_status, card_description, style, price, img_links, rate, review_count]
    
    # insert data in database
    def insert_in_database(self, columns: list) -> None:

        # List of product's values
        card_title, img_links, card_link, style, word, card_description, rate, review_count, price, shipment_status, dep = columns

        # Convert image link list to string
        img_links = '"'+'","'.join(img_links)+'"'

        # Insert data into database
        self.cursor.execute(
            f"INSERT INTO products (product_title,images,url,style,product_type,description,rate,review_count,price,shipping_canada,department,time)\
                VALUES ('{card_title}','[{img_links}]','{card_link}','{style}','{word}',{card_description},{rate},{review_count},{price},{shipment_status},'{dep}','{datetime.now()}')")
        self.connection.commit()
    
    # loop on products on page
    def loop_on_cards(
            self,
            cards,
            count,
            main_dep,
            main_style
    ):

        for card in cards:

            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[1])
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            else:
                self.driver.switch_to.window(self.driver.window_handles[0])

            try:
                card_link = card.find_element(
                    By.CLASS_NAME, "ProductTitle__StyledLink-f609cb-0").get_attribute("href")
                title = card.find_element(By.CLASS_NAME, "ProductTitle__StyledLink-f609cb-0").find_element(
                    By.CLASS_NAME, "hz-color-link__text").get_attribute("innerHTML")
            except:
                continue

            self.cursor.execute(
                f"SELECT url from products WHERE url = '{card_link}'")

            if len(self.cursor.fetchall()) != 0:
                continue

            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])

            try:
                card_specifications = self.get_card_specifications(card_link)
                if card_specifications == "err":
                    self.logger.error(
                        f"Houzz: Error in card {card_link}: couldn't get the right word")
                    continue

                if card_specifications == "continue":
                    self.logger.error(
                        f"Houzz: Error in card {card_link}: couldn't get the right style")
                    continue

            except Exception as e:
                try:
                    self.logger.warning("Houzz: "+str(e))
                    self.cursor.execute(
                        f"INSERT INTO failed (main_link,error,time) VALUES ('{card_link}','{e}','{datetime.now()}')")
                    self.connection.commit()
                except:
                    pass

                if len(self.driver.window_handles) > 1:
                    self.driver.switch_to.window(self.driver.window_handles[1])
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                else:
                    self.driver.switch_to.window(self.driver.window_handles[0])
                continue

            dep, word, card_title, shipment_status, card_description, style, price, img_links, rate, review_count = card_specifications

            if main_dep != dep or main_style != style:
                continue

            time.sleep(0.5)

            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[1])
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            else:
                self.driver.switch_to.window(self.driver.window_handles[0])

            try:
                table_cols = [card_title, img_links, card_link, style, word,
                              card_description, rate, review_count, price, shipment_status, dep]
                self.insert_in_database(table_cols)

            except Exception as e:
                try:
                    self.logger.warning("Houzz: " + str(e))
                    self.cursor.execute(
                        f"INSERT INTO failed (main_link,error,time) VALUES ('{card_link}','{e}','{datetime.now()}')")
                    self.connection.commit()
                except:
                    pass

                continue

            self.logger.info(f"Houzz: {count} - {card_link}")
            count += 1
            if count >= self.limit:
                break

        return count
    
    # scrape page and loop on products 
    def scrape_page(self, page_number, count, main_dep, main_style):
        if self.canada_shipment_filter == "True":
            url = f"https://www.houzz.com/products/{main_style}/{main_dep}/ship-to-country--canada/p/{page_number*36}"
        else:
            url = f"https://www.houzz.com/products/{main_style}/{main_dep}/p/{page_number*36}"

        self.logger.info(f"Houzz: Scraping page {url}")

        try:
            cards = self.get_cards_from_site(url)
        except Exception as e:
            self.logger.warning("Houzz: " + str(e))
            time.sleep(30)
            if "session" in str(e):
                try:
                    self.driver = webdriver.Chrome(
                        self.chromedriver_path, options=self.options)
                    cards = self.get_cards_from_site(url)
                except:
                    pass

            return count

        if len(cards) != 0:
            count = self.loop_on_cards(cards, count, main_dep, main_style)
            
        return count
    # main function
    def handle(self):

        for main_dep in self.departments:
            for main_style in self.styles:
                page_number = 0
                count = 0
                while count < self.limit:
                    count = self.scrape_page(
                        page_number, count, main_dep, main_style)
                    page_number += 1
                    if page_number > 10:
                        break
