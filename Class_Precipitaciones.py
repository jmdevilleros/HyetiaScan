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
    def obtener_columna_fechahora(self, columna):
        print(f'col_fechahora={columna}')
        # Verificar que haya columna candidata
        if columna not in self.df_lecturas.columns:
            self.col_fechahora = None
            self.df_eventos = pd.DataFrame()
            return False
        
        # Verificar tipo de fecha y hora
        # TODO: buscar por que se enloquece cuando se cambia si la col anterior es válida
        tipo_columna = self.df_lecturas[columna].dtype
        if tipo_columna == 'object':
            try:
                self.df_eventos[columna] = pd.to_datetime(self.df_lecturas[columna])
            except:
                self.col_fechahora = None
                return False
        elif tipo_columna == 'datetime64':
            self.df_eventos[columna] = self.df_lecturas[columna]
        else:
            self.col_fechahora = None
            return False
        
        self.col_fechahora = columna
        return True
