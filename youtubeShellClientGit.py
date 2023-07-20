#!/home/evgeny/Env/pyclientEnv/bin/python

from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

import sys
import re
import os
import sqlite3
import inquirer
from os.path import exists

#check if you have right permissions to write to this directory or change another emplacement
homedir = os.environ['HOME']
youshellConfigPath =  f"{homedir}.config/youshell"
databaseFile = f"{youshellConfigPath}/youshell2.db"
#channelsTable = 'Chanelll'
channelsTable = 'channels'
subscribtionsTextFile = f"{youshellConfigPath}/subscribe.txt"


def dMenuSelect(titlesSet, prompt):
    titlesString = '\n'.join(titlesSet)
    choice = os.popen(f"echo '{titlesString}' | dmenu -p '{prompt}' -l 20").read().replace("\n","")
    print("SELECTED TITLE: ",choice)
    return choice

def inquirerSelect(titlesSet, prompt):
    questions = [
            inquirer.List('choice',
                message=f"{prompt}",
                choices=list(titlesSet),
            ),
            ]
    answer = inquirer.prompt(questions)
    return answer["choice"]

def selectTitle(titleSet, prompt, promptManager):
    if (promptManager == 'dmenu'):
        return dMenuSelect(titleSet, prompt)
    return inquirerSelect(titleSet, prompt)

def selectAndPlayVideo(urlToParse, promptManager):
    patternForbiddenChars = r'[{}\[\]\(\)<>"\'\\\/;:!@#$%^&*|~`+=?,.]'
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    driver.get(urlToParse)
    videoBoxes = driver.find_elements(By.CLASS_NAME, 'h-box')
    videos = {}
    for box in videoBoxes:
        try:
            title=box.find_element(By.XPATH, './/p[@dir="auto"]').text
            cleanTitle = re.sub(patternForbiddenChars, '', title) if title is not None else 'null'
            link=box.find_element(By.XPATH, './/a').get_attribute('href')
            if 'watch' in link:
                videos[cleanTitle] = link
        except Exception as e:
            pass

    # a set of unique titles
    titles = set(list(videos.keys()))

    #extracting the value from dmenu (or other prompt managers) and value from videos object accordingly
    selectedVideoTitle = selectTitle(titles, 'Select video: ', promptManager)
    selectedVideoUrl = videos[selectedVideoTitle]

    #playing video
    playSelectedVideo(selectedVideoUrl, driver)



def selectPageToParse(selectedOption):
    playVideoFromSubscribtion(selectedOption)


def playSelectedVideo(videoUrl, driverToClose):
    print("closing web driver")
    driverToClose.quit()
    command = f"mpv {videoUrl}"
    os.system(command)

def runYoutubeMenu(promptManager):
    searchMenuOptions=getSearchMenuOptions()
    optionsTitles = set(list(searchMenuOptions.keys()))

    selectedOptionTitle = selectTitle(optionsTitles, 'Select source: ', promptManager)
    if selectedOptionTitle != 'SEARCH':
        return searchMenuOptions[selectedOptionTitle]

def getSearchMenuOptions():
    dMenuOptions = {'SEARCH': 'unknown' }

    #checking if the channels list exists
    if exists(databaseFile):
        dMenuOptions = extractValuesFromDatabase()
    else:
        #generate database
        print("Subscribtions database generation")

        db = sqlite3.connect(databaseFile)
        c = db.cursor()
        print(f'creating table {channelsTable}')
        c.execute(f"""CREATE TABLE IF NOT EXISTS {channelsTable} (
            ID INTEGER PRIMARY KEY,
            NAME TEXT,
            URL TEXT
        )""")

        db.commit()
        db.close()
        populateDatabase(subscribtionsTextFile)

        dMenuOptions = extractValuesFromDatabase()

    return dMenuOptions


def extractValuesFromDatabase():

    subscribtionsOptions = {}
    db = sqlite3.connect(databaseFile)
    c = db.cursor()
    channels = c.execute(f"SELECT NAME, URL FROM {channelsTable}").fetchall()
    for channel in channels:
        subscribtionsOptions[str(channel[0])]=str(channel[1])
    db.close()

    return subscribtionsOptions


def populateDatabase(subscribtionsTextFile):
    print("populating database")

    f = [i.strip('\n').split(',') for i in open(subscribtionsTextFile)]
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    db = sqlite3.connect(databaseFile)
    c = db.cursor()

    for k in f:
        h = (k[0])
        driver.get(h)
        time.sleep(3)
        element2 = driver.find_element(By.XPATH, """//*[@class="channel-name"]""")
        pre_canell = element2.text

        c.execute(f"""INSERT INTO {channelsTable}(NAME, URL) VALUES (?,?);""", (pre_canell, h))
        db.commit()
        print(pre_canell + "  Added to the database!  ")
    db.close()

def runYoutubeClient(promptManager = 'dmenu'):
    selectedUrl = runYoutubeMenu(promptManager)
    selectAndPlayVideo(selectedUrl, promptManager)

if __name__ == '__main__':

    if not os.path.exists(youshellConfigPath):
        os.makedirs(youshellConfigPath)
        print('youshell config path created')
        print(youshellConfigPath)
    if not os.path.exists(subscribtionsTextFile):
        with open(subscribtionsTextFile, "w"):
            print('youshell subscribtion text file created')
            pass

    if(len(sys.argv) > 1):
        if (sys.argv[1] == 'update'):
            populateDatabase(subscribtionsTextFile)
        menuChoice = sys.argv[1]
        runYoutubeClient(menuChoice)
    else:
        runYoutubeClient()
