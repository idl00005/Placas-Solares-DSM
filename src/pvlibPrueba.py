import locale

from meteostat import Point, Hourly
from pvlib.inverter import pvwatts
from pvlib.location import Location
import pandas as pd

from pvlib import irradiance
from pvlib.temperature import sapm_cell
from pvlib.pvsystem import PVSystem
import datetime

# Configurar localización en español
locale.setlocale(locale.LC_TIME, 'es_ES.utf8')

# Parámetros de ubicación en Jaén
lat, lon, tz, alt = 37.787694, -3.776444, 'Europe/Madrid', 667
loc = Location(lat, lon, tz, alt)

# Crear rango de tiempo para un año
times = pd.date_range(start='2023-01-01', end='2023-12-31', freq='1h')

# Posición solar
solar_position = loc.get_solarposition(times)

# Cargar el archivo Excel
archivo_excel = '../datos.xlsx'
df = pd.read_excel(archivo_excel)
# Extraer la hora
df['Hora'] = df['Tiempo'].str.extract(r'a las (\d{1,2}:\d{2})', expand=False)
# Extraer día y mes por separado
df[['Dia', 'Mes']] = df['Tiempo'].str.extract(r'(\d+) \((.*?)\)', expand=True)

# Combinar el día y el mes en una sola columna "Fecha"
df['Fecha'] = df['Dia'] + ' ' + df['Mes']

# Limpiar la columna "Fecha" eliminando la palabra "de"
df['Fecha'] = df['Fecha'].str.replace('de ', '', regex=False).str.strip()

# Concatenar fecha y hora
df['Fecha Completa'] = df['Fecha'] + ' ' + df['Hora']
df['Fecha Completa'] = df['Fecha Completa'].str.replace(r'^\d+\s', '', regex=True)

# Convertir a formato datetime
df['Tiempo'] = pd.to_datetime(df['Fecha Completa'], format='%d %B %H:%M', errors='coerce', dayfirst=True).apply(lambda x: x.replace(year=2023) if pd.notnull(x) else x)

# Eliminar filas con errores en la conversión
df = df.dropna(subset=['Tiempo'])

# Renombrar columnas del Excel para que coincidan con el DataFrame destino
df.rename(columns={
    'Radiación Global (kJ/m2)': 'GHI',  # GHI = Global Horizontal Irradiance
    'Radiación Difusa (kJ/m2)': 'DHI',  # DHI = Diffuse Horizontal Irradiance
    'Radiación Directa (kJ/m2)': 'DNI'  # DNI = Direct Normal Irradiance
}, inplace=True)

# Ajustar el índice al tiempo del Excel
df.set_index('Tiempo', inplace=True)

# Crear DataFrame completo para todo el año con valores en 0
data = pd.DataFrame(0.0, index=times, columns=['GHI', 'DHI', 'DNI','temp', 'wspd'])

# Actualizar el DataFrame completo con los valores del Excel
data.update(df)

# Imprimir el DataFrame completo (asegurando que no se trunque)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)

location = Point(37.787694, -3.776444)  # Madrid, España
start = datetime.datetime(2023, 1, 1)
end = datetime.datetime(2023, 12, 31)


# Descargar datos diarios
meteostatInfo = Hourly(location, start, end)
meteostatInfo = meteostatInfo.fetch()

# Imprimir el DataFrame completo
data['temp'] = meteostatInfo['temp']
data['wspd'] = meteostatInfo['wspd']
print(data)


# Esta variable representa la orientación del módulo
surface_azimuth = 180
# Esta variable representa la inclinación del módulo
surface_tilt = 30
irradiance_on_module = irradiance.get_total_irradiance(
    surface_tilt, surface_azimuth,
    solar_position['zenith'], solar_position['azimuth'],
    data['DNI'], data['GHI'], data['DHI']
)
poa_global = irradiance_on_module['poa_global']  # Irradiancia total

# Variables ambientales
temp_air = data['temp']  # Temperatura ambiente (°C)
wind_speed = data['wspd']  # Velocidad del viento (m/s)

# Parámetros del modelo SAPM
a = -3.47
b = -0.0594
deltaT = 3
# Calcular temperatura de las celdas
temp_cell = sapm_cell(
    poa_global=poa_global,
    temp_air=temp_air,
    wind_speed=wind_speed,
    a=a,
    b=b,
    deltaT=deltaT
)

# Parámetros del módulo e inversor (ejemplo)
module_params = {'pdc0': 300, 'gamma_pdc': -0.003}  # Potencia nominal (W), coeficiente temperatura
inverter_params = {'pdc0': 300}  # Potencia máxima del inversor

# Crear sistema fotovoltaico
system = PVSystem(
    surface_tilt=surface_tilt,
    surface_azimuth=surface_azimuth,
    module_parameters=module_params,
    inverter_parameters=inverter_params
)

# Calcular potencia DC
dc_power = system.pvwatts_dc(poa_global, temp_cell)

pdc0 = 300
ac_power = pvwatts(dc_power, pdc0)

annual_energy = ac_power.sum() / 1000
print(f"Energía anual generada: {annual_energy:.2f} kWh")