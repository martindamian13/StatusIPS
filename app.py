from flask import Flask, render_template, request, redirect

import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def parse_xml(file, fecha_a):
    # Parsear el XML
    tree = ET.parse(file)
    root = tree.getroot()

    # Espacio de nombres para buscar los elementos correctos
    ns = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}

    # Encontrar todas las filas del XML
    rows = root.findall(".//ss:Row", ns)
    
    data = []
    for row in rows[3:]:  # Saltamos las primeras 3 filas (títulos y metadatos)
        cells = row.findall("ss:Cell", ns)
        t_num_cedula = cells[1].find("ss:Data", ns)
        t_nombre = cells[2].find("ss:Data", ns)
        t_fecha = cells[3].find("ss:Data", ns)
        
        if len(cells) >= 4:  # Asegurar que la fila tiene suficientes celdas
            if t_num_cedula is not None:
                cedula = t_num_cedula.text  # Segunda columna (Id. de Usuario)
            if t_nombre is not None:
                name = t_nombre.text      # Tercera columna (Nombre)
            if t_fecha is not None:
                timestamp = t_fecha.text # Cuarta columna (Hora de Apertura)
                fecha = timestamp.split(" ")[0] # Extraer solo la fecha
            if fecha == fecha_a:
                data.append({"id": cedula,"name": name,"date": fecha})
    return data

def check_status(num_cedula):
    url = "https://servicios.ips.gov.py/constancias_aop/controladores/funcionesConstanciasAsegurados.php?opcion=consultarAsegurado"
    payload = {
        'parmCedula': num_cedula,
        'parmDocOrigen': '226'
    }
    response = requests.post(url, data = payload)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        mensaje = soup.find('p', class_='pMensajeOK')
        if mensaje:
            return mensaje.text.strip()
        else:
            return 'No se encontro el mensaje en la respuesta'
    else:
        return f'Error en la solicitud: {response.status_code}'
    
def resultado(data):
    no_asegurados = []
    asegurados = []
    no_checkeados = []
    for item in data:
        mensaje = check_status(item['id'])
        print(mensaje)
        if mensaje == "El Nro CIC no pertenece a un asegurado cotizante/beneficiario del IPS":
            no_asegurados.append(item)
        elif mensaje == "El Nro CIC pertenece a un asegurado cotizante en el IPS no puede generar la constancia.":
            asegurados.append(item)
        else:
            no_checkeados.append(item)
        print('Checking...')
    results = {'asegurados': asegurados, 'no_asegurados': no_asegurados, 'no_checkeados':no_checkeados}
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        fecha = request.form.get('fecha')
        parsed_file = parse_xml(file, fecha)
        resultados = resultado(parsed_file)
        total_asegurados = len(resultados['asegurados'])
        total_no_asegurados = len(resultados['no_asegurados'])
        no_checkeados = len(resultados['no_checkeados'])
    return render_template('results.html', resultados = resultados, total_asegurados = total_asegurados,total_no_asegurados = total_no_asegurados, no_chequeados = no_checkeados)

@app.route('/resultados')
def resultados():
    resultados = []
    total_checkeados = []
    no_checkeados = []
    return render_template('results.html', resultados = resultados, total_checkeados = total_checkeados, no_checkeados = no_checkeados)


if __name__ == '__main__':
    app.run(debug=True)