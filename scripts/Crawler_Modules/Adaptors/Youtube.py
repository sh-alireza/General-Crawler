from inquirer import errors
from inquirer.themes import GreenPassion
import inquirer
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import sqlite3
import yaml
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from BaseCrawler import BaseCrawler


class Youtube(BaseCrawler):

    def __init__(self, config_path=None):
        super(Youtube, self).__init__()

        if config_path:
            file = open(config_path)
            data = yaml.load(file, Loader=yaml.loader.SafeLoader)
            file.close()
            self.search_queries = data["Search_Queries"] or ["this is a default query"]
            self.limit = data["Limit"] or 1

        else:
            questions = [

                inquirer.Text('queries',
                              message='Write a list of queries to search in youtueb. (devide them by "," e.g. query1,query2,query3)',
                              default='q1,q2'),
                inquirer.Text('limit',
                              message='What do you prefer for the minimum number of videos per each query?',
                              default='1',
                              validate=self._limit_validate)
            ]

            answers = inquirer.prompt(questions, theme=GreenPassion())

            self.search_queries = answers['queries'].split(",")
            self.limit = eval(answers["limit"])

        self.database_path = "../data/databases/database_youtube.db"
        self.connection = sqlite3.connect(self.database_path)
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS videos (id INTEGER PRIMARY KEY,search_query TEXT,video_link TEXT,title TEXT,account_id TEXT,\
            account_sub_count INT,video_likes INT,views INT,upload_date TEXT,time timestamp)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS failed (id INTEGER PRIMARY KEY,error TEXT,search_query TEXT,\
            video_link TEXT,title TEXT,time timestamp)")
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

    def _to_integer(self, input):

        if "k" in input:
            input = eval(input[:-1])*1000
        elif "m" in input:
            input = eval(input[:-1])*1000000
        else:
            input = eval(input)
        return input

    def get_card_specifications(self, card_link):
        self.driver.get(card_link)
        time.sleep(3)

        try:
            title = self.driver.find_element(By.ID, "below").find_element(By.ID, "above-the-fold").\
                find_element(By.ID, "title").find_element(By.TAG_NAME, "h1").find_element(By.TAG_NAME, "yt-formatted-string")\
                .get_attribute("innerHTML")
            title = title.replace("'", "")
            title = title.replace('"', '')
            account_id = self.driver.find_element(By.ID, "below").find_element(By.ID, "above-the-fold").find_element(By.ID, "top-row")\
                .find_element(By.ID, "owner").find_element(By.TAG_NAME, "ytd-video-owner-renderer").find_element(By.ID, "upload-info")\
                .find_element(By.ID, "channel-name").find_element(By.ID, "container").find_element(By.TAG_NAME, "a").get_attribute("href")
            account_sub_count = self.driver.find_element(By.ID, "below").find_element(By.ID, "above-the-fold").find_element(By.ID, "top-row")\
                .find_element(By.ID, "owner").find_element(By.TAG_NAME, "ytd-video-owner-renderer").find_element(By.ID, "upload-info")\
                .find_element(By.ID, "owner-sub-count").get_attribute("innerHTML")
            account_sub_count = account_sub_count.split()[0].strip().lower()

            account_sub_count = self._to_integer(account_sub_count)

            video_likes = self.driver.find_element(By.ID, "below").find_element(By.ID, "above-the-fold").find_element(By.ID, "top-row")\
                .find_element(By.ID, "segmented-like-button").find_element(By.CLASS_NAME, "yt-spec-button-shape-next--button-text-content")\
                .find_element(By.TAG_NAME, "span").get_attribute("innerHTML")

            video_likes = video_likes.strip().lower()
            video_likes = self._to_integer(video_likes)

            views_elem = self.driver.find_element(By.ID, "below").find_element(By.ID, "above-the-fold").find_element(By.ID, "bottom-row")\
                .find_element(By.ID, "description-inner").find_element(By.ID, "info").find_elements(By.TAG_NAME, "span")
            views_date = ""
            for elm in views_elem:
                views_date += elm.get_attribute("innerHTML")

            views = views_date.split("views")[0].strip()
            views = views.strip().lower()
            views = self._to_integer(views)

            upload_date = views_date.split("views")[1].strip()
        except:
            return "continue"

        return title, account_id, account_sub_count, video_likes, views, upload_date

    def insert_in_database(self, cols):
        query, card_link, title, account_id, account_sub_count, video_likes, views, upload_date = cols
        try:
            self.cursor.execute(f"INSERT INTO videos (search_query,video_link,title,account_id,account_sub_count,\
                video_likes,views,upload_date,time) VALUES ('{query}','{card_link}','{title}',\
                '{account_id}',{account_sub_count},{video_likes},{views},'{upload_date}','{datetime.now()}')")
        except Exception as e:
            self.cursor.execute(f"INSERT INTO failed (error,search_query,video_link,title,time) VALUES ('{e}',\
                '{query}','{card_link}','{title}','{datetime.now()}')")

        self.connection.commit()

    def loop_on_cards(self, cards, query):
        count = 0
        for card in cards:

            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[1])
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            else:
                self.driver.switch_to.window(self.driver.window_handles[0])

            card_link = card.find_element(
                By.ID, "video-title").get_attribute("href")

            self.cursor.execute(
                f"SELECT video_link from videos WHERE video_link = '{card_link}'")
            if len(self.cursor.fetchall()) > 0:
                continue

            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])
            card_specs = self.get_card_specifications(card_link)
            if card_specs == "continue":
                continue

            title, account_id, account_sub_count, video_likes, views, upload_date = card_specs
            cols = [query, card_link, title, account_id,
                    account_sub_count, video_likes, views, upload_date]

            self.insert_in_database(cols)
            count += 1
            if count >= self.limit:
                break

    def handle(self):

        for query in self.search_queries:
            query = query.replace(" ", "+").lower().strip()

            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[1])
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            else:
                self.driver.switch_to.window(self.driver.window_handles[0])

            self.driver.get(
                f'https://www.youtube.com/results?search_query={query}&sp=EgIQAQ%253D%253D')
            count = 0
            while count <= self.limit:
                last_height = self.driver.execute_script(
                    "return document.documentElement.scrollHeight")
                self.driver.execute_script(
                    f"window.scrollTo(0, {last_height});")
                time.sleep(3)

                cards_cells = self.driver.find_elements(
                    By.TAG_NAME, "ytd-item-section-renderer")
                cards = []
                for cell in cards_cells:
                    cardss = cell.find_element(By.ID, "contents").find_elements(
                        By.TAG_NAME, "ytd-video-renderer")
                    for card in cardss:
                        cards.append(card)
                count = len(cards)

            self.loop_on_cards(cards[:self.limit], query)
            print("next query")
        return
