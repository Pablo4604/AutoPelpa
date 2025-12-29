# AutoPelpa -- Tablero de Vuelos Aerolíneas Argentinas (COR)

AutoPelpa es una aplicación web desarrollada en **Python + Flask** que
obtiene, procesa y muestra los vuelos de **Aerolíneas Argentinas (AR)**
que arriban y parten del **Aeropuerto Internacional Ingeniero Ambrosio
Taravella (COR)**.

La aplicación está diseñada para funcionar como un **tablero operativo**
simple, con renderizado **100% backend** y un **template HTML
estrictamente estático**, cumpliendo con las políticas de despliegue de
**Render**.

------------------------------------------------------------------------

## ✈️ Funcionalidad principal

-   Obtiene vuelos de llegada y salida desde FlightRadar24\
-   Filtra exclusivamente vuelos de Aerolíneas Argentinas (AR)\
-   Considera siempre un rango móvil de 24 horas\
-   Combina llegadas y salidas por matrícula de aeronave\
-   Maneja excepciones de vuelos que no deben combinarse\
-   Ordena los resultados en orden cronológico real, incluso al cruzar
    la medianoche\
-   Renderiza los datos en una tabla HTML estática

------------------------------------------------------------------------

## 🧠 Decisiones técnicas clave

### Orden cronológico correcto

El orden de los vuelos **no se basa en strings de hora (HH:MM)**, ya que
esto genera errores cuando hay vuelos nocturnos y vuelos del día
siguiente.

En su lugar: - Se conservan timestamps reales - El orden se resuelve en
backend - El template solo renderiza datos ya ordenados

Esto garantiza una visualización cronológicamente correcta sin lógica en
la vista.

------------------------------------------------------------------------

### Template estrictamente estático

Por políticas de Render y por decisión arquitectónica:

-   No se utiliza JavaScript dinámico
-   No hay fetch, AJAX, SSE ni WebSockets
-   No hay manipulación del DOM
-   No hay auto-refresh parcial

El HTML se renderiza completamente en el servidor.

------------------------------------------------------------------------

## 🏗️ Arquitectura general

FlightRadar24 API\
→ Backend Flask\
→ Procesamiento y orden cronológico\
→ Renderizado HTML (Jinja2)\
→ Cliente (tabla estática)

------------------------------------------------------------------------

## 📂 Estructura del proyecto

    .
    ├── app.py
    ├── templates/
    │   └── index.html
    ├── static/
    │   └── favicon.png
    ├── requirements.txt
    └── README.md

------------------------------------------------------------------------

## ⚙️ Requisitos

-   Python 3.9+
-   Cuenta en Render
-   Conexión a internet

------------------------------------------------------------------------

## 📦 Dependencias principales

-   Flask
-   Requests
-   Pandas

Instalación local:

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## 🚀 Ejecución local

``` bash
python app.py
```

Luego acceder a:

http://localhost:5000

------------------------------------------------------------------------

## ☁️ Despliegue en Render

La aplicación está pensada para ser desplegada como **Web Service** en
Render.

Cada request ejecuta el pipeline completo: - Obtención de vuelos -
Procesamiento - Orden cronológico - Renderizado

------------------------------------------------------------------------

## 📊 Columnas de la tabla

  Columna   Descripción
  --------- -------------------------------
  LLEGADA   Número de vuelo de llegada
  SALIDA    Número de vuelo de salida
  ETA       Hora estimada de arribo (ART)
  ETD       Hora estimada de salida (ART)
  ORIGEN    Aeropuerto de origen
  DESTINO   Aeropuerto de destino
  MAT       Matrícula de la aeronave

------------------------------------------------------------------------

## 📌 Limitaciones conocidas

-   No hay cacheo
-   No hay auto-refresh automático
-   Dependencia de FlightRadar24

------------------------------------------------------------------------

## 👤 Autor

Desarrollado por **PABLO PERALTA**

------------------------------------------------------------------------

## ⚠️ Disclaimer

Este proyecto no está afiliado oficialmente con Aerolíneas Argentinas ni
con FlightRadar24. Los datos se utilizan únicamente con fines
informativos.
