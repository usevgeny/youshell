#!/home/evgeny/Env/pyclientEnv/bin/python

from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import requests
import re
import sys
import html
import re
import os
import sqlite3
import inquirer
from os.path import exists
#from decouple import config

#homedir = config('HOMEDIR')
homedir = '/home/evgeny'
youshellConfigPath =  f"{homedir}/.config/youshell"
databaseFile = f"{youshellConfigPath}/youshell.db"
#channelsTable = 'Chanelll'
channelsTable = 'channels'
subscribtionsTextFile = f"{youshellConfigPath}/subscribe.txt"

patternForbiddenChars = r'[{}\[\]\(\)<>"\'\\\/;:!@#$%^&*|~`+=?,.]'

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

def customSearch(searchQuery):
    searchQuery=html.escape(searchQuery)
    return f"https://invidious.protokolla.fi/search?q={searchQuery}"

def getLinksFromSelenium(urlToParse):

    parsedLinksDict = {}
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    driver.get(urlToParse)
    videoBoxes = driver.find_elements(By.CLASS_NAME, 'h-box')
    for box in videoBoxes:
        try:
            title=box.find_element(By.XPATH, './/p[@dir="auto"]').text
            cleanTitle = re.sub(patternForbiddenChars, '', title) if title is not None else 'null'
            link=box.find_element(By.XPATH, './/a').get_attribute('href')
            if 'watch' in link:
                parsedLinksDict[cleanTitle] = link
        except Exception as e:
            pass
    print("closing web driver")
    driver.quit()
    return parsedLinksDict

def getLinksFromrequestsLib(urlToParse):

    parsedLinksDict ={}
    hostPattern=r'(https://[^/]+)'
    linksBlockPattern = r'<a href.*auto.*' # pattern for the link with name
    videoUrlPattern = r'(?<=<a href=")\/watch\?v=[^"]+' # pattern for the link url
    titlePattern =  r'<p .*?>(.*?)</p>' #patter for the title
    headers = {"user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",}
    with requests.session() as s:
        hostUrl = re.findall(hostPattern, urlToParse)[0]
        print("session_started")
        s.headers = headers
        response = html.unescape(s.get(urlToParse.rstrip()).text)
        matches = re.findall(linksBlockPattern, response)

        for match in matches:
            title=re.findall(titlePattern, match)[0]

            try:
                title = title.encode('iso-8859-1').decode('utf-8')
            except UnicodeDecodeError:
                # If UTF-8 decoding fails, try with ISO-8859-1
                title = title.encode('iso-8859-1').decode('iso-8859-1')

            cleanTitle = re.sub(patternForbiddenChars, '', title) if title is not None else 'null'
            videoUrl = re.findall(videoUrlPattern, match)[0]
            parsedLinksDict[cleanTitle] = f"{hostUrl}{videoUrl}"
        s.close()

    return parsedLinksDict



def getParsedVideoDict(urlToParse):
    #return getLinksFromrequestsLib(urlToParse)
    #return getLinksFromSelenium(urlToParse)
    return getLinksFromrequestsLib(urlToParse)

def selectAndPlayVideo(urlToParse, promptManager):
    videos = getParsedVideoDict(urlToParse)

    # a set of unique titles
    titles = set(list(videos.keys()))

    #extracting the value from dmenu (or other prompt managers) and value from videos object accordingly
    selectedVideoTitle = selectTitle(titles, 'Select video: ', promptManager)
    selectedVideoUrl = videos[selectedVideoTitle]

    #playing video
    playSelectedVideo(selectedVideoUrl)



def selectPageToParse(selectedOption):
    playVideoFromSubscribtion(selectedOption)


def playSelectedVideo(videoUrl):
    command = f"mpv {videoUrl}"
    os.system(command)

def runYoutubeMenu(promptManager):
    searchMenuOptions=getSearchMenuOptions()
    optionsTitles = set(list(searchMenuOptions.keys()))

    selectedOptionTitle = selectTitle(optionsTitles, 'Select source: ', promptManager)
    if selectedOptionTitle != 'SEARCH':
        return searchMenuOptions[selectedOptionTitle]
    else:
        searchPrompt = input("Enter the video you are looking for:")
        return (customSearch(searchPrompt))

def getSearchMenuOptions():

    #checking if the channels list exists
    if exists(databaseFile):
        menuOptions = extractValuesFromDatabase()
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

        menuOptions = extractValuesFromDatabase()

    menuOptions['SEARCH']='https://invidious.protokolla.fi/feed/popular'
    return menuOptions


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
