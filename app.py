from flask import Flask, render_template, request, redirect, url_for
import os
import xml.etree.ElementTree as ET

app = Flask(__name__)

def parse_xml(file):
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
        
        if len(cells) >= 4:  # Asegurar que la fila tiene suficientes celdas
            if cells[1].find("ss:Data", ns) is not None:
                user_id = cells[1].find("ss:Data", ns).text  # Segunda columna (Id. de Usuario)
            if cells[2].find("ss:Data", ns) is not None:
                name = cells[2].find("ss:Data", ns).text      # Tercera columna (Nombre)
            if cells[3].find("ss:Data", ns) is not None:
                timestamp = cells[3].find("ss:Data", ns).text # Cuarta columna (Hora de Apertura)
            date = timestamp.split(" ")[0]               # Extraer solo la fecha

            data.append({"id": user_id,"name": name,"date": date})
    return data


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        results = parse_xml(file)
        print(results)

    return redirect('/')

@app.route('/results', methods=['GET'])
def restults():
    return render_template('results.html', results = [])

if __name__ == '__main__':
    app.run(debug=True)