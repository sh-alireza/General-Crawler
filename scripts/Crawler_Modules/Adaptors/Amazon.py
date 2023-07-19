import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from BaseCrawler import BaseCrawler
from datetime import datetime
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
import  sqlite3
import yaml
import inquirer
from inquirer.themes import GreenPassion
from inquirer import errors


class Amazon(BaseCrawler):
    
    def __init__(self,config_path=None):
        super().__init__()
        
        self.departments = {
            'bed':3248804011,
            'chair':3733821,
            'dresser':1063306,
            'lamp':3736561,
            'sofa':1063318,
            'table':1055398
        }
        # get configuration
        if config_path:
            file = open(config_path)
            data = yaml.load(file, Loader=yaml.loader.SafeLoader)
            file.close()
            self.limit = data["Limit"] or 1
            self.words = data["Words"] or ["bed"]
            self.canada_shipment_filter = data["Canada_Shipment_Filter"]
        # if no configuration file is provided then ask the user for the configuration
        else:
            questions = [
                inquirer.Text('limit',
                                message='What do you prefer for the minimum number of objects per each class?',
                                default='1',
                                validate = self._limit_validate),
                inquirer.Checkbox('words',
                                message='Which departments do you want to crawl?',
                                choices=['bed','chair','dresser','lamp','sofa','table'],
                                default=['bed']
                                ),
                inquirer.List('canada',
                                message='Do you want to filter your data by ship to canada?',
                                choices=[('yes','True'),('no','False')],
                                default='yes'
                                )
            ]
            answers = inquirer.prompt(questions, theme=GreenPassion())
            self.limit = eval(answers["limit"])
            self.words = answers["words"]
            self.canada_shipment_filter = answers["canada"]
        
        self.database_path = os.path.join(os.getcwd(),"data/databases/database_amazon.db")
        
        self.connection = sqlite3.connect(self.database_path)
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY,product_title TEXT,\
            images TEXT,url VARCHAR(100),style VARCHAR(50),product_type VARCHAR(50),description TEXT,\
            rate FLOAT,review_count INT,price DOUBLE,shipping_canada INT,department TEXT,time timestamp)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS failed (id INTEGER PRIMARY KEY,main_link VARCHAR(100) NOT NULL,\
            error TEXT,time timestamp)")


        self.driver = webdriver.Chrome(self.chromedriver_path, options=self.options)
    
    def _limit_validate(self,_,limit):
        try:
            if eval(limit) < 1:
                raise errors.ValidationError('', reason='your number is lower than 1')
        except:
            raise errors.ValidationError('', reason='it\'s not a number')
        return True
    
    def check_canada(self,url,canada):
        
        while canada == "True":
            try:
                time.sleep(2)
                self.driver.find_element(By.ID,"nav-global-location-popover-link").click()
                time.sleep(3)
                self.driver.find_element(By.ID,"GLUXCountryListDropdown").click()
                time.sleep(2)
                self.driver.find_element(By.ID,"GLUXCountryList_45").click()
                time.sleep(2)
                self.driver.find_element(By.NAME,"glowDoneButton").click()
                time.sleep(2.5)
                canada = "False"
            except:
                self.logger.info('Amazon: net problem')
                self.driver.get(url)
        self.logger.info("Amazon: canada filter done")

    def get_cards_from_site(self,url,canada):
        self.driver.get(url)
        self.driver.get(url)
        self.check_canada(url,canada)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 's-product-image-container')))
        
        time.sleep(2.5)

        cards = self.driver.find_elements(By.CLASS_NAME,"s-product-image-container")
        return cards
    
    def get_card_specifications(self,card_link,word):
        
        # time.sleep(randrange(23,127))
        self.driver.get(card_link)
        self.driver.get(card_link)
        
        try:
            price_els = self.driver.find_element(By.ID,"corePriceDisplay_desktop_feature_div").find_elements(By.CLASS_NAME,"a-offscreen")
            prices = []
            for price in price_els:
                price = price.get_attribute("innerHTML")
                price = price.replace(",","")
                price = float(price.replace("$",""))
                prices.append(price)
            price = max(prices)

        except:
            price = 0.0

        time.sleep(1)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.ID, 'productDetails_detailBullets_sections1')))

        style_title = self.driver.find_element(By.ID,"productDetails_detailBullets_sections1").find_elements(By.CLASS_NAME,"prodDetSectionEntry")

        for elem in style_title:
            try:
                if elem.get_attribute("innerHTML").strip().lower() == "style":
                    style = elem.find_element(By.XPATH,"..").find_element(By.CLASS_NAME,"prodDetAttrValue").get_attribute("innerHTML").strip().lower().encode('ascii', 'ignore').decode("utf-8")
                    
                    break
                else:
                    style="none"
            except:
                style="none"
                
                continue
        
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.ID, 'feature-bullets')))

        desc_rows = self.driver.find_element(By.ID,"feature-bullets").find_elements(By.CLASS_NAME,"a-spacing-small")
        a = ""

        for desc in desc_rows:
            a += f"<li>{desc.get_attribute('innerHTML')}</li>"

        card_description = f"<ul>{a}</ul>"
        card_description = card_description.replace("'","")
        card_description = card_description.replace('"',"")
        card_description = f"'{card_description}'"
        
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.ID, 'main-image-container')))

        card_title = self.driver.find_element(By.ID,"productTitle").get_attribute("innerHTML").strip()
        review_count = self.driver.find_element(By.ID,"acrCustomerReviewText").get_attribute("innerHTML").strip().lower()
        review_count =  review_count.replace(",","")
        review_count = int(review_count.replace(" ratings",""))
        rate = self.driver.find_element(By.ID,"reviewsMedley").find_element(By.CLASS_NAME,"AverageCustomerReviews").find_element(By.CLASS_NAME,"a-size-medium").get_attribute("innerHTML")
        rate = float(rate.replace(" out of 5",""))

        img_links = []
        small_pics = self.driver.find_element(By.ID,"altImages").find_elements(By.CLASS_NAME,"imageThumbnail")

        for small_pic in small_pics:

            actions = ActionChains(self.driver)
            actions.move_to_element(small_pic)
            actions.perform()
            time.sleep(0.3)

        for i in range(10):
            try:
                img_link = self.driver.find_element(By.ID,"main-image-container").find_element(By.CLASS_NAME,f"itemNo{i}").find_element(By.CLASS_NAME,"a-dynamic-image").get_attribute("data-old-hires")
                img_links.append(img_link)
            except:
                pass
        
        img_links = list(dict.fromkeys(img_links))
        if self.canada_shipment_filter == "True":
            shipment_status = 1
        else:
            shipment_status = 0
        
        return [card_title,img_links,card_link,style,word,card_description,rate,review_count,price,shipment_status,str(self.departments[word])]
    
    def insert_in_database(self,columns):
        
        card_title,img_links,card_link,style,word,card_description,rate,review_count,price,shipment_status,dep = columns 
        img_links = '"'+'","'.join(img_links)+'"'
        self.cursor.execute(f"INSERT INTO products (product_title,images,url,style,product_type,description,rate,review_count,price,shipping_canada,department,time)\
            VALUES ('{card_title}','[{img_links}]','{card_link}','{style}','{word}',{card_description},{rate},{review_count},{price},{shipment_status},'{dep}','{datetime.now()}')")
        self.connection.commit()

    def loop_on_cards(self,cards,count,word,dep):
        
        for i,card in enumerate(cards):
                
            while len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[-1])
           
            try:
                card_link = card.find_element(By.CLASS_NAME,"a-link-normal").get_attribute("href")
            except Exception as e:
                continue

            card_link = card_link[:(card_link.find("ref="))]
            print(card_link)
            self.cursor.execute(f"SELECT url from products WHERE url = '{card_link}'")

            if len(self.cursor.fetchall()) !=0:
                continue

            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])

            try:
                card_specifications = self.get_card_specifications(card_link,word)

            except Exception as e:
                try:
                    card_specifications = self.get_card_specifications(card_link,word)
                except:

                    try:
                        print(e)
                        self.cursor.execute(f"INSERT INTO failed VALUES ('{card_link}','product','{e}','{dep}','{datetime.now()}')")
                        self.connection.commit()
                    except:
                        print(card_link)
                        continue

            time.sleep(1)

            try:
                self.insert_in_database(card_specifications)
                
            except Exception as e:

                try:
                    print(e)
                    self.cursor.execute(f"INSERT INTO failed (main_link,error,time) VALUES ('{card_link}','{e}','{datetime.now()}')")
                    self.connection.commit()
                except:
                    print(card_link)
                    
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

                continue

            count+=1
            
            if count >= self.limit:
                break
        return count

    def handle(self):
        
        for word in self.words:
            page_number = 0
            count = 0
            canada = self.canada_shipment_filter
            
            while count < self.limit:
                
                if page_number == 0:
                    url = f"https://www.amazon.com/s?k={word}&rh=n%3A{self.departments[word]}&s=review-rank"
                else:
                    url = f"https://www.amazon.com/s?k={word}&rh=n%3A{self.departments[word]}&page={page_number+1}&s=review-rank"
                
                print(url)
                print(count)
                
                try:
                    cards = self.get_cards_from_site(url,canada)
                except:
                    time.sleep(30)
                    try:
                        cards = self.get_cards_from_site(url,canada)
                    except Exception as e:
                        print(e)
                        page_number +=1
                        if page_number > 10:
                            break
                        continue
                
                if len(cards) == 0:
                    break
                
                count = self.loop_on_cards(cards,count,word,str(self.departments[word]))
                
                page_number +=1
            
            while len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[-1])

