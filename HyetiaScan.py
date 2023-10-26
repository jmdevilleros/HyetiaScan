# ---------------------------------------------------------------------------------------------
# HyetiaScan
# Análisis de lluvias, aguaceros y curvas de Huff
# ---------------------------------------------------------------------------------------------
VERSION = 'v0.5'

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
        mediciones              = (col_precipitacion, lambda p: p.tolist()),
    ).reset_index(drop=True)

    # Agregar coiumna de duracion
    df_resultado['duracion'] = \
        (df_resultado['termina'] - df_resultado['inicia']).dt.total_seconds() // 60 \
        + minutos_intervalo

    return df_resultado

# ---------------------------------------------------------------------------------------------
def unir_precipitaciones(df, pausa_maxima):
    """
    Unifica precipitaciones según criterio de contiguidad.

    Args:
        df: DataFrame con las precipitaciones.
        pausa_maxima: Duracion máxima de una pausa entre eventos de lluvia.

    Returns:
        DataFrame con las precipitaciones unificadas.
    """

    # Columna auxiliar para indicar si un evento es parte de lluvia continua o no
    # True = Evento es parte de lluvia continua
    # False = No hay lluvia (duracion > pausa_maxima)
    df['lluvia'] = (df['precipitacion_acumulada'] > 0) | (
        (df['duracion'] <= pausa_maxima) & (df['precipitacion_acumulada'] == 0)
    )

    # Columna auxiliar para enumerar eventos continuos con un numero de secuencia
    df['secuencia'] = df['lluvia'].ne(df['lluvia'].shift()).cumsum()

    return df

# ---------------------------------------------------------------------------------------------
def calcular_acumulados(lista_mediciones, factor=100):
    return (pd.Series(lista_mediciones).cumsum() * factor / sum(lista_mediciones)).to_list()

# ---------------------------------------------------------------------------------------------
def detectar_aguaceros(
        df, duracion_minima, pausa_maxima, minutos_intervalo, intensidad_minima,
):

    df_eventos = unir_precipitaciones(df.copy(), pausa_maxima)
    #st.dataframe(df_eventos)

    # Realizar la agregación basada en la secuencia de evento
    df_resultado = df_eventos.groupby('secuencia').agg(
        inicia                  = ('inicia', 'first'),
        termina                 = ('termina', 'last'),
        mediciones              = ('mediciones', lambda p: sum(p, [])),
        precipitacion_acumulada = ('precipitacion_acumulada', 'sum'),
    )

    # Recalcular columna de duracion
    df_resultado['duracion'] = \
        (df_resultado['termina'] - df_resultado['inicia']).dt.total_seconds() // 60 \
        + minutos_intervalo

    # Agregar intensidad
    df_resultado['intensidad'] = \
        60 * df_resultado['precipitacion_acumulada'] / df_resultado['duracion']
    
    # Agregar conteo de mediciones
    df_resultado['conteo'] = df_resultado['mediciones'].apply(len)

    # Calcular y agregar porcentaje acumulado de mediciones
    df_resultado['porcentaje_acumulado'] = df_resultado['mediciones'].apply(calcular_acumulados)
    
    # Filtrar precipitaciones de duracion pequeña
    df_resultado = df_resultado[
        (df_resultado['duracion'] >= duracion_minima) & \
        (df_resultado['precipitacion_acumulada'] != 0)
    ]

    # Filtrar por intensidad minima
    df_resultado = df_resultado[(df_resultado['intensidad'] >= intensidad_minima)]

    # Reordenar columnas
    df_resultado = df_resultado[[
        'inicia', 'termina', 'duracion', 
        'intensidad', 'precipitacion_acumulada', 'conteo', 
        'mediciones', 'porcentaje_acumulado',
    ]]

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

        parametro_intensidad = st.slider(
            'Seleccione la intensidad mínima de aguacero',
            min_value=1,
            max_value=30,
            value=1,
            step=1,
        )

        if st.toggle('Detectar aguaceros y calcular gráficas', value=False):
            df_aguaceros = detectar_aguaceros(
                df, parametro_duracion, parametro_pausa, minutos_intervalo, parametro_intensidad,
            )

            st.divider()        
            st.write('Aguaceros detectados:')
            st.write(df_aguaceros.describe())
            st.divider()
            st.dataframe(df_aguaceros)
        else:
            return None

        return df_aguaceros

# ---------------------------------------------------------------------------------------------
def seccion_graficar_aguaceros(df_aguaceros):
    numero_aguaceros = df_aguaceros.shape[0]
    with st.expander(':chart_with_upwards_trend: *Graficar aguaceros*', expanded=False):
        if st.button(f'Calcular {numero_aguaceros} curvas', type='primary'):
            barra_progreso = st.progress(0, '')
            fig, ax = plt.subplots(figsize=(15, 10))
            numero_aguaceros = df_aguaceros.shape[0]
            procesado = 0
            for _, aguacero in df_aguaceros.iterrows():
                conteo = aguacero['conteo']
                porcentaje_duracion = [(i + 1) / conteo * 100 for i in range(conteo)]
                porcentaje_precipitacion = list(aguacero['porcentaje_acumulado'])

                ax.plot(porcentaje_duracion, porcentaje_precipitacion)
                ax.scatter(porcentaje_duracion, porcentaje_precipitacion, marker='.')

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

            plt.title('Curvas de aguaceros')        
            st.pyplot(fig)

    return

# ---------------------------------------------------------------------------------------------
def seccion_graficar_curvas_frecuencia(df_aguaceros):
    with st.expander(':chart_with_upwards_trend: *Graficar curvas de frecuencia*', expanded=False):
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
def calcular_curvas_huff(df_aguaceros):
    # Calculo de curvas Huff

    # Preparar dataframe que almacenará datos para curvas Huff
    datos_huff = pd.DataFrame()

    # Calcular los valores de percentiles a partir de porcentaje_acumulado de aguaceros
    datos_huff['valores_percentiles'] = df_aguaceros['porcentaje_acumulado'].apply(
        lambda p: np.percentile(p, [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]).tolist()
    )
    # Calcular los valores de cuartiles a partir de porcentaje_acumulado de aguaceros
    datos_huff['valores_cuartiles'] = df_aguaceros['porcentaje_acumulado'].apply(
        lambda p: np.percentile(p, [25, 50, 75]).tolist()
    )

    # Calcula las diferencias entre los cuartiles
    datos_huff['deltas_cuartiles'] = datos_huff['valores_cuartiles'].apply(
        lambda p: [p[0], p[1] - p[0], p[2] - p[1], 100 - p[2]]
    )

    # Calcula el índice del mayor delta para usarlo como clasificacion de tipo de curva Huff
    # El mayor delta indica que en ese lapso el aguacero tuvo su mayor precipitación
    datos_huff['indice_mayor_delta'] = datos_huff['deltas_cuartiles'].apply(
        # enumerate genera tuplas (indice, valor), key indica que max debe comparar por el segundo
        # item de la tupla (x[1]), el valor que retorna max es una tupla (indice, valor mayor)
        # asi que extraemos el primer elemento [0], el del indice, para usarlo como categoria 
        # de cuartil
        lambda deltas: max(enumerate(deltas), key=lambda x: x[1])[0]
    )

    # Calcular curvas Huff como promedio de cada correspondiente valor de valores_percentiles
    curvas_huff = datos_huff.groupby('indice_mayor_delta').agg(
        {'valores_percentiles': lambda x: np.mean(list(zip(*x)), axis=1)}
    ).rename(columns={'valores_percentiles': 'curva_huff'}).reset_index()

    curvas_huff['Q'] = 'Q' + (curvas_huff['indice_mayor_delta'] + 1).astype(str)
    curvas_huff = curvas_huff.drop('indice_mayor_delta', axis=1)

    #st.dataframe(datos_huff)
    #st.dataframe(curvas_huff)

    return curvas_huff

# ---------------------------------------------------------------------------------------------
def seccion_graficar_curvas_huff(df_aguaceros):
    with st.expander(':chart_with_upwards_trend: *Graficar curvas de Huff*', expanded=False):
        curvas_huff = calcular_curvas_huff(df_aguaceros)
        fig, ax = plt.subplots(figsize=(8, 5))

        markers = "vDo^"
        # Se adiciona inicio de grafica desde punto 0,0 para mejor visalizacion
        valores_eje_x = [p for p in range(0,  101, 10)]
        for curve_index in range(0, 4):
            nombre_q = f"Q{curve_index + 1}"
            datos = [0] + list(curvas_huff.iloc[curve_index]['curva_huff'])
            ax.plot(valores_eje_x, datos, label=nombre_q, marker=markers[curve_index])

        ax.set_xticks(range(0,101, 10))
        ax.set_yticks(range(0,101, 10))

        ax.grid(which='both', linestyle='--', linewidth=0.5)
        ax.minorticks_on()
        ax.grid(which='minor', linestyle=':', linewidth=0.5)

        ax.set_xlabel('% duración')
        ax.set_ylabel('% precipitación')
        ax.legend()

        plt.title('Curvas de Huff')        

        st.pyplot(fig)

        curvas_huff['curva_huff'] = curvas_huff['curva_huff'].apply(
            lambda x: [round(i, 2) for i in x]
        )
        st.dataframe(curvas_huff)

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

st.set_page_config(page_title=f'HyetiaScan {VERSION}')

st.write(f'## HyetiaScan {VERSION} - Análisis de lluvias :rain_cloud:')
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
            if df_aguaceros is not None:
                st.divider()
                seccion_graficar_curvas_huff(df_aguaceros)
                seccion_graficar_curvas_frecuencia(df_aguaceros)
                seccion_graficar_aguaceros(df_aguaceros)
