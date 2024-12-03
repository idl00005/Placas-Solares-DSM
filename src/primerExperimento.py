import pvlib
import pandas as pd
import numpy as np
from datetime import datetime

# Coordenadas de la ubicación (ejemplo: Jaén, España)
latitude = 37.7796
longitude = -3.7849

# Fechas de las estaciones (en UTC)
seasons = {
    'invierno': ('2024-12-21', '2024-03-21'),
    'primavera': ('2024-03-21', '2024-06-21'),
    'verano': ('2024-06-21', '2024-09-21'),
    'otoño': ('2024-09-21', '2024-12-21'),
}

# Rango de ángulos de inclinación a probar (en grados)
angles = np.arange(0, 60, 5)

# Cargar los datos completos sin usar 'usecols'
data_df = pd.read_csv("datosCompletos.csv", names=['time', 'GHI', 'DHI', 'DNI', 'temp', 'wspd'], header=0, parse_dates=['time'])

# Convertir la columna 'time' a datetime y ajustarla a UTC
data_df['time'] = pd.to_datetime(data_df['time'], utc=True)
data_df.set_index('time', inplace=True)

# Función para simular la producción energética en un rango de fechas y un ángulo dado
def simulate_energy_production(season_start, season_end, angle):
    # Crear el rango de tiempo para la simulación
    times = pd.date_range(start=season_start, end=season_end, freq='1h', tz='UTC')

    # Obtener la posición solar
    solar_position = pvlib.solarposition.get_solarposition(times, latitude, longitude)
    solar_zenith = solar_position['apparent_zenith']
    solar_azimuth = solar_position['azimuth']

    # Interpolar los datos de irradiación para que coincidan con los tiempos de la simulación
    ghi = data_df.reindex(times, method='nearest')['GHI'].values
    dhi = data_df.reindex(times, method='nearest')['DHI'].values
    dni = data_df.reindex(times, method='nearest')['DNI'].values

    # Calcular la irradiancia total sobre el plano de la placa (POA)
    poa_global = pvlib.irradiance.get_total_irradiance(
        surface_tilt=angle,
        surface_azimuth=180,  # Orientación sur
        dni=dni,
        ghi=ghi,
        dhi=dhi,
        solar_zenith=solar_zenith,
        solar_azimuth=solar_azimuth,
        model='isotropic'  # Modelo para la radiación difusa
    )['poa_global']

    # Interpolar los datos de temperatura y viento para que coincidan con los tiempos de la simulación
    temperature_air = data_df.reindex(times, method='nearest')['temp'].values
    wind_speed = data_df.reindex(times, method='nearest')['wspd'].values

    # Calcular la temperatura de la celda utilizando la fórmula de SAPM
    temperature_cell = pvlib.temperature.sapm_cell(
        poa_global=poa_global,
        temp_air=temperature_air,
        wind_speed=wind_speed,
        a=-3.47,  # Coeficiente empírico típico
        b=-0.0594,  # Coeficiente empírico típico
        deltaT=3  # Incremento de temperatura
    )

    # Energía producida (aproximación) en kWh por metro cuadrado
    energy_produced = poa_global.sum() * 1e-3  # kWh/m²

    return energy_produced

# Iterar sobre cada estación y ángulo para calcular la producción energética
results = {}

for season, (start_date, end_date) in seasons.items():
    results[season] = {}
    for angle in angles:
        energy = simulate_energy_production(start_date, end_date, angle)
        results[season][angle] = energy

# Mostrar los resultados
for season, energies in results.items():
    optimal_angle = max(energies, key=energies.get)
    print(
        f"Estación: {season.capitalize()} - Ángulo óptimo: {optimal_angle}° - Energía producida: {energies[optimal_angle]:.2f} kWh/m²"
    )
