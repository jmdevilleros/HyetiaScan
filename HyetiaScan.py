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
# Globales
# =============================================================================================
if 'appconfig' not in st.session_state:
    st.session_state['appconfig'] = AppConfig()
if 'mediciones' not in st.session_state:
    st.session_state['mediciones'] = Precipitaciones()

# Variables de nombre breve para acceso a datos de sesión
apcfg = st.session_state['appconfig']
datos = st.session_state['mediciones']


# =============================================================================================
# Sección principal
# =============================================================================================

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
if st.toggle('Ver contenido', disabled=datos.df_lecturas is None):
    st.dataframe(datos.df_lecturas)