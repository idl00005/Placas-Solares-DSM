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

# Mostrar todas las temperaturas
print(data[['temp']])

# Guardar los resultados en un archivo CSV
data[['temp']].to_csv('temperaturas_hora.csv')

print("Datos guardados en 'temperaturas_hora.csv'")
