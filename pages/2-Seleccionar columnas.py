# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias, detección de aguaceros y gráficos de curvas de Huff
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
# Octubre-Noviembre de 2023
#
# Archivo: "2-Seleccionar columnas.py" - Elegir columnas de fecha/hora y precipitación
# *********************************************************************************************


# =============================================================================================
# Bibliotecas
# =============================================================================================

import streamlit as st


# =============================================================================================
# Procedimientos y funciones
# =============================================================================================

def busca_indice(lista, elemento):
    if (lista == None) | (elemento == None):
        return None
    
    indice = lista.index(elemento)
    return None if indice == -1 else indice


# =============================================================================================
# Sección principal
# =============================================================================================

# Verificar que se haya iniciado en pagina principal
if 'lluvias' not in st.session_state:
    st.error('No ha cargado ningún archivo.')
    st.stop()

# Variables de nombre breve para acceso a datos de sesión
apcfg = st.session_state['appconfig']
datos = st.session_state['lluvias']

# Preparar página
apcfg.configurar_pagina('Seleccionar columnas. :white_check_mark:')

# Verificar
if datos.df_lecturas is None:
    st.error(f'No hay columnas para seleccionar.')
    st.stop()

# Procesar
col1, col2 = st.columns(2)
with col1:
    if st.toggle('Revisar tipos de columnas?'):
        st.table(datos.df_lecturas.dtypes)

st.write('Seleccione una columna de **fecha-hora** y una columna de **precipitación**.')
datos.col_fechahora = st.selectbox(
    'Fecha y hora', 
    datos.df_lecturas.columns, 
    index=busca_indice(list(datos.df_lecturas.columns), datos.col_fechahora),
)
datos.col_precipitacion = st.selectbox(
    'Precipitacion', 
    datos.df_lecturas.columns, 
    index=busca_indice(list(datos.df_lecturas.columns), datos.col_precipitacion),
)

with col2:
    esta_deshabilitado = (datos.col_fechahora is None) | (datos.col_precipitacion is None)
    if st.toggle('Previsualizar algunos datos?', disabled=esta_deshabilitado):
        st.table(datos.df_lecturas[[datos.col_fechahora, datos.col_precipitacion]].head(5))
