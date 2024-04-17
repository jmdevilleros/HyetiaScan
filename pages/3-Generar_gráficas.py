# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias, detección de aguaceros y gráficos de curvas de Huff
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
# Octubre-Noviembre de 2023
#
# Archivo: "2-Generar_gráficas.py" - Visualizaciones de aguaceros detectados
# *********************************************************************************************


# =============================================================================================
# Bibliotecas
# =============================================================================================

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from math import floor, ceil, trunc
from pandas import cut


# =============================================================================================
# Procedimientos y funciones
# =============================================================================================

# ---------------------------------------------------------------------------------------------
def generar_piedepagina(datos):
    return \
        f'Primera medición: {datos.primera_fecha}'                               +'\n'  + \
        f'Última medición: {datos.ultima_fecha}'                                 +'\n'  + \
        f'Rango de duración: {datos.duracion_minima} - {datos.duracion_maxima}'  + '\n' + \
        f'Pausa máxima entre eventos: {datos.pausa_maxima}'                      + '\n' + \
        f'Intensidad mínima de aguacero: {datos.intensidad_minima}'              + '\n' + \
        f'Número de aguaceros: {datos.df_aguaceros.shape[0]}'                    + '\n' + \
        f'Medición/Sensor: {datos.col_precipitacion}'
    
# ---------------------------------------------------------------------------------------------
def seccion_graficar_aguaceros(datos):
    numero_aguaceros = datos.df_aguaceros.shape[0]
    if st.button(f'Calcular {numero_aguaceros} curvas', type='primary'):
        barra_progreso = st.progress(0, '')
        fig, ax = plt.subplots(figsize=(8, 6))
        numero_aguaceros = datos.df_aguaceros.shape[0]
        procesado = 0
        for _, aguacero in datos.df_aguaceros.iterrows():
            conteo = aguacero['conteo']
            porcentaje_duracion = [(i + 1) / conteo * 100 for i in range(conteo)]
            porcentaje_precipitacion = list(aguacero['porcentaje_acumulado'])

            ax.plot(porcentaje_duracion, porcentaje_precipitacion, linewidth=0.6)

            procesado = procesado + 1
            barra_progreso.progress(
                procesado/numero_aguaceros, 
                text=f'Curva {procesado} de {numero_aguaceros}'
            )
        barra_progreso.empty()

        ax.set_xticks(range(0,101, 10))
        ax.set_yticks(range(0,101, 10))
        ax.grid(which='both', linestyle='--', linewidth=0.5)
        ax.minorticks_on()
        ax.grid(which='minor', linestyle=':', linewidth=0.5)
        ax.set_xlabel('% duración')
        ax.set_ylabel('% precipitación')

        pie = generar_piedepagina(datos)
        plt.text(100, 5, 
            pie, fontsize=6, ha='right', 
            bbox={'facecolor': 'white', 'alpha': 1, 'pad': 2}
        )

        plt.title(f'Curvas de aguaceros {datos.nombre}', fontsize=10)        
        st.pyplot(fig)

    return


    if len(valores_y) <= 1:
        return None
    
    # Calcular derivada y detectar si hay puntos de inflexión
    derivada = np.gradient(valores_y)
    if len(derivada) <= 1:
        return None  # No hay suficientes puntos para definir un punto de inflexión.
    if np.all(derivada > 0) or np.all(derivada < 0):
        return None  # La derivada nunca cambia de signo, no hay puntos de inflexión.

    # Obtener coordenadas de primer punto de inflexión
    indice_inflexion = np.where(np.diff(np.sign(derivada)))[0][0]
    xy_inflexion     = (valores_x[indice_inflexion], valores_y[indice_inflexion])

    return xy_inflexion

# ---------------------------------------------------------------------------------------------
def preparar_curva_frecuencia(ax, df, columna):

    # Curva general
    valores       = df[[columna]].sort_values(columna, ascending=False)
    num_valores   = valores.shape[0]
    porcentajes_x = [(i + 1) / num_valores * 100 for i in range(num_valores)]
    ax.plot(porcentajes_x, valores, label='General', linestyle='-', linewidth=1.2)

    # Curvas por categoría Huff
    categorias = df['Q_Huff'].unique()
    categorias.sort()
    for categoria in categorias:
        valores       = df[df['Q_Huff'] == categoria][[columna]].sort_values(columna, ascending=False)
        num_valores   = valores.shape[0]
        porcentajes_x = [(i + 1) / num_valores * 100 for i in range(num_valores)]
        ax.plot(porcentajes_x, valores, label=categoria, linewidth=0.9, linestyle='-.')

    ax.set_ylabel(columna.capitalize())
    ax.set_xlabel('Probabilidad')
    ax.legend(fontsize=8)
    ax.grid(which='both', linestyle='--', linewidth=0.5)
    ax.minorticks_on()
    ax.grid(which='minor', linestyle=':', linewidth=0.5)

    return

# ---------------------------------------------------------------------------------------------
def seccion_graficar_curvas_frecuencia(datos):
    if datos.df_aguaceros.shape[0] <= 1:
        st.warning('Se requieren dos o mas aguaceros para calcular frecuencias.')
        return
    
    fig, (ax_duracion, ax_precipit) = plt.subplots(1, 2, figsize=(8, 4))
    
    preparar_curva_frecuencia(ax_duracion, datos.df_aguaceros, 'duracion')
    preparar_curva_frecuencia(ax_precipit, datos.df_aguaceros, 'precipitacion_acumulada')

    fig.suptitle(f'Curvas de frecuencia {datos.nombre}', fontsize=10, ha='center')
    pie = generar_piedepagina(datos)
    
    plt.gcf().text(0.5, -0.125, 
        pie, fontsize=5, ha='center', 
        bbox={'facecolor': 'white', 'alpha': 1, 'pad': 2}
    )
    st.pyplot(fig)

    return

# ---------------------------------------------------------------------------------------------
def seccion_graficar_curvas_huff(datos):
    intervalo_percentiles = st.select_slider(
        'Seleccione intervalo de percentiles Huff',
        options=[5, 10, 20, 25, 50],
        value=10,
    )

    curvas_huff = datos.calcular_curvas_huff(intervalo=intervalo_percentiles)
    valores_eje_x = range(0, 101, intervalo_percentiles)

    fig, ax = plt.subplots(figsize=(8, 6))
    marcas = "vDo^"
    for indice, curva in curvas_huff.iterrows():
        ax.plot(
            valores_eje_x,
            list(curva['valores_percentiles']),
            label=curva['Q'],
            marker=marcas[indice]
        )

    ax.set_xticks(range(0, 101, intervalo_percentiles))
    ax.set_yticks(range(0, 101, 5))

    ax.grid(which='both', linestyle='--', linewidth=0.5)
    ax.grid(which='minor', linestyle=':', linewidth=0.5)

    ax.set_xlabel('% duración')
    ax.set_ylabel('% precipitación')
    ax.legend()

    plt.title(f'Curvas de Huff {datos.nombre}', fontsize=10)
    pie = generar_piedepagina(datos)
    plt.text(100, 5, 
        pie, fontsize=6, ha='right', 
        bbox={'facecolor': 'white', 'alpha': 1, 'pad': 2}
    )

    st.pyplot(fig)

    if st.toggle('Ver valores percentiles'):
        curvas_huff['valores_percentiles'] = curvas_huff['valores_percentiles'].apply(
            lambda x: [round(i, 2) for i in x]
        )
        st.dataframe(curvas_huff, column_order=('Q', 'valores_percentiles'), hide_index=True)

    return

# ---------------------------------------------------------------------------------------------
def seccion_graficar_rangos_intensidad(datos):
    
    num_aguaceros = datos.df_aguaceros.shape[0]
    if num_aguaceros <= 2:
        st.error('Requiere mas de dos aguaceros.')
        return

    intensidad_min = floor(datos.df_aguaceros['intensidad'].min())
    intensidad_max = ceil(datos.df_aguaceros['intensidad'].max())
    intensidad_med = (intensidad_max - intensidad_min) // 2

    if intensidad_min == intensidad_max:
        st.error('No hay diferencia de intensidades')
        return
    
    num_rangos = st.slider(
        'Número de rangos:', 
        min_value=2, 
        max_value=intensidad_med
    )
    tamaño_rango = (intensidad_max - intensidad_min) / num_rangos
    limites_rangos = \
        [trunc(intensidad_min + i * tamaño_rango) for i in range(num_rangos + 1)]
    rangos = \
        [(limites_rangos[i], limites_rangos[i + 1]) for i in range(num_rangos)]

    df = datos.df_aguaceros[['Q_Huff', 'intensidad']].copy()

    df['rango'] = cut(
        datos.df_aguaceros['intensidad'], 
        bins=limites_rangos,
        labels=[f'{t}' for t in rangos],
    )

    conteo_por_categoria = df.groupby(['Q_Huff', 'rango'], observed=False).size()
    categorias = df['Q_Huff'].unique()
    categorias.sort()
    
    fig, ax = plt.subplots(figsize=(7, 4))
    colores = ['lightblue', 'cyan', 'blue', 'navy']
    for i, categoria in enumerate(categorias):
        ax.bar(
            [p + i * 0.15 for p in range(num_rangos)], 
            conteo_por_categoria.loc[categoria],
            width=0.15,
            label=categoria,
            color=colores[i]
        )

    ax.legend(title='Cuartil', loc='upper left', bbox_to_anchor=(1, 1))
    ax.set_xticks(range(num_rangos))
    ax.set_xticklabels(rangos, rotation=45, fontsize=8)
    ax.set_xlabel('Rangos de intensidad')
    ax.set_ylabel('Frecuencia')
    ax.grid(which='both', linestyle='--', linewidth=0.5, axis='y')
    ax.grid(which='minor', linestyle=':', linewidth=0.5, axis='y')

    pie = generar_piedepagina(datos)
    plt.gcf().text(1, 0.3, 
        pie, fontsize=5, ha='center', 
        bbox={'facecolor': 'white', 'alpha': 1, 'pad': 2}
    )
    plt.title(
        f'Distribución rangos de intensidad por cuartil Huff\n{datos.nombre}',
    )

    st.pyplot(fig)

    return

# ---------------------------------------------------------------------------------------------
def seccion_graficar_historico(datos):
    st.line_chart(datos.df_aguaceros, x='inicia', y='duracion', color='#00FF00')
    st.line_chart(datos.df_aguaceros, x='inicia', y='intensidad', color='#FFA500')
    st.line_chart(datos.df_aguaceros, x='inicia', y='precipitacion_acumulada', color='#1E90FF')


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
apcfg.configurar_pagina(subheader='Generar gráficas. :chart_with_upwards_trend:')

# Verificar que ya se hayan procesado medidiones y calculado eventos
if datos.df_aguaceros is None:
    st.error(f'No hay datos de aguaceros para graficar.')
    st.stop()

# Definir secciones con gráficos disponibles
secciones = {
    'Curvas de Huff'           : seccion_graficar_curvas_huff,
    'Rangos de intensidad'     : seccion_graficar_rangos_intensidad,
    'Curvas de frecuencia'     : seccion_graficar_curvas_frecuencia,
    'Curvas Huff individuales' : seccion_graficar_aguaceros,
    'Histórico de aguaceros'   : seccion_graficar_historico,
}

# Mostrar secciones
for titulo, seccion in secciones.items():
    with st.expander(titulo, expanded=False):
        seccion(datos)
