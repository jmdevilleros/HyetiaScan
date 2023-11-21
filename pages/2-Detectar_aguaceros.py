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
        zona_fecha1, zona_fecha2 = st.columns(2)
        datos.primera_fecha = zona_fecha1.date_input(
            'Seleccionar fecha inicial:', 
            value=datos.primera_fecha,
            min_value=datos.df_mediciones[datos.col_fechahora].min(),
            max_value=datos.df_mediciones[datos.col_fechahora].max(),
        )

        datos.ultima_fecha = zona_fecha2.date_input(
            'Seleccionar fecha final:', 
            value=datos.ultima_fecha,
            min_value=datos.df_mediciones[datos.col_fechahora].min(),
            max_value=datos.df_mediciones[datos.col_fechahora].max(),
        )

        zona_minima, zona_maxima = st.columns(2)
        datos.duracion_minima = zona_minima.slider(
            "Duración mínima (minutos)", 
            min_value=int(datos.intervalo_mediciones), 
            max_value=int(datos.duracion_maxima), 
            value=datos.duracion_minima,
            step=int(datos.intervalo_mediciones),
        )


        datos.duracion_maxima = zona_maxima.slider(
            "Duración maxima (minutos)", 
            min_value=int(datos.duracion_minima), 
            max_value=int(datos.duracion_tope), 
            value=datos.duracion_maxima,
            step=int(datos.intervalo_mediciones),
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
            max_value=50,
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