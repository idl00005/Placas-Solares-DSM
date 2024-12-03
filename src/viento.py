import pandas as pd
import datetime
from meteostat import Point, Hourly

# Cambiar configuración para mostrar todas las filas
pd.set_option('display.max_rows', None)

# Coordenadas de la ubicación (Jaén, España)
lat = 37.7796
lon = -3.7849

# Rango de fechas para obtener datos
start = datetime.datetime(2023, 1, 1)
end = datetime.datetime(2023, 12, 31)

# Crear el objeto Point para la ubicación
location = Point(lat, lon)

# Descargar datos horarios
data = Hourly(location, start, end)
data = data.fetch()

# Mostrar todas las velocidades del viento
print(data[['wspd']])  # 'wspd' es la velocidad del viento en m/s

# Guardar los resultados de la velocidad del viento en un archivo CSV
data[['wspd']].to_csv('viento_hora.csv')

print("Datos del viento por hora guardados en 'viento_hora.csv'")
