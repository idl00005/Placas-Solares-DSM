from pvlib.inverter import pvwatts
from pvlib.location import Location
import pandas as pd
import numpy as np
from pvlib import irradiance
from pvlib.temperature import sapm_cell
from pvlib.pvsystem import PVSystem

# Parámetros de ubicación
lat, lon, tz, alt = 40.0, -3.7, 'Europe/Madrid', 667  # Ejemplo: Madrid
loc = Location(lat, lon, tz, alt)

# Crear rango de tiempo para un año
times = pd.date_range(start='2023-01-01', end='2023-12-31', freq='1h',tz='Europe/Madrid')
# Posición solar
solar_position = loc.get_solarposition(times)

# Crear datos sintéticos para un año (8760 horas)
data = pd.DataFrame(index=times)
data['GHI'] = np.maximum(0, 100 * np.sin(np.linspace(0, 2 * np.pi, len(times))))  # Ejemplo simplificado
data['DNI'] = data['GHI'] * 0.7
data['DHI'] = data['GHI'] * 0.3
data['Temp'] = 20 + 10 * np.sin(np.linspace(0, 2 * np.pi, len(times)))  # Variación diaria de temperatura
data['WindSpeed'] = 2 + np.random.rand(len(times))  # Aleatorio entre 2-3 m/s
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
temp_air = data['Temp']  # Temperatura ambiente (°C)
wind_speed = data['WindSpeed']  # Velocidad del viento (m/s)
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