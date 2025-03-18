from flask import Flask, render_template, request, url_for, send_file

import os
import requests

import xml.etree.ElementTree as ET
import pandas as pd
from bs4 import BeautifulSoup
from io import BytesIO

app = Flask(__name__)

db = {}

def parse_xml(file, dia):
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
                name = t_nombre.text    # Tercera columna (Nombre)
                nombre, company = separar_texto(name)
            if t_fecha is not None:
                timestamp = t_fecha.text # Cuarta columna (Hora de Apertura)
                fecha = timestamp.split(" ")[0] # Extraer solo la fecha
            if fecha == dia:
                data.append({"id": cedula,
                            "name": nombre,
                            "date": fecha,
                            "company": company})
    return data

def separar_texto(texto):
    if not texto:  # Verifica si es None o cadena vacía
        return None, None
    
    partes = texto.split("_", 1)  # Divide en máximo 2 partes

    nombre = partes[0].strip()
    company = partes[1].strip() if len(partes) > 1 else None  # Si no hay segunda parte, company es None

    return nombre, company


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
    
    sorted_asegurados = sorted(asegurados, key=lambda x:x['company'] or '')
    sorted_no_asegurados = sorted(no_asegurados, key=lambda x: x['company'] or '')
    sorted_no_checkeados = sorted(no_checkeados, key=lambda x: x['company'] or '')
    results = {'asegurados': sorted_asegurados, 
               'no_asegurados':sorted_no_asegurados, 
               'no_checkeados':sorted_no_checkeados
               }
    global db
    db = results
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
    return render_template('results.html', 
                            resultados = resultados,
                            total_asegurados = total_asegurados,
                            total_no_asegurados = total_no_asegurados, 
                            no_chequeados = no_checkeados)

# Ruta para descargar el archivo Excel
@app.route('/download-excel')
def download_excel():
    # Simulación de resultados (reemplaza con tu lógica real)
    global db

    # Crear un DataFrame de Pandas con los resultados
    data = []
    for categoria, personas in db.items():
        for persona in personas:
            data.append({
                'Categoría': categoria,
                'ID': persona['id'],
                'Nombre': persona['name'],
                'Contratista': persona['company'],
                'Fecha': persona['date']
            })
    df = pd.DataFrame(data)

    # Crear un archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    output.seek(0)

    # Devolver el archivo Excel como una descarga
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='resultados.xlsx'
    )

if __name__ == '__main__':
    app.run(debug=True)