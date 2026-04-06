import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
import io
from datetime import datetime

def indent(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def create_iss_from_kypcb(df, col_map):
    root = ET.Element("productionProgram")
    
    # 1. Header Data
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
    
    # 2. Core
    core = ET.SubElement(root, "core")
    pwb = ET.SubElement(core, "pwbBasic")
    ET.SubElement(pwb, "pwbName").text = "GENERATED_PWB"
    ET.SubElement(pwb, "pwbSize", x="250000", y="200000", t="1600")
    
    pwb_cfg = ET.SubElement(core, "pwbConfiguration")
    ET.SubElement(pwb_cfg, "transferDirection").text = "LEFT_TO_RIGHT"
    
    # 3. Placement Data
    placement_data = ET.SubElement(core, "placementData")
    
    idx = 1
    for _, row in df.iterrows():
        try:
            # Usar el mapeo seleccionado
            c_name = str(row[col_map['name']]).strip()
            c_part = str(row[col_map['part']]).strip()
            c_x = str(int(float(row[col_map['x']]) * 1000))
            c_y = str(int(float(row[col_map['y']]) * 1000))
            c_rot = str(int(float(row[col_map['rot']]) * 1000))

            place = ET.SubElement(placement_data, "placement", index=str(idx))
            ET.SubElement(place, "componentId").text = c_part
            ET.SubElement(place, "designator").text = c_name
            ET.SubElement(place, "coordinate", x=c_x, y=c_y, theta=c_rot)
            idx += 1
        except:
            continue

    # 4. Model
    model = ET.SubElement(root, "model")
    conv_data = ET.SubElement(model, "pwbConveyorData")
    ET.SubElement(conv_data, "pwbSupportCondition").text = "0"
    ET.SubElement(conv_data, "conveyorSpeed", value="400")

    return indent(root)

# --- Streamlit ---
st.set_page_config(page_title="SMT Converter Dialight", layout="wide")
st.title("🛠 Convertidor KYpcb a ISS (Multi-Formato)")

archivo = st.file_uploader("Sube tu archivo KYpcb", type=['csv', 'txt', 'kypcb'])

if archivo:
    try:
        # Intento de lectura automático
        df = pd.read_csv(archivo, sep=None, engine='python')
        st.write("### Vista previa del archivo subido:")
        st.dataframe(df.head(5))
        
        columnas = df.columns.tolist()
        
        st.sidebar.header("Configuración de Columnas")
        st.sidebar.info("Si los nombres no coinciden, cámbialos aquí:")

        # Función para buscar coincidencia inteligente
        def find_col(options, targets):
            for t in targets:
                for o in options:
                    if t.lower() in o.lower(): return o
            return options[0]

        # Selección de columnas (con sugerencia automática)
        sel_name = st.sidebar.selectbox("Columna de Nombre/Designador", columnas, index=columnas.index(find_col(columnas, ['component name', 'name'])))
        sel_part = st.sidebar.selectbox("Columna de Part Number", columnas, index=columnas.index(find_col(columnas, ['part'])))
        sel_x = st.sidebar.selectbox("Columna X", columnas, index=columnas.index(find_col(columnas, ['x'])))
        sel_y = st.sidebar.selectbox("Columna Y", columnas, index=columnas.index(find_col(columnas, ['y'])))
        sel_rot = st.sidebar.selectbox("Columna Ángulo/Rot", columnas, index=columnas.index(find_col(columnas, ['rot', 'angulo'])))

        mapping = {'name': sel_name, 'part': sel_part, 'x': sel_x, 'y': sel_y, 'rot': sel_rot}

        if st.button("Generar Archivo .ISS"):
            xml_final = create_iss_from_kypcb(df, mapping)
            st.success("¡Archivo generado!")
            st.download_button("📥 Descargar PROGRAMA.iss", xml_final, "PROGRAMA_DIALIGHT.iss", "text/xml")
            
    except Exception as e:
        st.error(f"Error: {e}")