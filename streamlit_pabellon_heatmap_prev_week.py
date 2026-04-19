import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from zoneinfo import ZoneInfo

st.set_page_config(page_title='Ocupación de pabellón', layout='wide')
st.title('Visualización de ocupación de pabellón')

st.markdown(
    'Carga un archivo **CSV** o **Excel** con las columnas de fecha/hora para reproducir el mismo mapa de calor.'
)

uploaded_file = st.file_uploader('Sube tu archivo de datos', type=['csv', 'xlsx', 'xls'])

required_cols = ['DATETIME_ING_PACIENTE', 'DATETIME_SALIDA_PACIENTE']
optional_datetime_cols = [
    'DATETIME_ING_PACIENTE',
    'DATETIME_SALIDA_PACIENTE',
    'DATETIME_INICIO_CIR',
    'DATETIME_TERMINO_CIR'
]


def load_data(file):
    if file.name.lower().endswith('.csv'):
        return pd.read_csv(file)
    return pd.read_excel(file)


if uploaded_file is None:
    st.info('Sube un archivo para comenzar.')
    st.stop()

try:
    df = load_data(uploaded_file).copy()
except Exception as e:
    st.error(f'No se pudo leer el archivo: {e}')
    st.stop()

missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f'Faltan columnas requeridas: {", ".join(missing)}')
    st.stop()

for col in optional_datetime_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

df = df.dropna(subset=['DATETIME_ING_PACIENTE', 'DATETIME_SALIDA_PACIENTE']).copy()
if df.empty:
    st.warning('No hay datos válidos después de convertir las fechas.')
    st.stop()

pab_col = 'PAB'
if pab_col not in df.columns:
    df[pab_col] = 'Sin especificar'

df[pab_col] = df[pab_col].astype(str).str.strip()

day_mapping = {
    0: 'Lunes',
    1: 'Martes',
    2: 'Miércoles',
    3: 'Jueves',
    4: 'Viernes',
    5: 'Sábado',
    6: 'Domingo'
}

df['FECHA'] = df['DATETIME_ING_PACIENTE'].dt.normalize()
df['AÑO'] = df['DATETIME_ING_PACIENTE'].dt.year
df['DIA_SEMANA_NUM'] = df['DATETIME_ING_PACIENTE'].dt.dayofweek
df['DIA_SEMANA'] = df['DIA_SEMANA_NUM'].map(day_mapping)

iso_cal = df['DATETIME_ING_PACIENTE'].dt.isocalendar()
df['ISO_YEAR'] = iso_cal.year.astype(int)
df['SEMANA_ISO'] = iso_cal.week.astype(int)

st.sidebar.header('Filtros')

pab_options = sorted(df[pab_col].dropna().unique().tolist())
anio_options = sorted(df['ISO_YEAR'].dropna().unique().tolist())
semana_options = sorted(df['SEMANA_ISO'].dropna().unique().tolist())
dia_options = ['Todos'] + [
    'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'
]

# Inicializar por defecto en la semana ISO anterior a la actual
hoy = pd.Timestamp.now(tz=ZoneInfo('America/Santiago'))
fecha_semana_anterior = (hoy - pd.Timedelta(days=7)).date()
iso_prev = fecha_semana_anterior.isocalendar()
default_iso_year = int(iso_prev.year)
default_semana = int(iso_prev.week)

default_anios = [default_iso_year] if default_iso_year in anio_options else anio_options
default_semanas = [default_semana] if default_semana in semana_options else semana_options

selected_pabellones = st.sidebar.multiselect(
    'Pabellón',
    options=pab_options,
    default=pab_options
)
selected_anios = st.sidebar.multiselect(
    'Año ISO',
    options=anio_options,
    default=default_anios
)
selected_semanas = st.sidebar.multiselect(
    'Semana ISO',
    options=semana_options,
    default=default_semanas
)
selected_dia = st.sidebar.selectbox('Día de la semana', options=dia_options, index=0)

hora_inicio = st.sidebar.text_input('Hora inicio', value='07:30')
hora_fin = st.sidebar.text_input('Hora fin', value='18:00')
frecuencia = st.sidebar.selectbox('Resolución', options=['10min', '15min', '30min'], index=0)

filtered = df.copy()
if selected_pabellones:
    filtered = filtered[filtered[pab_col].isin(selected_pabellones)]
if selected_anios:
    filtered = filtered[filtered['ISO_YEAR'].isin(selected_anios)]
if selected_semanas:
    filtered = filtered[filtered['SEMANA_ISO'].isin(selected_semanas)]
if selected_dia != 'Todos':
    filtered = filtered[filtered['DIA_SEMANA'] == selected_dia]

if filtered.empty:
    st.warning('No hay datos para la combinación actual de filtros.')
    st.stop()


def single_or_multiple(series):
    vals = sorted(series.dropna().astype(str).unique().tolist())
    if len(vals) == 0:
        return 'Todos'
    if len(vals) == 1:
        return vals[0]
    return 'Múltiples'

selected_pabellon_label = single_or_multiple(filtered[pab_col])
selected_anio_label = single_or_multiple(filtered['ISO_YEAR'])
selected_semana_label = single_or_multiple(filtered['SEMANA_ISO'])
selected_fecha_label = single_or_multiple(filtered['FECHA'].dt.strftime('%Y-%m-%d'))
selected_dia_label = single_or_multiple(filtered['DIA_SEMANA'])

try:
    slots = pd.date_range(
        f'2000-01-01 {hora_inicio}',
        f'2000-01-01 {hora_fin}',
        freq=frecuencia
    )
    slots = slots[:-1]
except Exception as e:
    st.error(f'Error en el rango horario: {e}')
    st.stop()

if len(slots) == 0:
    st.error('El rango horario no genera bloques válidos.')
    st.stop()

slot_labels = slots.strftime('%H:%M')
fechas = sorted(pd.to_datetime(filtered['FECHA'].dropna().unique()))

if len(fechas) == 0:
    st.warning('No hay fechas disponibles tras aplicar filtros.')
    st.stop()

matriz = pd.DataFrame(0, index=fechas, columns=slot_labels)
slot_minutes = pd.to_timedelta(frecuencia).total_seconds() / 60

for _, row in filtered.iterrows():
    inicio = row['DATETIME_ING_PACIENTE']
    fin = row['DATETIME_SALIDA_PACIENTE']

    if pd.isna(inicio) or pd.isna(fin) or fin <= inicio:
        continue

    fecha_base = pd.Timestamp(row['FECHA'])

    for slot in slots:
        bloque_inicio = fecha_base + pd.Timedelta(hours=slot.hour, minutes=slot.minute)
        bloque_fin = bloque_inicio + pd.Timedelta(minutes=slot_minutes)

        if (bloque_inicio < fin) and (bloque_fin > inicio):
            matriz.loc[fecha_base, slot.strftime('%H:%M')] += 1

matriz.index = [pd.to_datetime(f).strftime('%Y-%m-%d') for f in matriz.index]

fig_h = 14
fig_w = 18
fig, ax = plt.subplots(figsize=(fig_w, fig_h))

im = ax.imshow(
    matriz.values,
    aspect='auto',
    interpolation='none',
    cmap='viridis'
)

step = max(1, int(30 / slot_minutes))
xticks_idx = np.arange(0, len(matriz.columns), step)
ax.set_xticks(xticks_idx)
ax.set_xticklabels(
    [matriz.columns[i] for i in xticks_idx],
    rotation=45,
    ha='right',
    size=15
)

ax.set_yticks(np.arange(len(matriz.index)))
ax.set_yticklabels(matriz.index)

ax.set_xlabel('\nHora del día', size=18)
ax.set_ylabel('Fecha', size=18)

title_main = f'Ocupación de pabellón - {selected_pabellon_label}'
title_sub = (
    f'Año ISO: {selected_anio_label} | Semana: {selected_semana_label} '
    f'| Fecha: {selected_fecha_label} | Día: {selected_dia_label}'
)
ax.set_title(f'{title_main}\n{title_sub}\n', size=25)

ax.set_xticks(np.arange(-0.5, len(matriz.columns), 1), minor=True)
ax.set_yticks(np.arange(-0.5, len(matriz.index), 1), minor=True)
ax.grid(which='minor', color='white', linestyle='-', linewidth=0.3)
ax.tick_params(which='minor', bottom=False, left=False)

plt.tight_layout()
st.pyplot(fig, use_container_width=True)

st.subheader('Matriz de ocupación')
st.dataframe(matriz, use_container_width=True)
