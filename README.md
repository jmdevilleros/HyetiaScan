*************************************************************************
# HyetiaScan
Análisis de lluvias, detección de aguaceros y gráficos de curvas de Huff
Juan Manuel de Villeros Arias
Mónica Liliana Gallego Jaramillo
Octubre-Noviembre de 2023
*************************************************************************

Cargue información desde un archivo .csv con datos de precipitaciones. 
Debe contener mediciones consecutivas en serie de tiempo ordenada, con 
al menos una columna de fecha/hora (datetime) y al menos una columna 
numérica de precipitación.

Permite especificar criterios para establecer si una lluvia se convierte en aguacero según:
- Duración total
- Continuidad (pausas breves entre eventos de precipitación)
- Intensidad

Gráficas disponibles:

- Curva de aguaceros (% duración vs % precipitación)
- Curvas de frecuencia
- Curvas de Huff
