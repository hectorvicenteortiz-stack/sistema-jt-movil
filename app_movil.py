import streamlit as st
import uuid
from datetime import datetime
from supabase import create_client, Client

# --- CREDENCIALES DE SUPABASE ---
SUPABASE_URL = "https://piqelelxosnaexoecmpd.supabase.co"
SUPABASE_KEY = "sb_publishable_Q3I7sihSipRL2copimL_Jw_9NZyAxyj"

# Conectar a la nube
@st.cache_resource
def conectar_base_datos():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = conectar_base_datos()
except Exception as e:
    st.error(f"Error de conexión a internet: {e}")

# --- DISEÑO VISUAL PARA CELULARES ---
st.set_page_config(page_title="JT Logística Móvil", layout="centered")
st.title("🚚 JT Logística - Control en Ruta")

# Selección de Rol cómoda para pantalla táctil
rol = st.radio("Seleccione su Rol de Trabajo:", ["🚚 Personal en Terreno", "🔑 Oficina / Admin"], horizontal=True)

st.divider()

# --- MODO OFICINA: REGISTRAR ---
if rol == "🔑 Oficina / Admin":
    st.subheader("Registrar Nuevo Paquete")
    with st.form("formulario_registro", clear_on_submit=True):
        rem = st.text_input("Nombre del Remitente:")
        dest = st.text_input("Nombre del Destinatario:")
        dir_dest = st.text_input("Dirección de Destino:")
        btn_guardar = ft.Button if hasattr(ft, 'Button') else st.form_submit_button("Guardar en Oficina") # Adaptación visual alternativa
        
        if btn_guardar:
            if rem and dest and dir_dest:
                codigo = str(uuid.uuid4())[:8].upper()
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    supabase.table("paquetes").insert({
                        "id": codigo, "remitente": rem, "destinatario": dest, 
                        "destino": dir_dest, "estado": "En Centro de Distribución", "fecha_actualizacion": fecha,
                        "receptor_nombre": "", "receptor_rut": ""
                    }).execute()
                    st.success(f"¡Paquete registrado con éxito! Código: {codigo}")
                except Exception as ex:
                    st.error(f"Error en la nube: {ex}")
            else:
                st.warning("Por favor, rellena todos los campos.")

# --- MODO CHOFER: ACTUALIZAR ESTADO EN RUTA ---
st.subheader("Listado y Gestión de Entregas")

try:
    # Traer paquetes en tiempo real
    respuesta = supabase.table("paquetes").select("*").execute()
    lista_paquetes = respuesta.data
    
    if lista_paquetes:
        # Selector de paquete para el chofer
        opciones_paquetes = {f"{p['id']} - Para: {p['destinatario']} ({p['estado']})": p for p in lista_paquetes}
        paquete_seleccionado_texto = st.selectbox("Seleccione el paquete a gestionar:", list(opciones_paquetes.keys()))
        paquete = opciones_paquetes[paquete_seleccionado_texto]
        
        st.info(f"**Dirección de Entrega:** {paquete['destino']}")
        
        # Formulario de actualización de estado
        nuevo_estado = st.selectbox("Cambiar Estado a:", ["En tránsito", "En sucursal", "En reparto", "Entregado", "Devuelto"])
        
        # Activar campos de recepción solo si marca "Entregado"
        nombre_recibe = ""
        rut_recibe = ""
        if nuevo_estado == "Entregado":
            nombre_recibe = st.text_input("Nombre de quién recibe:")
            rut_recibe = st.text_input("RUT de quién recibe:")
            
        if st.button("Confirmar Estado / Validar Entrega", type="primary"):
            if nuevo_estado == "Entregado" and (not nombre_recibe or not rut_recibe):
                st.error("Obligatorio: Debes ingresar el Nombre y RUT de la persona que recibe el paquete.")
            else:
                fecha_act = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    supabase.table("paquetes").update({
                        "estado": nuevo_estado,
                        "fecha_actualizacion": fecha_act,
                        "receptor_nombre": nombre_recibe if nuevo_estado == "Entregado" else "",
                        "receptor_rut": rut_recibe if nuevo_estado == "Entregado" else ""
                    }).eq("id", paquete['id']).execute()
                    st.success(f"¡Paquete {paquete['id']} actualizado a {nuevo_estado} con éxito!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error al actualizar: {ex}")
    else:
        st.write("No hay paquetes registrados en la nube.")
except Exception as e:
    st.error(f"Error al cargar datos desde internet: {e}")