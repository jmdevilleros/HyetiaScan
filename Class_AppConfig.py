# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias, detección de aguaceros y gráficos de curvas de Huff
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
# Octubre-Noviembre de 2023
#
# Archivo: AppConfig.py - Definición de clase para configuración de aplicación
# *********************************************************************************************


# =============================================================================================
# Bibliotecas
# =============================================================================================

import streamlit as st

# ---------------------------------------------------------------------------------------------
class AppConfig:

    # -----------------------------------------------------------------------------------------
    def __init__(self):
        self.APPNAME = 'HyetiaScan'
        self.VERSION = '1.1'

    # -----------------------------------------------------------------------------------------
    def configurar_pagina(self, header=None, subheader=None):
        st.set_page_config(
            page_title=f'{self.APPNAME} {self.VERSION}', 
            layout='wide', 
            initial_sidebar_state='auto', 
            page_icon=':rain_cloud:',
            menu_items={
                'About' : '''
                    ### HyetiaScan - Análisis de lluvias
                    - Juan Manuel de Villeros Arias
                    - Mónica Liliana Gallego Jaramillo

                    Noviembre/2023

                    Contacto: hyetiascan@teoktonos.com
                '''
            }
        )
        if header is not None:
            st.header(header)
        if subheader is not None:
            st.subheader(subheader)
            