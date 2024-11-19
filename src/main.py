from pysolar.solar import get_altitude
import datetime

# Prueba de cálculo con coordenadas
lat = 40.4168  # Latitud de Madrid
lon = -3.7038  # Longitud de Madrid
date = datetime.datetime.utcnow()

altitud = get_altitude(lat, lon, date)
print(f"Altitud solar: {altitud:.2f}°")