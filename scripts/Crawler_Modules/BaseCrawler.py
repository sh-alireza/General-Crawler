from selenium import webdriver
from decouple import config
import logging
from logging.handlers import RotatingFileHandler



class BaseCrawler():
    '''Base class for all crawlers.'''
    # init method or constructor
    def __init__(self):
        
        self.save_path = config("SAVE_PATH")
        self.chromedriver_path = config("CHROMEDRIVER_PATH")
        
        # driver configuration
        self.options = webdriver.ChromeOptions()
        self.options.headless = False
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--no-sandbox")
        
        # logger configuration
        format = logging.Formatter("%(asctime)s - %(lineno)d - %(levelname)s - %(message)s")
        self.logger = logging.getLogger('crawler_logger')
        self.logger.setLevel(logging.DEBUG)
        handler = RotatingFileHandler('../logs/crawler-logs/crawler.logs', mode="a", maxBytes=5000000, backupCount=5)
        handler.setFormatter(format)
        self.logger.addHandler(handler)
        
    def insert_in_database(self):
        raise NotImplementedError

    def get_cards_from_site(self):
        raise NotImplementedError
    
    def get_config(self):
        raise NotImplementedError
    
    def get_card_specifications(self):
        raise NotImplementedError

    def loop_on_cards(self):
        raise NotImplementedError
    
    def getConfig(self):
        raise NotImplementedError
