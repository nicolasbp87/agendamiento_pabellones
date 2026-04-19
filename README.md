# Visualización de ocupación de pabellón en Streamlit

Aplicación en Streamlit para visualizar la ocupación de pabellón mediante un mapa de calor construido a partir de intervalos de ingreso y salida de pacientes.

## Archivo principal

- `streamlit_pabellon_heatmap_prev_week.py`

## Dependencias

Este proyecto usa las siguientes librerías:

- streamlit
- pandas
- numpy
- matplotlib
- openpyxl
- xlrd

## Estructura recomendada del repositorio

```text
mi-app-streamlit/
├── streamlit_pabellon_heatmap_prev_week.py
├── requirements.txt
└── README.md
```

## Cómo ejecutar localmente

1. Instala las dependencias:

```bash
pip install -r requirements.txt
```

2. Ejecuta la app:

```bash
streamlit run streamlit_pabellon_heatmap_prev_week.py
```

## Formato esperado de los datos

La aplicación requiere, al menos, estas columnas:

- `DATETIME_ING_PACIENTE`
- `DATETIME_SALIDA_PACIENTE`

Columnas opcionales:

- `DATETIME_INICIO_CIR`
- `DATETIME_TERMINO_CIR`
- `PAB`

Puedes cargar archivos:

- `.csv`
- `.xlsx`
- `.xls`

## Publicación en Streamlit Community Cloud

1. Sube estos archivos a un repositorio de GitHub.
2. Entra a Streamlit Community Cloud.
3. Elige **Deploy an app**.
4. Selecciona tu repositorio, rama y archivo principal:

```text
streamlit_pabellon_heatmap_prev_week.py
```

5. Si corresponde, ajusta la versión de Python en **Advanced settings**.
6. Publica la app.

## Recomendación de datos

Si vas a compartir la app fuera del hospital, evita subir datos clínicos identificables. Para demos públicas, utiliza datos anonimizados o de prueba.
