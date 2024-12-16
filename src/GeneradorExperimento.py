import pandas as pd
import pvlib
import numpy as np
from pvlib.inverter import pvwatts

from pvlib.location import Location
from pvlib import pvsystem, modelchain, irradiance
from pvlib.solarposition import get_solarposition
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS, sapm_cell


## @brief Obtiene datos desde un archivo CSV y los procesa.
#
# @return Un DataFrame con los datos filtrados y renombrados.
def obterer_datos_excel():
    file_path = 'datos2.csv'

    raw_data = pd.read_csv(file_path, sep=',', skiprows=0, header=0, low_memory=False)

    # Renombramos las columnas con los nombres correctos basándonos en el formato proporcionado
    raw_data.columns = [
        "ObservationTime(LST)",
        "Global Horizontal Irradiance (GHI) W/m2",
        "Direct Normal Irradiance (DNI) W/m2",
        "AmbientTemperature (deg C)",
        "WindSpeed (m/s)",
        "Wind Direction (degrees)",
        "Wind-Speed 100m (m/s)",
        "Wind Direction 100m (degrees)",
        "WindGust (m/s)",
        "Relative Humidity (%)",
        "Liquid Precipitation (kg/m2)",
        "Solid Precipitation (kg/m2)",
        "Snow Depth (m)",
        "Clear Sky GHI",
        "Clear Sky DNI",
        "Clear Sky DHI",
        "IrradianceObservationType",
        "LeadTime",
        "DataVersion",
        "ObservationTime(GMT)",
        "Diffuse Horizontal Irradiance (DIF) W/m2",
        "AmbientTemperatureObservationType",
        "WindSpeedObservationType",
        "Albedo",
        "Particulate Matter 10 (mug/m3)",
        "Particulate Matter 2.5 (mug/m3)"
    ]
    try:
        raw_data['ObservationTime(LST)'] = pd.to_datetime(raw_data['ObservationTime(LST)'], format='%m/%d/%Y %H:%M',
                                                          dayfirst=True)
    except ValueError as e:
        print(f"Error al convertir fechas: {e}")
        raise

    # Establecer la columna de tiempo como índice
    # inplace=True modifica el DataFrame original estableciendo esta columna como índice
    raw_data.set_index('ObservationTime(LST)', inplace=True)

    # Seleccionar las columnas de interés
    # Estas son las columnas específicas que queremos extraer del conjunto de datos
    columns_of_interest = [
        'Global Horizontal Irradiance (GHI) W/m2',  # Irradiancia horizontal global
        'Direct Normal Irradiance (DNI) W/m2',  # Irradiancia directa normal
        'AmbientTemperature (deg C)',  # Temperatura ambiente en grados Celsius
        'WindSpeed (m/s)'  # Velocidad del viento en metros por segundo
    ]
    data_filtered = raw_data[columns_of_interest]

    # Renombrar las columnas para simplificar el acceso
    data_filtered = data_filtered.rename(columns={
        'Global Horizontal Irradiance (GHI) W/m2': 'ghi',
        'Direct Normal Irradiance (DNI) W/m2': 'dni',
        'AmbientTemperature (deg C)': 'temp',
        'WindSpeed (m/s)': 'wspd'
    })
    return data_filtered


## @brief Crea un modelo fotovoltaico con los parámetros especificados.
#
# @param tilt Inclinación de los paneles.
# @param azimuth Orientación de los paneles.
# @param pdc0 Potencia nominal de los módulos.
# @param eta_inv_nom Eficiencia nominal del inversor.
# @param modulo Tipo de módulo fotovoltaico.
# @return Un objeto PVSystem configurado.

def crear_modelo(tilt, azimuth, pdc0, eta_inv_nom, modulo):
    temp_model_params = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']

    cec_modules = pvlib.pvsystem.retrieve_sam('CECMod')

    if modulo == 'Monocristalino':
        module_params = cec_modules.get('Canadian_Solar_CS6X_300M', cec_modules.iloc[:, 0])
    elif modulo == 'Policristalino':
        module_params = cec_modules.get('Trina_Solar_TSM_250PA05', cec_modules.iloc[:, 1])
    elif modulo == 'Película delgada':
        module_params = cec_modules.get('First_Solar_FS_385', cec_modules.iloc[:, 2])
    else:
        module_params = {
            'Name': 'Generic Module',
            'pdc0': pdc0,
            'gamma_pdc': -0.004,
            'area': 1.6
        }

    system = pvsystem.PVSystem(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        module_parameters=module_params,
        inverter_parameters={'pdc0': pdc0, 'eta_inv_nom': eta_inv_nom},
        temperature_model_parameters=temp_model_params
    )
    return system

## @brief Crea una cadena de modelo (ModelChain) para simular un sistema fotovoltaico.
#
# @param system Objeto PVSystem que representa el sistema.
# @param site Ubicación del sistema fotovoltaico.
# @return Un objeto ModelChain configurado.
def crear_mc(system, site):
    return modelchain.ModelChain(system, site, aoi_model="physical", spectral_model="no_loss")


## @brief Calcula la irradiancia difusa horizontal (DHI) si falta en los datos.
#
# @param weather DataFrame con las condiciones climáticas.
# @param times Serie de tiempo de los datos.
# @param site Ubicación del sistema fotovoltaico.
# @return El DataFrame actualizado con la columna dhi calculada.

def obtener_dhi(weather, times, site):
    solar_position = get_solarposition(times, site.latitude, site.longitude)
    weather['solar_zenith'] = solar_position['zenith']

    # Calculamos dhi si faltan datos
    weather['dhi'] = weather['ghi'] - weather['dni'] * solar_position['zenith'].apply(
        lambda z: max(0, np.cos(np.radians(z))))

    # Asegurarse de que dhi no sea negativo
    weather['dhi'] = weather['dhi'].clip(lower=0)
    return weather

## @brief Clase que representa un generador de experimentos fotovoltaicos.
class GeneradorExperimento:
    ## @brief Constructor de la clase.
    #
    # @param lat Latitud de la ubicación.
    # @param lon Longitud de la ubicación.
    # @param tz Zona horaria de la ubicación.
    # @param alt Altitud de la ubicación.
    # @param tilt Inclinación inicial de los paneles.
    # @param azimuth Orientación inicial de los paneles.
    # @param start Fecha de inicio del experimento.
    # @param end Fecha de fin del experimento.
    # @param frecuencia Frecuencia de los datos temporales (ej. 'H' para horas).
    # @param pdc0 Potencia nominal de los módulos.
    # @param eta_inv_nom Eficiencia nominal del inversor.
    # @param modulo Tipo de módulo fotovoltaico (opcional).

    def __init__(self, lat, lon, tz, alt, tilt, azimuth,start,end, frecuencia, pdc0, eta_inv_nom, modulo = ''):
        self.pdc0 = pdc0
        self.eta_inv_nom = eta_inv_nom
        self.site = Location(lat, lon, tz, alt)
        self.tilt = tilt
        self.azimuth = azimuth
        self.times = pd.date_range(start=start, end=end, freq=frecuencia)
        self.data = obterer_datos_excel()
        self.weather = self.data.loc[(self.data.index >= start) & (self.data.index <= end), ['ghi', 'dni']].copy()
        self.weather = obtener_dhi(self.weather, self.data.index, self.site)
        self.weather['temp_air'] = self.data['temp']
        self.weather['wind_speed'] = self.data['wspd']
        self.system = crear_modelo(tilt, azimuth, pdc0, eta_inv_nom, modulo)
        self.mc = crear_mc(self.system, self.site)

    ## @brief Cambia la inclinación del sistema fotovoltaico.
    #
    # @param tilt Nueva inclinación.

    def set_tilt(self, tilt):
        self.tilt = tilt
        self.mc.system.surface_tilt = tilt

    ## @brief Cambia la orientación del sistema fotovoltaico.
    #
    # @param azimuth Nueva orientación.

    def set_azimuth(self, azimuth):
        self.azimuth = azimuth
        self.mc.system.surface_azimuth = azimuth

    ## @brief Calcula la irradiancia sobre el módulo considerando la inclinación y orientación.
    #
    # @return Un DataFrame con los valores de irradiancia total sobre el módulo.

    def calculate_irradiance_with_tilt_azimuth(self):
        # Obtener la posición solar en los tiempos proporcionados
        solar_position = self.site.get_solarposition(self.times)

        # Calcular la irradiancia sobre el módulo usando los parámetros de inclinación y orientación proporcionados
        irradiance_on_module = irradiance.get_total_irradiance(
            self.tilt, self.azimuth,
            solar_position['zenith'], solar_position['azimuth'],
            self.weather['dni'], self.weather['ghi'], self.weather['dhi']
        )
        return irradiance_on_module['poa_global']

    ## @brief Calcula la temperatura de las celdas fotovoltaicas.
    #
    # @return Un array con las temperaturas de las celdas.

    def calculate_cell_temperature(self):
        a = -3.47
        b = -0.0594
        deltaT = 3
        return sapm_cell(
            poa_global= self.calculate_irradiance_with_tilt_azimuth(),
            temp_air= self.weather['temp_air'],
            wind_speed= self.weather['wind_speed'],
            a=a,
            b=b,
            deltaT=deltaT
        )

    ## @brief Calcula la potencia en corriente alterna generada por el sistema.
    #
    # @return Un DataFrame con los valores de potencia AC generados.

    def calculate_ac_power(self):
        poa_global = self.calculate_irradiance_with_tilt_azimuth()
        temp_cell = self.calculate_cell_temperature()
        dc_power = self.system.pvwatts_dc(poa_global, temp_cell)
        return pvwatts(dc_power, 300)

    ## @brief Cambia el tipo de módulo fotovoltaico utilizado en el sistema.
    #
    # @param modulo Nuevo tipo de módulo fotovoltaico.
    # @return El sistema actualizado.

    def set_modulo(self, modulo):
        self.system = crear_modelo(self.tilt, self.azimuth, self.pdc0, self.eta_inv_nom, modulo)
        self.mc = crear_mc(self.system, self.site)
        return self.system

    ## @brief Calcula la desviación típica de la energía diaria generada.
    #
    # @return Un valor numérico con la desviación típica de la energía diaria.
    def calcular_desviacion_tipica(self):
        energia_diaria = self.calculate_ac_power().resample('D').sum()
        return energia_diaria.std()



        

