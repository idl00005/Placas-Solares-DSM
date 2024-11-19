from pysolar.solar import get_altitude
from meteostat import Point, Daily
import datetime

# Prueba de cálculo con coordenadas
lat = 40.4168  # Latitud de Madrid
lon = -3.7038  # Longitud de Madrid
date = datetime.datetime.now(datetime.timezone.utc)

altitud = get_altitude(lat, lon, date)
print(f"Altitud solar: {altitud:.2f}°")

# Coordenadas y rango de fechas
location = Point(40.4168, -3.7038)  # Madrid, España
start = datetime.datetime(2023, 1, 1)
end = datetime.datetime(2023, 1, 31)

# Descargar datos diarios
data = Daily(location, start, end)
data = data.fetch()

# Mostrar los datos
print(data)