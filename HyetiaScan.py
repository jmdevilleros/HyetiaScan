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

import streamlit as st
import pandas as pd


# =============================================================================================
# Clases
# =============================================================================================

# ---------------------------------------------------------------------------------------------
class Precipitaciones:

    # -----------------------------------------------------------------------------------------
    def __init__(self):
        self.archivo_io  = None
        self.df_lecturas = None

        self.col_fechahora     = None
        self.col_precipitacion = None

    # -----------------------------------------------------------------------------------------
    def obtener_lecturas(self):
        # Reiniciar variables dependientes del contenido
        self.col_fechahora     = None
        self.col_precipitacion = None

        # TODO: Deteccion de encoding
        try:
            self.df_lecturas = pd.read_csv(self.archivo_io)
        except:
            self.df_lecturas = None

# ---------------------------------------------------------------------------------------------
class AppConfig:

    # -----------------------------------------------------------------------------------------
    def __init__(self):
        self.APPNAME = 'HyetiaScan'
        self.VERSION = '1.0'

    # -----------------------------------------------------------------------------------------
    def configurar_pagina(self, header=None, subheader=None):
        st.set_page_config(
            page_title=f'{self.APPNAME} {self.VERSION}', 
            layout='wide', 
            initial_sidebar_state='expanded', 
            page_icon=':rain_cloud:',
        )
        if header is not None:
            st.header(header)
        if subheader is not None:
            st.subheader(subheader)


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
apcfg.configurar_pagina(
    header=f'{apcfg.APPNAME} {apcfg.VERSION} :rain_cloud:',
    #subheader='Análisis de lluvias.',
)
st.write(
    '''
    Examine y analice eventos de precipitación pluviométrica.
    Detecte aguaceros de acuerdo con parámetros configurables.
    Genere gráficos de curvas de precipitación, frecuencia, Huff.
    '''
)
#st.divider()
st.subheader('Cargar archivo de precipitaciones.')
st.write(
    '''
    El archivo debe contener mediciones consecutivas en serie de 
    tiempo ordenada, con al menos una columna de fecha/hora (datetime)
    y al menos una columna numérica de precipitación.
    '''
)

# Cargar archivo y obtener registros
if datos.archivo_io is None:
    datos.archivo_io = st.file_uploader('Selección de archivo:', type=['csv'])
    datos.obtener_lecturas()
else:
    st.warning(f'Tiene cargado [**{datos.archivo_io.name}**]')
    st.warning(
        f'Columnas seleccionadas: ' 
        f'[**{datos.col_fechahora}**], '
        f'[**{datos.col_precipitacion}**]'
    )
    if st.button('Cargar otro archivo', type='primary'):
        datos.archivo_io = None
        st.rerun()
