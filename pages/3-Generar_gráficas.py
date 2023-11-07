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


# =============================================================================================
# Procedimientos y funciones
# =============================================================================================

# ---------------------------------------------------------------------------------------------
def generar_piedepagina(datos):
    primera_medicion = datos.df_mediciones[datos.col_fechahora].min()
    ultima_medicion  = datos.df_mediciones[datos.col_fechahora].max()

    pie= \
        f'Primera medición: {primera_medicion}'                      +'\n'  + \
        f'Última medición: {ultima_medicion}'                        +'\n'  + \
        f'Duracion minima de aguacero: {datos.duracion_minima}'      + '\n' + \
        f'Pausa máxima entre eventos: {datos.pausa_maxima}'          + '\n' + \
        f'Intensidad mínima de aguacero: {datos.intensidad_minima}'  + '\n' + \
        f'Número de aguaceros: {datos.df_aguaceros.shape[0]}'        + '\n' + \
        f'Medición/Sensor: {datos.col_precipitacion}'
    
    return pie

# ---------------------------------------------------------------------------------------------
def seccion_graficar_aguaceros(datos):
    numero_aguaceros = datos.df_aguaceros.shape[0]
    with st.expander('Curvas individuales de aguaceros', expanded=False):
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

# ---------------------------------------------------------------------------------------------
def calcular_punto_inflexion(valores_x, valores_y):
    derivada         = np.gradient(valores_y)
    indice_inflexion = np.where(np.diff(np.sign(derivada)))[0][0]
    xy_inflexion     = (valores_x[indice_inflexion], valores_y[indice_inflexion])
    return xy_inflexion

# ---------------------------------------------------------------------------------------------
def preparar_curva_frecuencia(ax, df, columna):
    valores       = df[[columna]].sort_values(columna, ascending=False)
    num_valores   = valores.shape[0]
    porcentajes_x = [(i+1)/num_valores * 100 for i in range(num_valores)]

    # Curva
    ax.plot(porcentajes_x, valores)

    # Punto de inflexión
    xy_inflexion = calcular_punto_inflexion(porcentajes_x, valores[columna].to_numpy())
    ax.plot(xy_inflexion[0], xy_inflexion[1], 'ro', markersize=3)
    ax.text(
        xy_inflexion[0] + 3, xy_inflexion[1] + 3,
        f'Punto de Inflexión f\':\n({xy_inflexion[0]:.2f}, {xy_inflexion[1]:.2f})', 
        fontsize=6, 
        bbox={'facecolor': 'white', 'alpha': 1, 'pad': 1, 'linewidth': 0.5}
    )

    ax.set_ylabel(columna.capitalize())
    ax.set_xlabel('Probabilidad')

    ax.grid(which='both', linestyle='--', linewidth=0.5)
    ax.minorticks_on()
    ax.grid(which='minor', linestyle=':', linewidth=0.5)

    return

# ---------------------------------------------------------------------------------------------
def seccion_graficar_curvas_frecuencia(datos):
    with st.expander('Curvas de frecuencia', expanded=False):
        fig, (ax_duracion, ax_precipit) = plt.subplots(1, 2, figsize=(8, 4))
        
        preparar_curva_frecuencia(ax_duracion, datos.df_aguaceros, 'duracion')
        preparar_curva_frecuencia(ax_precipit, datos.df_aguaceros, 'precipitacion_acumulada')

        fig.suptitle(f'Curvas de frecuencia {datos.nombre}', fontsize=10, ha='center')
        pie = generar_piedepagina(datos)
        plt.text(-10, -25, 
            pie, fontsize=6, ha='center', 
            bbox={'facecolor': 'white', 'alpha': 1, 'pad': 2}
        )
        st.pyplot(fig)

    return

# ---------------------------------------------------------------------------------------------
def seccion_graficar_curvas_huff(datos):
    with st.expander('Curvas de Huff', expanded=False):
        intervalo_percentiles = st.select_slider(
            'Seleccione intervalo de percentiles Huff',
            options=[5, 10, 20, 25, 50],
            value=10,
        )

        curvas_huff = datos.calcular_curvas_huff(intervalo=intervalo_percentiles)
        valores_eje_x = range(0, 101, intervalo_percentiles)

        fig, ax = plt.subplots(figsize=(8, 6))
        markers = "vDo^"
        for indice_curva in range(0, 4):
            nombre_q = f"Q{indice_curva + 1}"
            valores = list(curvas_huff.iloc[indice_curva]['valores_percentiles'])
            ax.plot(valores_eje_x, valores, label=nombre_q, marker=markers[indice_curva])

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

seccion_graficar_curvas_huff(datos)
seccion_graficar_curvas_frecuencia(datos)
seccion_graficar_aguaceros(datos)
