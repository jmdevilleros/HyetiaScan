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
        self.df_eventos  = pd.DataFrame() # Luego preprocesamiento de lecturas

        self.col_fechahora     = None
        self.col_precipitacion = None

    # -----------------------------------------------------------------------------------------
    def obtener_lecturas(self):
        # Reiniciar variables dependientes del contenido
        self.df_eventos        = pd.DataFrame()
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
        else:
            self.col_fechahora = col_fechahora
            self.col_precipitacion = col_precipitacion
            self.df_eventos = pd.DataFrame(
                {col_fechahora : fechashoras, col_precipitacion : precipitaciones}
            )
            return True
