import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
import io
from datetime import datetime

# Función para dar formato al XML (Pretty Print)
def indent(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def create_iss_from_kypcb(df):
    root = ET.Element("productionProgram")
    
    # 1. Header Data (Configuración Dialight)
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
    
    # 2. Core y PWB
    core = ET.SubElement(root, "core")
    pwb = ET.SubElement(core, "pwbBasic")
    ET.SubElement(pwb, "pwbName").text = "PWB_GENERADO"
    ET.SubElement(pwb, "pwbSize", x="250000", y="200000", t="1600")
    
    pwb_cfg = ET.SubElement(core, "pwbConfiguration")
    ET.SubElement(pwb_cfg, "transferDirection").text = "LEFT_TO_RIGHT"
    
    # 3. Placement Data
    placement_data = ET.SubElement(core, "placementData")
    
    idx = 1
    for _, row in df.iterrows():
        try:
            # Extraemos los datos basándonos en la imagen que mandaste
            c_name = str(row['component name']).strip()
            c_part = str(row['part']).strip()
            # Conversión a micras (x1000)
            c_x = str(int(float(row['x']) * 1000))
            c_y = str(int(float(row['y']) * 1000))
            c_rot = str(int(float(row['rot']) * 1000))

            place = ET.SubElement(placement_data, "placement", index=str(idx))
            ET.SubElement(place, "componentId").text = c_part
            ET.SubElement(place, "designator").text = c_name
            ET.SubElement(place, "coordinate", x=c_x, y=c_y, theta=c_rot)
            idx += 1
        except:
            continue

    # 4. Model (Sección para JANET)
    model = ET.SubElement(root, "model")
    conv_data = ET.SubElement(model, "pwbConveyorData")
    ET.SubElement(conv_data, "pwbSupportCondition").text = "0"
    ET.SubElement(conv_data, "conveyorSpeed", value="400")

    return indent(root)

# --- App Streamlit ---
st.set_page_config(page_title="Convertidor Dialight ISS", layout="wide")
st.title("⚙️ Convertidor Automático KYpcb ➔ ISS")

archivo = st.file_uploader("Sube tu archivo KYpcb", type=['csv', 'txt', 'kypcb'])

if archivo:
    try:
        # Cargamos el archivo y limpiamos los nombres de columnas
        df = pd.read_csv(archivo, sep=None, engine='python')
        
        # ELIMINAMOS ESPACIOS EXTRAS EN LOS NOMBRES DE LAS COLUMNAS
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Verificamos si están las columnas de tu imagen
        required = ['component name', 'part', 'x', 'y', 'rot']
        check = all(item in df.columns for item in required)
        
        if check:
            st.success("✅ Columnas detectadas: component name, part, x, y, rot")
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
            st.error("Faltan columnas o los nombres no coinciden.")
            st.write("Columnas encontradas en tu archivo:", df.columns.tolist())
            st.info("Asegúrate de que la primera fila de tu archivo tenga los títulos: component name, part, x, y, rot")
            
    except Exception as e:
        st.error(f"Error: {e}")