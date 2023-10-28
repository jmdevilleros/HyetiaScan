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
apcfg.configurar_pagina('Visualizar archivo. :page_facing_up:')

if datos.df_lecturas is None:
    st.error(f'No hay lecturas para visualizar.')
else:
    st.write(f'Contenido de {datos.archivo_io.name}')
    if st.toggle('Incluir descripción?'):
        st.table(datos.df_lecturas.describe(include='all'))
    st.dataframe(datos.df_lecturas)