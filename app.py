from datetime import date, datetime
from pathlib import Path
import csv
import streamlit as st

st.set_page_config(page_title="Registro de los TULACHI", layout="wide")

CARPETA_FOTOS = Path("fotos_ot")
CARPETA_FOTOS.mkdir(exist_ok=True)

ARCHIVO_CSV = Path("registro_diario.csv")
if "form_id" not in st.session_state:
    st.session_state.form_id = 0
if "ot_input" not in st.session_state:
    st.session_state.ot_input = ""
if "h60_input" not in st.session_state:
    st.session_state.h60_input = 0.0
if "h100_input" not in st.session_state:
    st.session_state.h100_input = 0.0
if "limpiar_campos" not in st.session_state:
    st.session_state.limpiar_campos = False

if st.session_state.limpiar_campos:
    st.session_state.ot_input = ""
    st.session_state.h60_input = 0.0
    st.session_state.h100_input = 0.0
    st.session_state.form_id += 1
    st.session_state.limpiar_campos = False
ENCABEZADOS = ["Fecha", "Turno", "OT", "Horas extras 60%", "Horas extras 100%", "Ruta_Foto"]

if "ultimo_guardado" not in st.session_state:
    st.session_state.ultimo_guardado = None

if st.session_state.ultimo_guardado:
    mensaje_ok, ruta_ok = st.session_state.ultimo_guardado
    st.success(mensaje_ok)
    if ruta_ok:
        st.caption(ruta_ok)

st.title("Registro de los TULACHI")

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    fecha = st.date_input("Fecha")
with c2:
    turno = st.selectbox("Turno", ["Día", "Noche"])
with c3:
    ot = st.text_input("OT", placeholder="Ej: OT123", key="ot_input")
with c4:
    horas_60 = st.number_input(
        "Horas extras 60%", min_value=0.0, step=0.5, format="%.1f", key="h60_input"
    )
with c5:
    horas_100 = st.number_input(
        "Horas extras 100%", min_value=0.0, step=0.5, format="%.1f", key="h100_input"
    )
col_btn, col_up = st.columns([1, 2])
with col_btn:
    guardar = st.button("Guardar registro", type="secondary")
with col_up:
    foto = st.file_uploader(
    "Adjuntar foto",
    type=["jpg", "jpeg", "png"],
    key=f"foto_uploader_{st.session_state.form_id}",
)

if guardar:
    if not ot.strip():
        st.error("Debes ingresar el número de OT.")
    else:
        ruta_foto = ""
        if foto is not None:
            extension = Path(foto.name).suffix.lower() or ".jpg"
            marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
            ot_limpia = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in ot.strip())
            destino_foto = CARPETA_FOTOS / f"{marca_tiempo}_{ot_limpia}{extension}"
            destino_foto.write_bytes(foto.getbuffer())
            ruta_foto = str(destino_foto)

        existe = ARCHIVO_CSV.exists()
        with open(ARCHIVO_CSV, "a", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            if not existe:
                escritor.writerow(ENCABEZADOS)
            escritor.writerow([
    str(fecha),
    turno,
    ot.strip(),
    f"{horas_60:.1f}",
    f"{horas_100:.1f}",
    ruta_foto,
])

        st.session_state.ultimo_guardado = (
            "Guardado con éxito",
            ruta_foto if ruta_foto else "Registro guardado sin foto.",
        )
        st.session_state.limpiar_campos = True
        st.rerun()
    

MESES_ES = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}

def obtener_clave_periodo(fecha_str: str):
    try:
        f = date.fromisoformat(str(fecha_str).strip()[:10])
    except ValueError:
        return ("9999-99", "Sin fecha")

    if f.day >= 21:
        if f.month == 12:
            anio_cierre, mes_cierre = f.year + 1, 1
        else:
            anio_cierre, mes_cierre = f.year, f.month + 1
    else:
        anio_cierre, mes_cierre = f.year, f.month

    clave_orden = f"{anio_cierre:04d}-{mes_cierre:02d}"
    nombre_mes = MESES_ES[mes_cierre]
    return (clave_orden, nombre_mes, anio_cierre)

def a_float(valor) -> float:
    try:
        return float(str(valor or "0").replace(",", ".").strip())
    except ValueError:
        return 0.0

datos = []
if ARCHIVO_CSV.exists():
    with open(ARCHIVO_CSV, "r", newline="", encoding="utf-8") as f:
        filas = list(csv.reader(f))
    if len(filas) > 1:
        enc_csv = filas[0]
        for fila in filas[1:]:
            ajustada = (fila + [""] * len(enc_csv))[:len(enc_csv)]
            datos.append(dict(zip(enc_csv, ajustada)))

periodos_map = {}
for fila in datos:
    clave_orden, nombre_mes, anio_cierre = obtener_clave_periodo(fila.get("Fecha", ""))
    if clave_orden not in periodos_map:
        periodos_map[clave_orden] = {
            "nombre_mes": nombre_mes,
            "anio_cierre": anio_cierre,
            "filas": [],
            "total_60": 0.0,
            "total_100": 0.0,
        }
    h60 = a_float(fila.get("Horas extras 60%", 0))
    h100 = a_float(fila.get("Horas extras 100%", 0))
    periodos_map[clave_orden]["filas"].append(fila)
    periodos_map[clave_orden]["total_60"] += h60
    periodos_map[clave_orden]["total_100"] += h100

claves_ordenadas = sorted(periodos_map.keys(), reverse=True)
etiquetas_periodos = []
for clave in claves_ordenadas:
    info = periodos_map[clave]
    total_mes = info["total_60"] + info["total_100"]
    if clave == "9999-99":
        etiquetas_periodos.append(f"Sin fecha = {total_mes:g}")
    else:
        etiquetas_periodos.append(f"Horas extras {info['nombre_mes']} = {total_mes:g}")

fila_sel = None
filas_periodo = []

col_izq, col_der = st.columns([1.8, 1])

with col_izq:
    st.subheader("Registros guardados")
    if datos:
        periodo_elegido = st.selectbox("Seleccionar periodo (21 al 20)", etiquetas_periodos)
        clave_activa = claves_ordenadas[etiquetas_periodos.index(periodo_elegido)]
        info_activa = periodos_map[clave_activa]
        filas_periodo = info_activa["filas"]
        total_60 = info_activa["total_60"]
        total_100 = info_activa["total_100"]
        total_general = total_60 + total_100

        st.info(
            f"Desglose {info_activa['nombre_mes']}: **{total_general:g} hrs totales** "
            f"(**{total_100:g}** al 100% y **{total_60:g}** al 60%)"
        )

        evento = st.dataframe(
            filas_periodo,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )
        filas_elegidas = evento.selection.rows
        if filas_elegidas:
            fila_sel = filas_periodo[filas_elegidas[0]]
        else:
            fila_sel = filas_periodo[-1]
    else:
        st.info("El archivo CSV aún no tiene registros.")

with col_der:
    st.subheader("Visualizador de Foto")
    if fila_sel:
        st.caption(
            f"OT {fila_sel.get('OT', 'Sin OT')} · {fila_sel.get('Turno', '')} · {fila_sel.get('Fecha', '')} · "
            f"60%: {fila_sel.get('Horas extras 60%', '0')} | 100%: {fila_sel.get('Horas extras 100%', '0')}"
        )
        posible_ruta = ""
        for clave, valor in fila_sel.items():
            if "ruta" in clave.lower() or "foto" in clave.lower():
                posible_ruta = str(valor or "").strip()
                break
        if not posible_ruta:
            for valor in fila_sel.values():
                texto_val = str(valor or "").strip()
                if texto_val.lower().endswith((".jpg", ".jpeg", ".png")):
                    posible_ruta = texto_val
                    break

        ruta_img = Path(posible_ruta)
        if posible_ruta and not ruta_img.exists():
            alternativa = CARPETA_FOTOS / ruta_img.name
            if alternativa.exists():
                ruta_img = alternativa

        if posible_ruta and ruta_img.exists():
            st.image(str(ruta_img), caption=f"Foto: {ruta_img.name}", use_container_width=True)
        else:
            st.caption("Este registro no tiene foto guardada o no se encontró el archivo.")
    else:
        st.caption("Haz clic en un registro de la tabla para ver su foto.")
