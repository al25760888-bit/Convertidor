import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
import io
from datetime import datetime

# Función para formatear el XML (Pretty Print)
def indent(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def create_iss_from_kypcb(df, col_map):
    root = ET.Element("productionProgram")
    
    # 1. Header Data (Estructura idéntica a tus archivos DRV485...)
    header = ET.SubElement(root, "headerData")
    ET.SubElement(header, "targetMachine").text = "ISS"
    ET.SubElement(header, "targetVersion", revision="15", version="3", level="0")
    ET.SubElement(header, "programMode").text = "0"
    ET.SubElement(header, "editMachine").text = "ISS"
    ET.SubElement(header, "editVersion", revision="10", version="0", level="0")
    
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-07:00")
    ET.SubElement(header, "lastEdit").text = now
    ET.SubElement(header, "lastOptimized").text = now

    # Configuración de Línea (Basada en tus archivos de Dialight)
    line_cfg = ET.SubElement(header, "lineConfiguration")
    ET.SubElement(line_cfg, "lineName", id="2").text = "Line 2"
    cfg = ET.SubElement(line_cfg, "configuration")
    m1 = ET.SubElement(cfg, "machine", no="1")
    ET.SubElement(m1, "typeCode").text = "3020VA"
    ET.SubElement(m1, "subTypeId").text = "75"
    ET.SubElement(m1, "name").text = "3020VAL"
    ET.SubElement(m1, "conveyorLane").text = "SINGLE"
    
    # 2. Core
    core = ET.SubElement(root, "core")
    
    # PWB Data (Vital para JANET)
    pwb = ET.SubElement(core, "pwbBasic")
    ET.SubElement(pwb, "pwbName").text = "GENERATED_PWB"
    ET.SubElement(pwb, "pwbSize", x="250000", y="200000", t="1600")
    
    pwb_cfg = ET.SubElement(core, "pwbConfiguration")
    ET.SubElement(pwb_cfg, "transferDirection").text = "LEFT_TO_RIGHT"
    
    # 3. Placement Data
    placement_data = ET.SubElement(core, "placementData")
    
    for i, row in df.iterrows():
        # Extraer datos usando el mapeo de columnas seleccionado por el usuario
        comp_id = str(row[col_map['Part']])
        designator = str(row[col_map['Ref']])
        # Conversión a micras (multiplicar por 1000 si el archivo viene en mm)
        pos_x = str(int(float(row[col_map['X']]) * 1000))
        pos_y = str(int(float(row[col_map['Y']]) * 1000))
        theta = str(int(float(row[col_map['Angle']]) * 1000))

        place = ET.SubElement(placement_data, "placement", index=str(i+1))
        ET.SubElement(place, "componentId").text = comp_id
        ET.SubElement(place, "designator").text = designator
        ET.SubElement(place, "coordinate", x=pos_x, y=pos_y, theta=theta)

    # 4. Model (Sección que faltaba en el programa anterior)
    model = ET.SubElement(root, "model")
    conv_data = ET.SubElement(model, "pwbConveyorData")
    ET.SubElement(conv_data, "pwbSupportCondition").text = "0"
    ET.SubElement(conv_data, "conveyorSpeed", value="400")

    return indent(root)

# Interfaz de Streamlit
st.set_page_config(page_title="KYpcb to ISS Converter", layout="wide")
st.title("🛠 SMT Converter: KYpcb ➔ ISS")

file = st.file_uploader("Sube tu archivo KYpcb (CSV o TXT)", type=['csv', 'txt', 'kypcb'])

if file:
    # Intentar leer el archivo
    try:
        df = pd.read_csv(file)
        st.write("### Vista previa de tus datos:")
        st.dataframe(df.head(5))
        
        cols = df.columns.tolist()
        
        st.sidebar.header("Mapeo de Columnas")
        st.sidebar.info("Selecciona qué columna corresponde a cada dato:")
        
        # Selectores para que el usuario elija la columna correcta
        col_ref = st.sidebar.selectbox("Designator (RefDes)", cols)
        col_part = st.sidebar.selectbox("Part Number / Component ID", cols)
        col_x = st.sidebar.selectbox("Coordenada X", cols)
        col_y = st.sidebar.selectbox("Coordenada Y", cols)
        col_angle = st.sidebar.selectbox("Ángulo", cols)
        
        mapping = {'Ref': col_ref, 'Part': col_part, 'X': col_x, 'Y': col_y, 'Angle': col_angle}

        if st.button("Generar archivo .ISS para JANET"):
            output_xml = create_iss_from_kypcb(df, mapping)
            
            st.success("¡Archivo generado!")
            st.download_button(
                label="📥 Descargar PROGRAMA_FINAL.iss",
                data=output_xml,
                file_name="PROGRAMA_FINAL.iss",
                mime="text/xml"
            )
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")