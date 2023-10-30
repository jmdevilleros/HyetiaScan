# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias, detección de aguaceros y gráficos de curvas de Huff
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
# Octubre-Noviembre de 2023
#
# Archivo: "3-Examinar eventos.py" - Preprocesar datos y examinar eventos de precipitación
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
apcfg.configurar_pagina('Examinar eventos. :umbrella_with_rain_drops:')

# Verificar que haya datos y columnas seleccionadas
if datos.df_lecturas is None:
    st.error(f'No hay eventos para visualizar.')
    st.stop()
if (datos.col_fechahora is None) | (datos.col_precipitacion is None):
    st.error('Debe seleccionar columnas de **fecha/hora** y de **precipítación**.')
    st.stop()

# Procesar
st.dataframe(datos.df_eventos)
