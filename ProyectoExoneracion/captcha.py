import pytesseract
import sys
import cv2
import argparse
from PIL import Image
from subprocess import check_output
import requests
from bs4 import BeautifulSoup
import urllib.request
import cv2
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter


def resolve(path):
    #check_output(['convert', path, '-resample', '600', path])
    pytesseract.pytesseract.tesseract_cmd = r'D:/Programas/teseract/tesseract.exe'
    return pytesseract.image_to_string(Image.open(path))

async def solve_captcha():
    img = cv2.imread("captcha.png")


    #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    pytesseract.pytesseract.tesseract_cmd = r'D:/Programas/teseract/tesseract.exe'

    im_gray = cv2.imread("captcha.png", cv2.IMREAD_GRAYSCALE)
    (thresh, im_bw) = cv2.threshold(im_gray, 85, 255, cv2.THRESH_BINARY)
    # although thresh is used below, gonna pick something suitable
    im_bw = cv2.threshold(im_gray, thresh, 255, cv2.THRESH_BINARY)[1]

    text = pytesseract.image_to_string(im_bw)


    return text

def load_cedulas(path_cedulas):
        return [line.rstrip() for line in open(path_cedulas)]

def get_image(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    links = soup.find_all('img', {'id': 'formPrincipal:capimg'})
    for i in links:
        new_link = f"https://www.senescyt.gob.ec{i['src']}"
        #print(new_link)
    return new_link

def submit_form(urlform,cedula, captcha):
    print(cedula)
    print(captcha)

    params ={
    'captchaSellerInput': captcha,
    'identificacion':cedula
    } 

    response = requests.post(url,data=params)
    content = response.content
    #soup = BeautifulSoup(content,"lxml")

    print(content) # is always an empty list

if __name__=="__main__":
    url = "https://www.senescyt.gob.ec/web/guest/consultas"
    urlform = "https://www.senescyt.gob.ec/web/guest/consultas#formPrincipal"
    image = get_image(url)
    urllib.request.urlretrieve(image, "local_captcha.jpg")

    captcha_text = resolve('local_captcha.jpg')
    print('Extracted Text', captcha_text)

    #Submit form
    #submit_form(urlform,'0102835691',captcha_text)
    