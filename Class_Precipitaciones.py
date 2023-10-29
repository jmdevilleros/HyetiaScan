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
    def obtener_columna_fechahora(self, nombre_columna):
        es_valida = \
            (nombre_columna in self.df_lecturas.columns)  & \
            (self.df_lecturas[nombre_columna].dtype in  ['object', 'datetime64'])

        if es_valida:
            try:
                columna = pd.to_datetime(self.df_lecturas[nombre_columna])
            except:
                es_valida = False

        if es_valida:
            self.col_fechahora = nombre_columna
            self.df_eventos[nombre_columna] = columna

        return es_valida

