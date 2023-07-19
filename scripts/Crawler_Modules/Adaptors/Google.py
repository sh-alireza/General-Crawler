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
import pdb
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from BaseCrawler import BaseCrawler


class Google(BaseCrawler):
    
    def __init__(self,config_path=None):
        super(Google,self).__init__()
        
        if config_path:
            file = open(config_path)
            data = yaml.load(file, Loader=yaml.loader.SafeLoader)
            file.close()
            self.limit = data["Limit"] or 1
            self.search_queries = data["Search_Queries"] or ["Google"]
        # if no config file is provided, ask the user for the data
        else:
            questions = [

                inquirer.Text('queries',
                              message='Write a list of queries to search in google. (devide them by "," e.g. query1,query2,query3)',
                              default='q1,q2'),
                inquirer.Text('limit',
                              message='What do you prefer for the minimum number of pictures per each query?',
                              default='1',
                              validate=self._limit_validate)
            ]
            
            answers = inquirer.prompt(questions, theme=GreenPassion())

            self.search_queries = answers['queries'].split(",")
            self.limit = eval(answers["limit"])
            

        self.database_path = os.path.join(os.getcwd(),"data/databases/database_google.db")
        self.connection = sqlite3.connect(self.database_path)
        self.cursor = self.connection.cursor()
        
        self.cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY,search_query TEXT,images TEXT,title TEXT,source TEXT,time timestamp)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS failed (id INTEGER PRIMARY KEY,error TEXT,search_query TEXT,images TEXT,title TEXT,time timestamp)")
        
        self.driver = webdriver.Chrome(
            self.chromedriver_path, options=self.options)
        
        
    def _limit_validate(self, _, limit):
        try:
            if eval(limit) < 1:
                raise errors.ValidationError(
                    '', reason='your number is lower than 1')
        except:
            raise errors.ValidationError('', reason='it\'s not a number')
        return True

    def insert_in_database(self, cols):
        query, images, title, source = cols
        self.cursor.execute(f"SELECT * FROM products WHERE search_query='{query}' AND images='{images}'")
        if len(self.cursor.fetchall()) != 0:
            return "false"
        try:
            self.cursor.execute(f"INSERT INTO products (search_query,images,title,source,time) VALUES ('{query}','{images}','{title}',\
                '{source}','{datetime.now()}')")
        except Exception as e:
            e = str(e).replace("'", "")
            e = e.replace('"', "")
            
            self.cursor.execute(f"INSERT INTO failed (error,search_query,images,title,time) VALUES ('{e}',\
                '{query}','{images}','{title}','{datetime.now()}')")

        self.connection.commit()
        return "true"

    def loop_on_cards(self, cards, query):
        count = 0
        for card in cards:
            card.click()
            time.sleep(5)
            card_data = self.driver.find_elements(By.CLASS_NAME, "KAlRDb")
            if len(card_data) == 1:
                card_data = card_data[0]
            else:
                continue
            
            
            images = card_data.get_attribute("src")
            title = card_data.get_attribute("alt")
            title = title.replace("'", "")
            title = title.replace('"', "")
            
            source = card_data.find_element(By.XPATH,"..").get_attribute("href")
            
            cols = [query, images, title, source]
            out = self.insert_in_database(cols)
            
            if out == "false":
                continue
            
            count += 1
            if count >= self.limit:
                break
        
        
    def handle(self):
        for query in self.search_queries:
            query = query.replace(" ", "+").lower().strip()
            self.driver.get(
                f'https://www.google.com/search?q={query}&tbm=isch')
            count = 0
            while count <= self.limit:
                last_height = self.driver.execute_script(
                    "return document.documentElement.scrollHeight")
                self.driver.execute_script(
                    f"window.scrollTo(0, {last_height});")
                time.sleep(3)
                
                cards = self.driver.find_elements(
                    By.CLASS_NAME, "BUooTd")
                
                count = len(cards)
                
            self.loop_on_cards(cards, query)
            print("next query")
