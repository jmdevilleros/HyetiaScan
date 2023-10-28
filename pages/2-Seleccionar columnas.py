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
apcfg.configurar_pagina('Seleccionar columnas. :white_check_mark:')

if datos.df_lecturas is None:
    st.error(f'No hay columnas para seleccionar.')
else:
    if st.toggle('Visualizar tipos de datos?'):
        st.table(datos.df_lecturas.dtypes)

    # TODO: asignar en objeto global de session
    # TODO: ubicar en el seleccionado anteriormente 
    # TODO: tratar de detectar en cual inicia?
    st.write('Seleccione una columna de **fecha-hora** y una columna de **precipitación**.')
    col_fechahora = st.selectbox('Fecha y hora', datos.df_lecturas.columns, index=None)
    col_precipitacion = st.selectbox('Precipitacion', datos.df_lecturas.columns, index=None)
