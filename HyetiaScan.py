# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias, detección de aguaceros y gráficos de curvas de Huff
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
# Octubre-Noviembre de 2023
# *********************************************************************************************


# =============================================================================================
# Bibliotecas
# =============================================================================================

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================================
# Clases
# =============================================================================================

# ---------------------------------------------------------------------------------------------
class Precipitaciones:

    # -----------------------------------------------------------------------------------------
    def __init__(self):
        self.archivo_io = None
        self.df_lecturas   = None

    # -----------------------------------------------------------------------------------------
    def obtener_lecturas(self):
        # TODO: Deteccion de encoding
        try:
            self.df_lecturas = pd.read_csv(self.archivo_io)
        except:
            self.df_lecturas = None

# ---------------------------------------------------------------------------------------------
class AppConfig:
    APPNAME = 'HyetiaScan'
    VERSION = '1.0'

    # -----------------------------------------------------------------------------------------
    def configurar_pagina(self, header=None):
        st.set_page_config(
            page_title=f'{self.APPNAME} {self.VERSION}', 
            layout='wide', 
            initial_sidebar_state='expanded', 
            page_icon=':rain_cloud:',
        )
        if header is not None:
            st.header(header)


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
apcfg.configurar_pagina('Análisis de lluvias. :rain_cloud:')
st.write(
    '''
    Cargue información desde un archivo *.csv* con datos de precipitaciones. 
    Debe contener mediciones consecutivas en serie de tiempo ordenada,
    con al menos una columna de fecha/hora (datetime) y al menos una columna 
    numérica de precipitación.
    '''
)

# Cargar archivo y obtener registros
if datos.archivo_io is None:
    datos.archivo_io = st.file_uploader('Selección de archivo:', type=['csv'])
    datos.obtener_lecturas()
else:
    st.warning(f'Tiene cargado **{datos.archivo_io.name}**')
    if st.button('Cargar otro archivo', type='primary'):
        datos.archivo_io = None
        st.rerun()

# st.write(f'archivo_io: {datos.archivo_io is not None}')
# st.write(f'  df_datos: {datos.df_datos is not None}')
