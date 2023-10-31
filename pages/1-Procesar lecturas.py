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
if 'mediciones' not in st.session_state:
    st.error('No ha cargado ningún archivo.')
    st.stop()

# Variables de nombre breve para acceso a datos de sesión
apcfg = st.session_state['appconfig']
datos = st.session_state['mediciones']

# Preparar página
apcfg.configurar_pagina(subheader='Procesar lecturas. :white_check_mark:')

# Verificar que ya se haya cargadpo archivo
if datos.df_lecturas is None:
    st.error(f'No hay columnas para seleccionar.')
    st.stop()

# Visualizar nombre de archivo en uso
st.caption(f'Archivo: [:orange[{datos.nombre}]]')

# Selección de columnas
lista_columnas = list(datos.df_lecturas.columns)
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
    with salida4:
        st.dataframe(
            datos.df_lecturas.dtypes, 
            column_config={
                ''  : 'Columna',
                '0' : 'Tipo',
            }
        )

if aplicar_cambios:
    # Asignar columnas elegidas
    if datos.asignar_columnas_seleccionadas(fechahora, precipitacion):
        st.toast('Columnas asignadas.')
    else:
        st.error('Al menos una de las columnas seleccionadas no tiene el tipo apropiado.')
        st.stop()

    # Detectar intervalo
    if not datos.detectar_intervalo_mediciones():
        st.error('Error detectando intervalo entre mediciones.')
        st.stop()

    # Manejar lagunas en los datos

    # Calcular eventos
    datos.calcular_eventos_precipitacion()
    st.toast('Eventos calculados.')

    # Marcar fin exitoso de calculo de eventos
    flag_eventos_procesados = True


# Visualizar eventos calculados
if st.toggle('Visualizar eventos?'):
    st.write(f'Intervalo entre mediciones: [:orange[{datos.intervalo_mediciones}]] minutos')
    st.dataframe(datos.df_eventos)
