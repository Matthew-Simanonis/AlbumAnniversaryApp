import requests
import re
import pandas as pd
import smtplib
import csv
from bs4 import BeautifulSoup
from urllib.error import HTTPError


def main():  
    action = input('What would you like to do? [add, check] ')
    try:
        with open('albums.csv') as csvfile:         # Open CSV File
            df = pd.read_csv(csvfile)               # Pandas read to dataframe
            df.drop_duplicates(subset='title', keep='first', inplace=True)   # Drop any duplicates
            print(df.iloc[:,0:3])                               # Show Dataframe
            df.to_csv('albums.csv', index=False)
            if 'a' in action:
                addalbum()                          # Add album to csv file
                exit(0)
            elif 'c' in action:
                index = checkdate(df)           # Get index using checkdate
                if len(index) >= 1:             # If index found, send email with info
                    send_mail(df, index)

                
    except FileNotFoundError:                   # If no CSV file 'albums.cv'
        with open('albums.csv', 'w') as f:
            writer = csv.writer(f, lineterminator='\n')     # Create new CSV file with headers 'title' 'artist' 'release'
            writer.writerow(['title','artist','release', 'URL'])

def checkdate(dataframe):
    today = pd.to_datetime('today').strftime('%m-%d')       # Grab MM-DD from today's date
    regex = r'\d{4}-' + today                               # Create regular expression
    bools = dataframe.release.str.contains(regex)           # Boolean array if matches todays date
    index = bools[bools].index.values                       # Get index values
    return(index)                                           # Return index values

def addalbum():
    album = []
    albumname = smart_title(input('Input album name: '))
    artistname = smart_title(input('Input artist name: '))
    albumtitle, albumartist, albumrelease, URL = getrelease(artistname, albumname)       # Getrelease() returns 'title, artist, release'
    album.append(albumtitle)            
    album.append(albumartist)           # Add Title, artist and release date to list
    album.append(albumrelease)
    album.append(URL)    
    with open('albums.csv', 'a') as f:
            writer = csv.writer(f, lineterminator='\n')      # Write 'title, artist, release' to CSV
            writer.writerow(album)
    print('Added:', album)
        
def getrelease(artist, albumname):
    artisturl = artist.replace(' ', '_')
    artist_the = artist.replace('the ','')      # Convert artist and album name to URL formatting
    albumname = albumname.replace(' ', '_')
    lowerwords = {'_The_':'_the_','_Of_':'_of_','_And_':'_and_','_A_':'_a_', '_With_':'_with_', '_To_':'_to_', '_In_':'_in_', '\'M':'\'m', '\'S':'\'s'}       # Dict of lowercase words
    albumname = replace_all(albumname, lowerwords)                      # Lowercase words that wikipedia randomly lowercases in URLs
    print(albumname)

    try:
        URL = requests.get(f"https://en.wikipedia.org/wiki/{albumname}_(album)")    # Open Wikipedia URL
        soup = BeautifulSoup(URL.content, 'html.parser')
        if len(soup.find_all(class_="infobox vevent haudio")) < 1:                  # Check if URL has album info
            URL = requests.get(f"https://en.wikipedia.org/wiki/{albumname}")       # Else try different URL format
            soup = BeautifulSoup(URL.content, 'html.parser')
            if len(soup.find_all(class_="infobox vevent haudio")) < 1:  
                URL = requests.get(f"https://en.wikipedia.org/wiki/{albumname}_({artisturl}_album)")
                soup = BeautifulSoup(URL.content, 'html.parser')
                if len(soup.find_all(class_="infobox vevent haudio")) < 1:
                    URL = requests.get(f"https://en.wikipedia.org/wiki/{albumname}_({artist_the}_album)")
                    soup = BeautifulSoup(URL.content, 'html.parser')
    except HTTPError:
        print('ERROR 404')
    page = URL.url
    release = soup.find_all(class_="published")[0].get_text()       # Find release date
    title = soup.find_all(class_='summary album')[0].get_text()     # Find album title
    artist = soup.find_all('th', {'class':'description'})[0].get_text()     # Find artist name
    artist = re.search(r'by (.*)', artist).group(1)        # Separate artist from "Album by (artist)"
    try:
        release = re.search(r'\((.*?)\)', release).group(1)      
    except  AttributeError:  # Date not formatted
        day = re.search(r'(\d{1,2})', release).group(0)
        month = re.search(r'([a-zA-z]{3,20})', release).group(0)        # Format date to YYYY-MM-DD
        year = re.search(r'(\d{4})', release).group(0)
        month = month_string_to_number(month)
        release = f'{year}-{month:02d}-{day.zfill(2)}' 
    URL.close()                     
    return(title, artist.title(), release, page)              # Return title, artist, and release date

def send_mail(dataframe, index):
    title = dataframe.iloc[index]['title'].iloc[0]
    artist = dataframe.iloc[index]['artist'].iloc[0]    # Find title, artist, release, URL from dataframe at index
    release = dataframe.iloc[index]['release'].iloc[0]
    URL = dataframe.iloc[index]['URL'].iloc[0]
    server = smtplib.SMTP('smtp.gmail.com', 587)    # Sever Stuff
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login('Youremail@xyz.com', 'password')

    subject = 'Happy Anniversary ' + title + '!'
    body = f'The album {title} by {artist} was released today in {release[0:4]}\n\n\n\n More info:\n {URL} \n\n\n\n\n\n\n\n\n\n\n\n\n\n\n THIS IS AN AUTOMATICALLY GENERATED EMAIL'

    msg = f'Subject:  {subject}\n\n{body}'
    emails = []
    server.sendmail("Youremail@xyz.com","Youremail@xyz.com",msg)
    print('Email has been sent')
    server.quit()

def month_string_to_number(string):   # From https://stackoverflow.com/a/33736132
    m = {
        'jan': 1,
        'feb': 2,
        'mar': 3,
        'apr':4,
         'may':5,
         'jun':6,       # Change month from word, to a number
         'jul':7,
         'aug':8,
         'sep':9,
         'oct':10,
         'nov':11,
         'dec':12
        }
    s = string.strip()[:3].lower()
    try:
        out = m[s]
        return out
    except:
        raise ValueError('Not a month')

def replace_all(text, dic):  # From https://stackoverflow.com/a/6117042
    for i, j in dic.items():
        text = text.replace(i, j)      # Replaces text from tuples in dictionary
    return text 

def smart_title(s):     # From https://stackoverflow.com/a/25513135
    return ' '.join(w if w.isupper() else w.capitalize() for w in s.split())    # .title capitalization, but keeps original caps

main()
