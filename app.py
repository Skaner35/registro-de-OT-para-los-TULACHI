import streamlit as st
import pandas as pd
from datetime import datetime, date
from pathlib import Path

st.set_page_config(page_title="Registro de OT", page_icon="🛠️", layout="wide")

ENCABEZADOS = ["Fecha", "OT", "Horas_60", "Horas_100", "Periodo", "Foto"]
ARCHIVO_CSV = Path("registros_ot.csv")
CARPETA_FOTOS = Path("fotos_ot")
CARPETA_FOTOS.mkdir(parents=True, exist_ok=True)


def cargar_datos():
    if not ARCHIVO_CSV.exists():
        df_vacio = pd.DataFrame(columns=ENCABEZADOS)
        df_vacio.to_csv(ARCHIVO_CSV, index=False, encoding="utf-8")
        return df_vacio

    df = pd.read_csv(ARCHIVO_CSV, encoding="utf-8")
    if df.empty:
        return pd.DataFrame(columns=ENCABEZADOS)

    for col in ENCABEZADOS:
        if col not in df.columns:
            df[col] = ""
    return df[ENCABEZADOS]


def guardar_fila(fecha_str, ot_str, h60, h100, periodo_str, ruta_foto_str):
    df_actual = cargar_datos()
    nueva_fila = pd.DataFrame([{
        "Fecha": str(fecha_str),
        "OT": str(ot_str),
        "Horas_60": float(h60),
        "Horas_100": float(h100),
        "Periodo": str(periodo_str),
        "Foto": str(ruta_foto_str),
    }])
    df_actualizado = pd.concat([df_actual, nueva_fila], ignore_index=True)
    df_actualizado.to_csv(ARCHIVO_CSV, index=False, encoding="utf-8")


def calcular_periodo(fecha_obj):
    meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    if fecha_obj.day >= 26:
        mes = 1 if fecha_obj.month == 12 else fecha_obj.month + 1
        anio = fecha_obj.year + 1 if fecha_obj.month == 12 else fecha_obj.year
    else:
        mes = fecha_obj.month
        anio = fecha_obj.year
    return f"{meses[mes - 1]} {anio}"


# --- Limpieza segura de campos tras guardar ---
if st.session_state.get("limpiar_campos", False):
    st.session_state["input_ot"] = ""
    st.session_state["input_h60"] = 0.0
    st.session_state["input_h100"] = 0.0
    st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1
    st.session_state["limpiar_campos"] = False

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

st.title("🛠️ Registro de Órdenes de Trabajo (OT)")

col_form, col_tabla = st.columns([1, 2])

with col_form:
    st.subheader("Nuevo Registro")
    fecha = st.date_input("Fecha", value=date.today())
    ot = st.text_input("Número de OT", key="input_ot")
    h60 = st.number_input("Horas Extra 60%", min_value=0.0, step=0.5, key="input_h60")
    h100 = st.number_input("Horas Extra 100%", min_value=0.0, step=0.5, key="input_h100")
    foto = st.file_uploader(
        "Subir foto (JPG / PNG)",
        type=["jpg", "jpeg", "png"],
        key=f"foto_{st.session_state['uploader_key']}",
    )

    if st.button("Guardar Registro", type="primary", use_container_width=True):
        if not ot.strip():
            st.warning("Ingresa un número de OT antes de guardar.")
        else:
            ruta_foto = ""
            if foto is not None:
                extension = Path(foto.name).suffix.lower() or ".jpg"
                nombre_archivo = f"{fecha}_{ot.strip()}_{datetime.now().strftime('%H%M%S')}{extension}"
                destino = CARPETA_FOTOS / nombre_archivo
                destino.write_bytes(foto.getbuffer())
                ruta_foto = destino.as_posix()

            periodo = calcular_periodo(fecha)
            guardar_fila(fecha.strftime("%Y-%m-%d"), ot.strip(), h60, h100, periodo, ruta_foto)
            st.session_state["limpiar_campos"] = True
            st.success("Registro guardado correctamente.")
            st.rerun()

with col_tabla:
    st.subheader("Registros Guardados")
    df = cargar_datos()

    if df.empty:
        st.info("Aún no hay registros guardados.")
    else:
        periodos = ["Todos"] + sorted(df["Periodo"].dropna().unique().tolist(), reverse=True)
        periodo_sel = st.selectbox("Filtrar por Periodo", periodos)

        df_filtrado = df if periodo_sel == "Todos" else df[df["Periodo"] == periodo_sel]

        c1, c2, c3 = st.columns(3)
        c1.metric("Total OTs", len(df_filtrado))
        c2.metric("Total Horas 60%", f"{pd.to_numeric(df_filtrado['Horas_60'], errors='coerce').fillna(0).sum():.1f}")
        c3.metric("Total Horas 100%", f"{pd.to_numeric(df_filtrado['Horas_100'], errors='coerce').fillna(0).sum():.1f}")

        evento = st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

        filas_sel = evento.selection.rows
        if filas_sel:
            fila = df_filtrado.iloc[filas_sel[0]]
            posible_ruta = str(fila.get("Foto", "")).replace("\\", "/").strip()
            ruta_img = Path(posible_ruta) if posible_ruta else None
            if ruta_img and not ruta_img.exists():
                alternativa = CARPETA_FOTOS / ruta_img.name
                if alternativa.exists():
                    ruta_img = alternativa

            st.markdown("**Visualizador de Foto**")
            if ruta_img and ruta_img.is_file():
                st.image(str(ruta_img), caption=f"OT {fila['OT']} - {fila['Fecha']}", use_container_width=True)
            else:
                st.caption("Este registro no tiene foto guardada o el archivo ya no está en el servidor.")
