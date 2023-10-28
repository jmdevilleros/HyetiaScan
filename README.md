*************************************************************************
# HyetiaScan 1.0
Análisis de lluvias, detección de aguaceros y gráficos de curvas de Huff.

- Juan Manuel de Villeros Arias
- Mónica Liliana Gallego Jaramillo

Octubre-Noviembre de 2023
*************************************************************************

Examine y analice eventos de precipitación pluviométrica. Detecte aguaceros de acuerdo con parámetros configurables. Genere gráficos de curvas de precipitación, frecuencia, Huff.

El archivo debe contener mediciones consecutivas en serie de tiempo ordenada, con al menos una columna de fecha/hora (datetime) y al menos una columna numérica de precipitación.

Permite especificar criterios para establecer si una lluvia se convierte en aguacero según:
- Duración total.
- Continuidad (pausas breves entre eventos de precipitación).
- Intensidad.

Gráficas disponibles:

- Curva de aguaceros (% duración vs % precipitación).
- Curvas de frecuencia.
- Curvas de Huff.
