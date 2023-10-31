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
if 'mediciones' not in st.session_state:
    st.error('No ha cargado ningún archivo.')
    st.stop()

# Variables de nombre breve para acceso a datos de sesión
apcfg = st.session_state['appconfig']
datos = st.session_state['mediciones']

# Preparar página
apcfg.configurar_pagina('Examinar eventos. :umbrella_with_rain_drops:')

# Verificar que haya datos y columnas seleccionadas
if datos.df_lecturas is None:
    st.error(f'No hay lecturas para procesar.')
    st.stop()
if (datos.col_fechahora is None) | (datos.col_precipitacion is None):
    st.error('Debe seleccionar columnas de **fecha/hora** y de **precipítación**.')
    st.stop()

# Detectar y mostrar intervalo de mediciones
if not datos.detectar_intervalo_mediciones():
    st.write('Error detectando intervalo entre mediciones.')
    st.stop()

# Mostrar intervalo detectado
st.caption(f'Intervalo detectado entre mediciones: {datos.intervalo_mediciones} minutos')

# Verificar si hay vacíos o "lagunas" en las mediciones
num_vacios, df_vacios = datos.detectar_vacios()
if num_vacios > 0:
    st.warning(f'Atención: {num_vacios} vacios detectados en la serie de mediciones.')
    c1, c2 = st.columns(2)
    with c1:
        rellenar = st.button('Rellenar con ceros?')
    with c2:
        ver_vacios = st.toggle('Ver detalle de vacíos', disabled=num_vacios <= 0)

    if ver_vacios:
        st.dataframe(df_vacios)
        recibidos = datos.df_lecturas.shape[0]
        st.caption('Faltantes:')

    if (rellenar):
        st.toast('Rellenando con ceros las mediciones faltantes...')
        datos.rellenar_vacios()
        st.rerun()
    else:
        st.error('No se pueden procesar eventos con vacíos en las lecturas.')
        st.stop()

# Calcular eventos
datos.calcular_eventos_precipitacion()
st.dataframe(datos.df_eventos)

