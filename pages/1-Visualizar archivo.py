# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias, detección de aguaceros y gráficos de curvas de Huff
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
# Octubre-Noviembre de 2023
#
# Archivo: "1-Visualizar archivo.py" - Ver contenido de archivo .csv origen de datos
# *********************************************************************************************


# =============================================================================================
# Bibliotecas
# =============================================================================================

import streamlit as st


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
apcfg.configurar_pagina('Visualizar archivo. :page_facing_up:')

# Verificar que haya lecturas
if datos.df_lecturas is None:
    st.error(f'No hay lecturas para visualizar.')
    st.stop()

# Visualizar
st.write(f'Contenido de {datos.archivo_io.name}')
if st.toggle('Incluir descripción?'):
    st.table(datos.df_lecturas.describe(include='all'))
st.toast('Desplegando archivo...')
st.dataframe(datos.df_lecturas)