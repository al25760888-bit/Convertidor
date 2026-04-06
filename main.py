import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
import io
from datetime import datetime

# Función para dar formato al XML
def indent(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def create_iss_from_kypcb(df):
    root = ET.Element("productionProgram")
    
    # 1. Cabecera idéntica a tus archivos DRV485 (Dialight)
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
    
    # 2. Sección Core y PWB
    core = ET.SubElement(root, "core")
    pwb = ET.SubElement(core, "pwbBasic")
    ET.SubElement(pwb, "pwbName").text = "GENERATED_PWB"
    ET.SubElement(pwb, "pwbSize", x="250000", y="200000", t="1600") # Valores estándar en micras
    
    pwb_cfg = ET.SubElement(core, "pwbConfiguration")
    ET.SubElement(pwb_cfg, "transferDirection").text = "LEFT_TO_RIGHT"
    
    # 3. Datos de Colocación (Mapeo solicitado: component name, part, x, y, rot)
    placement_data = ET.SubElement(core, "placementData")
    
    idx = 1
    for _, row in df.iterrows():
        try:
            # Extraemos los datos usando los nombres corregidos
            c_name = str(row['component name']).strip()
            c_part = str(row['part']).strip()
            # Convertimos a micras (multiplicando por 1000)
            c_x = str(int(float(row['x']) * 1000))
            c_y = str(int(float(row['y']) * 1000))
            c_rot = str(int(float(row['rot']) * 1000))

            place = ET.SubElement(placement_data, "placement", index=str(idx))
            ET.SubElement(place, "componentId").text = c_part
            ET.SubElement(place, "designator").text = c_name
            ET.SubElement(place, "coordinate", x=c_x, y=c_y, theta=c_rot)
            idx += 1
        except Exception:
            # Si una fila tiene error (ej. cabeceras repetidas), la saltamos
            continue

    # 4. Sección Model (Crucial para que JANET no lo rechace)
    model = ET.SubElement(root, "model")
    conv_data = ET.SubElement(model, "pwbConveyorData")
    ET.SubElement(conv_data, "pwbSupportCondition").text = "0"
    ET.SubElement(conv_data, "conveyorSpeed", value="400")

    return indent(root)

# --- Interfaz Streamlit ---
st.set_page_config(page_title="SMT Dialight Converter", layout="wide")
st.title("🛠 Convertidor KYpcb a ISS (Versión Final)")

archivo = st.file_uploader("Sube tu archivo KYpcb", type=['csv', 'txt', 'kypcb'])

if archivo:
    try:
        # Leemos el archivo detectando automáticamente si usa comas o tabulaciones
        df = pd.read_csv(archivo, sep=None, engine='python')
        
        # NORMALIZACIÓN DE COLUMNAS: Quitamos espacios y pasamos a minúsculas
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Lista de columnas que DEBEN estar en el archivo
        requeridas = ['component name', 'part', 'x', 'y', 'rot']
        existentes = [c for c in requeridas if c in df.columns]
        
        if len(existentes) == len(requeridas):
            st.success("✅ Estructura de columnas reconocida.")
            st.dataframe(df.head(10))
            
            if st.button("Generar Archivo .ISS"):
                xml_resultado = create_iss_from_kypcb(df)
                st.download_button(
                    label="📥 Descargar PROGRAMA_DIALIGHT.iss",
                    data=xml_resultado,
                    file_name="PROGRAMA_DIALIGHT.iss",
                    mime="text/xml"
                )
        else:
            st.error(f"Faltan columnas en tu archivo. Necesito: {requeridas}")
            st.write("Columnas detectadas en tu archivo:", df.columns.tolist())
            
    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")