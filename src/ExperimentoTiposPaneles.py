import pvlib
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de localización
location = pvlib.location.Location(latitude=40.0, longitude=-105.0, altitude=1600, tz='Etc/GMT+7')

# Fecha y rango de tiempo
times = pd.date_range(start='2023-06-21', end='2023-06-21 23:59:59', freq='1h', tz=location.tz)

# Datos meteorológicos simulados
solar_position = location.get_solarposition(times)
clear_sky = location.get_clearsky(times)

# Añadir columna precipitable_water requerida
clear_sky['precipitable_water'] = 1.5

# Carga de la base de datos CEC
cec_modules = pvlib.pvsystem.retrieve_sam('CECMod')

# Mostrar nombres de módulos disponibles
#print("Módulos disponibles en la base de datos CEC:")
#print(cec_modules.columns.tolist())

# Definición de sistemas PV usando módulos válidos
sistemas = {
    "Monocristalino": cec_modules.get('Canadian_Solar_CS6X_300M', cec_modules.iloc[:, 0]),
    "Policristalino": cec_modules.get('Trina_Solar_TSM_250PA05', cec_modules.iloc[:, 1]),
    "Película delgada": cec_modules.get('First_Solar_FS_385', cec_modules.iloc[:, 2])
}

# Configuración de sistema PV y clima
temp_air = 25  # °C
wind_speed = 2  # m/s
resultados = {}

# Parámetros del inversor
default_inverter = {
    'pdc0': 4000,  # Potencia de entrada nominal en W
    'eta_inv_nom': 0.96  # Eficiencia nominal
}

# Simulación usando ModelChain
for nombre, modulo in sistemas.items():
    sistema = pvlib.pvsystem.PVSystem(
        module_parameters=modulo,
        inverter_parameters=default_inverter,
        temperature_model_parameters=pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
    )
    model_chain = pvlib.modelchain.ModelChain(sistema, location, aoi_model='no_loss')
    model_chain.run_model(clear_sky)
    resultados = model_chain.results.ac.values
    print(f"Sistema PV '{nombre}': {resultados.sum()/1000:.2f} kWh")