# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
# Junio - Agosto 2024
#
# Archivo: HyetiaScan.py - Punto de entrada a aplicación Streamlit
# *********************************************************************************************

# =============================================================================================
# Bibliotecas
# =============================================================================================

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

from mensajes_es import TEXTOS
import hyetiascan_core as nucleo

# =============================================================================================
# Globales
# =============================================================================================

# =============================================================================================
# Procedimientos y funciones
# =============================================================================================

# ---------------------------------------------------------------------------------------------
def inicializar():
    if 'iniciado' not in st.session_state:
        st.session_state.iniciado = True
        st.set_page_config(
            page_title=f'{TEXTOS["appname"]} {TEXTOS["appversion"]}', 
            layout='wide', 
            initial_sidebar_state='expanded',
            page_icon=':material/rainy:',
            menu_items={'About' : TEXTOS['about']}
        )
    st.sidebar.subheader(f':blue[{TEXTOS["appname"]} {TEXTOS["appversion"]}]')
    st.sidebar.caption(TEXTOS['appdescription'])

# ---------------------------------------------------------------------------------------------
@st.cache_data(show_spinner=TEXTOS['stcachespinner'])
def cargar_archivo_de_cache(archivo: BytesIO, decimal: str, codificacion: str) -> pd.DataFrame:
    try:
        df = nucleo.cargar_csv(archivo, decimal=decimal, codificacion=codificacion)
    except Exception as ex:
        st.sidebar.error(ex)
        return None
    return df

# ---------------------------------------------------------------------------------------------
def obtener_archivo_lecturas() -> tuple[pd.DataFrame, str]:
    tab_carga, tab_config = st.sidebar.tabs([TEXTOS['tabcarga'], TEXTOS['tabconfig']])
    with tab_config:
        decimal = st.radio(
            TEXTOS['elegirdecimal'], 
            options=['.', ','], 
            captions=[TEXTOS['captionpunto'], TEXTOS['captioncoma']],
            horizontal=True,
        )
        codificacion = st.selectbox(
            TEXTOS['elegircodificacion'],
            options=['utf-8', 'utf-16', 'utf-32', 'latin-1', 'iso-8859-1', 'ascii'],
        )
        st.divider()

    archivo = tab_carga.file_uploader(
        ' ', type=['csv'], help=TEXTOS['fileuploaderhelp'], label_visibility='collapsed',
    )
    if archivo is None:
        return None, None
    
    df = cargar_archivo_de_cache(archivo, decimal=decimal, codificacion=codificacion)
    if not nucleo.verificar_lecturas_cargadas(df):
        st.sidebar.error(TEXTOS['errorlecturas'])
        return None, None

    return df, archivo.name

# ---------------------------------------------------------------------------------------------
def elegir_nombre_columna(prompt: str, tipos_validos: list[str], df: pd.DataFrame) -> str:
    lista_columnas = df.select_dtypes(include=tipos_validos).columns
    nombre_col = st.sidebar.selectbox(prompt, lista_columnas, index=0)
    if len(lista_columnas) < 1:
        st.sidebar.warning(TEXTOS['errortipocols'](tipos_validos))
        return None
    if nombre_col is None:
        return None
    return nombre_col

# ---------------------------------------------------------------------------------------------
def buscar_errores_fechahora(df):
    error = nucleo.buscar_errores_fechahora(df)
    if error is not None:
        col, indice, valor_fechahora = error
        st.error(TEXTOS['errorfechahora'](col, indice, f':orange[{valor_fechahora}]'))

# ---------------------------------------------------------------------------------------------
def desplegar_archivo(df: pd.DataFrame):
    st.write(TEXTOS['previsualarchivo'])

    if sum(df.dtypes == 'datetime64') < 1: 
        buscar_errores_fechahora(df) 

    c1, c2 = st.columns([0.3, 0.7])

    # Obtener columnas y sus tipos (df.dtypes genera warnings)
    tipos_columna = pd.DataFrame({
        TEXTOS['previsualcolnom']: df.dtypes.index,
        TEXTOS['previsualtipnom']: df.dtypes.values.astype(str)
    })
    c1.dataframe(tipos_columna, hide_index=True, use_container_width=True)

    c1.divider()

    # Mostrar cantidad de registros deseados
    num_vista = c1.slider(
        TEXTOS['previsualcantidad'], 
        min_value=10, max_value=df.shape[0], 
        value=10, step=int(df.shape[0] / 100) + 1,
        key='num_enarchivo',
    )
    c2.dataframe(
        df.head(num_vista), 
        use_container_width=True,
        column_config={'_index': TEXTOS['previsualindice']},
    )

# ---------------------------------------------------------------------------------------------
@st.cache_data(show_spinner=TEXTOS['stcachespinner'])
def extraer_lecturas(df: pd.DataFrame, col1: str, col2: str) -> pd.DataFrame:
    return nucleo.extraer_lecturas(df, col1, col2)

# ---------------------------------------------------------------------------------------------
@st.cache_data(show_spinner=TEXTOS['stcachespinner'])
def estimar_intervalo_lecturas(df: pd.DataFrame) -> int:
    return nucleo.estimar_intervalo_lecturas(df)

# ---------------------------------------------------------------------------------------------
@st.cache_data(show_spinner=TEXTOS['stcachespinner'])
def agrupar_lecturas(
    df: pd.DataFrame, 
    intervalo_base: str, 
    intervalo_grupo: str,
    umbral_precipitacion : float = 600.0,
) -> pd.DataFrame:
    return nucleo.agrupar_lecturas(df, intervalo_base, intervalo_grupo, umbral_precipitacion)

# ---------------------------------------------------------------------------------------------
def ver_dataframe(df: pd.DataFrame, titulo: str = None):
    if titulo:
        st.write(titulo)
    cantidad = st.slider(
        TEXTOS['previsualcantidad'],
        min_value=0, 
        max_value=df.shape[0], 
        value=10, 
        step=int(df.shape[0] / 100) + 1,
        key=f'slider_{titulo}'
    )
    st.dataframe(df.head(cantidad), hide_index=True, use_container_width=True,)

# ---------------------------------------------------------------------------------------------
@st.cache_data(show_spinner=TEXTOS['stcachespinner'])
def controlar_duplicadas(df: pd.DataFrame, control: str) -> pd.DataFrame:
    # control es el texto de la opción elegida en la interfaz
    opciones = {
        TEXTOS['opcdejarprimera'] : nucleo.DUPLICADAS_PRIMERA,
        TEXTOS['opcdejarultima']  : nucleo.DUPLICADAS_ULTIMA,
        TEXTOS['opcsumar']        : nucleo.DUPLICADAS_SUMAR,
        TEXTOS['opcpromediar']    : nucleo.DUPLICADAS_PROMEDIAR,
        TEXTOS['opcborrar']       : nucleo.DUPLICADAS_BORRAR,
    }
    return nucleo.controlar_duplicadas(df, opciones.get(control))

# ---------------------------------------------------------------------------------------------
def desplegar_lecturas(df_individuales: pd.DataFrame, intervalo: int) -> pd.DataFrame : 
    col_fechahora = df_individuales.columns[0]
    agrupaciones = {
        TEXTOS['descripciondia'] : nucleo.AGRUPACION_DIA, 
        TEXTOS['descripcionmes'] : nucleo.AGRUPACION_MES, 
        TEXTOS['descripcionano'] : nucleo.AGRUPACION_ANO,
    }
    lista_categorias = list(nucleo.LISTA_CATEGORIAS)
    lista_anormales = lista_categorias[1:]

    # Preparar zonas de visualización ---------------------------------------------------------
    with st.container(border=True):
        zona_grafico_agrupadas, zona_metricas = st.columns([0.7, 0.3])

    with st.container(border=True):
        zona_categorias, zona_control = st.columns([0.7, 0.3], gap='medium')

    with st.expander(TEXTOS['detallelecturas'], expanded=False):
        zona_detalle_agrupadas, zona_detalle_individuales = \
            st.columns([0.7, 0.3], gap='medium')

    # -----------------------------------------------------------------------------------------
    # Controles deben ir antes de visualizaciones, pues modifican dataframe
    zona_control.subheader(TEXTOS['controlanormales'])

    # Control de duplicadas -------------------------------------------------------------------
    opcion_control_duplicadas = zona_control.radio(
        TEXTOS['lecturasduplicadas'], 
        options=[
            TEXTOS['opcnomodificar'], 
            TEXTOS['opcdejarprimera'], 
            TEXTOS['opcdejarultima'], 
            TEXTOS['opcsumar'],
            TEXTOS['opcpromediar'],
            TEXTOS['opcborrar'],
        ], 
        horizontal=True,
    )
    if opcion_control_duplicadas != TEXTOS['opcnomodificar']:
        df_individuales = controlar_duplicadas(df_individuales, opcion_control_duplicadas)

    # Control corruptas -----------------------------------------------------------------------
    control_corruptas = zona_control.radio(
        TEXTOS['lecturascorruptas'], 
        options=[TEXTOS['opcnomodificar'], TEXTOS['opcborrar']], horizontal=True,
    )
    if control_corruptas == TEXTOS['opcborrar']:
        df_individuales = nucleo.borrar_corruptas(df_individuales)

    # Control de atípicas ---------------------------------------------------------------------
    zc1, zc2 = zona_control.columns(2)
    control_atipicas = zc1.radio(
        TEXTOS['lecturasatipicas'], 
        options=[TEXTOS['opcnomodificar'], TEXTOS['opcborrar']], horizontal=True,
    )
    umbral_atipicas = zc2.number_input(
        TEXTOS['captionumbralatipicas'],
        value=nucleo.UMBRAL_ATIPICAS,
        min_value=1,
        step=1,
    )
    if control_atipicas == TEXTOS['opcborrar']:
        df_individuales = nucleo.borrar_atipicas(df_individuales, umbral_atipicas)

    # Control de perdidas ---------------------------------------------------------------------
    # Debe ser el último control pues los otros pueden borrar
    control_perdidas = zona_control.radio(
        TEXTOS['lecturasperdidas'], 
        options=[TEXTOS['opcnomodificar'], TEXTOS['opcasumircero']], horizontal=True,
    )
    if control_perdidas == TEXTOS['opcasumircero']:
        df_individuales = nucleo.rellenar_perdidas_con_cero(df_individuales, intervalo)

    # Generar datos agrupados según criterio y calcular métricas -------------------------------
    criterio = zona_grafico_agrupadas.radio(TEXTOS['lecturasagrupadas'], 
        options=list(agrupaciones.keys()), index=1, horizontal=True,
    )
    df_agrupado   = agrupar_lecturas(
        df_individuales, 
        intervalo_base=f'{intervalo}min', 
        intervalo_grupo=agrupaciones[criterio],
        umbral_precipitacion=umbral_atipicas,
    )
    suma_columnas, porcentajes = nucleo.resumir_categorias(df_agrupado)
    metricas = [
        f'{label}: {value:.0f} ({porcentaje:.2f}%)' 
        for label, value, porcentaje in zip(suma_columnas.index, suma_columnas, porcentajes)
    ]

    # Mostrar gráfico de precipitaciones ------------------------------------------------------
    zona_grafico_agrupadas.line_chart(df_agrupado, x=col_fechahora, y=TEXTOS['colpacumulada'])

    # Mostrar gráfico de categoria de lecturas -----------------------------------------------
    categorias_elegidas = zona_categorias.multiselect(
        TEXTOS['lecturasanormales'], options=lista_categorias, default=lista_anormales,
    )
    zona_categorias.bar_chart(df_agrupado, x=col_fechahora, y=categorias_elegidas)

    # Diagrama de tarta con métricas ----------------------------------------------------------
    fig, ax = plt.subplots()
    pie = ax.pie(suma_columnas)
    plt.legend(pie[0], metricas, fontsize='medium', loc='lower center')
    fig.patch.set_alpha(0)
    zona_metricas.pyplot(fig)

    # Detalle de lecturas ---------------------------------------------------------------------
    with zona_detalle_agrupadas:
        ver_dataframe(df_agrupado, TEXTOS['lecturasagrupadas'])
    with zona_detalle_individuales:
        ver_dataframe(df_individuales, TEXTOS['lecturasindividuales'])

    # Verificar si aún quedan valores anormales por procesar ----------------------------------
    if nucleo.quedan_anormales(suma_columnas):
        return None
    
    # -----------------------------------------------------------------------------------------
    return df_individuales

# ---------------------------------------------------------------------------------------------
@st.cache_data(show_spinner=TEXTOS['stcachespinner'])
def normalizar_lecturas(df: pd.DataFrame, intervalo_minutos: int) -> pd.DataFrame:
    return nucleo.normalizar_lecturas(df, intervalo_minutos)

# ---------------------------------------------------------------------------------------------
@st.cache_data(show_spinner=TEXTOS['stcachespinner'])
def consolidar_lecturas(
    df: pd.DataFrame, 
    fecha_inicial, fecha_final, 
    intervalo: int,
) -> pd.DataFrame:
    return nucleo.consolidar_lecturas(df, fecha_inicial, fecha_final, intervalo)

# ---------------------------------------------------------------------------------------------
def definir_parametros(df_procesadas: pd.DataFrame, intervalo: int) -> pd.DataFrame:
    col_fechahora = df_procesadas.columns[0]

    # Parámetros de fecha
    primera_fecha = st.date_input(
        TEXTOS['paramfechainicial'],
        value=df_procesadas[col_fechahora].min(),
        min_value=df_procesadas[col_fechahora].min(),
        max_value=df_procesadas[col_fechahora].max(),
    )
    ultima_fecha = st.date_input(
        TEXTOS['paramfechafinal'],
        value=df_procesadas[col_fechahora].max(),
        min_value=df_procesadas[col_fechahora].min(),
        max_value=df_procesadas[col_fechahora].max(),
    )
    st.caption('')

    # Parámetros de precipitación
    duracion_minima = st.number_input(
        TEXTOS['paramduracionmin'],
        value=nucleo.DURACION_MINIMA,
        min_value=intervalo,
    )
    duracion_maxima = st.number_input(
        TEXTOS['paramduracionmax'],
        value=nucleo.DURACION_MAXIMA,
        min_value=intervalo,
    )
    intensidad_minima = st.number_input(
        TEXTOS['paramintensidadmin'],
        value=nucleo.INTENSIDAD_MINIMA,
        min_value=1,
        step=1,
    )
    st.caption('')

    # Parámetros de continuidad
    pausa_maxima = st.number_input(
        TEXTOS['parampausamax'],
        value=intervalo * 2,
        min_value=0,
        step=intervalo,
        help=TEXTOS['pausamaximahelp'],
    )
    incluir_pausa_igual = st.selectbox(
        TEXTOS['paramincluirpausaigual'],
        options=[True, False],
        format_func=(
            lambda x: TEXTOS['opcincluirpausaigual'] if x else TEXTOS['opcsepararpausaigual']
        ),
        help=TEXTOS['incluirpausaigualhelp'],
    )

    # La fecha final incluye el día completo (hasta 23:59:59), igual que en la CLI
    df_consolidadas = consolidar_lecturas(
        df_procesadas, primera_fecha, nucleo.fin_del_dia(ultima_fecha), intervalo
    )
    df_eventos_calculados = nucleo.calcular_eventos(
        df_consolidadas,
        duracion_minima, duracion_maxima,
        pausa_maxima, intensidad_minima,
        intervalo, incluir_pausa_igual
    )

    return df_eventos_calculados

# ---------------------------------------------------------------------------------------------
def seccion_graficar_curvas_huff(df_eventos: pd.DataFrame):

    zona_grafico = st.empty()
    c1, c2 = st.columns(2)
    intervalo_percentiles = c1.select_slider(
        TEXTOS['captionintervalprcntles'],
        options=[5, 10, 20, 25, 50],
        value=nucleo.INTERVALO_PERCENTILES,
    )

    curvas_huff = nucleo.calcular_curvas_huff(df_eventos, intervalo=intervalo_percentiles)
    valores_eje_x = range(0, 101, intervalo_percentiles)

    fig, ax = plt.subplots(figsize=(6, 4))
    marcas = "vDo^"
    for indice, curva in curvas_huff.iterrows():
        ax.plot(
            valores_eje_x,
            list(curva[TEXTOS['colpercentiles']]),
            label=curva['Q'],
            marker=marcas[indice]
        )

    ax.set_xticks(range(0, 101, intervalo_percentiles))
    ax.set_yticks(range(0, 101, 5))

    ax.grid(which='both', linestyle='--', linewidth=0.5)
    ax.grid(which='minor', linestyle=':', linewidth=0.5)

    ax.set_xlabel(TEXTOS['label%duracion'])
    ax.set_ylabel(TEXTOS['label%precipitacion'])

    ax.legend(fontsize=8)

    zona_grafico.pyplot(fig)

    with c2.popover(TEXTOS['captionverpercentiles'], use_container_width=True):
        curvas_huff[TEXTOS['colpercentiles']] = curvas_huff[TEXTOS['colpercentiles']].apply(
            lambda x: [round(i, 2) for i in x]
        )
        st.dataframe(
            curvas_huff,
            column_order=('Q', TEXTOS['colpercentiles']), 
            hide_index=True,
        )

    return

# ---------------------------------------------------------------------------------------------
def preparar_curva_frecuencia(ax, df, nombrecol, zona):

    # Curva general
    porcentajes_x, valores = nucleo.curva_frecuencia(df, nombrecol)
    ax.plot(porcentajes_x, valores, label=TEXTOS['labelgeneral'], linestyle='-', linewidth=1.2)

    # Tabla general interpolada
    zona.write(f'{TEXTOS['labelprobabilidad']} (interpolada) vs {nombrecol}')
    tabla = nucleo.tabla_frecuencia_interpolada(porcentajes_x, valores, nombrecol)

    zona.dataframe(
        tabla,
        hide_index=True,
        use_container_width=True,
        column_config={
            nombrecol : st.column_config.NumberColumn(format='%.2f'),
        }
    )

    # Curvas por categoría Huff
    for categoria, porcentajes_x, valores in nucleo.curvas_frecuencia_por_categoria(df, nombrecol):
        ax.plot(porcentajes_x, valores, label=categoria, linewidth=0.9, linestyle='-.')

    ax.set_ylabel(nombrecol.capitalize())
    ax.set_xlabel(TEXTOS['labelprobabilidad'])

    ax.legend(fontsize=8)
    ax.grid(which='both', linestyle='--', linewidth=0.5)
    ax.minorticks_on()
    ax.grid(which='minor', linestyle=':', linewidth=0.5)

    return

# ---------------------------------------------------------------------------------------------
def seccion_graficar_curvas_frecuencia(df: pd.DataFrame):
    if df.shape[0] <= 1:
        st.warning(TEXTOS['errorpocoseventos'])
        return

    zona_graficas = st.empty()
    zona_tabla1, _, zona_tabla2 = st.columns([0.45, 0.1, 0.45])
    fig, (ax_duracion, ax_precipit) = plt.subplots(1, 2, figsize=(7, 4))

    preparar_curva_frecuencia(ax_duracion, df, TEXTOS['colduracion'], zona_tabla1)
    preparar_curva_frecuencia(ax_precipit, df, TEXTOS['colpacumulada'], zona_tabla2)

    zona_graficas.pyplot(fig)

    return

# ---------------------------------------------------------------------------------------------
def seccion_graficar_rangos_intensidad(df_eventos):
    
    num_aguaceros = df_eventos.shape[0]
    if num_aguaceros <= 2:
        st.warning(TEXTOS['errorpocoseventos'])
        return

    intensidad_min, intensidad_max = nucleo.limites_intensidad(df_eventos)

    if intensidad_min == intensidad_max:
        st.warning(TEXTOS['errorigualintensidad'])
        return

    zona_grafico = st.empty()
    num_rangos = st.slider(
        TEXTOS['captionnumrangos'],
        value=3,
        min_value=2, 
        max_value=10,
    )
    rangos, conteo_por_categoria, categorias = nucleo.calcular_rangos_intensidad(
        df_eventos, num_rangos, intensidad_min, intensidad_max,
    )

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
    ax.set_xlabel(TEXTOS['labelrangosintensidad'])
    ax.set_ylabel(TEXTOS['labelfrecuencia'])
    ax.grid(which='both', linestyle='--', linewidth=0.5, axis='y')
    ax.grid(which='minor', linestyle=':', linewidth=0.5, axis='y')

    zona_grafico.pyplot(fig)

    return

# ---------------------------------------------------------------------------------------------
@st.cache_data(show_spinner=TEXTOS['stcachespinner'])
def obtener_acumulados(df: pd.DataFrame) -> pd.DataFrame:
    return nucleo.obtener_acumulados(df)

# ---------------------------------------------------------------------------------------------
def seccion_graficar_acumulados_lapso(df: pd.DataFrame):

    df_acumulados = obtener_acumulados(df)
    st.write(TEXTOS['statsacumulados'])
    st.dataframe(df_acumulados.describe(include=np.number), use_container_width=True)
    ver_dataframe(df_acumulados, titulo=TEXTOS['detalleacumulados'])

    return

# ---------------------------------------------------------------------------------------------
def desplegar_info_eventos(df_eventos: pd.DataFrame):
    lista_tabs = [
        TEXTOS['tabdetalle'],
        TEXTOS['tabhuff'],
        TEXTOS['tabfrecuencia'],
        TEXTOS['tabrangos'],
        TEXTOS['tabacumulados'],
    ]
    t0, t1, t2, t3, t4 = st.tabs(lista_tabs)

    with t0:
        desplegar_eventos(df_eventos)
    with t1:
        seccion_graficar_curvas_huff(df_eventos)
    with t2:
        seccion_graficar_curvas_frecuencia(df_eventos)
    with t3:
        seccion_graficar_rangos_intensidad(df_eventos)
    with t4:
        seccion_graficar_acumulados_lapso(df_eventos)

    return

# ---------------------------------------------------------------------------------------------
def desplegar_eventos(df: pd.DataFrame):
    zona_seleccion = st.empty()
    st.write(TEXTOS['statseventos'])
    columnas_seleccionadas = zona_seleccion.multiselect(
        'Columnas a visualizar',
        options=df.columns, 
        default=[
            TEXTOS['colinicia'], 
            TEXTOS['colduracion'], 
            TEXTOS['colpacumulada'], 
            TEXTOS['colintensidad'],
            TEXTOS['colconteo'],
        ],
    )
    st.dataframe(
        df[columnas_seleccionadas].describe(include=np.number), 
        use_container_width=True,
    )
    ver_dataframe(df[columnas_seleccionadas], TEXTOS['detalleeventos'])

    return

# =============================================================================================
# Sección principal
# =============================================================================================

inicializar()

zona_descripcion = st.empty()
zona_TEXTOS = st.empty()
lista_tabs = [
    TEXTOS['tabarchivo'],
    TEXTOS['tablecturas'],
    TEXTOS['tabeventos']
]
tab_archivo, tab_lecturas, tab_eventos = st.tabs(lista_tabs)

# ---------------------------------------------------------------------------------------------
df_archivo, nombre_archivo = obtener_archivo_lecturas()
if df_archivo is None:
    zona_TEXTOS.info(TEXTOS['elegirarchivo'])
    st.stop()

# ---------------------------------------------------------------------------------------------
zona_descripcion.write(f'**{nombre_archivo}**')
with tab_archivo:
    desplegar_archivo(df_archivo)

# ---------------------------------------------------------------------------------------------
col_fechahora = elegir_nombre_columna(
    prompt=TEXTOS['elegircolfechahora'], 
    tipos_validos=['datetime64'],
    df=df_archivo,
)
if (col_fechahora is None):
    zona_TEXTOS.info(TEXTOS['elegircolfechahora'])
    st.stop()

# ---------------------------------------------------------------------------------------------
col_precipitacion = elegir_nombre_columna(
    prompt=TEXTOS['elegircolprecipitacion'], 
    tipos_validos=['int64', 'float64'],
    df=df_archivo
)
if (col_precipitacion is None):
    zona_TEXTOS.info(TEXTOS['elegircolprecipitacion'])
    st.stop()

# ---------------------------------------------------------------------------------------------
df_lecturas = extraer_lecturas(df_archivo, col_fechahora, col_precipitacion)

# Detectar intervalo y normalizar/alinear lecturas a él ---------------------------------------
intervalo = estimar_intervalo_lecturas(df_lecturas)
df_lecturas = normalizar_lecturas(df_lecturas, intervalo)
st.sidebar.caption(
    f'*{TEXTOS["lecturasnormalizadas"](intervalo)}*'
)

# Procesamiento de lecturas -------------------------------------------------------------------
with tab_lecturas:
    df_lecturas_procesadas = desplegar_lecturas(df_lecturas, intervalo)

# Prcesamiento de eventos ---------------------------------------------------------------------
with tab_eventos:
    if df_lecturas_procesadas is None:
        st.warning(TEXTOS['lecturasporcontrolar'])
        st.stop()

    c1, c2 = st.columns([0.15, 0.85], gap='medium')
    with c1:
        df_eventos = definir_parametros(df_lecturas_procesadas, intervalo)
    with c2:
        desplegar_info_eventos(df_eventos)
