# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias, detección de aguaceros y gráficos de curvas de Huff
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
# Octubre-Noviembre de 2023
#
# Archivo: "1-Procesar lecturas.py" - Elegir columnas y calcular eventos de precipitación
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
apcfg.configurar_pagina(subheader='Procesar lecturas. :white_check_mark:')

# Verificar que ya se haya cargadpo archivo
if datos.df_lecturas is None:
    st.error(f'No hay columnas para seleccionar.')
    st.stop()

# ---------------------------------------------------------------------------------------------
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
    aplicar_cambios = st.form_submit_button('Aplicar', type='primary')

# ---------------------------------------------------------------------------------------------
# Opciones de previsualización
salida1, salida2 = st.columns(2)
with salida1:
    if st.toggle('Revisar tipos de columnas?'):
        st.table(datos.df_lecturas.dtypes)
with salida2:
    flag_visualizar_eventos = st.toggle('Visualizar eventos?')

# ---------------------------------------------------------------------------------------------
# Procesar cambios
if aplicar_cambios:
    if not datos.asignar_columnas_seleccionadas(fechahora, precipitacion):
        st.error('Al menos una de las columnas seleccionadas no tiene el tipo apropiado.')
        st.stop()

# ---------------------------------------------------------------------------------------------
# Visualizar eventos calculados
if flag_visualizar_eventos:
    st.divider()
    st.subheader('Eventos de precipitación generados:')
    st.dataframe(datos.df_eventos)
