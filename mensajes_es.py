# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
#
# Archivo: mensajes_es.py - Texto de mensajes en español
# *********************************************************************************************

TEXTOS = {
    'appname'                 : 'HyetiaScan',
    'appversion'              : '2.1.2',
    'appdescription'          : 'Análisis de eventos de precipitación.',

    'about' : '''
        ### HyetiaScan - Análisis de lluvias
        - Juan Manuel de Villeros Arias
        - Mónica Liliana Gallego Jaramillo
        ### Contacto: hyetiascan@teoktonos.com
        ''',

    'fileuploaderhelp'        : '''
            El archivo debe contener lecturas de precipitación consecutivas en serie 
            de tiempo ordenada, con al menos una columna de fecha/hora (datetime) y
            al menos una columna numérica de precipitación.
            ''',
    
    'pausamaximahelp'         : '''
            Criterio de continuidad en minutos. \n
            Tiempo máximo de lecturas en cero para \n
            considerarlas parte de un evento continuo.
            ''',

    'stcachespinner'          : 'Cargando...',

    'errorlecturas'           : 'Error en archivo seleccionado.',
    'errorfechahora'          : lambda c, i, v: f'Error de formato en columna "{c}", índice {i}: [{v}]',
    'errortipocols'           : lambda t: f'No se detectan columnas de tipo {t}',
    'errorpocoseventos'       : 'Se requieren dos o mas eventos.',
    'errorigualintensidad'    : 'No hay diferencia de intensidades',
    
    'elegirdecimal'           : 'Separador decimal',
    'elegircodificacion'      : 'Codificación',
    'elegirarchivo'           : 'Seleccione archivo de lecturas.',
    'elegircolfechahora'      : 'Seleccione columna de fecha-hora.',
    'elegircolprecipitacion'  : 'Seleccione columna de precipitación.',

    'tabcarga'                : 'Cargar archivo',
    'tabconfig'               : 'Configurar carga',
    'tabarchivo'              : 'Archivo',
    'tablecturas'             : 'Lecturas',
    'tabeventos'              : 'Eventos',

    'tabdetalle'              : 'Detalle',
    'tabhuff'                 : 'Huff',
    'tabfrecuencia'           : 'Frecuencia',
    'tabrangos'               : 'Rangos',
    'tabacumulados'           : 'Acumulados',

    'previsualarchivo'        : 'Previsualizar registros.',
    'previsualcolnom'         : 'Columna',
    'previsualtipnom'         : 'Tipo',
    'previsualcantidad'       : 'Cantidad a visualizar',
    'previsualindice'         : 'Índice',

    'descripciondia'          : 'Dia',
    'descripcionmes'          : 'Mes',
    'descripcionano'          : 'Año',

    'lecturasnormalizadas'    : lambda i: f'Lecturas normalizadas a intervalos de {i} minuto{"s" if i > 1 else ""}',
    'lecturasporcontrolar'    : 'Aún quedan lecturas anormales por controlar',
    'lecturasanormales'       : 'Lecturas anormales',
    'lecturasatipicas'        : 'Atípicas',
    'lecturasduplicadas'      : 'Duplicadas',
    'lecturascorruptas'       : 'Corruptas',
    'lecturasperdidas'        : 'Perdidas',
    'lecturasagrupadas'       : 'Lecturas agrupadas',
    'lecturasindividuales'    : 'Lecturas individuales',

    'controlanormales'        : 'Control de lecturas anormales',
    'detallelecturas'         : 'Detalle de lecturas',
    'detalleeventos'          : 'Detalle de eventos',
    'detalleacumulados'       : 'Detalle de acumulados',
    'statsacumulados'         : 'Estadísticas de acumulados',
    'statseventos'            : 'Estadísticas de eventos',

    'colpacumulada'           : 'P_acumulada',
    'colcorrectas'            : 'correctas',
    'colperdidas'             : 'perdidas',
    'colduplicadas'           : 'duplicadas',
    'colatipicas'             : 'atípicas',
    'colcorruptas'            : 'corruptas',
    'colinicia'               : 'inicia',
    'coltermina'              : 'termina',
    'colduracion'             : 'duracion',
    'colintensidad'           : 'intensidad',
    'collecturas'             : 'lecturas',
    'colsecuencia'            : 'secuencia',
    'colporcentajes'          : 'porcentajes',
    'colpercentiles'          : 'percentiles',
    'colconteo'               : 'conteo',
    'collluvia'               : 'lluvia',
    'colrango'                : 'rango',

    'opcnomodificar'          : 'No modificar',
    'opcborrar'               : 'Borrar',
    'opcdejarprimera'         : 'Dejar primera',
    'opcdejarultima'          : 'Dejar última', 
    'opcsumar'                : 'Sumar',
    'opcpromediar'            : 'Promediar',
    'opcasumircero'           : 'Asumir 0 (cero)',

    'paramfechainicial'       : 'Fecha inicial',
    'paramfechafinal'         : 'Fecha final',
    'paramduracionmin'        : 'Duración mínima (minutos)',
    'paramduracionmax'        : 'Duración máxima (minutos)',
    'parampausamax'           : 'Pausa máxima (minutos)',
    'paramintensidadmin'      : 'Intensidad mínima (mm/h)',

    'paramincluirpausaigual'  : 'Manejo de pausa máxima',
    'opcincluirpausaigual'    : 'Incluir (es lluvia)',
    'opcsepararpausaigual'    : 'Separar (es interrupción)',
    'incluirpausaigualhelp'   : '''
        Controla si las pausas en la lluvia (mediciones consecutivas en cero) con 
        duración exactamente igual a la "pausa máxima" definida por el usuario se 
        consideran parte del mismo evento de lluvia o como interrupciones que 
        separan eventos. 
        Por ejemplo, si "pausa máxima" es 15 minutos, "Incluir" tratará una pausa 
        de exactamente 15 minutos como parte de la lluvia, mientras que "Separar" 
        la tratará como una interrupción que divide los eventos.
    ''',

    'label%duracion'          : '% duración',
    'label%precipitacion'     : '% precipitación',
    'labelprobabilidad'       : 'Probabilidad',
    'labelrangosintensidad'   : 'Rangos de intensidad',
    'labelfrecuencia'         : 'Frecuencia',
    'labelgeneral'            : 'General',

    'captionintervalprcntles' : 'Intervalo de percentiles',
    'captionverpercentiles'   : 'Ver valores percentiles',
    'captionpunto'            : 'Punto',
    'captioncoma'             : 'Coma',
    'captionnumrangos'        : 'Número de rangos',
    'captionumbralatipicas'   : 'Umbral atípicas',
}