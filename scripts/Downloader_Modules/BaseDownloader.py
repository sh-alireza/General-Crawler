import os
import sqlite3
from collections import defaultdict
import yaml
from decouple import config
import logging
from logging.handlers import RotatingFileHandler

class BaseDownloader():
    def __init__(self,site_flag):
        self.save_path = config("SAVE_PATH")
        self.chromedriver_path = config("CHROMEDRIVER_PATH") 
        self.site_flag = site_flag
        databases = os.listdir("../data/databases")
        self.main_database = None
        for db in databases:
            if self.site_flag in db:
                self.main_database = db
                break
        if not self.main_database:
            raise Exception("No database in ../data/databases")
        
        self.main_db_path = os.path.join("../data/databases",self.main_database)
        
        # logger configuration
        format = logging.Formatter("%(asctime)s - %(lineno)d - %(levelname)s - %(message)s")
        self.logger = logging.getLogger('downloader_logger')
        self.logger.setLevel(logging.DEBUG)
        handler = RotatingFileHandler('../logs/downloader-logs/downloader.logs', mode="a", maxBytes=5000000, backupCount=5)
        handler.setFormatter(format)
        self.logger.addHandler(handler)
    
    def make_folder(self,folder_name):
        path = f"../data/downloaded_files/{self.site_flag}/{folder_name}"
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    
    def get_links_from_database(self,table,downloadables):
        connection = sqlite3.connect(self.main_db_path)
        cursor = connection.cursor()
        download_links = defaultdict(list)
        for col in downloadables:
            cursor.execute(f"SELECT {col} from {table}")
            data = cursor.fetchall()
            for d in data:
                try:
                    links = eval(d[0])
                except:
                    links = d[0]
                
                if not isinstance(links,list):
                    n = []
                    n.append(links)
                    links = n

                for l in links:
                    download_links[col].append(l)

        return download_links

    def check_download_type(self):
        
        pass
    