import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from BaseDownloader import BaseDownloader
import requests
from PIL import Image, ImageOps
from datetime import datetime
from uuid import uuid4

class Image_Downloader(BaseDownloader):
    
    def __init__(self,site_flag):
        super(Image_Downloader, self).__init__(site_flag)

    def download_links(self,links_dict):
        
        for col in list(links_dict.keys()):
            path = self.make_folder(col)
            
            if not os.path.exists(path):
                self.logger.error("something's wrong with save_path")
            self.logger.info(f"Downloading {col} files")
            for i,link in enumerate(links_dict[col]):
                
                try:
                    response = requests.get(link,stream=True)
                except:
                    self.logger.error(f"Error downloading {link}")
                    continue
                
                d_name = datetime.now().strftime('%Y%m-%d%H-%M%S-') + str(uuid4())
                
                if i == 0:
                    d_name+="_main"
                
                image = Image.open(response.raw)
                image = ImageOps.exif_transpose(image)
                image = image.convert("RGB")
                image.save(os.path.join(path,d_name+".jpg"))
            self.logger.info(f"Downloaded {col} files")
    
    def handle(self):
        download_links = self.get_links_from_database("products",["images"])
        self.download_links(download_links)

