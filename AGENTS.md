# AGENTS.md — HyetiaScan

Instrucciones para agentes autónomos (y personas) que clonan y ejecutan este repositorio.

## Qué es

HyetiaScan analiza series de tiempo de precipitación (lluvia). Lee un CSV de lecturas y controla las lecturas anormales (perdidas, duplicadas, corruptas y atípicas). Luego identifica eventos de lluvia y calcula duración, intensidad, cuartil de Huff, curvas Huff y acumulados por lapso.

- `hyetiascan_cli.py`: interfaz de línea de comandos. **Úsala para cualquier ejecución autónoma o no interactiva.**
- `HyetiaScan.py`: aplicación Streamlit. Úsala solo si una persona la va a manejar desde un navegador, porque el CSV se carga con un botón.
- `hyetiascan_core.py`: lógica de cálculo, importable sin Streamlit. La usan la CLI y la app.

Versión de Python soportada: **3.13** (ver `.python-version`). Las dependencias están fijadas en `requirements.txt`.

## Instalación

```bash
git clone https://github.com/jmdevilleros/HyetiaScan
cd HyetiaScan
python3 -m venv .venv
```

Activa el entorno:

- Linux / macOS: `source .venv/bin/activate`
- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- Windows (cmd): `.venv\Scripts\activate.bat`

Luego instala las dependencias:

```bash
pip install -r requirements.txt
```

En Windows usa `python` en lugar de `python3`. Con el entorno activo, `python` sirve en todos los sistemas.

## Prueba de humo

```bash
python tests/smoke_test.py
```

Resultado esperado (código de salida 0):

```
OK  CLI con controles: código 0, 30 eventos
OK  CLI sin controles: código 3 (quedan lecturas anormales), sin eventos
OK  Argumentos inválidos: código 2
OK  Formatos DD/MM/AAAA, AAAA/MM/DD, zona horaria y ";"+",": mismos eventos que ISO
OK  Último día: fecha final sin hora incluye el día completo
OK  App Streamlit sin archivo: sin excepciones
OK  App Streamlit con archivo: 30 eventos; con evento el último día, 31 (igual que la CLI)
Prueba de humo superada.
```

Prueba manual equivalente:

```bash
python hyetiascan_cli.py ejemplos/lluvia_ejemplo_5min.csv --salida resultados_hyetiascan \
    --duplicadas primera --corruptas borrar --atipicas borrar --perdidas cero --json
```

Debe terminar con código 0 e imprimir `Eventos: 30`.

## Formato del CSV de entrada

- Una fila de encabezados, al menos 2 filas y 2 columnas.
- **Separador de columnas**: se detecta en el encabezado. Se usa `,` salvo que predominen `;` o el tabulador. Para forzarlo: `--separador ";"` (o `","`, `tab`, `"|"`).
- **Columna de fecha-hora**. Formatos reconocidos, con hora opcional `HH:MM` o `HH:MM:SS`:
  - ISO `AAAA-MM-DD HH:MM:SS`, también con `T` (`AAAA-MM-DDTHH:MM:SS`);
  - `AAAA/MM/DD` y `AAAA.MM.DD`;
  - `DD/MM/AAAA`, `DD-MM-AAAA` y `DD.MM.AAAA`.

  Una columna solo se convierte si **todos** sus valores cumplen el mismo formato.
  - **Día o mes primero:** por defecto se asume **día primero** (`05/03/2024` = 5 de marzo). Para archivos `MM/DD/AAAA` usa `--mes-primero`. Si todas las fechas son ambiguas (día y mes ≤ 12), la CLI lo avisa en stderr y en `resumen.json` (`notas_fechahora`).
  - **Formato explícito**, para cualquier otro caso: `--formato-fecha "%d/%m/%Y %H:%M"` (strftime).
  - **Zona horaria** (`2024-03-01T00:05:00-05:00`, `...Z`): si todos los valores tienen el mismo desplazamiento, se conserva la hora local escrita y se quita la zona. Si hay desplazamientos distintos, se convierten a UTC. Con `--zona-horaria America/Bogota` se convierten a esa zona. El resultado siempre es una fecha-hora sin zona.
  - Si no se reconoce ninguna columna de fecha-hora, la CLI termina con código 1 e indica el primer valor con problemas.
- **Columna de precipitación** numérica, en **mm por lectura** (lo acumulado en cada intervalo). No debe ser una intensidad.
- Las lecturas deben ir en orden cronológico y a intervalo regular (por ejemplo cada 5 min). El intervalo se estima con la moda de las diferencias entre las primeras 1000 lecturas.
- **Separador decimal** `.` por defecto. Con `--decimal ,`, el archivo debe separar columnas con `;` (se detecta solo) o poner los valores entre comillas (`"1,5"`).
- Codificación `utf-8` por defecto; usa `--codificacion latin-1` (u otra) si hace falta.
- Puede haber más columnas. Por defecto se toman la primera columna de fecha-hora y la primera numérica. Si hay varias, indícalas: `--col-fechahora NOMBRE --col-precipitacion NOMBRE`.

La aplicación Streamlit usa el mismo cargador: también reconoce estos formatos de fecha, la zona horaria y el separador `;`, siempre con día primero y sin opciones adicionales en pantalla.

Ejemplo: `ejemplos/lluvia_ejemplo_5min.csv`, con columnas `fechahora,precipitacion_mm`.

## Comando recomendado

```bash
python hyetiascan_cli.py ENTRADA.csv --salida resultados_hyetiascan \
    --duplicadas primera --corruptas borrar --atipicas borrar --perdidas cero --json
```

- `--duplicadas primera`: entre lecturas con la misma fecha-hora conserva la primera. Las otras opciones son `ultima`, `sumar`, `promediar` y `borrar`.
- `--corruptas borrar`: elimina las lecturas negativas.
- `--atipicas borrar`: elimina las lecturas mayores que `--umbral-atipicas` (20 mm por defecto).
- `--perdidas cero`: rellena con 0 las lecturas faltantes. Se aplica después de los otros controles, así que también rellena lo que estos borran.

Sin estos controles, si el archivo tiene lecturas anormales **no se calculan eventos** (código 3).

Parámetros de eventos, con sus valores por defecto:

- `--duracion-minima 20` y `--duracion-maxima 9999`, en minutos.
- `--intensidad-minima 3`, en mm/h.
- `--pausa-maxima`: por defecto 2 × intervalo.
- `--pausa-igual incluir|separar`: decide si una pausa igual a la máxima se considera lluvia o interrupción.
- `--fecha-inicial` y `--fecha-final`, en cualquiera de los formatos de fecha anteriores, con hora opcional. Una `--fecha-final` **sin hora incluye el día completo** (hasta 23:59:59). Por defecto el rango va desde el primer día hasta el día completo de la última lectura. La aplicación Streamlit hace lo mismo: su "Fecha final" incluye el día completo.
- `--agrupacion dia|mes|ano` e `--intervalo-percentiles 5|10|20|25|50`.

Ayuda completa: `python hyetiascan_cli.py --help`.

## Códigos de salida

| Código | Significado |
|---|---|
| 0 | Correcto. Se calcularon eventos (puede haber 0 eventos). |
| 1 | Error de carga o de datos: archivo ilegible, falta una columna de fecha-hora o numérica, columna inexistente o de tipo incorrecto, o intervalo no estimable. El mensaje va a stderr con el prefijo `Error:`. Una excepción no controlada también termina con 1 (traceback de Python). |
| 2 | Argumentos inválidos (argparse). stderr empieza con `usage:`. |
| 3 | Quedan lecturas anormales sin controlar. Se escriben las lecturas, pero no los eventos; en stderr aparece `Aún quedan lecturas anormales por controlar`. |

## Archivos de salida (en `--salida`, por defecto `resultados_hyetiascan/`)

| Archivo | Contenido |
|---|---|
| `lecturas_procesadas.csv` | Lecturas después de normalizar y aplicar los controles. Tiene las dos columnas de entrada (fecha-hora y precipitación). |
| `lecturas_agrupadas.csv` | Resumen por día, mes o año: `P_acumulada`, `correctas`, `perdidas`, `duplicadas`, `corruptas`, `atípicas`. |
| `eventos.csv` | Un evento por fila: `inicia`, `termina`, `duracion` (min), `intensidad` (mm/h), `P_acumulada` (mm), `conteo` (lecturas), `lecturas` (lista JSON en mm), `porcentajes` (lista JSON del % acumulado), `Q_Huff` (`Q1`–`Q4`). |
| `acumulados.csv` | Por evento: `inicia` y la precipitación acumulada en `lapso 10 min` … `lapso 120 min` (vacío si el evento es más corto que el lapso). |
| `curvas_huff.csv` | `Q` y `percentiles`: lista JSON del % de precipitación acumulada en cada % de duración (0, intervalo, …, 100). |
| `resumen.json` | Solo con `--json`. Incluye parámetros, columnas usadas, `intervalo_minutos`, cantidad y porcentaje por categoría de lectura, y `eventos` (`cantidad`, `por_cuartil_huff`, `estadisticas`, `curvas_huff`). Si quedan anormales, `eventos` es `null`. |

`lecturas_procesadas.csv` y `lecturas_agrupadas.csv` se escriben siempre. `eventos.csv` solo se escribe si no quedan anormales, y `acumulados.csv` y `curvas_huff.csv` solo si además hay al menos un evento.

## Uso como módulo de Python

```python
import hyetiascan_core as nucleo

df = nucleo.cargar_csv('ejemplos/lluvia_ejemplo_5min.csv')
lecturas = nucleo.extraer_lecturas(df, 'fechahora', 'precipitacion_mm')
intervalo = nucleo.estimar_intervalo_lecturas(lecturas)          # 5
lecturas = nucleo.normalizar_lecturas(lecturas, intervalo)
lecturas = nucleo.procesar_lecturas(
    lecturas, intervalo, control_duplicadas=nucleo.DUPLICADAS_PRIMERA,
    corruptas_borrar=True, atipicas_borrar=True, perdidas_asumir_cero=True,
)
fechas = lecturas['fechahora']
consolidadas = nucleo.consolidar_lecturas(
    lecturas, fechas.min().normalize(), nucleo.fin_del_dia(fechas.max()), intervalo)
eventos = nucleo.calcular_eventos(
    consolidadas, duracion_minima=20, duracion_maxima=9999,
    pausa_maxima=2 * intervalo, intensidad_minima=3,
    intervalo=intervalo, incluir_pausa_igual=True,
)                                                                  # 30 filas
curvas = nucleo.calcular_curvas_huff(eventos, intervalo=10)
acumulados = nucleo.obtener_acumulados(eventos)
```

Ejecuta el código desde la raíz del repositorio, o agrega esa carpeta a `sys.path`: el módulo importa `mensajes_es.py`.

## Aplicación Streamlit (solo con una persona y un navegador)

```bash
streamlit run HyetiaScan.py
```

- Corre en modo headless (`.streamlit/config.toml`) y no abre navegador.
- URL: **http://localhost:8501/analysis**, porque `baseUrlPath = "/analysis"`. La raíz `/` no sirve la app.
- Chequeo de salud: `curl http://localhost:8501/analysis/_stcore/health`, que responde `ok`.
- Solo escucha en `localhost`. Para exponerla usa `--server.address 0.0.0.0` y, si hace falta, `--server.port`.
- Detén el proceso al terminar.
