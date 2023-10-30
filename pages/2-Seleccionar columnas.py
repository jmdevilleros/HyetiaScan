# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias, detección de aguaceros y gráficos de curvas de Huff
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
# Octubre-Noviembre de 2023
#
# Archivo: "2-Seleccionar columnas.py" - Elegir columnas de fecha/hora y precipitación
# *********************************************************************************************


# =============================================================================================
# Bibliotecas
# =============================================================================================

import streamlit as st


# =============================================================================================
# Procedimientos y funciones
# =============================================================================================

def busca_indice(lista, elemento):
    if (lista == None) | (elemento == None):
        return None
    
    indice = lista.index(elemento)
    return None if indice == -1 else indice


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

# Verificar
if datos.df_lecturas is None:
    st.error(f'No hay columnas para seleccionar.')
    st.stop()

# Selección de columnas
lista_columnas = list(datos.df_lecturas.columns)
with st.form('Selección de columnas'):
    fechahora = st.selectbox(
        'Fecha-hora', 
        lista_columnas, 
        index=busca_indice(lista_columnas, datos.col_fechahora),
    )
    precipitacion = st.selectbox(
        'Precipitacion', 
        lista_columnas, 
        index=busca_indice(lista_columnas, datos.col_precipitacion),
    )
    if st.form_submit_button('Aplicar columnas', type='primary'):
        if not datos.asignar_columnas_seleccionadas(fechahora, precipitacion):
            st.error('Al menos una de las columnas seleccionadas no tiene el tipo apropiado.')

# Opciones de previsualización
col1, col2 = st.columns(2)
with col1:
    if st.toggle('Revisar tipos de columnas?'):
        st.table(datos.df_lecturas.dtypes)
with col2:
    esta_deshabilitado = (datos.col_fechahora is None) | (datos.col_precipitacion is None)
    if st.toggle('Previsualizar algunos datos?', disabled=esta_deshabilitado):
        st.table(datos.df_lecturas[[datos.col_fechahora, datos.col_precipitacion]].head(5))
