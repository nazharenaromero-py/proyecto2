import streamlit as st  # pyright: ignore[reportMissingImports]
import pandas as pd  # pyright: ignore[reportMissingModuleSource]
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Gestión Centros Deportivos", layout="wide")
st.title("Sistema de Gestión de Centros Deportivos")

DATABASE_URL = "mysql+pymysql://root:ROOT@localhost:3306/gestion_centros_deportivos"
engine = create_engine(DATABASE_URL)

def leer_tabla(query):
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)

try:
    tablas = [
        "comuna",
        "centro_deportivo",
        "espacio_deportivo",
        "actividad",
        "programacion_actividad",
        "inscripcion",
        "evaluacion",
        "orden_mantencion",
    ]

    st.subheader("Resumen de registros poblados")
    cols = st.columns(4)
    for idx, tabla in enumerate(tablas):
        df_count = leer_tabla(f"SELECT COUNT(*) AS total FROM {tabla}")
        total = int(df_count["total"].iloc[0])
        cols[idx % 4].metric(label=tabla, value=total)

    st.divider()
    tabla_elegida = st.selectbox("Selecciona una tabla para ver sus datos:", tablas)
    limite = st.slider("Cantidad de filas a mostrar:", min_value=5, max_value=100, value=20)

    df_datos = leer_tabla(f"SELECT * FROM {tabla_elegida} LIMIT {limite}")
    st.dataframe(df_datos, use_container_width=True)

except Exception as e:
    st.error(f"Error de conexión o consulta: {e}")