import streamlit as st
import uuid
from datetime import datetime
from supabase import create_client, Client

# --- CREDENCIALES DE SUPABASE ---
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sb_publishable_Q3i7sihSiPrL2copimL_Jw_9NZyAxyj"

@st.cache_resource
def conectar_base_datos():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = conectar_base_datos()
except Exception as e:
    st.error(f"Error de conexión a internet: {e}")

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JT Logística Móvil", layout="centered")
st.title("🚚 JT Logística - Gestión Integral")

# Menú principal
opcion_menu = st.radio(
    "Seleccione la operación a realizar:", 
    ["📋 Gestión de Envíos", "🏢 Inventario Bodega", "📦 Registrar Retiro"], 
    horizontal=True
)

st.divider()

# =========================================================
# PESTAÑA: INVENTARIO EN BODEGA (MUESTRA ENVÍOS Y RETIROS)
# =========================================================
if opcion_menu == "🏢 Inventario Bodega":
    st.subheader(" Paquetes Físicos en Bodega / Centro de Distribución")
    st.write("A continuación se muestran los paquetes y retiros que se encuentran físicamente en bodega esperando despacho:")

    try:
        # Consultar paquetes en bodega o sucursal
        respuesta = supabase.table("paquetes").select("*").in_("estado", ["En Centro de Distribución", "En sucursal", "Retirado en Bodega"]).execute()
        paquetes_bodega = respuesta.data

        if paquetes_bodega:
            st.metric(label="Total de Cargas en Bodega", value=len(paquetes_bodega))
            
            for p in paquetes_bodega:
                # Identificar visualmente si es un envío normal o viene de un retiro
                icono = "📥" if p['id'].startswith("RET-") else "📦"
                with st.expander(f"{icono} Código: {p['id']} - Para: {p['destinatario']}"):
                    st.write(f"**Remitente / Cliente:** {p['remitente']}")
                    st.write(f"**Dirección:** {p['destino']}")
                    st.write(f"**Estado Actual:** {p['estado']}")
                    st.write(f"**Último Movimiento:** {p['fecha_actualizacion']}")
        else:
            st.success("¡Bodega al día! No hay bultos retenidos en almacenamiento en este momento.")
            
    except Exception as e:
        st.error(f"Error al cargar el inventario de bodega: {e}")

# =========================================================
# PESTAÑA: INGRESO DE PAQUETES RETIRADOS (CON COPIA A BODEGA)
# =========================================================
elif opcion_menu == "📦 Registrar Retiro":
    st.subheader("Formulario de Paquetes Retirados")
    
    with st.form("formulario_retiros", clear_on_submit=True):
        cliente = st.text_input("Cliente Solicitante (Empresa o Persona):")
        direccion = st.text_input("Dirección Exacta del Retiro:")
        telefono = st.text_input("Teléfono de Contacto:")
        chofer = st.text_input("Nombre del Chofer / Recolector:")
        comentarios = st.text_area("Comentarios o Descripción de la Carga (Ej: Destinatario Carlos Pérez, Destino Valparaíso):")
        
        btn_guardar_retiro = st.form_submit_button("Confirmar y Registrar Retiro")
        
        if btn_guardar_retiro:
            if cliente and direccion and telefono and chofer:
                id_retiro = "RET-" + str(uuid.uuid4())[:5].upper()
                fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                try:
                    # 1. Guardar en la tabla histórica de retiros
                    supabase.table("retiros").insert({
                        "id": id_retiro, "cliente_solicitante": cliente, "direccion_retiro": direccion,
                        "contacto_telefono": telefono, "fecha_hora_retiro": fecha_hora,
                        "chofer_asignado": chofer, "estado_retiro": "Retirado con Éxito", "comentarios": comentarios
                    }).execute()
                    
                    # 2. ACCIÓN INTELIGENTE: Insertar automáticamente en la tabla de bodega para que la oficina lo gestione
                    supabase.table("paquetes").insert({
                        "id": id_retiro,
                        "remitente": f"RETIRO: {cliente}",
                        "destinatario": "Por Clasificar (Ver comentarios)",
                        "destino": "Por Asignar",
                        "estado": "Retirado en Bodega",
                        "fecha_actualizacion": fecha_hora,
                        "receptor_nombre": "", "receptor_rut": ""
                    }).execute()
                    
                    st.success(f"¡Retiro registrado! Se envió una copia automática al Inventario de Bodega. Código: {id_retiro}")
                except Exception as ex:
                    st.error(f"Error al procesar: {ex}")
            else:
                st.warning("Por favor, rellena todos los campos obligatorios.")

    st.subheader("Historial de Retiros")
    try:
        res_retiros = supabase.table("retiros").select("*").execute()
        datos_retiros = res_retiros.data
        if datos_retiros:
            for r in datos_retiros:
                with st.expander(f"📦 {r['id']} - {r['cliente_solicitante']}"):
                    st.write(f"**Dirección Retiro:** {r['direccion_retiro']}")
                    st.write(f"**Chofer Recolector:** {r['chofer_asignado']}")
                    st.write(f"**Detalles de Carga:** {r['comentarios']}")
        else:
            st.write("No hay retiros registrados.")
    except Exception as e:
        pass

# =========================================================
# PESTAÑA: GESTIÓN DE ENVÍOS (OFICINA Y ENTREGAS)
# =========================================================
elif opcion_menu == "📋 Gestión de Envíos":
    rol = st.radio("Seleccione su Rol de Trabajo:", ["🚚 Personal en Terreno", "🔑 Oficina / Admin"], horizontal=True)
    st.divider()

    if rol == "🔑 Oficina / Admin":
        st.subheader("Registrar Nuevo Paquete (Oficina)")
        with st.form("formulario_registro", clear_on_submit=True):
            rem = st.text_input("Nombre del Remitente:")
            dest = st.text_input("Nombre del Destinatario:")
            dir_dest = st.text_input("Dirección de Destino:")
            btn_guardar = st.form_submit_button("Guardar en Oficina")
            
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

    st.subheader("Listado y Gestión de Entregas")
    try:
        respuesta = supabase.table("paquetes").select("*").execute()
        lista_paquetes = respuesta.data
        
        if lista_paquetes:
            opciones_paquetes = {f"{p['id']} - Para: {p['destinatario']} ({p['estado']})": p for p in lista_paquetes}
            paquete_seleccionado_texto = st.selectbox("Seleccione el paquete a gestionar:", list(opciones_paquetes.keys()))
            paquete = opciones_paquetes[paquete_seleccionado_texto]
            
            st.info(f"**Dirección de Entrega:** {paquete['destino']}")
            nuevo_estado = st.selectbox("Cambiar Estado a:", ["En tránsito", "En sucursal", "En reparto", "Entregado", "Devuelto"])
            
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
                        st.success(f"¡Paquete {paquete['id']} actualizado con éxito!")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error al actualizar: {ex}")
        else:
            st.write("No hay paquetes registrados en la nube.")
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
