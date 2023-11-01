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

# Visualizar nombre de archivo en uso
st.caption(f'Archivo: [:orange[{datos.nombre}]]')

# Selección de columnas
lista_columnas = list(datos.df_origen.columns)
salida1, salida2, _ = st.columns(3)
salida1.write('Selección de columnas:')
salida3, salida4 = st.columns(2)
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
        st.error('Al menos una de las columnas seleccionadas no tiene el tipo apropiado.')
        st.stop()

    # Detectar intervalo
    if not datos.detectar_intervalo_mediciones():
        st.error('Error en intervalo entre mediciones.')
        st.stop()

    # Detectar lagunas en datos
    num_lagunas, df_lagunas = datos.detectar_lagunas()
    if num_lagunas > 0:
        st.warning((f'{num_lagunas} lagunas detectadas'))
        ver_lagunas = st.toggle('Visualizar lagunas?')
        if ver_lagunas:
            st.write('aca lagunas')

    # Calcular eventos
    if num_lagunas == 0:
        datos.calcular_eventos_precipitacion()
        st.toast('Eventos calculados.')

if st.toggle('Visualizar eventos?', disabled=datos.df_eventos is None):
    st.write(f'Intervalo entre mediciones: [:orange[{datos.intervalo_mediciones}]] minutos')
    st.dataframe(datos.df_eventos)

# # Manejar lagunas en los datos
# if datos.df_mediciones is not None:
#     num_lagunas, df_lagunas = datos.detectar_lagunas()
#     if num_lagunas > 0:
#         salida5, salida6, _ = st.columns(3)
#         salida5.warning(f'{num_lagunas} lagunas detectadas')
#         if salida6.toggle('Visualizar?'):
#             st.dataframe(df_lagunas)
#         if salida6.toggle('Rellenar?'):
#             datos.rellenar_faltantes()
#             st.success('Datos faltantes rellenados.')

# Calcular eventos
# if datos.df_eventos is None:
#     #datos.calcular_eventos_precipitacion()
#     st.success('Aca cuando se calculen los eventos.')
# else:
#     if st.toggle('Visualizar eventos?'):
#         st.dataframe(datos.df_mediciones)
