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

def create_iss_from_kypcb(df, col_map):
    root = ET.Element("productionProgram")
    
    # 1. Cabecera (Header) - Configuración exacta de Dialight
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
    
    # 2. Core y PWB Basic (Esto es lo que JANET requiere para abrir el archivo)
    core = ET.SubElement(root, "core")
    pwb = ET.SubElement(core, "pwbBasic")
    ET.SubElement(pwb, "pwbName").text = "PWB_GENERADO"
    # Dimensiones estándar en micras
    ET.SubElement(pwb, "pwbSize", x="250000", y="200000", t="1600")
    
    pwb_cfg = ET.SubElement(core, "pwbConfiguration")
    ET.SubElement(pwb_cfg, "transferDirection").text = "LEFT_TO_RIGHT"
    
    # 3. Placement Data (Datos de componentes)
    placement_data = ET.SubElement(core, "placementData")
    
    idx = 1
    for _, row in df.iterrows():
        try:
            # Extraemos los datos usando el mapeo que tú selecciones en la web
            c_name = str(row[col_map['name']]).strip()
            c_part = str(row[col_map['part']]).strip()
            # Conversión de mm a micras (multiplicar por 1000)
            c_x = str(int(float(row[col_map['x']]) * 1000))
            c_y = str(int(float(row[col_map['y']]) * 1000))
            c_rot = str(int(float(row[col_map['rot']]) * 1000))

            place = ET.SubElement(placement_data, "placement", index=str(idx))
            ET.SubElement(place, "componentId").text = c_part
            ET.SubElement(place, "designator").text = c_name
            ET.SubElement(place, "coordinate", x=c_x, y=c_y, theta=c_rot)
            idx += 1
        except:
            continue # Si una fila está mal, la salta y no bloquea el programa

    # 4. Model (Crucial para JANET)
    model = ET.SubElement(root, "model")
    conv_data = ET.SubElement(model, "pwbConveyorData")
    ET.SubElement(conv_data, "pwbSupportCondition").text = "0"
    ET.SubElement(conv_data, "conveyorSpeed", value="400")

    return indent(root)

# --- Interfaz Streamlit ---
st.set_page_config(page_title="Convertidor Dialight SMT", layout="wide")
st.title("🛠 SMT Converter: KYpcb ➔ ISS")

archivo = st.file_uploader("Sube tu archivo KYpcb (CSV o TXT)", type=['csv', 'txt', 'kypcb'])

if archivo:
    try:
        # Detectar el separador automáticamente
        df = pd.read_csv(archivo, sep=None, engine='python')
        
        st.write("### ✅ Archivo cargado correctamente")
        st.write("Verifica que tus datos aparezcan en columnas separadas abajo:")
        st.dataframe(df.head(10))
        
        columnas = df.columns.tolist()
        
        # BARRA LATERAL: Aquí es donde tú seleccionas el nombre real
        st.sidebar.header("⚙️ Configuración Manual")
        st.sidebar.write("Selecciona qué columna corresponde a cada dato:")
        
        # Estos selectores evitan el error de "KeyError"
        sel_name = st.sidebar.selectbox("Designador (Name)", columnas)
        sel_part = st.sidebar.selectbox("Part Number (Part)", columnas)
        sel_x = st.sidebar.selectbox("Coordenada X", columnas)
        sel_y = st.sidebar.selectbox("Coordenada Y", columnas)
        sel_rot = st.sidebar.selectbox("Ángulo (Rot)", columnas)
        
        mapping = {
            'name': sel_name, 
            'part': sel_part, 
            'x': sel_x, 
            'y': sel_y, 
            'rot': sel_rot
        }

        if st.button("🚀 Generar y Descargar Archivo ISS"):
            resultado_xml = create_iss_from_kypcb(df, mapping)
            st.success("¡Programa generado con éxito!")
            st.download_button(
                label="📥 Descargar PROGRAMA_FINAL.iss",
                data=resultado_xml,
                file_name="PROGRAMA_FINAL.iss",
                mime="text/xml"
            )
            
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.info("Sugerencia: Asegúrate de que el archivo KYpcb sea un archivo de texto con columnas claras.")