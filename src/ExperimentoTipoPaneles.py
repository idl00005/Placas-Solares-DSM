import datetime

import pandas as pd
import pvlib

from src.GeneradorExperimento import GeneradorExperimento

lat = 38.732602
lon = -9.116373
tz = 'Europe/Lisbon'
alt = 10
start = datetime.datetime(2023, 1, 1)
end = datetime.datetime(2023, 12, 31)
tilt = 25
azimuth = 200
pdc0 = 300
eta_inv_nom = 0.96
    
generador = GeneradorExperimento(lat, lon, tz, alt, 0, 0, start,
                                 end, '1h', pdc0, eta_inv_nom )

# Carga de la base de datos CEC
cec_modules = pvlib.pvsystem.retrieve_sam('CECMod')

# Definición de sistemas PV usando módulos válidos
sistemas = {
    "Monocristalino": cec_modules.get('Canadian_Solar_CS6X_300M', cec_modules.iloc[:, 0]),
    "Policristalino": cec_modules.get('Trina_Solar_TSM_250PA05', cec_modules.iloc[:, 1]),
    "Película delgada": cec_modules.get('First_Solar_FS_385', cec_modules.iloc[:, 2])
}


# Parámetros del inversor
default_inverter = {
    'pdc0': 300,  # Potencia de entrada nominal en W
    'eta_inv_nom': 0.96  # Eficiencia nominal
}
generador.weather['precipitable_water'] = 0.1
# Simulación usando ModelChain
for nombre, modulo in sistemas.items():
    generador.system = pvlib.pvsystem.PVSystem(
        module_parameters=modulo,
        inverter_parameters=default_inverter,
        temperature_model_parameters=pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
    )
    generador.mc = pvlib.modelchain.ModelChain(generador.system, generador.site, aoi_model='no_loss')
    generador.mc.run_model(generador.weather)
    resultados = generador.mc.results.ac.values
    print(f"Sistema PV '{nombre}': {resultados.sum()/1000:.2f} kWh")
