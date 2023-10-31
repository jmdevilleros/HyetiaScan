# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias, detección de aguaceros y gráficos de curvas de Huff
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
# Octubre-Noviembre de 2023
#
# Archivo: HyetiaScan.py - Punto de entrada a aplicación Streamlit
# *********************************************************************************************


# =============================================================================================
# Bibliotecas
# =============================================================================================

from Class_AppConfig import AppConfig
from Class_Precipitaciones import Precipitaciones
import streamlit as st


# =============================================================================================
# Sección principal
# =============================================================================================

# Inicializar globales
if 'appconfig' not in st.session_state:
    st.session_state['appconfig'] = AppConfig()
if 'lluvias' not in st.session_state:
    st.session_state['lluvias'] = Precipitaciones()

# Variables de nombre breve para acceso a datos de sesión
apcfg = st.session_state['appconfig']
datos = st.session_state['lluvias']

# Preparar página
apcfg.configurar_pagina(subheader=f'{apcfg.APPNAME} {apcfg.VERSION} :rain_cloud:')
st.caption(
    '''
    Examine y analice eventos de precipitación pluviométrica.
    Detecte aguaceros de acuerdo con parámetros configurables.
    Genere gráficos de curvas de precipitación, frecuencia, Huff.
    '''
)

archivo_io = st.file_uploader('Selección de archivo:', type=['csv'])
if archivo_io is not None:
    datos.obtener_lecturas(archivo_io)

# Descripción
st.caption(
    '''
    El archivo debe contener mediciones consecutivas en serie de 
    tiempo ordenada, con al menos una columna de fecha/hora (datetime)
    y al menos una columna numérica de precipitación.
    '''
)

# Visualizar?
if datos.df_lecturas is not None:
    if st.toggle('Ver contenido'):
        st.dataframe(datos.df_lecturas)