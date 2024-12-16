## @file simulacion_pv.py
# @brief Simulación de producción de energía para diferentes tipos de módulos fotovoltaicos en un rango de años.
#
# Este script utiliza la biblioteca `pvlib` para modelar la producción energética de sistemas fotovoltaicos
# con diferentes tecnologías de módulos solares (monocristalino, policristalino y película delgada).
# La simulación se realiza para un rango de tiempo específico, considerando las condiciones meteorológicas
# históricas de una ubicación geográfica determinada.
#
# ### Funcionalidades principales:
# - Dividir los datos meteorológicos por año para análisis detallado.
# - Configurar y simular diferentes sistemas fotovoltaicos con módulos específicos.
# - Usar el modelo `ModelChain` de `pvlib` para calcular la energía producida anualmente.
# - Generar gráficos comparativos de la producción energética anual por tipo de módulo.
# - Calcular estadísticas relevantes como producción total, promedio anual y desviación estándar.
#
# ### Aplicaciones:
# Este script es útil para evaluar y comparar la eficiencia de diferentes tecnologías de módulos
# solares en una ubicación específica y determinar la opción más adecuada según la producción
# energética esperada.



import datetime
import pandas as pd
import pvlib
import matplotlib.pyplot as plt
from src.GeneradorExperimento import GeneradorExperimento

# Configuración inicial de ubicación y sistema
lat = 38.732602
lon = -9.116373
tz = 'Europe/Lisbon'
alt = 10
start = datetime.datetime(2013, 1, 1)
end = datetime.datetime(2023, 12, 31)
tilt = 25
azimuth = 200
pdc0 = 300
eta_inv_nom = 0.96

# @brief Crear una instancia del generador de experimentos.
generador = GeneradorExperimento(lat, lon, tz, alt, 0, 0, start, end, '1h', pdc0, eta_inv_nom)

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
# Dividir el weather por años
weather_by_year = {year: generador.weather[generador.weather.index.year == year] for year in
                   range(start.year, end.year + 1)}

# Diccionario para almacenar los resultados
resultados_por_sistema = {nombre: [] for nombre in sistemas.keys()}

# Simulación usando ModelChain para cada año
for year, weather in weather_by_year.items():
    generador.weather = weather
    for nombre, modulo in sistemas.items():
        generador.system = pvlib.pvsystem.PVSystem(
            module_parameters=modulo,
            inverter_parameters=default_inverter,
            temperature_model_parameters=pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
        )
        generador.mc = pvlib.modelchain.ModelChain(generador.system, generador.site, aoi_model='no_loss')
        generador.mc.run_model(generador.weather)
        resultados = generador.mc.results.ac.values

        # Almacenar los resultados
        resultados_por_sistema[nombre].append((year, resultados.sum() / 1000))

# Generar el gráfico
plt.figure(figsize=(10, 6))
for nombre, resultados in resultados_por_sistema.items():
    anios, produccion = zip(*resultados)
    plt.plot(anios, produccion, label=nombre)

plt.xlabel('Año')
plt.ylabel('Producción de Energía (kWh)')
plt.title('Producción de Energía por Año para Diferentes Tipos de Placas')
plt.legend()
plt.grid(True)
plt.show()

# Calcular y mostrar estadísticas
for nombre, resultados in resultados_por_sistema.items():
    df_resultados = pd.DataFrame(resultados, columns=['Año', 'Producción'])
    produccion_total = df_resultados['Producción'].sum()
    produccion_media = df_resultados['Producción'].mean()
    desviacion_tipica = df_resultados['Producción'].std()

    print(f"Estadísticas para el sistema PV '{nombre}':")
    print(f"Producción Total: {produccion_total:.2f} kWh")
    print(f"Producción Media: {produccion_media:.2f} kWh")
    print(f"Desviación Típica: {desviacion_tipica:.2f} kWh\n")