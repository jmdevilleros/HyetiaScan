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
if 'precipitaciones' not in st.session_state:
    st.error('No ha cargado ningún archivo.')
    st.stop()

# Variables de nombre breve para acceso a datos de sesión
apcfg = st.session_state['appconfig']
datos = st.session_state['precipitaciones']

# Preparar página
apcfg.configurar_pagina(subheader='Procesar lecturas. :white_check_mark:')

# Verificar que ya se haya cargadpo archivo
if datos.df_origen is None:
    st.error(f'No hay columnas para seleccionar.')
    st.stop()

# Encabezado con información
st.caption(f'Archivo: [:orange[{datos.nombre}]]')
salida_intervalo = st.empty()

salida_estado, _    = st.columns(2)
salida1, salida2, _ = st.columns(3)
salida3, salida4    = st.columns(2)

# Selección de columnas

lista_columnas = list(datos.df_origen.columns)
salida1.write('Selección de columnas:')
with salida3:
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
        aplicar_cambios = st.form_submit_button('Procesar', type='primary')
if salida2.toggle('Ver tipos?'):
    salida4.dataframe(datos.df_origen.dtypes, column_config={'': 'Columna', '0': 'Tipo'})

if aplicar_cambios:
    # Asignar columnas elegidas
    if not datos.asignar_columnas_seleccionadas(fechahora, precipitacion):
        salida_estado.error('Error en tipo de columnas.')
        st.stop()

# ************************************
# TODO: Detectar mediciones duplicadas
# ************************************

# Detectar intervalo
if (datos.df_mediciones is not None) & (not datos.calcular_intervalo_mediciones()):
    salida_estado.error('Error en intervalo entre mediciones.')
    st.stop()

# Detectar lagunas en datos
num_lagunas = 0
if (datos.df_mediciones is not None) & (datos.intervalo_mediciones is not None):
    num_lagunas, df_lagunas = datos.detectar_lagunas()
    if num_lagunas > 0:
        if st.toggle('Rellenar faltantes con CEROS?'):
            datos.rellenar_faltantes()
            st.rerun()
        if st.toggle('Ver detalle de lagunas?'):
            st.dataframe(df_lagunas)

# Calcular eventos
if (num_lagunas == 0) & (datos.df_eventos is None) & (datos.df_mediciones is not None):
    datos.calcular_eventos_precipitacion()

# Indicar si ya se ejecutó procesamiento
salida_intervalo.caption(
    f'Intervalo entre mediciones: [ :orange[{datos.intervalo_mediciones}] ] minutos'
)
if datos.df_eventos is not None:
    salida_estado.success('Estado: Procesado.')
elif num_lagunas > 0:
    salida_estado.error((f'{num_lagunas} lagunas detectadas'))
else:
    salida_estado.warning('Estado: No procesado.')

# Ver eventos calculados
if st.toggle('Visualizar eventos?', disabled=datos.df_eventos is None):
    st.dataframe(datos.df_eventos)
