from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

def setup():
    driver = webdriver.Chrome()
    driver.get("https://servicios.ips.gov.py/constancias_aop/consNoSerAseguradoCot.php?")
    return driver


def verificarCI(Cedula):
    driver = setup()

    # Elementos 
    campo = driver.find_element(by=By.NAME, value="parmCedula")
    boton = driver.find_element(by=By.NAME, value="btnBuscar")

    #Escribir los datos
    campo.send_keys(Cedula)
    boton.click()
    time.sleep(0.5)

    # Verificar el estado de la persona
    mensaje = driver.find_element(by=By.CSS_SELECTOR, value="#divResultados > p.pMensajeOK")
    if mensaje.text == "El Nro CIC pertenece a un asegurado cotizante en el IPS no puede generar la constancia.":
        return True
    else:
        return False
    
    

print(verificarCI("4512668"))
print(verificarCI("3767299"))
