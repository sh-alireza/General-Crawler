import logging
import os
from typing import List

import inquirer
from Crawler_Modules import *
from Downloader_Modules import *
from inquirer.themes import GreenPassion
from To_csv import To_csv


# define the function that gets the downloader flags
def get_downloader_flags() -> List[str]:
    # Return a list of the files in the Downloader_Modules/Adaptors directory
    return os.listdir("Downloader_Modules/Adaptors")

# define the function that gets the crawler flags


def get_crawler_flags() -> List[str]:
    """Get a list of all crawler flags from the Adaptors directory.

    Returns:
        A list of all crawler flags from the Adaptors directory.
    """
    # List all files in the Adaptors directory
    all_files = os.listdir("Crawler_Modules/Adaptors")

    # Return all files in the Adaptors directory
    return all_files

# define the function that gets the site flags


def get_site_flags() -> List[str]:
    # Get a list of all the crawler files in the current directory
    crawler_files = get_crawler_flags()
    # Create a list of just the filenames without the .py extension
    # and with all characters in lowercase
    crawler_flags = [c[:-3].lower() for c in crawler_files if ".py" in c]
    # Return the list of flags
    return crawler_flags

# define the function that starts the program


def start():
    # define a list of questions
    questions = [
        # the first question is a list question
        inquirer.List('command',
                      message="Choose your command",
                      choices=['crawl', 'download', 'to csv'],
                      ),
        # the second question is a list question
        inquirer.List('site_flag',
                      message="Choose the site you want to work with",
                      choices=get_site_flags(),
                      ),
    ]
    # get the answers from the user
    answers = inquirer.prompt(questions, theme=GreenPassion())
    # if the user chose to crawl
    if answers["command"] == "crawl":
        crawl(answers['site_flag'])
    # if the user chose to download
    elif answers["command"] == "download":
        download(answers["site_flag"])
    # if the user chose to convert to csv
    elif answers["command"] == "to csv":
        csv(answers["site_flag"])
    # if the user chose something else
    else:
        raise Exception("something is wrong")

# define the function that crawls the site


def crawl(site_flag):
    '''Crawl the site
    :param site_flag: the site flag
    :param type: str
    :return: None
    '''
    # Loop through all the crawler flags
    for key in get_crawler_flags():
        # If the site flag is in the crawler flag
        if site_flag.strip().lower() in key.lower():
            # Create a question to ask the user if they have a config file
            questions = [
                inquirer.List('config',
                              message='Do you have any config file?',
                              choices=['Yes', 'No'],
                              default='Yes'
                              ),
                inquirer.Text('config_path',
                              message='Please write your config path',
                              ignore=lambda x:x["config"] == "No"
                              )
            ]
            # Get the answers from the user
            answers = inquirer.prompt(questions, theme=GreenPassion())
            # If the user has a config file
            try:
                config_path = answers["config_path"]
            except:
                config_path = None
            # Create a crawler object
            crawler = eval(key[:-3]+"(config_path)")
            crawler.handle()
            break

    # If the crawler flag is not found
    if "crawler" not in locals():
        logging.error("Invalid Flag Or Something's Wrong in .env")
        return
    return

# define the function that downloads the data


def download(site_flag):
    '''Download the data
    :param site_flag: the site flag
    :param type: str
    :return: None
    '''
    # Loop through all the downloader flags
    done = False
    for key in get_downloader_flags():
        # If the site flag is in the downloader flag
        if site_flag.strip().lower() in key.lower():
            downloader = eval(key[:-3]+"(site_flag)")
            downloader.handle()
            done = True
            break
    # If the downloader flag is not found
    if not done:
        # Ask the user to choose the file type
        question = [
            inquirer.List('file_type',
                          message="Choose the file_type you want to download",
                          choices=['image', 'video', 'audio'],
                          default='image'

                          )
        ]
        # Get the answers from the user
        answers = inquirer.prompt(question, theme=GreenPassion())
        file_type = answers['file_type']
        # Loop through all the downloader flags
        for key in get_downloader_flags():
            if file_type in key.lower():
                downloader = eval(key[:-3]+"(site_flag)")
                downloader.handle()
                done = True
                break
    # If the downloader flag is not found
    if "downloader" not in locals():
        logging.error("Invalid Flag Or Something's Wrong in .env")
        return

    return

# define the function that converts the database to csv


def csv(site_flag):
    '''Convert the database to csv
    :param site_flag: the site flag
    :param type: str
    :return: None
    '''
    # Get a list of all the databases
    db_list = os.listdir("../data/databases")
    # Loop through all the databases
    for db in db_list:
        # If the site flag is in the database
        if site_flag in db:
            tocsv = To_csv(os.path.join("../data/databases", db))
            tocsv.handle()
