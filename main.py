import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
import io
from datetime import datetime

# Función para el formato XML "Pretty Print"
def indent(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def create_iss_from_kypcb(df):
    root = ET.Element("productionProgram")
    
    # 1. Header Data (Configuración técnica para máquinas Dialight)
    header = ET.SubElement(root, "headerData")
    ET.SubElement(header, "targetMachine").text = "ISS"
    ET.SubElement(header, "targetVersion", revision="15", version="3", level="0")
    ET.SubElement(header, "programMode").text = "0"
    ET.SubElement(header, "editMachine").text = "ISS"
    ET.SubElement(header, "editVersion", revision="10", version="0", level="0")
    
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-07:00")
    ET.SubElement(header, "lastEdit").text = now
    ET.SubElement(header, "lastOptimized").text = now

    line_cfg = ET.SubElement(header, "lineConfiguration")
    ET.SubElement(line_cfg, "lineName", id="2").text = "Line 2"
    cfg = ET.SubElement(line_cfg, "configuration")
    m1 = ET.SubElement(cfg, "machine", no="1")
    ET.SubElement(m1, "typeCode").text = "3020VA"
    ET.SubElement(m1, "subTypeId").text = "75"
    ET.SubElement(m1, "name").text = "3020VAL"
    ET.SubElement(m1, "conveyorLane").text = "SINGLE"
    
    # 2. Core - Definición de la Placa
    core = ET.SubElement(root, "core")
    pwb = ET.SubElement(core, "pwbBasic")
    ET.SubElement(pwb, "pwbName").text = "GENERATED_PWB"
    ET.SubElement(pwb, "pwbSize", x="250000", y="200000", t="1600")
    
    pwb_cfg = ET.SubElement(core, "pwbConfiguration")
    ET.SubElement(pwb_cfg, "transferDirection").text = "LEFT_TO_RIGHT"
    
    # 3. Placement Data (Mapeo: component name, part, x, y, rot)
    placement_data = ET.SubElement(core, "placementData")
    
    count = 1
    for _, row in df.iterrows():
        try:
            # Usamos los nombres de columna actualizados
            comp_id = str(row['part']).strip()
            designator = str(row['component name']).strip()
            
            # Conversión a micras (x1000)
            pos_x = str(int(float(row['x']) * 1000))
            pos_y = str(int(float(row['y']) * 1000))
            theta = str(int(float(row['rot']) * 1000))

            place = ET.SubElement(placement_data, "placement", index=str(count))
            ET.SubElement(place, "componentId").text = comp_id
            ET.SubElement(place, "designator").text = designator
            ET.SubElement(place, "coordinate", x=pos_x, y=pos_y, theta=theta)
            count += 1
        except Exception:
            continue

    # 4. Model (Sección necesaria para JANET)
    model = ET.SubElement(root, "model")
    conv_data = ET.SubElement(model, "pwbConveyorData")
    ET.SubElement(conv_data, "pwbSupportCondition").text = "0"
    ET.SubElement(conv_data, "conveyorSpeed", value="400")

    return indent(root)

# --- App de Streamlit ---
st.set_page_config(page_title="Convertidor Dialight ISS", layout="wide")
st.title("⚙️ Convertidor KYpcb a ISS")

archivo = st.file_uploader("Sube el archivo KYpcb", type=['csv', 'txt', 'kypcb'])

if archivo:
    try:
        # Carga y normalización de nombres de columnas
        df = pd.read_csv(archivo, sep=None, engine='python')
        
        # Limpieza: quitamos espacios y pasamos a minúsculas para evitar errores de lectura
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Columnas requeridas (ahora con 'component name')
        required = ['component name', 'part', 'x', 'y', 'rot']
        check = all(item in df.columns for item in required)
        
        if check:
            st.success("✅ Columnas detectadas correctamente.")
            st.dataframe(df.head(10))
            
            if st.button("Generar Archivo .ISS"):
                xml_final = create_iss_from_kypcb(df)
                st.download_button(
                    label="📥 Descargar PROGRAMA_FINAL.iss",
                    data=xml_final,
                    file_name="PROGRAMA_FINAL.iss",
                    mime="text/xml"
                )
        else:
            st.error(f"Error: No se encontraron todas las columnas necesarias.")
            st.write("El archivo debe tener estas columnas exactamente: component name, part, x, y, rot")
            st.write("Columnas encontradas en tu archivo:", df.columns.tolist())
            
    except Exception as e:
        st.error(f"Ocurrió un error: {e}")