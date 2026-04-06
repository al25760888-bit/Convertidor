import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
import io
from datetime import datetime

# Función para dar formato legible al XML
def indent(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def create_iss_from_kypcb(df, col_map):
    root = ET.Element("productionProgram")
    
    # 1. Header Data (Copia fiel de tus archivos DRV485...)
    header = ET.SubElement(root, "headerData")
    ET.SubElement(header, "targetMachine").text = "ISS"
    ET.SubElement(header, "targetVersion", revision="15", version="3", level="0")
    ET.SubElement(header, "programMode").text = "0"
    ET.SubElement(header, "editMachine").text = "ISS"
    ET.SubElement(header, "editVersion", revision="10", version="0", level="0")
    
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-07:00")
    ET.SubElement(header, "lastEdit").text = now
    ET.SubElement(header, "lastOptimized").text = now

    # Configuración de Línea 2
    line_cfg = ET.SubElement(header, "lineConfiguration")
    ET.SubElement(line_cfg, "lineName", id="2").text = "Line 2"
    cfg = ET.SubElement(line_cfg, "configuration")
    m1 = ET.SubElement(cfg, "machine", no="1")
    ET.SubElement(m1, "typeCode").text = "3020VA"
    ET.SubElement(m1, "subTypeId").text = "75"
    ET.SubElement(m1, "name").text = "3020VAL"
    ET.SubElement(m1, "conveyorLane").text = "SINGLE"
    
    # 2. Core (Estructura de la placa)
    core = ET.SubElement(root, "core")
    
    # Datos básicos de PWB (Parámetros que JANET necesita)
    pwb = ET.SubElement(core, "pwbBasic")
    ET.SubElement(pwb, "pwbName").text = "GENERATED_PWB"
    ET.SubElement(pwb, "pwbSize", x="250000", y="200000", t="1600")
    
    pwb_cfg = ET.SubElement(core, "pwbConfiguration")
    ET.SubElement(pwb_cfg, "transferDirection").text = "LEFT_TO_RIGHT"
    
    # 3. Placement Data (Aquí procesamos tus columnas)
    placement_data = ET.SubElement(core, "placementData")
    
    for i, row in df.iterrows():
        try:
            # Extraemos los datos usando el mapeo seleccionado
            comp_id = str(row[col_map['Part']])
            designator = str(row[col_map['Ref']])
            
            # Conversión a micras (JANET usa unidades de 0.001mm)
            # Si tus datos están en mm, multiplicamos por 1000
            pos_x = str(int(float(row[col_map['X']]) * 1000))
            pos_y = str(int(float(row[col_map['Y']]) * 1000))
            theta = str(int(float(row[col_map['Angle']]) * 1000))

            place = ET.SubElement(placement_data, "placement", index=str(i+1))
            ET.SubElement(place, "componentId").text = comp_id
            ET.SubElement(place, "designator").text = designator
            ET.SubElement(place, "coordinate", x=pos_x, y=pos_y, theta=theta)
        except Exception:
            continue # Salta líneas vacías o con errores de formato

    # 4. Model (Sección necesaria para el manejo del transportador)
    model = ET.SubElement(root, "model")
    conv_data = ET.SubElement(model, "pwbConveyorData")
    ET.SubElement(conv_data, "pwbSupportCondition").text = "0"
    ET.SubElement(conv_data, "conveyorSpeed", value="400")

    return indent(root)

# Interfaz de Streamlit
st.set_page_config(page_title="Convertidor SMT Dialight", layout="wide")
st.title("⚙️ Convertidor KYpcb a ISS (Versión compatible JANET)")

uploaded_file = st.file_uploader("Sube tu archivo KYpcb", type=['csv', 'txt', 'kypcb'])

if uploaded_file:
    # Detectar formato y cargar datos
    try:
        # Leemos el archivo intentando detectar si es coma o espacio
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        st.write("### Vista previa de los datos detectados:")
        st.dataframe(df.head(10))
        
        columnas = df.columns.tolist()
        
        st.sidebar.header("Mapeo de Columnas")
        st.sidebar.write("Selecciona qué columna corresponde a cada dato del archivo KYpcb:")
        
        # Selectores dinámicos
        sel_ref = st.sidebar.selectbox("Designador (Ej: R1, C1)", columnas)
        sel_part = st.sidebar.selectbox("Part Number (Ej: 123-456)", columnas)
        sel_x = st.sidebar.selectbox("Coordenada X", columnas)
        sel_y = st.sidebar.selectbox("Coordenada Y", columnas)
        sel_angle = st.sidebar.selectbox("Ángulo", columnas)
        
        mapping = {'Ref': sel_ref, 'Part': sel_part, 'X': sel_x, 'Y': sel_y, 'Angle': sel_angle}

        if st.button("Generar Archivo .ISS"):
            iss_content = create_iss_from_kypcb(df, mapping)
            
            st.success("¡Archivo ISS generado exitosamente!")
            st.download_button(
                label="📥 Descargar PROGRAMA_FINAL.iss",
                data=iss_content,
                file_name="PROGRAMA_FINAL.iss",
                mime="text/xml"
            )
            
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")