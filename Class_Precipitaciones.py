# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias, detección de aguaceros y gráficos de curvas de Huff
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
# Abril 2024
#
# Archivo: Precipitaciones.py - Definición de clase para manejo de Precipitaciones de lluvia
# *********************************************************************************************


# =============================================================================================
# Bibliotecas
# =============================================================================================

import pandas as pd
import numpy as np
import re


# ---------------------------------------------------------------------------------------------
class Precipitaciones:

    # -----------------------------------------------------------------------------------------
    def __init__(self):
        self.nombre    = None # Nombre de archivo de lecturas
        self.df_origen = None # Dataframe con contenido de archivo
        self.inicializa_lecturas()

    # -----------------------------------------------------------------------------------------
    def inicializa_lecturas(self):
        self.df_mediciones        = None # Mediciones individuales según columnas seleccionadas
        self.df_eventos           = None # Eventos de precipitación con inicio y fin
        self.df_aguaceros         = None # Aguaceros detectados segpun criterios especificados

        self.col_fechahora        = None # Columna elegida para marca de tiempo
        self.col_precipitacion    = None # Columna elegida para valor de medida
        self.intervalo_mediciones = None # Intervalo en minutos entre medidas

        # Criterios de aguacero por defecto
        self.duracion_minima   = 15
        self.duracion_maxima   = 120
        self.duracion_tope     = 10000
        self.pausa_maxima      = 5
        self.intensidad_minima = 2
        self.primera_fecha     = None
        self.ultima_fecha      = None

    # -----------------------------------------------------------------------------------------
    def obtener_lecturas(self, archivo_io):
        self.inicializa_lecturas()

        # TODO: Deteccion de encoding
        try:
            self.df_origen = pd.read_csv(archivo_io)
            self.nombre = archivo_io.name
        except:
            self.df_origen = None

    # -----------------------------------------------------------------------------------------
    # Retorna True si obtuvo columna, False si no la obtuvo
    def _obtener_columna_fechahora(self, nombre_columna):

        # ------------------------------------------------------------------------------------
        def extraer(mensaje_error):
            buscar_fechas_fallidas = re.findall(r'\"(.*?)\"', mensaje_error)
            if len(buscar_fechas_fallidas) > 0:
                fecha_fallida = buscar_fechas_fallidas[0]
                position = re.findall(r'position (\d+)', mensaje_error)[0]
                return fecha_fallida, int(position)
            else:
                return mensaje_error, 0

        if nombre_columna is None:
            return None, 'Nombre vacío'
        if nombre_columna not in self.df_origen.columns:
            return None, 'Columna inexistente'
        tipo_columna = self.df_origen[nombre_columna].dtype
        if tipo_columna not in  ['object', 'datetime64']:
            return None, f'Tipo {tipo_columna} no compatible con fecha-hora'

        try:
            columna = pd.to_datetime(self.df_origen[nombre_columna])
            return columna, ''
        except ValueError as ve:
            val, pos = extraer(str(ve))
            return None, f'{val} en registro {pos}'
        except Exception as e:
            return None, str(e)

    # -----------------------------------------------------------------------------------------
    # Retorna True si obtuvo columna, False si no la obtuvo
    def _obtener_columna_precipitacion(self, nombre_columna):

        if nombre_columna is None:
            return None
        if nombre_columna not in self.df_origen.columns:
            return None
        tipo_columna = self.df_origen[nombre_columna].dtype
        if tipo_columna == 'object':
            try:
                columna = self.df_origen[nombre_columna].apply(
                    lambda x: float(x.replace(',', '.'))
                )
                return columna
            except:
                return None
        else:
            try:
                columna = pd.to_numeric(self.df_origen[nombre_columna])
                return columna
            except ValueError:
                return None
        
    # -----------------------------------------------------------------------------------------
    def asignar_columnas_seleccionadas(self, col_fechahora, col_precipitacion):
        self.inicializa_lecturas()

        fechashoras, msg  = self._obtener_columna_fechahora(col_fechahora)
        precipitaciones = self._obtener_columna_precipitacion(col_precipitacion)

        if (fechashoras is None):
            return False, f'columna fecha-hora: {msg}'
        
        if (precipitaciones is None):
            return False, 'columna de precipitación'

        self.col_fechahora = col_fechahora
        self.col_precipitacion = col_precipitacion
        self.df_mediciones = pd.DataFrame(
            {col_fechahora : fechashoras, col_precipitacion : precipitaciones}
        )

        return True, None

    # -----------------------------------------------------------------------------------------
    def agrupar_mediciones(self, df=None, frecuencia="D"):
        if (self.col_fechahora is None) or (self.col_precipitacion is None):
            return None
        
        if df is None:
            df = self.df_mediciones
        
        frecuencias_validas = ['min', 'h', 'D', 'W', 'ME', 'YE'] 
        if frecuencia not in frecuencias_validas:
            frecuencia = 'D'

        agrupacion = pd.Grouper(key=self.col_fechahora, freq=frecuencia)
        funcion_agregacion = {self.col_precipitacion: 'sum'}  
        return df.groupby(agrupacion).agg(funcion_agregacion)
        
    # -----------------------------------------------------------------------------------------
    def estimar_intervalo_mediciones(self):
        # Iniciar asumiendo que no hay intervalo válido
        self.intervalo_mediciones = None

        if self.df_mediciones is None:
            return False
        
        es_intervalo_detectable = \
            (isinstance(self.df_mediciones, pd.DataFrame)) & \
            (self.df_mediciones.shape[0] > 1)              & \
            (self.col_fechahora is not None)

        if not es_intervalo_detectable:
            return False
        
        # Intenta calcular intervalo con la moda de los delta_t entre los primeros registros
        try:
            s_delta_t = pd.to_timedelta(
                self.df_mediciones[self.col_fechahora].head(1000).diff().fillna(0)
            )
            intervalo = s_delta_t.mode()[0]
            detectado = intervalo.total_seconds() / 60
        except:
            return False

        if detectado <= 0:
            return False

        self.intervalo_mediciones = detectado

        return True

    # -----------------------------------------------------------------------------------------
    def detectar_lagunas(self):
        # Asumir valores <0 como mediciones faltantes
        df_tmp = self.df_mediciones[self.df_mediciones[self.col_precipitacion] >= 0].copy()

        delta = pd.Timedelta(minutes=self.intervalo_mediciones)
        vacios = df_tmp[self.col_fechahora].diff() > delta
        vacios_indices = df_tmp.loc[vacios, self.col_fechahora]
        
        num_lagunas = len(vacios_indices)
        if num_lagunas <= 0:
            return 0, None
        
        inicia  = df_tmp.loc[vacios.shift(-1, fill_value=False), self.col_fechahora].tolist()
        termina = df_tmp.loc[vacios, self.col_fechahora].tolist()
        df_lagunas = pd.DataFrame({
            'inicia'  : inicia, 
            'termina' : termina,
        })
        df_lagunas['duracion'] = \
            (df_lagunas['termina'] - df_lagunas['inicia']).dt.total_seconds() // 60

        return num_lagunas, df_lagunas

    # -----------------------------------------------------------------------------------------
    def rellenar_faltantes(self, valor_relleno=0):
        # Asumir valores <0 como mediciones faltantes
        self.df_mediciones = self.df_mediciones[self.df_mediciones[self.col_precipitacion] >= 0]

        rango_completo = pd.date_range(
            start=self.df_mediciones[self.col_fechahora].min(), 
            end=self.df_mediciones[self.col_fechahora].max(), 
            freq=f'{self.intervalo_mediciones}min'
        )
        timestamps_faltantes = rango_completo.difference(self.df_mediciones[self.col_fechahora])
        df_faltantes = pd.DataFrame(timestamps_faltantes, columns=[self.col_fechahora])

        df_faltantes[self.col_precipitacion] = valor_relleno
        self.df_mediciones = \
            pd.concat([self.df_mediciones, df_faltantes]).sort_values(by=self.col_fechahora)

        self.df_mediciones.reset_index(drop=True, inplace=True)

        return
    
    # -----------------------------------------------------------------------------------------
    def calcular_eventos_precipitacion(self):
        if self.intervalo_mediciones is None:
            self.df_eventos = None
            return
        
        self.df_eventos = self.df_mediciones.copy()

        # Crear una columna adicional para marcar los cambios de 0 a otro valor y viceversa
        self.df_eventos['cambio'] = \
            (self.df_eventos[self.col_precipitacion] != 0) != \
            (self.df_eventos[self.col_precipitacion] != 0).shift(1)
        self.df_eventos['grupo'] = self.df_eventos['cambio'].cumsum()

        # Realizar la agregación basada en el grupo
        self.df_eventos = self.df_eventos.groupby('grupo').agg(
            inicia                  = (self.col_fechahora, 'first'),
            termina                 = (self.col_fechahora, 'last'),
            conteo                  = (self.col_precipitacion, 'count'),
            precipitacion_acumulada = (self.col_precipitacion, 'sum'),
            mediciones              = (self.col_precipitacion, lambda p: p.tolist()),
        ).reset_index(drop=True)

        # Agregar coiumna de duracion
        self.df_eventos['duracion'] = self.intervalo_mediciones + \
            (self.df_eventos['termina'] - self.df_eventos['inicia']).dt.total_seconds() // 60
        
        # Estimar duracion tope e inicializar maxima en ese mismo valor
        # Diferente de la maxima: "maxima" define el criterio de deteccion,
        # "tope" estima el valor tope que puede tomar la duracion con los datos.
        # Se estima como la duracion conjunta de los dos eventos mas largos.
        self.duracion_tope = int(
            self.df_eventos.loc[
                self.df_eventos['precipitacion_acumulada'] > 0, 
                'duracion'
            ].nlargest(2).sum()
        )
        self.duracion_maxima = self.duracion_tope

    # -----------------------------------------------------------------------------------------
    def detectar_aguaceros(self):

        # -------------------------------------------------------------------------------------
        def calcular_acumulados(lista_mediciones, factor=100):
            return  \
                (pd.Series(lista_mediciones).cumsum() * factor \
                 / sum(lista_mediciones)).to_list()

        # Consolidar eventos que se consideren contiguos
        df = self._unir_precipitaciones(
            self.df_eventos.copy(),
            self.pausa_maxima,
        )

        # Realizar la agregación basada en la secuencia de evento
        df = df.groupby('secuencia').agg(
            inicia                  = ('inicia', 'first'),
            termina                 = ('termina', 'last'),
            mediciones              = ('mediciones', lambda p: sum(p, [])),
            precipitacion_acumulada = ('precipitacion_acumulada', 'sum'),
        )

        # Filtrar por rango de fechas deseadas
        df = df.loc[
            (df['termina'] >= pd.to_datetime(self.primera_fecha)) & \
            (df['termina'] <= pd.to_datetime(self.ultima_fecha))
        ]

        # Recalcular columna de duracion
        df['duracion'] = \
            (df['termina'] - df['inicia']).dt.total_seconds() // 60 \
            + self.intervalo_mediciones

        # Agregar intensidad
        df['intensidad'] = \
            60 * df['precipitacion_acumulada'] / df['duracion']
        
        # Agregar conteo de mediciones
        df['conteo'] = df['mediciones'].apply(len)

        # Filtrar precipitaciones por duración
        df = df[
            (df['duracion'] >= self.duracion_minima) & \
            (df['duracion'] <= self.duracion_maxima) & \
            (df['precipitacion_acumulada'] != 0)
        ]

        # Filtrar por intensidad minima
        df = df[(df['intensidad'] >= self.intensidad_minima)]

        # Calcular y agregar porcentaje acumulado de mediciones
        df['porcentaje_acumulado'] = df['mediciones'].apply(calcular_acumulados)

        # Calcular y agregar cuartil de Huff
        df['Q_Huff'] = \
            df['porcentaje_acumulado'].apply(self.determinar_cuartil_huff)
        
        # Reordenar columnas
        df = df[[
            'inicia', 'termina', 'duracion', 
            'intensidad', 'precipitacion_acumulada', 'conteo', 
            'mediciones', 'porcentaje_acumulado', 'Q_Huff',
        ]]

        self.df_aguaceros = df.reset_index(drop=True)

    # -----------------------------------------------------------------------------------------
    def _unir_precipitaciones(self, df, pausa_maxima):
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
    def determinar_cuartil_huff(self, acumulados):
        
        # Calcular valor de cuartiles
        Q = np.percentile(acumulados, [25, 50, 75]).tolist()

        # Calcula las diferencias entre los cuartiles
        deltas = [
            Q[0], 
            Q[1] - Q[0], 
            Q[2] - Q[1], 
            100  - Q[2]
        ]

        # Calcular el índice del mayor delta para usarlo como clasificacion de tipo de curva Huff
        # El mayor delta indica que en ese lapso el aguacero tuvo su mayor precipitación
        # enumerate genera tuplas (indice, valor), key indica que max debe 
        # comparar por el segundo item de la tupla (x[1]), el valor que retorna 
        # max es una tupla (indice, valor mayor) asi que extraemos el
        # primer elemento [0], el del indice, para usarlo como categoria de cuartil
        indice_mayor_delta = max(enumerate(deltas), key=lambda x: x[1])[0]

        # Nombre del cuartil calculado. Empiezan en cero, el nombre debe empezar en 1
        Qname = f"Q{indice_mayor_delta + 1}"

        return Qname

    # ---------------------------------------------------------------------------------------------
    def calcular_curvas_huff(self, intervalo=5):
        datos_huff = pd.DataFrame()

        # Generar percentiles a partir de porcentaje_acumulado de aguaceros
        # Usar intervalo especificado como argumento de la función
        datos_huff['valores_percentiles'] = self.df_aguaceros['porcentaje_acumulado'].apply(
            lambda p: np.percentile(p, range(intervalo, 101, intervalo))
        )

        # Determinar cuartil de cada curva
        datos_huff['Q'] = self.df_aguaceros['Q_Huff']

        # Calcular curvas Huff como promedio de cada correspondiente valor de valores_percentiles
        curvas_huff = datos_huff.groupby('Q').agg(
            {'valores_percentiles': lambda x: np.mean(list(zip(*x)), axis=1)}
        ).reset_index()

        # Agregar un cero al principio de cada lista en 'valores_percentiles'
        curvas_huff['valores_percentiles'] = curvas_huff['valores_percentiles'].apply(
            lambda x: [0] + list(x)
        )

        return curvas_huff
