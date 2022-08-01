# -*- coding: utf-8 -*-
import pandas as pd
import os
from datetime import datetime
import logging
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from PIL import Image
from bs4 import BeautifulSoup
import psycopg2, psycopg2.extras
from sqlalchemy import create_engine
from time import sleep
import cv2
import pytesseract
import chromedriver_autoinstaller

#Extraemos el txt de las cedulas y lo ubicamos en un df
estudiantes = pd.read_csv('./cedulas.txt', sep=" ", header=None, dtype = str)
#Agregamos la columna de identifiacion
estudiantes.columns = ["IDENTIFICACION"]

#Instalacion de Drivers
chromedriver_autoinstaller.install()
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

#Variables de rutas
path_base = 'D:\\Trabajos\\Periodo60\\PracticasNegocios\\ProyectoExoneracion\\'
url_base = 'https://www.senescyt.gob.ec/consulta-titulos-web/faces/vista/consulta/consulta.xhtml'




def tableDataText(table):       
    rows = []
    trs = table.find_all('tr')
    #print(table.find_all('td'))
    #print('TR = '+ trs)
    headerow = [td.get_text(strip=True) for td in trs[0].find_all('th')] # header row
    if headerow: # if there is a header row include first
        rows.append(headerow)
        #print('headerow = '+headerow)
        trs = trs[1:]
    for tr in trs: # for every table row
        #print(td.get_text(strip=True) for td in tr.find_all('td'))
        rows.append([td.get_text(strip=True) for td in tr.find_all('td')]) # data row
    #print(rows)
    return rows


def extraerTabla(table):
    list_table = tableDataText(table)
    dftable = pd.DataFrame(list_table[1:], columns=list_table[0])
    dftable.head(4)
    return dftable
        

#Configuracion del driver de Chrome
options = Options()
options.headless = True
options.add_argument("--lang=en")
driver = webdriver.Chrome(path_base + 'chromedriver.exe', options=options)
driver.set_page_load_timeout(30)  # Tiempo en segundos


options.add_experimental_option('prefs', {"download.default_directory": path_base,"download.prompt_for_download": False,"download.directory_upgrade": True,"plugins.plugins_disabled": ["Chrome PDF Viewer"]})

#engine = create_engine('postgresql://USUARIO:CONTRASEÑA@localhost:5432/senescyt');

#Instanciamos la lista final de valores
final_list = []

#Iteramos por cedulas
for index, row in estudiantes.iterrows():
    
    sleep(5)
       
    identificacion = str(row.IDENTIFICACION)
    print('identificacion a mandar = '+identificacion)
    cedula = 0
    mensaje = 0
    #--------------------------------------------------------------
    #---------- FASE 1: RECONOCIMIENTO DE CAPTCHA -----------------
    #--------------------------------------------------------------
    while cedula == 0:
        try:
            sleep(2)
            datos_estudiante = {}
            driver.get(url_base)
            driver.set_window_size(974, 1040)
            driver.find_element(By.ID, "formPrincipal:identificacion").click()
            driver.find_element(By.ID, "formPrincipal:identificacion").send_keys(identificacion)
            driver.save_screenshot(path_base + "captcha.png")
            img = Image.open(path_base + "captcha.png")
            area = (154, 467, 272, 496)
            cropped_img = img.crop(area)
            cropped_img.save(path_base + "img_captcha.png")
            path_image = path_base + "img_captcha.png"

            #Utilizamos OpenCV con threshold
            image = cv2.imread(path_image)
            #Convertimos la imagen el b/n
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            #Aplicamos el threshold de Otsu's
            thresh = cv2.threshold(gray, 85, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            # Invertimos color para que sea fondo blanco y texto negro
            thresh = 255 - thresh
            #--psm = Specify page segmentation mode.
            data = pytesseract.image_to_string(thresh, lang='eng',config='-c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyz --psm 6')


            subdata = data.strip()
            subdata.replace(" ", "")

            texto = subdata
            print('Texto extraido del captcha = '+texto)
            driver.find_element(By.ID, "formPrincipal:captchaSellerInput").click()
            driver.find_element(By.ID, "formPrincipal:captchaSellerInput").send_keys(texto)
            
            
            
            sleep(3)
            
            driver.find_element(By.ID, "formPrincipal:boton-buscar").click()
            
            
            
            sleep(5)
            
            df = pd.DataFrame()
            
            
            #Si paso captcha, se recupera la cedula para pasar a siguiente fase
            cedula = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/main/form/div/span/div[1]/div[2]/div/div/div/div/div[1]/table/tbody/tr[1]/td[2]/label').text

            #print('cedula recuperada de pagina = '+ cedula)
            
        except Exception as e:
            print('----Error de reconocimiento de Captcha----')
            print('----Se intenta de nuevo hasta reconocer el captcha----')
            #print(e)
            pass
            
    #--------------------------------------------------------------
    #---------- FASE 2: EXTRACCION DE CONTENIDO -------------------
    #--------------------------------------------------------------
    if cedula != 1:
    
        nombres = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/main/form/div/span/div[1]/div[2]/div/div/div/div/div[1]/table/tbody/tr[2]/td[2]/label').text
        genero = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/main/form/div/span/div[1]/div[2]/div/div/div/div/div[1]/table/tbody/tr[3]/td[2]/label').text
        nacionalidad = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/main/form/div/span/div[1]/div[2]/div/div/div/div/div[1]/table/tbody/tr[4]/td[2]/label').text
        
        #df = df.append({'cedula': cedula, 'nombres':nombres, 'genero':genero, 'nacionalidad':nacionalidad}, ignore_index=True)
        
        soup = BeautifulSoup(driver.page_source,'html.parser')
        #print(soup)
        try:
            
            title = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/main/form/div/span/div[2]/div[1]/h4').text
            print('TITULO= '+title)
            if title == 'Título(s) de cuarto nivel o posgrado':
                print('Titulos de Cuarto Nivel')

                contentGrado = soup.find_all('table')[4]   
                dftable_grado = extraerTabla(contentGrado)

                #Agregamos la identificacion al df
                dftable_grado['identificacion'] = pd.Series([cedula for x in range(len(dftable_grado.index))]) 
                #Agregamos el nivel al df
                dftable_grado['Nivel'] = pd.Series(['4to' for x in range(len(dftable_grado.index))])
                #Agregamos los nombres al df
                dftable_grado['Nombres'] = pd.Series([nombres for x in range(len(dftable_grado.index))])
            
                #print(dftable_grado)
                #dftable_grado.to_sql('grado', engine,if_exists = 'append', index=False);
                #Agregamos a una lista
                aux_list = dftable_grado.values.tolist()
                #print(aux_list)
                for i in aux_list:
                    final_list.append(i)
                #final_list.append(aux_list)
                #df.to_sql('principal', engine,if_exists = 'append', index=False);
                sleep(2)
                titlex = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/main/form/div/span/div[3]/div[1]/h4').text
                if titlex == 'Título(s) de tercer nivel de grado':
                    print('Titulos de Tercer Nivel')

                    contentGrado = soup.find_all('table')[5]   
                    dftable_grado = extraerTabla(contentGrado)
                    
                    #Agregamos la identificacion al df
                    dftable_grado['identificacion'] = pd.Series([cedula for x in range(len(dftable_grado.index))]) 
                    #Agregamos el nivel al df
                    dftable_grado['Nivel'] = pd.Series(['3er' for x in range(len(dftable_grado.index))])
                    #Agregamos los nombres al df
                    dftable_grado['Nombres'] = pd.Series([nombres for x in range(len(dftable_grado.index))])

                    aux_list = dftable_grado.values.tolist()
                    #print(aux_list)
                    for i in aux_list:
                        final_list.append(i)
                    #print(dftable_grado)
                    #dftable_grado.to_sql('grado', engine,if_exists = 'append', index=False);
                    
                    #df.to_sql('principal', engine,if_exists = 'append', index=False);
                    sleep(2)

            
            if title == 'Título(s) de tercer nivel de grado':
                print('Titulos de Tercer Nivel')

                contentGrado = soup.find_all('table')[4]   
                dftable_grado = extraerTabla(contentGrado)
                
                #Agregamos la identificacion al df
                dftable_grado['identificacion'] = pd.Series([cedula for x in range(len(dftable_grado.index))]) 
                #Agregamos el nivel al df
                dftable_grado['Nivel'] = pd.Series(['3er' for x in range(len(dftable_grado.index))])
                #Agregamos los nombres al df
                dftable_grado['Nombres'] = pd.Series([nombres for x in range(len(dftable_grado.index))])

                aux_list = dftable_grado.values.tolist()
                #print(aux_list)
                for i in aux_list:
                    final_list.append(i)
            
                #print(dftable_grado)
                #dftable_grado.to_sql('grado', engine,if_exists = 'append', index=False);
                
                #df.to_sql('principal', engine,if_exists = 'append', index=False);
                sleep(2)
        
        except Exception as e:
            print(e)
            print('----El Usuario no tiene titulos----')
            sleep(2)
            pass

#Salimos del driver     
driver.quit()



print(final_list)
df = pd.DataFrame(final_list, columns =['Titulo', 'Institucion', 'Tipo', 'Reconocido',
'Numero_Registro','Fecha_Registro','Observacion','Identificacion','Nivel','Nombres'], dtype = str)

df.to_csv('salida.csv', sep=',', encoding='utf-8', index=False)