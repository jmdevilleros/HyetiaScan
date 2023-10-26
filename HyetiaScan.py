# ---------------------------------------------------------------------------------------------
# Calculo de curvas HUff para precipitaciones
# ---------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------
# Bibliotecas
# ---------------------------------------------------------------------------------------------

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------------------------
# Rutinas y funciones
# ---------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------
@st.cache_data
def readcsv(csv_file):
    return pd.read_csv(
        csv_file, 
         #nrows=100000,
    )

# ---------------------------------------------------------------------------------------------
def cargar_archivo_datos():
    uploaded_file = st.file_uploader('Selección de archivo', type=['csv'])
    if uploaded_file is not None:
        # Falta detectar el encoding
        df = readcsv(uploaded_file)
        return df
    else:
        return None

# ---------------------------------------------------------------------------------------------
def seccion_visualizar(df, titulo='', expand=False):
    with st.expander(f':page_facing_up: *{titulo}*', expanded=expand):
        st.write('Descripción:')
        st.write(df.dtypes)
        st.write(df.describe(include='all'))
        st.divider()
        st.write('Contenido:')
        st.dataframe(df, hide_index=True)

    return

# ---------------------------------------------------------------------------------------------
def seccion_seleccionar_columnas(df):
    col_fechahora, col_precipitacion = None, None

    with st.expander(':white_check_mark: *Seleccionar columnas*'):
        col_fechahora = st.selectbox('Fecha y hora', df.columns, index=None)
        col_precipitacion = st.selectbox('Precipitacion', df.columns, index=None)

    return col_fechahora, col_precipitacion

# ---------------------------------------------------------------------------------------------
def preprocesar_datos(df, col_fechahora, col_precipitacion):
    df_resultado = pd.DataFrame()

    # Verificar tipo de fecha y hora
    if df[col_fechahora].dtype == 'object':
        df_resultado[col_fechahora] = pd.to_datetime(df[col_fechahora])
    elif df[col_fechahora].dtype == 'datetime64':
        df_resultado[col_fechahora] = df[col_fechahora]
    else:
        st.error('Error en columna de fecha y hora')
        return None

    # Cambiar signo de decimal y convertir a float si es un string
    if df[col_precipitacion].dtype == 'object':
        df_resultado[col_precipitacion] = df[col_precipitacion].apply(
            lambda x: float(x.replace(',', '.'))
        )
    elif df[col_precipitacion].dtype in ['int', 'float', 'int64', 'float64']:
        df_resultado[col_precipitacion] = df[col_precipitacion]
    else:
        st.error('Error en columna de precipitación')
        return None

    # Valores de precipitacion menor a cero son errores de medición, eliminarlos 
    # para dejar que se procesen en las lineas siguientes como lagunas de datos
    df_resultado = df_resultado[df_resultado[col_precipitacion] >= 0]

    # Detectar intervalo entre mediciones
    t0 = df_resultado.iloc[0][col_fechahora]
    t1 = df_resultado.iloc[1][col_fechahora]
    minutos_intervalo = (t1 - t0).seconds // 60

    # Identificar lagunas de mediciones faltantes
    lagunas = df_resultado[col_fechahora].diff() > pd.Timedelta(minutes=minutos_intervalo)
    lagunas_indices = df_resultado.loc[lagunas, col_fechahora]

    num_lagunas = len(lagunas_indices)
    if num_lagunas > 0:
        with st.expander(':hole: **Lagunas**', expanded=True):
            st.warning(f'{num_lagunas} lagunas detectadas en los datos.')

            inicio = df_resultado.loc[lagunas.shift(-1, fill_value=False), col_fechahora].tolist()
            termina = df_resultado.loc[lagunas, col_fechahora].tolist()
            df_lagunas = pd.DataFrame({'inicio_laguna': inicio, 'termina_laguna': termina})
            df_lagunas['duracion_laguna'] = \
                (df_lagunas['termina_laguna'] - df_lagunas['inicio_laguna']).dt.total_seconds() // 60
            st.dataframe(df_lagunas)

            rango_completo = pd.date_range(
                start=df_resultado[col_fechahora].min(), 
                end=df_resultado[col_fechahora].max(), 
                freq=f'{minutos_intervalo}T'
            )
            timestamps_faltantes = rango_completo.difference(df_resultado[col_fechahora])
            df_faltantes = pd.DataFrame(timestamps_faltantes, columns=[col_fechahora])

            esperadas = len(rango_completo)
            recibidas = df.shape[0]
            faltantes = df_faltantes.shape[0]

            st.write(f'Mediciones recibidas: {recibidas}')
            st.write(f'Mediciones esperadas: {esperadas}')
            st.write(f'Mediciones faltantes: {faltantes} ({faltantes/esperadas:.2%})')

            fill_zeros = st.toggle('**Rellenar con CEROS** :question:', value=False)
            if fill_zeros:
                df_faltantes[col_precipitacion] = 0
                df_resultado = pd.concat(
                    [df_resultado, df_faltantes]
                ).sort_values(by=col_fechahora)
            else:
                return None

    # Crear una columna adicional para marcar los cambios de 0 a otro valor y viceversa
    df_resultado['cambio'] = \
        (df_resultado[col_precipitacion] != 0) != \
        (df_resultado[col_precipitacion] != 0).shift(1)
    df_resultado['grupo'] = df_resultado['cambio'].cumsum()

    # Realizar la agregación basada en el grupo
    df_resultado = df_resultado.groupby('grupo').agg(
        inicia                  = (col_fechahora, 'first'),
        termina                 = (col_fechahora, 'last'),
        conteo                  = (col_precipitacion, 'count'),
        precipitacion_acumulada = (col_precipitacion, 'sum'),
    ).reset_index(drop=True)

    # Agregar coiumna de duracion
    df_resultado['duracion'] = \
        (df_resultado['termina'] - df_resultado['inicia']).dt.total_seconds() // 60 \
        + minutos_intervalo

    return df_resultado

# ---------------------------------------------------------------------------------------------
def detectar_aguaceros(df, duracion_minima, pausa_maxima, minutos_intervalo):
    # Filtrar pausas pequeñas
    df_resultado = df[(df['duracion'] > pausa_maxima) | (df['precipitacion_acumulada'] != 0)]

    # Unificar precipitaciones contiguas
    df_resultado['cambio'] = \
        (df_resultado['precipitacion_acumulada'] != 0) != \
        (df_resultado['precipitacion_acumulada'] != 0).shift(1)
    df_resultado['grupo'] = df_resultado['cambio'].cumsum()

    # # Realizar la agregación basada en el grupo
    df_resultado = df_resultado.groupby('grupo').agg(
        inicia=('inicia', 'first'),
        termina=('termina', 'last'),
        precipitacion_acumulada=('precipitacion_acumulada', 'sum')
    )

    # Recalcular coiumna de duracion
    df_resultado['duracion'] = \
        (df_resultado['termina'] - df_resultado['inicia']).dt.total_seconds() // 60 \
        + minutos_intervalo

    # Filtrar precipitaciones de duracion pequeña
    df_resultado = df_resultado[
        (df_resultado['duracion'] >= duracion_minima) & \
        (df_resultado['precipitacion_acumulada'] != 0)
    ]

    # Agregar intensidad
    df_resultado['intensidad'] = 60 * df_resultado['precipitacion_acumulada'] / df_resultado['duracion']

    return df_resultado.reset_index(drop=True)

# ---------------------------------------------------------------------------------------------
def seccion_examinar_aguaceros(df):
    with st.expander(':sleuth_or_spy: *Examinar aguaceros*', expanded=False):
        # Detectar intervalo
        minutos_intervalo = df.iloc[0]['duracion'] / df.iloc[0]['conteo']

        st.write(
            f'Intervalo entre mediciones: {int(minutos_intervalo)} ' 
            f'minuto{"s" if minutos_intervalo > 1 else ""}'
        )

        parametro_duracion = st.slider(
            "Seleccionar duración mínima de aguacero (minutos)", 
            min_value=5, 
            max_value=60, 
            value=15,
            step=5
        )

        parametro_pausa = st.slider(
            "Seleccionar duración máxima de pausa (minutos)", 
            min_value=1, 
            max_value=parametro_duracion, 
            value=parametro_duracion,
            step=1
        )
        df_aguaceros = detectar_aguaceros(
            df, parametro_duracion, parametro_pausa, minutos_intervalo,
        )

        st.divider()        
        st.write('Aguaceros detectados:')
        st.write(df_aguaceros.describe())
        st.divider()
        st.dataframe(df_aguaceros)

        return df_aguaceros

# ---------------------------------------------------------------------------------------------
def seccion_graficar_aguaceros(df_aguaceros):
    with st.expander(':bar_chart: *Graficar aguaceros*', expanded=False):
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Barra para la duración
        ax1.bar(
            df_aguaceros.index, df_aguaceros['duracion'], 
            color='navy', alpha=0.7, label='Duración'
        )
        ax1.set_xlabel('Aguaceros')
        ax1.set_ylabel('Tiempo (minutos)', color='b')
        ax1.tick_params('y', colors='b')

        # Crear el segundo eje y para la precipitación
        ax2 = ax1.twinx()
        ax2.plot(
            df_aguaceros.index, df_aguaceros['precipitacion_acumulada'], 
            color='cyan', marker='o', linestyle='--', label='Precipitación acumulada'
        )
        ax2.set_ylabel('Precipitación acumulada', color='b')
        ax2.tick_params('y', colors='b')

        # Añadir leyendas y título
        ax1.legend(loc=2)
        ax2.legend(loc=1)
        plt.title('Duración y Precipitación de Aguaceros')        

        st.pyplot(fig)

    return

# ---------------------------------------------------------------------------------------------
def seccion_graficar_curvas_frecuencia(df_aguaceros):
    with st.expander(':bar_chart: *Graficar curvas de frecuencia*', expanded=False):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

        # Ordenar por duración de mayor a menor
        df_duracion = df_aguaceros.sort_values('duracion', ascending=False)
        duracion_max = df_duracion['duracion'].max()
        porcentaje_duracion = [
            (i+1)/len(df_duracion) * 100 for i in range(len(df_duracion))
        ]

        # Graficar la curva de frecuencia por duración
        ax1.plot(
            porcentaje_duracion, 
            df_duracion['duracion'], 
        )

        # Ordenar por precipitación acumulada de mayor a menor
        df_precipitacion = df_aguaceros.sort_values('precipitacion_acumulada', ascending=False)
        precipitacion_max = df_precipitacion['precipitacion_acumulada'].max()
        porcentaje_precipitacion = [
            (i+1)/len(df_precipitacion) * 100 for i in range(len(df_precipitacion))
        ]

        # Graficar la curva de frecuencia por precipitación acumulada
        ax2.plot(
            porcentaje_precipitacion, 
            df_precipitacion['precipitacion_acumulada'], 
        )

        # Añadir leyenda y etiquetas
        ax1.set_xlabel('Probabilidad')
        ax1.set_ylabel('Duración (minutos)')
        #ax1.set_title(f'Curva de frecuencia por duración (max={duracion_max})')
        ax2.set_xlabel('Probabilidad')
        ax2.set_ylabel('Precipitación acumulada (mm)')
        #ax2.set_title(f'Curva de frecuencia por precipitación (max={precipitacion_max})')

        # Ajustar la cuadrícula
        ax1.grid(which='both', linestyle='--', linewidth=0.5)
        ax1.minorticks_on()
        ax1.grid(which='minor', linestyle=':', linewidth=0.5)

        ax2.grid(which='both', linestyle='--', linewidth=0.5)
        ax2.minorticks_on()
        ax2.grid(which='minor', linestyle=':', linewidth=0.5)

        # Ajustar y mostrar la figura
        fig.suptitle('Curvas de frecuencia', fontsize=16, ha='center')
        st.pyplot(fig)

    return

# ---------------------------------------------------------------------------------------------
def seccion_graficar_curva_aguaceros(df_aguaceros):
    return

# ---------------------------------------------------------------------------------------------
def son_columnas_validas(df, col_fechahora, col_precipitacion):
    if (col_fechahora is None) | (col_precipitacion is None):
        return False

    if df[col_fechahora].dtype not in ['object', 'datetime64']:
        st.warning('Seleccione una columna válida para fecha y hora')
        return False

    if df[col_precipitacion].dtype not in ['object', 'int', 'float', 'int64', 'float64']:
        st.warning('Seleccione una columna válida para precipitación. (data type)')
        return False

    if df[col_precipitacion].dtype == 'object':
        try:
            x = float(df.iloc[0][col_precipitacion].replace(',', '.'))
        except ValueError:
            st.warning('Seleccione una columna válida para precipitación. (numeric format)')
            return False

    return True


# ---------------------------------------------------------------------------------------------
# Sección principal
# ---------------------------------------------------------------------------------------------

st.set_page_config(page_title="HyetiaScan - Análisis de lluvias")

st.write('## HyetiaScan - Análisis de lluvias :rain_cloud:')
st.divider()

with st.expander(':open_file_folder: *Cargar datos*', expanded=True):
    df_datos = cargar_archivo_datos()

if df_datos is not None:
    seccion_visualizar(df_datos, titulo='Ver datos de origen')
    
    col_fechahora, col_precipitacion = seccion_seleccionar_columnas(df_datos)

    if son_columnas_validas(df_datos, col_fechahora, col_precipitacion):

        st.divider()

        df_work = preprocesar_datos(df_datos, col_fechahora, col_precipitacion)

        if df_work is not None:
            #seccion_visualizar(df_work, 'Ver datos preprocesados')

            df_aguaceros = seccion_examinar_aguaceros(df_work)

            st.divider()

            seccion_graficar_aguaceros(df_aguaceros)

            seccion_graficar_curvas_frecuencia(df_aguaceros)

            seccion_graficar_curva_aguaceros(df_aguaceros)
