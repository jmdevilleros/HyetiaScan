# *********************************************************************************************
# HyetiaScan
# Análisis de lluvias
# Juan Manuel de Villeros Arias
# Mónica Liliana Gallego Jaramillo
# Junio - Agosto 2024
#
# Archivo: hyetiascan_cli.py - Interfaz de línea de comandos (sin Streamlit)
#
# Ejemplo:
#   python hyetiascan_cli.py ejemplos/lluvia_ejemplo_5min.csv --salida resultados \
#       --duplicadas primera --corruptas borrar --atipicas borrar --perdidas cero --json
# *********************************************************************************************

# =============================================================================================
# Bibliotecas
# =============================================================================================

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

import hyetiascan_core as nucleo
from mensajes_es import TEXTOS

# =============================================================================================
# Globales
# =============================================================================================

AGRUPACIONES = {
    'dia' : nucleo.AGRUPACION_DIA,
    'mes' : nucleo.AGRUPACION_MES,
    'ano' : nucleo.AGRUPACION_ANO,
}

SEPARADORES = {'tab': '\t', '\\t': '\t'}

COLUMNAS_LISTA = [TEXTOS['collecturas'], TEXTOS['colporcentajes'], TEXTOS['colpercentiles']]

# Códigos de salida
SALIDA_OK          = 0
SALIDA_ERROR       = 1
SALIDA_ARGUMENTOS  = 2   # argparse, argumentos inválidos
SALIDA_ANORMALES   = 3

# =============================================================================================
# Procedimientos y funciones
# =============================================================================================

# ---------------------------------------------------------------------------------------------
def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='hyetiascan_cli.py',
        description=(
            'HyetiaScan sin interfaz gráfica: procesa un CSV de lecturas de precipitación, '
            'controla lecturas anormales y calcula eventos de lluvia (Huff, acumulados). '
            'Usa la misma lógica que la aplicación Streamlit.'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Códigos de salida:\n'
            f'  {SALIDA_OK}  correcto (puede haber 0 eventos)\n'
            f'  {SALIDA_ERROR}  error de carga o de datos\n'
            f'  {SALIDA_ARGUMENTOS}  argumentos inválidos\n'
            f'  {SALIDA_ANORMALES}  quedan lecturas anormales sin controlar (perdidas, duplicadas,\n'
            '     corruptas o atípicas): igual que en la aplicación, no se calculan eventos.\n'
            '\n'
            'Fechas reconocidas: ISO (AAAA-MM-DD HH:MM[:SS], también con T), AAAA/MM/DD,\n'
            'DD/MM/AAAA, DD-MM-AAAA y DD.MM.AAAA (hora opcional HH:MM[:SS]). Con fechas\n'
            'ambiguas se asume día primero (use --mes-primero para MM/DD/AAAA). Valores con\n'
            'zona (-05:00, Z): se conserva la hora local escrita si todos tienen el mismo\n'
            'desplazamiento; si no, se convierten a UTC o a --zona-horaria.'
        ),
    )
    parser.add_argument('archivo', help='Archivo CSV de lecturas.')
    parser.add_argument('-o', '--salida', default='resultados_hyetiascan',
        help='Directorio de salida (se crea si no existe). Por defecto: %(default)s')

    carga = parser.add_argument_group('Carga de archivo')
    carga.add_argument('--decimal', choices=['.', ','], default='.',
        help='Separador decimal. Por defecto: "%(default)s"')
    carga.add_argument('--separador', default=None,
        help=(
            'Separador de columnas ("," ";" "tab" o "|"). Por defecto se detecta en el '
            'encabezado: ";" o tabulador si predominan sobre ",". Use ";" con --decimal ,'
        ))
    carga.add_argument('--formato-fecha', default=None,
        help='Formato strftime de la columna de fecha-hora, ej. "%%d/%%m/%%Y %%H:%%M". '
             'Por defecto se detecta.')
    carga.add_argument('--mes-primero', action='store_true',
        help='Interpretar fechas con barras/guiones como MM/DD/AAAA (por defecto DD/MM/AAAA).')
    carga.add_argument('--zona-horaria', default=None,
        help='Zona IANA (ej. America/Bogota) a la que se convierten fechas con zona horaria.')
    carga.add_argument('--codificacion', default='utf-8',
        help='Codificación del archivo (utf-8, utf-16, latin-1, ...). Por defecto: %(default)s')
    carga.add_argument('--col-fechahora', default=None,
        help='Columna de fecha-hora. Por defecto: la primera columna tipo fecha-hora.')
    carga.add_argument('--col-precipitacion', default=None,
        help='Columna de precipitación. Por defecto: la primera columna numérica.')

    control = parser.add_argument_group('Control de lecturas anormales')
    control.add_argument('--duplicadas', default='no-modificar',
        choices=['no-modificar', *nucleo.OPCIONES_DUPLICADAS],
        help='Control de lecturas duplicadas. Por defecto: %(default)s')
    control.add_argument('--corruptas', choices=['no-modificar', 'borrar'], default='no-modificar',
        help='Lecturas corruptas (negativas). Por defecto: %(default)s')
    control.add_argument('--atipicas', choices=['no-modificar', 'borrar'], default='no-modificar',
        help='Lecturas atípicas (mayores al umbral). Por defecto: %(default)s')
    control.add_argument('--umbral-atipicas', type=float, default=nucleo.UMBRAL_ATIPICAS,
        help='Umbral de lecturas atípicas (mm por lectura). Por defecto: %(default)s')
    control.add_argument('--perdidas', choices=['no-modificar', 'cero'], default='no-modificar',
        help='Lecturas perdidas: "cero" las asume en 0. Por defecto: %(default)s')
    control.add_argument('--agrupacion', choices=list(AGRUPACIONES), default='mes',
        help='Agrupación del resumen de lecturas. Por defecto: %(default)s')

    eventos = parser.add_argument_group('Parámetros de eventos')
    eventos.add_argument('--fecha-inicial', default=None,
        help='Fecha inicial (AAAA-MM-DD, con hora opcional). Por defecto: la primera lectura.')
    eventos.add_argument('--fecha-final', default=None,
        help=(
            'Fecha final (AAAA-MM-DD, con hora opcional). Una fecha sin hora incluye el día '
            'completo (hasta 23:59:59). Por defecto: el día completo de la última lectura.'
        ))
    eventos.add_argument('--duracion-minima', type=int, default=nucleo.DURACION_MINIMA,
        help='Duración mínima en minutos. Por defecto: %(default)s')
    eventos.add_argument('--duracion-maxima', type=int, default=nucleo.DURACION_MAXIMA,
        help='Duración máxima en minutos. Por defecto: %(default)s')
    eventos.add_argument('--intensidad-minima', type=float, default=nucleo.INTENSIDAD_MINIMA,
        help='Intensidad mínima en mm/h. Por defecto: %(default)s')
    eventos.add_argument('--pausa-maxima', type=int, default=None,
        help='Pausa máxima en minutos. Por defecto: dos veces el intervalo de lecturas.')
    eventos.add_argument('--pausa-igual', choices=['incluir', 'separar'], default='incluir',
        help=(
            'Pausas iguales a la pausa máxima: "incluir" (es lluvia, <=) o '
            '"separar" (es interrupción, <). Por defecto: %(default)s'
        ))
    eventos.add_argument('--intervalo-percentiles', type=int, default=nucleo.INTERVALO_PERCENTILES,
        choices=[5, 10, 20, 25, 50],
        help='Intervalo de percentiles para curvas Huff. Por defecto: %(default)s')

    parser.add_argument('--json', action='store_true',
        help='Escribe además resumen.json con parámetros, conteos y estadísticas.')
    return parser

# ---------------------------------------------------------------------------------------------
def error(mensaje: str) -> int:
    print(f'Error: {mensaje}', file=sys.stderr)
    return SALIDA_ERROR

# ---------------------------------------------------------------------------------------------
def guardar_csv(df: pd.DataFrame, ruta: Path, index: bool = False):
    # Columnas con listas se guardan como JSON para poder leerlas de nuevo
    df = df.copy()
    for col in COLUMNAS_LISTA:
        if col in df.columns:
            df[col] = df[col].apply(lambda v: json.dumps([float(x) for x in v]))
    df.to_csv(ruta, index=index)

# ---------------------------------------------------------------------------------------------
def a_json(valor):
    if isinstance(valor, pd.Timestamp):
        return valor.isoformat()
    if hasattr(valor, 'item'):
        return valor.item()
    return valor

# ---------------------------------------------------------------------------------------------
def elegir_columna(df: pd.DataFrame, nombre: str, tipos_validos: list[str], descripcion: str):
    columnas = nucleo.columnas_por_tipo(df, tipos_validos)
    if nombre is None:
        if not columnas:
            raise ValueError(TEXTOS['errortipocols'](tipos_validos))
        return columnas[0]
    if nombre not in df.columns:
        raise ValueError(f'La columna de {descripcion} "{nombre}" no existe. Columnas: {list(df.columns)}')
    if nombre not in columnas:
        raise ValueError(
            f'La columna de {descripcion} "{nombre}" no es de tipo {tipos_validos} '
            f'(es {df[nombre].dtype}).'
        )
    return nombre

# ---------------------------------------------------------------------------------------------
def main(argv=None) -> int:
    args = crear_parser().parse_args(argv)
    salida = Path(args.salida)

    # Carga ------------------------------------------------------------------------------------
    separador = SEPARADORES.get(args.separador, args.separador)
    if separador is None:
        try:
            separador = nucleo.detectar_separador(Path(args.archivo).read_bytes(), args.codificacion)
        except OSError as ex:
            return error(f'{TEXTOS["errorlecturas"]} {ex}')
        if args.decimal == ',' and separador == ',':
            print('Aviso: --decimal , con columnas separadas por ","; si el archivo usa ";" '
                  'indique --separador ";" (o ponga los valores entre comillas).', file=sys.stderr)
    try:
        df_archivo = nucleo.cargar_csv(
            args.archivo, decimal=args.decimal, codificacion=args.codificacion,
            separador=separador, formato_fecha=args.formato_fecha,
            dia_primero=not args.mes_primero, zona_horaria=args.zona_horaria,
        )
    except Exception as ex:
        return error(f'{TEXTOS["errorlecturas"]} {ex}')
    for nota in df_archivo.attrs.get('notas_fechahora', []):
        print(f'Aviso: {nota}', file=sys.stderr)
    if not nucleo.verificar_lecturas_cargadas(df_archivo):
        return error(TEXTOS['errorlecturas'])

    try:
        col_fechahora = elegir_columna(df_archivo, args.col_fechahora, ['datetime64'], 'fecha-hora')
        col_precipitacion = elegir_columna(
            df_archivo, args.col_precipitacion, ['int64', 'float64'], 'precipitación')
    except ValueError as ex:
        error_fh = nucleo.buscar_errores_fechahora(df_archivo)
        if error_fh is not None:
            print(TEXTOS['errorfechahora'](*error_fh), file=sys.stderr)
        return error(f'{ex}. Revise el formato de fecha (--formato-fecha, --mes-primero).')

    # Lecturas ---------------------------------------------------------------------------------
    df_lecturas = nucleo.extraer_lecturas(df_archivo, col_fechahora, col_precipitacion)
    intervalo = nucleo.estimar_intervalo_lecturas(df_lecturas)
    if intervalo <= 0:
        return error('No fue posible estimar el intervalo de lecturas.')
    df_lecturas = nucleo.normalizar_lecturas(df_lecturas, intervalo)
    print(TEXTOS['lecturasnormalizadas'](intervalo))

    df_procesadas = nucleo.procesar_lecturas(
        df_lecturas, intervalo,
        control_duplicadas=None if args.duplicadas == 'no-modificar' else args.duplicadas,
        corruptas_borrar=(args.corruptas == 'borrar'),
        atipicas_borrar=(args.atipicas == 'borrar'),
        umbral_atipicas=args.umbral_atipicas,
        perdidas_asumir_cero=(args.perdidas == 'cero'),
    )
    df_agrupado = nucleo.agrupar_lecturas(
        df_procesadas,
        intervalo_base=f'{intervalo}min',
        intervalo_grupo=AGRUPACIONES[args.agrupacion],
        umbral_precipitacion=args.umbral_atipicas,
    )
    suma_columnas, porcentajes = nucleo.resumir_categorias(df_agrupado)

    salida.mkdir(parents=True, exist_ok=True)
    guardar_csv(df_procesadas, salida / 'lecturas_procesadas.csv')
    guardar_csv(df_agrupado, salida / 'lecturas_agrupadas.csv')

    resumen = {
        'archivo'            : str(args.archivo),
        'col_fechahora'      : col_fechahora,
        'col_precipitacion'  : col_precipitacion,
        'intervalo_minutos'  : intervalo,
        'separador'          : separador,
        'notas_fechahora'    : df_archivo.attrs.get('notas_fechahora', []),
        'parametros'         : {k: v for k, v in vars(args).items() if k not in ('archivo', 'json')},
        'categorias_lecturas': {
            k: {'cantidad': a_json(suma_columnas[k]), 'porcentaje': a_json(porcentajes[k])}
            for k in suma_columnas.index
        },
    }
    for k in suma_columnas.index:
        print(f'  {k}: {suma_columnas[k]:.0f} ({porcentajes[k]:.2f}%)')

    # Eventos ----------------------------------------------------------------------------------
    codigo = SALIDA_OK
    if nucleo.quedan_anormales(suma_columnas):
        print(TEXTOS['lecturasporcontrolar'] + '. Use --duplicadas, --corruptas, '
              '--atipicas y/o --perdidas.', file=sys.stderr)
        resumen['eventos'] = None
        codigo = SALIDA_ANORMALES
    else:
        fechas = df_procesadas[df_procesadas.columns[0]]
        dia_primero = not args.mes_primero
        try:
            if args.fecha_inicial:
                fecha_inicial, _ = nucleo.interpretar_fecha(args.fecha_inicial, dia_primero)
            else:
                fecha_inicial = fechas.min().normalize()
            # Una fecha final sin hora incluye el día completo (la aplicación usa las 00:00)
            if args.fecha_final:
                fecha_final, tiene_hora = nucleo.interpretar_fecha(args.fecha_final, dia_primero)
                if not tiene_hora:
                    fecha_final = nucleo.fin_del_dia(fecha_final)
            else:
                fecha_final = nucleo.fin_del_dia(fechas.max())
        except ValueError as ex:
            return error(str(ex))
        pausa_maxima  = intervalo * 2 if args.pausa_maxima is None else args.pausa_maxima

        df_consolidadas = nucleo.consolidar_lecturas(
            df_procesadas, fecha_inicial, fecha_final, intervalo)
        df_eventos = nucleo.calcular_eventos(
            df_consolidadas,
            args.duracion_minima, args.duracion_maxima,
            pausa_maxima, args.intensidad_minima,
            intervalo, args.pausa_igual == 'incluir',
        )
        guardar_csv(df_eventos, salida / 'eventos.csv')

        resumen['parametros_eventos'] = {
            'fecha_inicial': str(fecha_inicial), 'fecha_final': str(fecha_final),
            'pausa_maxima': pausa_maxima, 'incluir_pausa_igual': args.pausa_igual == 'incluir',
        }
        resumen['eventos'] = {'cantidad': int(df_eventos.shape[0])}
        print(f'Eventos: {df_eventos.shape[0]}')

        if not df_eventos.empty:
            df_acumulados = nucleo.obtener_acumulados(df_eventos)
            guardar_csv(df_acumulados, salida / 'acumulados.csv')
            curvas_huff = nucleo.calcular_curvas_huff(df_eventos, intervalo=args.intervalo_percentiles)
            guardar_csv(curvas_huff, salida / 'curvas_huff.csv')

            estadisticas = df_eventos.describe(include='number')
            resumen['eventos'].update({
                'por_cuartil_huff': {k: int(v) for k, v in df_eventos['Q_Huff'].value_counts().sort_index().items()},
                'estadisticas': {
                    col: {fila: a_json(estadisticas.at[fila, col]) for fila in estadisticas.index}
                    for col in estadisticas.columns
                },
                'curvas_huff': {
                    fila['Q']: [float(x) for x in fila[TEXTOS['colpercentiles']]]
                    for _, fila in curvas_huff.iterrows()
                },
            })

    if args.json:
        with open(salida / 'resumen.json', 'w', encoding='utf-8') as f:
            json.dump(resumen, f, ensure_ascii=False, indent=2, default=str)

    print(f'Resultados en: {salida}')
    return codigo

# =============================================================================================
# Sección principal
# =============================================================================================

if __name__ == '__main__':
    sys.exit(main())
