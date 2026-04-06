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
    
    # 1. Header Data (Configuración de máquina 3020VA de Dialight)
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
    
    # 2. Core - Estructura de la Placa (PWB)
    core = ET.SubElement(root, "core")
    pwb = ET.SubElement(core, "pwbBasic")
    ET.SubElement(pwb, "pwbName").text = "GENERATED_PWB"
    ET.SubElement(pwb, "pwbSize", x="250000", y="200000", t="1600")
    
    pwb_cfg = ET.SubElement(core, "pwbConfiguration")
    ET.SubElement(pwb_cfg, "transferDirection").text = "LEFT_TO_RIGHT"
    
    # 3. Placement Data (Uso de columnas: name, part, x, y, rot)
    placement_data = ET.SubElement(core, "placementData")
    
    count = 1
    for i, row in df.iterrows():
        try:
            # Mapeo directo según tu información
            comp_id = str(row['part']).strip()
            designator = str(row['name']).strip()
            # Conversión de mm a micras (x1000)
            pos_x = str(int(float(row['x']) * 1000))
            pos_y = str(int(float(row['y']) * 1000))
            theta = str(int(float(row['rot']) * 1000))

            place = ET.SubElement(placement_data, "placement", index=str(count))
            ET.SubElement(place, "componentId").text = comp_id
            ET.SubElement(place, "designator").text = designator
            ET.SubElement(place, "coordinate", x=pos_x, y=pos_y, theta=theta)
            count += 1
        except Exception:
            continue # Salta filas con errores o vacías

    # 4. Model (Sección crítica para el transportador en JANET)
    model = ET.SubElement(root, "model")
    conv_data = ET.SubElement(model, "pwbConveyorData")
    ET.SubElement(conv_data, "pwbSupportCondition").text = "0"
    ET.SubElement(conv_data, "conveyorSpeed", value="400")

    return indent(root)

# --- Interfaz de Streamlit ---
st.set_page_config(page_title="Convertidor Dialight KYpcb a ISS", layout="wide")
st.title("🚀 Convertidor KYpcb ➔ ISS (Mapeo Automático)")

uploaded_file = st.file_uploader("Sube el archivo KYpcb", type=['csv', 'txt', 'kypcb'])

if uploaded_file:
    try:
        # Intenta leer con diferentes delimitadores comunes
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        
        # Verificar que las columnas existan
        required_cols = ['name', 'part', 'x', 'y', 'rot']
        found_cols = [c for c in required_cols if c in df.columns]
        
        if len(found_cols) == len(required_cols):
            st.success("✅ Columnas detectadas: name, part, x, y, rot")
            st.dataframe(df.head(10))
            
            if st.button("Generar Archivo ISS"):
                iss_xml = create_iss_from_kypcb(df)
                st.download_button(
                    label="📥 Descargar PROGRAMA_FINAL.iss",
                    data=iss_xml,
                    file_name="PROGRAMA_FINAL.iss",
                    mime="text/xml"
                )
        else:
            st.error(f"Error: El archivo debe contener las columnas: {required_cols}")
            st.write("Columnas actuales en tu archivo:", df.columns.tolist())
            
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")