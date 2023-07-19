import os
import sqlite3
from collections import defaultdict
from decouple import config
import logging
from logging.handlers import RotatingFileHandler

class BaseDownloader():
    def __init__(self,site_flag):
        self.save_path = os.path.join(os.getcwd(), config("SAVE_PATH"))
        self.chromedriver_path = os.path.join(os.getcwd(), config("CHROMEDRIVER_PATH"))
        self.site_flag = site_flag
        databases = os.listdir(os.path.join(os.getcwd(),"data/databases"))
        self.main_database = None
        for db in databases:
            if self.site_flag in db:
                self.main_database = db
                break
        if not self.main_database:
            raise Exception("No database in /data/databases")
        
        self.main_db_path = os.path.join(os.getcwd(),"data/databases",self.main_database)
        
        # logger configuration
        format = logging.Formatter("%(asctime)s - %(lineno)d - %(levelname)s - %(message)s")
        self.logger = logging.getLogger('downloader_logger')
        self.logger.setLevel(logging.DEBUG)
        
        if not os.path.exists(os.getcwd() + "/logs/downloader-logs"):
            os.makedirs(os.getcwd() + "/logs/downloader-logs")
            
        if not os.path.exists(os.getcwd() + "/data/downloaded_files"):
            os.makedirs(os.getcwd() + "/data/downloaded_files")
            
        handler = RotatingFileHandler(os.getcwd()+'/logs/downloader-logs/downloader.logs', mode="a", maxBytes=5000000, backupCount=5)
        handler.setFormatter(format)
        self.logger.addHandler(handler)
    
    def make_folder(self,folder_name):
        path = os.getcwd() + f"/data/downloaded_files/{self.site_flag}/{folder_name}"
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    
    def get_links_from_database(self,table,downloadables):
        connection = sqlite3.connect(self.main_db_path)
        cursor = connection.cursor()
        download_links = defaultdict(list)
        self.logger.info(f"Getting {table} links from database")
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
    