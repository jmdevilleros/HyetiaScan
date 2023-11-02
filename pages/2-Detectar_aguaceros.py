# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias, detección de aguaceros y gráficos de curvas de Huff
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
# Octubre-Noviembre de 2023
#
# Archivo: "2-Detectar_aguaceros.py" - Detectar aguaceros según criterios
# *********************************************************************************************


# =============================================================================================
# Bibliotecas
# =============================================================================================

import streamlit as st


# =============================================================================================
# Sección principal
# =============================================================================================

# Verificar que se haya iniciado en pagina principal
if 'precipitaciones' not in st.session_state:
    st.error('No ha cargado ningún archivo.')
    st.stop()

# Variables de nombre breve para acceso a datos de sesión
apcfg = st.session_state['appconfig']
datos = st.session_state['precipitaciones']

# Preparar página
apcfg.configurar_pagina(subheader='Detectar aguaceros. :sleuth_or_spy:')

# Verificar que ya se hayan procesado medidiones y calculado eventos
if datos.df_eventos is None:
    st.error(f'No hay eventos para analizar.')
    st.stop()

# Definir parámetros para detectar aguaceros
with st.expander('Parámetros.', expanded=True):
    with st.form('Definir parámetros', ):
        datos.duracion_minima = st.slider(
            "Seleccionar duración mínima de aguacero (minutos)", 
            min_value=int(datos.intervalo_mediciones), 
            max_value=120, 
            value=datos.duracion_minima,
            step=int(datos.intervalo_mediciones)
        )

        datos.pausa_maxima = st.slider(
            "Seleccionar tiempo máximo de pausa (minutos)", 
            min_value=int(datos.intervalo_mediciones), 
            max_value=datos.duracion_minima, 
            value=datos.pausa_maxima,
            step=int(datos.intervalo_mediciones)
        )

        datos.intensidad_minima = st.slider(
            'Seleccione la intensidad mínima de aguacero',
            min_value=1,
            max_value=30,
            value=datos.intensidad_minima,
            step=1,
        )
        aplicar_parametros = \
            st.form_submit_button('Detectar', type='primary')

if aplicar_parametros:
    datos.detectar_aguaceros()

if datos.df_aguaceros is not None:
    st.write('**Aguaceros detectados:**')
    st.table(datos.df_aguaceros.describe())
    st.dataframe(datos.df_aguaceros)