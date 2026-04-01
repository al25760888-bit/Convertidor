import streamlit as st
import xml.etree.ElementTree as ET
from datetime import datetime
import io

# 1. Lógica para procesar el archivo KYPCB
def procesar_kypcb(archivo_subido):
    try:
        # Leemos el contenido del archivo subido
        string_data = archivo_subido.read()
        root_xml = ET.fromstring(string_data)
        componentes = root_xml.findall(".//component")
        
        datos = []
        for comp in componentes:
            datos.append({
                'name': comp.get('name', 'N/A'),
                'part': comp.get('part', 'N/A'),
                'x': comp.get('x', '0'),
                'y': comp.get('y', '0'),
                'rot': comp.get('rot', '0')
            })
        return datos
    except Exception as e:
        st.error(f"Error al analizar el archivo: {e}")
        return None

# 2. Generador de TXT (Limpio, sin encabezados)
def generar_txt_limpio(datos):
    output = io.StringIO()
    for c in datos:
        output.write(f"{c['name']} {c['part']} {c['x']} {c['y']} {c['rot']}\n")
    return output.getvalue()

# 3. Generador de archivo ISS (Formato Industrial)
def generar_iss(datos):
    fecha_actual = datetime.now().isoformat()
    xml_header = f'<?xml version="1.0" encoding="utf-8"?>\n<productionProgram>\n  <headerData>\n    <targetMachine>ISS</targetMachine>\n    <lastEdit>{fecha_actual}</lastEdit>\n  </headerData>\n  <core>\n    <placementData>'
    xml_footer = '\n    </placementData>\n  </core>\n</productionProgram>'
    
    cuerpo = ""
    for i, c in enumerate(datos):
        cuerpo += f"""
      <placement index="{i}">
        <placementId>{c['name']}</placementId>
        <baseCircuitId>A</baseCircuitId>
        <componentName>{c['part']}</componentName>
        <placementPosition x="{c['x']}" y="{c['y']}" rangeOver="False" />
        <placementAngle angle="{c['rot']}" />
        <attribute>
          <skip placement="NO" adhesive="NO" />
          <station placement="0" />
        </attribute>
      </placement>"""
    return xml_header + cuerpo + xml_footer

# --- INTERFAZ WEB (STREAMLIT) ---
st.set_page_config(page_title="SMT Dialight Converter", page_icon="⚙️")

st.title("⚙️ Conversor SMT Dialight")
st.markdown("Carga tu archivo `.kypcb` para generar archivos de producción.")

archivo = st.file_uploader("Subir archivo KYPCB", type=["kypcb"])

if archivo:
    datos = procesar_kypcb(archivo)
    
    if datos:
        st.success(f"✅ Se extrajeron {len(datos)} componentes con éxito.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Configuración TXT")
            nombre_txt = st.text_input("Nombre del archivo:", "datos_limpios.txt")
            txt_data = generar_txt_limpio(datos)
            st.download_button("Descargar TXT Limpio", data=txt_data, file_name=nombre_txt)
            
        with col2:
            st.subheader("Configuración ISS")
            nombre_iss = st.text_input("Nombre del archivo:", "programa_smt.iss")
            iss_data = generar_iss(datos)
            st.download_button("Descargar ISS", data=iss_data, file_name=nombre_iss)

        with st.expander("Ver vista previa de componentes"):
            st.table(datos)