*************************************************************************
# HyetiaScan 2.1.2

Análisis de lluvias

- Juan Manuel de Villeros Arias
- Mónica Liliana Gallego Jaramillo

Junio - Agosto 2024

Contacto: hyetiascan@teoktonos.com


*************************************************************************

### Instalación

Requiere **Python 3.13** (ver `.python-version`). Las dependencias están fijadas en `requirements.txt`.

```bash
git clone https://github.com/jmdevilleros/HyetiaScan
cd HyetiaScan
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python tests/smoke_test.py         # prueba de humo: 30 eventos en el ejemplo
```

- Aplicación web: `streamlit run HyetiaScan.py` y abrir http://localhost:8501/analysis
- Sin interfaz: `python hyetiascan_cli.py ENTRADA.csv --duplicadas primera --corruptas borrar --atipicas borrar --perdidas cero --json`

**Agentes autónomos:** leer [AGENTS.md](./AGENTS.md). Ahí están los comandos exactos, el formato del CSV de entrada (fecha-hora ISO `AAAA-MM-DD HH:MM:SS`, `DD/MM/AAAA HH:MM` o `AAAA/MM/DD`, con o sin zona horaria; precipitación en mm por lectura; separador `,` o `;`), los códigos de salida y las columnas de cada archivo de resultados.

*************************************************************************

### Cambios - Octubre 2026

- **Fecha final completa:** en la aplicación y en la CLI, la fecha final incluye todo ese día (hasta 23:59:59). Antes la aplicación cortaba a las 00:00, así que dejaba fuera los eventos del último día.
- **Más formatos de entrada** (aplicación y CLI): fechas `DD/MM/AAAA`, `AAAA/MM/DD` y con zona horaria, y columnas separadas por `;`, que permite decimales con coma.
- **CLI:** el código de salida 3 indica lecturas anormales sin controlar, y hay opciones nuevas `--separador`, `--formato-fecha`, `--mes-primero` y `--zona-horaria`.

*************************************************************************

### Cambios en versión 2.1.2 - Julio 2025

#### Nueva Opción para Controlar la Inclusión de Pausas Iguales a la Pausa Máxima

Se ha añadido una nueva funcionalidad en la interfaz de la pestaña "Eventos" que permite al usuario decidir si las pausas con una duración exactamente igual a la pausa máxima (definida en minutos) se consideran parte de una lluvia continua o como interrupciones que separan eventos de precipitación. 

El usuario puede elegir entre: 
- Incluir (tratar como lluvia): Las pausas de duración igual a la pausa máxima se consideran parte del mismo evento de lluvia (usa <= pausa_maxima).  
- Separar (tratar como interrupción): Las pausas de duración igual a la pausa máxima se tratan como interrupciones que dividen eventos (usa < pausa_maxima).

Este cambio mejora la flexibilidad del análisis de eventos de precipitación, especialmente para casos donde el criterio especificado de pausa máxima es igual al intervalo de medición, permitiendo un control más preciso sobre la definición de eventos continuos. 

*************************************************************************

### Uso sin interfaz (CLI y módulo)

La lógica de cálculo está en `hyetiascan_core.py`, un módulo sin dependencia de Streamlit. La aplicación (`HyetiaScan.py`) lo usa para todos sus cálculos, de modo que la interfaz, la línea de comandos y cualquier programa Python obtienen los mismos resultados.

#### Aplicación Streamlit (sin cambios)

```bash
pip install -r requirements.txt
streamlit run HyetiaScan.py        # http://localhost:8501/analysis
```

#### Línea de comandos

```bash
python hyetiascan_cli.py ejemplos/lluvia_ejemplo_5min.csv --salida resultados \
    --duplicadas primera --corruptas borrar --atipicas borrar --perdidas cero --json
```

Genera en `resultados/`: `lecturas_procesadas.csv`, `lecturas_agrupadas.csv`, `eventos.csv`, `acumulados.csv`, `curvas_huff.csv` y, con `--json`, `resumen.json`. Las columnas con listas (`lecturas`, `porcentajes`, `percentiles`) se guardan como JSON.

Opciones principales (ver `python hyetiascan_cli.py --help`):

- Carga: `--decimal {.,,}`, `--codificacion`, `--col-fechahora`, `--col-precipitacion`.
- Control de anormales: `--duplicadas {no-modificar,primera,ultima,sumar,promediar,borrar}`, `--corruptas borrar`, `--atipicas borrar`, `--umbral-atipicas` (20), `--perdidas cero`.
- Eventos: `--fecha-inicial`, `--fecha-final`, `--duracion-minima` (20), `--duracion-maxima` (9999), `--intensidad-minima` (3), `--pausa-maxima` (2 × intervalo), `--pausa-igual {incluir,separar}`, `--intervalo-percentiles` (10).

Igual que en la aplicación, si quedan lecturas anormales sin controlar no se calculan eventos; el programa guarda las lecturas y termina con código 3. Códigos de salida: 0 correcto, 1 error de carga o de datos, 2 argumentos inválidos, 3 quedan lecturas anormales.

La CLI también acepta `--separador` (`;` para archivos con `--decimal ,`), `--formato-fecha`, `--mes-primero` y `--zona-horaria`. Una `--fecha-final` sin hora incluye el día completo, igual que la "Fecha final" de la aplicación Streamlit.

#### Como módulo de Python

```python
import hyetiascan_core as nucleo

df = nucleo.cargar_csv('ejemplos/lluvia_ejemplo_5min.csv')
lecturas = nucleo.extraer_lecturas(df, 'fechahora', 'precipitacion_mm')
intervalo = nucleo.estimar_intervalo_lecturas(lecturas)
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
)
curvas = nucleo.calcular_curvas_huff(eventos, intervalo=10)
acumulados = nucleo.obtener_acumulados(eventos)
```

`ejemplos/lluvia_ejemplo_5min.csv` es un archivo sintético (45 días, lecturas cada 5 minutos) con varios eventos, un vacío de 30 minutos, una lectura duplicada, una corrupta y una atípica, útil para probar los controles.

---

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](./LICENSE).
