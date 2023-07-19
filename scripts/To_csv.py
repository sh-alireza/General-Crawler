import os
import csv
import sqlite3
from scripts.Crawler_Modules import BaseCrawler

class To_csv(BaseCrawler):
    
    def __init__(self,db_path):

        self.db_path = db_path

        if not os.path.exists(os.getcwd() + "/data/csv_files"):
            os.makedirs(os.getcwd() + "/data/csv_files")

    def get_info_from_database(self):
        
        if not os.path.exists(self.db_path):
            print("Database Not Found")
            return False

        conncetion = sqlite3.connect(self.db_path)
        cursor = conncetion.cursor()
        
        unfetched_data = cursor.execute("SELECT * from products")
        cols = []
        for col in unfetched_data.description:
            cols.append(col[0])
            
        fetched_data = cursor.fetchall()
        
        cursor.close()
        conncetion.close()
        
        return cols,fetched_data
    
    def handle(self):
        csv_name = os.path.basename(self.db_path)
        csv_file = open(os.getcwd() + f"/data/csv_files/{csv_name[:-3]}.csv","w")
        csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
        cols,data = self.get_info_from_database()
        csv_writer.writerow(cols)
        for row in data:
            csv_writer.writerow(list(row))
        csv_file.close()

