import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from BaseDownloader import BaseDownloader
import yt_dlp
import random
import inquirer
from inquirer.themes import GreenPassion
from inquirer import errors

class Youtube_Downloader(BaseDownloader):

    def __init__(self,site_flag):
        super(Youtube_Downloader,self).__init__(site_flag)
        questions = [
                inquirer.List('type',
                                message='Choose your prefered downloaded file type',
                                choices=[('Only Video','v'),('Only Audio','a'),('Full','av')],
                                default='Full'
                                ),
                inquirer.List('minres',
                                message='Choose the minimum resolution for your video',
                                choices=["0","240","360","480","720","1080"],
                                ignore = lambda x : x["type"] == "a" 
                                ),
                inquirer.List('maxres',
                                message='Choose the minimum resolution for your video',
                                choices= ["240","360","480","720","1080"],
                                ignore = lambda x : x["type"] == "a" 
                                ),
            ]

        answers = inquirer.prompt(questions, theme=GreenPassion())
        
        
        self.headers_directory = os.getcwd()+"/resources/headers.txt"
        self.type = answers['type']
        self.min_res = eval(answers['minres'])
        self.max_res = eval(answers['maxres'])

    def read_headers_file(self):
        headers = []
        try:
            headers_file = open(self.headers_directory, "r")
        except IOError:
            raise IOError("headers file does not exist")
        for header in headers_file:
            header_splited = header.split('\\')[0]
            headers.append(str(header_splited))
        headers_file.close()
        return headers

    def get_random_header(self):
        random_header = random.choice(self.read_headers_file())
        refactored_header = random_header[:len(random_header)-1]
        header_dict = {"User-Agent": str(refactored_header)}
        return header_dict

    def download_links(self,links_dict):

        for col in list(links_dict.keys()):
            path = self.make_folder(col)

            if not os.path.exists(path):
                self.logger.error("something's wrong with save_path")
            self.logger.info(f"Downloading {col} files")
            for i,link in enumerate(links_dict[col]):
                outtmpl = os.path.join(path, '%(id)s.%(ext)s')
                add_header = self.get_random_header()

                if self.type == "a":
                    format = 'bestaudio[ext=webm]'
                elif self.type == "v":
                    format = f'bestvideo[height>={self.min_res}][height<={self.max_res}][ext=mp4]'
                elif self.type == "av":
                    format = f'best[height>={self.min_res}][height<={self.max_res}][ext=mp4]'

                if 'format' in locals():
                    ydl_opts = {
                        'format': format,
                        'outtmpl': outtmpl,
                        'add_header': add_header,
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([link])

    def handle(self):
        download_links = self.get_links_from_database("videos",["video_link"])
        self.download_links(download_links)
