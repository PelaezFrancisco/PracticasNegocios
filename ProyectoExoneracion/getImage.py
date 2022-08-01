from distutils.command.clean import clean
from hashlib import new
from multiprocessing import context
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
from IPython.display import Image
import csv
import re
import urllib.request


def crawler(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    links = soup.find_all('img', {'id': 'formPrincipal:capimg'})
    for i in links:
        new_link = f"https://www.senescyt.gob.ec{i['src']}"
        #print(new_link)
    return new_link
       
imagen = crawler('https://www.senescyt.gob.ec/web/guest/consultas')
urllib.request.urlretrieve(imagen, "local-filename.jpg")
print(imagen)