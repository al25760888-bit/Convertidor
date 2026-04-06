import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
import io
from datetime import datetime

def indent(elem):
    """Añade indentación para que el XML sea legible (pretty-print)."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def create_iss_from_kypcb(kypcb_content):
    # Intentar leer el archivo KYpcb (asumiendo formato CSV/Texto basado en columnas)
    try:
        df = pd.read_csv(io.StringIO(kypcb_content), sep=None, engine='python')
    except Exception as e:
        return None, f"Error al leer KYpcb: {e}"

    # Races del XML según los archivos operativos
    root = ET.Element("productionProgram")
    
    # 1. Header Data (Copia exacta de los archivos funcionales)
    header = ET.SubElement(root, "headerData")
    ET.SubElement(header, "targetMachine").text = "ISS"
    ET.SubElement(header, "targetVersion", revision="15", version="3", level="0")
    ET.SubElement(header, "programMode").text = "0"
    ET.SubElement(header, "editMachine").text = "ISS"
    ET.SubElement(header, "editVersion", revision="10", version="0", level="0")
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-07:00")
    ET.SubElement(header, "lastEdit").text = now
    ET.SubElement(header, "lastOptimized").text = now

    # 2. Line Configuration (Estructura de la máquina 3020VA)
    line_cfg = ET.SubElement(header, "lineConfiguration")
    ET.SubElement(line_cfg, "lineName", id="2").text = "Line 2"
    cfg = ET.SubElement(line_cfg, "configuration")
    m1 = ET.SubElement(cfg, "machine", no="1")
    ET.SubElement(m1, "typeCode").text = "3020VA"
    ET.SubElement(m1, "subTypeId").text = "75"
    ET.SubElement(m1, "name").text = "3020VAL"
    ET.SubElement(m1, "conveyorLane").text = "SINGLE"
    
    # 3. Core (Donde vive la lógica de la placa y componentes)
    core = ET.SubElement(root, "core")
    
    # PWB Data (Faltaba en el anterior)
    pwb = ET.SubElement(core, "pwbBasic")
    ET.SubElement(pwb, "pwbName").text = "GENERATED_PWB"
    ET.SubElement(pwb, "pwbSize", x="250000", y="200000", t="1600") # Valores ejemplo en micras
    
    pwb_cfg = ET.SubElement(core, "pwbConfiguration")
    ET.SubElement(pwb_cfg, "transferDirection").text = "LEFT_TO_RIGHT"
    
    # 4. Placement Data (Iteración sobre el DataFrame de KYpcb)
    # Nota: Aquí debes mapear las columnas reales de tu archivo KYpcb
    # Supongamos columnas: 'Designator', 'X', 'Y', 'Angle', 'Part_Number'
    placement_data = ET.SubElement(core, "placementData")
    for i, row in df.iterrows():
        place = ET.SubElement(placement_data, "placement", index=str(i+1))
        ET.SubElement(place, "componentId").text = str(row.get('Part_Number', 'UNKNOWN'))
        ET.SubElement(place, "designator").text = str(row.get('Designator', f'REF{i}'))
        ET.SubElement(place, "coordinate", 
                      x=str(int(row.get('X', 0) * 1000)), 
                      y=str(int(row.get('Y', 0) * 1000)), 
                      theta=str(int(row.get('Angle', 0) * 1000)))

    # 5. Model (Sección crítica para el transportador de JANET)
    model = ET.SubElement(root, "model")
    conv_data = ET.SubElement(model, "pwbConveyorData")
    ET.SubElement(conv_data, "pwbSupportCondition").text = "0"
    # Añadir parámetros de motor/velocidad que JANET espera
    ET.SubElement(conv_data, "conveyorSpeed", value="400")

    return indent(root), None

# Interfaz de Streamlit
st.set_page_config(page_title="Convertidor KYpcb a ISS", page_icon="⚙️")
st.title("🛠 Convertidor KYpcb a ISS (Versión Dialight)")
st.write("Sube tu archivo KYpcb para generar un archivo .iss compatible con JANET.")

uploaded_file = st.file_uploader("Elegir archivo KYpcb", type=['txt', 'csv', 'kypcb'])

if uploaded_file is not None:
    content = uploaded_file.getvalue().decode("utf-8")
    
    if st.button("Generar Archivo ISS"):
        iss_xml, error = create_iss_from_kypcb(content)
        
        if error:
            st.error(error)
        else:
            st.success("¡Archivo generado correctamente!")
            st.download_button(
                label="Descargar PROGRAMA_CORREGIDO.iss",
                data=iss_xml,
                file_name="PROGRAMA_CORREGIDO.iss",
                mime="application/xml"
            )
            st.code(iss_xml[:1000] + "...", language='xml')