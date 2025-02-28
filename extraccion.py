import xml.etree.ElementTree as ET
import pandas as pd

# Ruta al archivo.
file_path = "./Card_Punch_Records_0.xml"

# Parsear el XML
tree = ET.parse(file_path)
root = tree.getroot()

# Espacio de nombres para buscar los elementos correctos
ns = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}

# Encontrar todas las filas del XML
rows = root.findall(".//ss:Row", ns)

data = []
for row in rows[3:]:  # Saltamos las primeras 3 filas (títulos y metadatos)
    cells = row.findall("ss:Cell", ns)
    
    if len(cells) >= 4:  # Asegurar que la fila tiene suficientes celdas
        user_id = cells[1].find("ss:Data", ns).text  # Segunda columna (Id. de Usuario)
        name = cells[2].find("ss:Data", ns).text      # Tercera columna (Nombre)
        timestamp = cells[3].find("ss:Data", ns).text # Cuarta columna (Hora de Apertura)
        date = timestamp.split(" ")[0]               # Extraer solo la fecha

        data.append([user_id, name, date])

print(data)