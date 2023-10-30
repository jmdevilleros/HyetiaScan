# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias, detección de aguaceros y gráficos de curvas de Huff
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
# Octubre-Noviembre de 2023
#
# Archivo: Precipitaciones.py - Definición de clase para manejo de Precipitaciones de lluvia
# *********************************************************************************************


# =============================================================================================
# Bibliotecas
# =============================================================================================

import pandas as pd


# ---------------------------------------------------------------------------------------------
class Precipitaciones:

    # -----------------------------------------------------------------------------------------
    def __init__(self):
        self.archivo_io  = None # Objeto BytesIO para lectura física de archivo
        self.df_lecturas = None # Dataframe que almacena las lecturas de precipitacion
        self.df_eventos  = None # Luego de preprocesamiento de lecturas

        self.col_fechahora        = None
        self.col_precipitacion    = None
        self.intervalo_mediciones = None

    # -----------------------------------------------------------------------------------------
    def obtener_lecturas(self):
        # Reiniciar variables dependientes del contenido
        self.df_eventos        = None
        self.col_fechahora     = None
        self.col_precipitacion = None

        # TODO: Deteccion de encoding
        try:
            self.df_lecturas = pd.read_csv(self.archivo_io)
        except:
            self.df_lecturas = None

    # -----------------------------------------------------------------------------------------
    # Retorna True si obtuvo columna, False si no la obtuvo
    def _obtener_columna_fechahora(self, nombre_columna):
        if (nombre_columna not in self.df_lecturas.columns) \
            | (self.df_lecturas[nombre_columna].dtype not in  ['object', 'datetime64']):
            return None

        try:
            columna = pd.to_datetime(self.df_lecturas[nombre_columna])
            return columna
        except:
            return None

    # -----------------------------------------------------------------------------------------
    # Retorna True si obtuvo columna, False si no la obtuvo
    def _obtener_columna_precipitacion(self, nombre_columna):
        if nombre_columna not in self.df_lecturas.columns:
            return None
        
        tipo_columna = self.df_lecturas[nombre_columna].dtype

        if tipo_columna == 'object':
            try:
                columna = self.df_lecturas[nombre_columna].apply(
                    lambda x: float(x.replace(',', '.'))
                )
                return columna
            except:
                return None
        else:
            try:
                columna = pd.to_numeric(self.df_lecturas[nombre_columna])
                return columna
            except ValueError:
                return None
        
    # -----------------------------------------------------------------------------------------
    def asignar_columnas_seleccionadas(self, col_fechahora, col_precipitacion):
        fechashoras = self._obtener_columna_fechahora(col_fechahora)
        precipitaciones = self._obtener_columna_precipitacion(col_precipitacion)

        if (fechashoras is None) | (precipitaciones is None):
            return False

        self.col_fechahora = col_fechahora
        self.col_precipitacion = col_precipitacion
        self.df_eventos = pd.DataFrame(
            {col_fechahora : fechashoras, col_precipitacion : precipitaciones}
        )
        self.intervalo_mediciones = 0

        return True

    # -----------------------------------------------------------------------------------------
    def detectar_intervalo_mediciones(self):
        if self.intervalo_mediciones > 0:
            # Ya detectado, terminar
            return True
        
        es_intervalo_detectable = \
            (isinstance(self.df_eventos, pd.DataFrame)) & \
            (self.df_eventos.shape[0] > 1)              & \
            (self.col_fechahora is not None)

        if not es_intervalo_detectable:
            return False
        
        t0 = self.df_eventos.iloc[0][self.col_fechahora]
        t1 = self.df_eventos.iloc[1][self.col_fechahora]
        self.intervalo_mediciones = (t1 - t0).seconds / 60

        if self.intervalo_mediciones < 1:
            return False

        return True

    # -----------------------------------------------------------------------------------------
    def detectar_vacios(self):
        # Valores de precipitacion menor a cero son errores de medición, eliminarlos 
        # para dejar que se procesen en las lineas siguientes como lagunas de datos
        self.df_eventos = self.df_eventos[self.df_eventos[self.col_precipitacion] >= 0]

        delta = pd.Timedelta(minutes=self.intervalo_mediciones)
        vacios = self.df_eventos[self.col_fechahora].diff() > delta
        vacios_indices = self.df_eventos.loc[vacios, self.col_fechahora]
        
        num_vacios = len(vacios_indices)
        if num_vacios <= 0:
            return 0, None
        
        inicio_vacios = self.df_eventos.loc[
            vacios.shift(-1, fill_value=False), self.col_fechahora
        ].tolist()
        termina_vacios = self.df_eventos.loc[
            vacios, self.col_fechahora
        ].tolist()
        df_vacios = pd.DataFrame({
            'inicia_vacio'  : inicio_vacios, 
            'termina_vacio' : termina_vacios,
        })
        df_vacios['duracion_vacio'] = \
            (df_vacios['termina_vacio'] - df_vacios['inicia_vacio']).dt.total_seconds() // 60

        return num_vacios, df_vacios

    # -----------------------------------------------------------------------------------------
    def rellenar_vacios(self):
        rango_completo = pd.date_range(
            start=self.df_eventos[self.col_fechahora].min(), 
            end=self.df_eventos[self.col_fechahora].max(), 
            freq=f'{self.intervalo_mediciones}T'
        )
        timestamps_faltantes = rango_completo.difference(self.df_eventos[self.col_fechahora])
        df_faltantes = pd.DataFrame(timestamps_faltantes, columns=[self.col_fechahora])

        df_faltantes[self.col_precipitacion] = 0
        self.df_eventos = \
            pd.concat([self.df_eventos, df_faltantes]).sort_values(by=self.col_fechahora)

        self.df_eventos.reset_index(drop=True, inplace=True)

        return
    
    # -----------------------------------------------------------------------------------------
    def calcular_eventos_precipitacion(self):
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
        self.df_eventos['duracion'] = \
            (self.df_eventos['termina'] - self.df_eventos['inicia']).dt.total_seconds() // 60 \
            + self.intervalo_mediciones

    
    
    