# *********************************************************************************************
# HyetiaScan - Prueba de humo
#
# Uso (desde la raíz del repositorio, con el entorno virtual activo):
#   python tests/smoke_test.py
#
# 1. CLI con el archivo de ejemplo y control de anormales: código 0 y 30 eventos.
# 2. CLI sin control de anormales: código 3 y sin eventos.
# 3. Archivos equivalentes en otros formatos (DD/MM/AAAA, con zona horaria, ';' con decimal ',')
#    producen exactamente los mismos eventos que el ejemplo ISO.
# 4. Un evento el último día se incluye (fecha final sin hora = día completo), en la CLI
#    y en la aplicación Streamlit (AppTest con el archivo cargado).
# 5. Argumentos inválidos: código 2.
# 6. Aplicación Streamlit (AppTest) sin archivo cargado: se ejecuta sin excepciones.
# *********************************************************************************************

import json
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EJEMPLO = RAIZ / 'ejemplos' / 'lluvia_ejemplo_5min.csv'
EVENTOS_ESPERADOS = 30
CONTROLES = ['--duplicadas', 'primera', '--corruptas', 'borrar',
             '--atipicas', 'borrar', '--perdidas', 'cero']

# ---------------------------------------------------------------------------------------------
def correr_cli(salida: Path, *opciones: str, archivo: Path = EJEMPLO) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RAIZ / 'hyetiascan_cli.py'), str(archivo), '--salida', str(salida), *opciones],
        capture_output=True, text=True, cwd=RAIZ,
    )

# ---------------------------------------------------------------------------------------------
def eventos_cli(tmp: Path, nombre: str, archivo: Path, *opciones: str) -> str:
    salida = tmp / nombre
    r = correr_cli(salida, *CONTROLES, *opciones, archivo=archivo)
    assert r.returncode == 0, f'{nombre}: código {r.returncode}\n{r.stdout}\n{r.stderr}'
    return (salida / 'eventos.csv').read_text(encoding='utf-8')

# ---------------------------------------------------------------------------------------------
def probar_cli_con_controles():
    with tempfile.TemporaryDirectory() as tmp:
        salida = Path(tmp)
        r = correr_cli(salida, *CONTROLES, '--json')
        assert r.returncode == 0, f'Código {r.returncode}\n{r.stdout}\n{r.stderr}'
        for archivo in ['lecturas_procesadas.csv', 'lecturas_agrupadas.csv', 'eventos.csv',
                        'acumulados.csv', 'curvas_huff.csv', 'resumen.json']:
            assert (salida / archivo).is_file(), f'Falta {archivo}'
        resumen = json.loads((salida / 'resumen.json').read_text(encoding='utf-8'))
        cantidad = resumen['eventos']['cantidad']
        filas = len((salida / 'eventos.csv').read_text(encoding='utf-8').strip().splitlines()) - 1
        assert cantidad == filas == EVENTOS_ESPERADOS, \
            f'Se esperaban {EVENTOS_ESPERADOS} eventos; resumen={cantidad}, eventos.csv={filas}'
        assert f'Eventos: {EVENTOS_ESPERADOS}' in r.stdout
    print(f'OK  CLI con controles: código 0, {EVENTOS_ESPERADOS} eventos')

# ---------------------------------------------------------------------------------------------
def probar_cli_sin_controles():
    with tempfile.TemporaryDirectory() as tmp:
        salida = Path(tmp)
        r = correr_cli(salida)
        assert r.returncode == 3, f'Código {r.returncode}, se esperaba 3\n{r.stderr}'
        assert not (salida / 'eventos.csv').exists()
        assert (salida / 'lecturas_procesadas.csv').is_file()
    print('OK  CLI sin controles: código 3 (quedan lecturas anormales), sin eventos')

# ---------------------------------------------------------------------------------------------
def probar_argumentos_invalidos():
    with tempfile.TemporaryDirectory() as tmp:
        r = correr_cli(Path(tmp), '--opcion-inexistente')
        assert r.returncode == 2 and r.stderr.startswith('usage:'), (r.returncode, r.stderr)
    print('OK  Argumentos inválidos: código 2')

# ---------------------------------------------------------------------------------------------
def leer_ejemplo() -> list[tuple[str, str]]:
    lineas = EJEMPLO.read_text(encoding='utf-8').strip().splitlines()[1:]
    return [tuple(l.split(',')) for l in lineas]

# ---------------------------------------------------------------------------------------------
def escribir(ruta: Path, encabezado: str, filas: list[str]):
    ruta.write_text('\n'.join([encabezado, *filas]) + '\n', encoding='utf-8')

# ---------------------------------------------------------------------------------------------
def probar_formatos_equivalentes():
    filas = leer_ejemplo()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        base = eventos_cli(tmp, 'iso', EJEMPLO)

        # DD/MM/AAAA HH:MM (sin segundos)
        dmy = tmp / 'dmy.csv'
        escribir(dmy, 'fechahora,precipitacion_mm', [
            f'{f[8:10]}/{f[5:7]}/{f[0:4]} {f[11:16]},{p}' for f, p in filas])
        assert eventos_cli(tmp, 'dmy', dmy) == base, 'DD/MM/AAAA: eventos distintos'
        # Mismo archivo con formato explícito
        assert eventos_cli(tmp, 'dmy_fmt', dmy, '--formato-fecha', '%d/%m/%Y %H:%M') == base

        # AAAA/MM/DD HH:MM:SS
        ymd = tmp / 'ymd.csv'
        escribir(ymd, 'fechahora,precipitacion_mm', [f'{f.replace("-", "/")},{p}' for f, p in filas])
        assert eventos_cli(tmp, 'ymd', ymd) == base, 'AAAA/MM/DD: eventos distintos'

        # ISO con zona horaria -05:00: se conserva la hora local
        tz = tmp / 'tz.csv'
        escribir(tz, 'fechahora,precipitacion_mm', [f'{f.replace(" ", "T")}-05:00,{p}' for f, p in filas])
        assert eventos_cli(tmp, 'tz', tz) == base, 'Zona horaria: eventos distintos'

        # Separador ';' y decimal ',' sin comillas (separador detectado y explícito)
        pc = tmp / 'pc.csv'
        escribir(pc, 'fechahora;precipitacion_mm', [f'{f};{p.replace(".", ",")}' for f, p in filas])
        assert eventos_cli(tmp, 'pc', pc, '--decimal', ',') == base, '";" y ",": eventos distintos'
        assert eventos_cli(tmp, 'pc2', pc, '--decimal', ',', '--separador', ';') == base
    print('OK  Formatos DD/MM/AAAA, AAAA/MM/DD, zona horaria y ";"+",": mismos eventos que ISO')

# ---------------------------------------------------------------------------------------------
def escribir_ultimo_dia(archivo: Path):
    # Ejemplo con un evento adicional el último día (14/04/2024 15:00-15:40)
    lluvia = {f'2024-04-14 15:{m:02d}:00': v for m, v in zip(range(0, 45, 5), [1, 2, 3, 4, 3, 2, 1, 1, 1])}
    escribir(archivo, 'fechahora,precipitacion_mm',
             [f'{f},{lluvia.get(f, p)}' for f, p in leer_ejemplo()])

# ---------------------------------------------------------------------------------------------
def probar_ultimo_dia():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        archivo = tmp / 'ultimo_dia.csv'
        escribir_ultimo_dia(archivo)
        for opciones in [(), ('--fecha-final', '2024-04-14'), ('--fecha-final', '14/04/2024')]:
            eventos = eventos_cli(tmp, 'u', archivo, *opciones)
            assert len(eventos.strip().splitlines()) - 1 == EVENTOS_ESPERADOS + 1, opciones
            assert '2024-04-14 15:00:00' in eventos, opciones
        # Con hora explícita se respeta la hora
        eventos = eventos_cli(tmp, 'u2', archivo, '--fecha-final', '2024-04-14 12:00')
        assert len(eventos.strip().splitlines()) - 1 == EVENTOS_ESPERADOS
    print('OK  Último día: fecha final sin hora incluye el día completo')

# ---------------------------------------------------------------------------------------------
def probar_app_sin_archivo():
    from streamlit.testing.v1 import AppTest
    from mensajes_es import TEXTOS
    at = AppTest.from_file(str(RAIZ / 'HyetiaScan.py'), default_timeout=60)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert TEXTOS['elegirarchivo'] in [i.value for i in at.info]
    print('OK  App Streamlit sin archivo: sin excepciones')

# ---------------------------------------------------------------------------------------------
def eventos_en_app(archivo: Path) -> int:
    # Ejecuta la app completa con AppTest, simulando la carga del archivo en file_uploader
    # y eligiendo los mismos controles de anormales que CONTROLES; retorna el número de eventos.
    from streamlit.testing.v1 import AppTest
    from streamlit.delta_generator import DeltaGenerator
    from streamlit.runtime.uploaded_file_manager import UploadedFile, UploadedFileRec
    from types import SimpleNamespace
    from mensajes_es import TEXTOS

    original = DeltaGenerator.file_uploader
    def file_uploader_simulado(self, *args, **kwargs):
        original(self, *args, **kwargs)
        registro = UploadedFileRec('prueba', archivo.name, 'text/csv', archivo.read_bytes())
        return UploadedFile(registro, SimpleNamespace(upload_url='', delete_url='', file_id='prueba'))
    DeltaGenerator.file_uploader = file_uploader_simulado
    try:
        at = AppTest.from_file(str(RAIZ / 'HyetiaScan.py'), default_timeout=120)
        at.run()
        radios = {r.label: r for r in at.radio}
        radios[TEXTOS['lecturasduplicadas']].set_value(TEXTOS['opcdejarprimera'])
        radios[TEXTOS['lecturascorruptas']].set_value(TEXTOS['opcborrar'])
        radios[TEXTOS['lecturasatipicas']].set_value(TEXTOS['opcborrar'])
        radios[TEXTOS['lecturasperdidas']].set_value(TEXTOS['opcasumircero'])
        at.run()
        assert not at.exception, [e.value for e in at.exception]
        # Primera tabla de estadísticas de eventos (describe): fila 'count'
        for df in (d.value for d in at.dataframe):
            if 'count' in df.index and TEXTOS['colduracion'] in df.columns:
                return int(df.loc['count', TEXTOS['colduracion']])
        raise AssertionError('La app no mostró estadísticas de eventos')
    finally:
        DeltaGenerator.file_uploader = original

# ---------------------------------------------------------------------------------------------
def probar_app_con_archivo():
    n = eventos_en_app(EJEMPLO)
    assert n == EVENTOS_ESPERADOS, f'App: {n} eventos, se esperaban {EVENTOS_ESPERADOS}'
    with tempfile.TemporaryDirectory() as tmp:
        archivo = Path(tmp) / 'ultimo_dia.csv'
        escribir_ultimo_dia(archivo)
        n = eventos_en_app(archivo)
        assert n == EVENTOS_ESPERADOS + 1, \
            f'App con evento el último día: {n} eventos, se esperaban {EVENTOS_ESPERADOS + 1}'
    print(f'OK  App Streamlit con archivo: {EVENTOS_ESPERADOS} eventos; con evento el último día, '
          f'{EVENTOS_ESPERADOS + 1} (igual que la CLI)')

# =============================================================================================
# Sección principal
# =============================================================================================

if __name__ == '__main__':
    sys.path.insert(0, str(RAIZ))
    probar_cli_con_controles()
    probar_cli_sin_controles()
    probar_argumentos_invalidos()
    probar_formatos_equivalentes()
    probar_ultimo_dia()
    probar_app_sin_archivo()
    probar_app_con_archivo()
    print('Prueba de humo superada.')
