# OtrosCalculos.py
import numpy as np
from pvlib.inverter import pvwatts
from pvlib import irradiance
from pvlib.temperature import sapm_cell
from pvlib.pvsystem import PVSystem


def calculate_irradiance(loc, times, data):
    """
    @brief Calcula la irradiancia total sobre el módulo solar, dada una ubicación y datos meteorológicos.

    @param loc Objeto Location de pvlib, que contiene la ubicación geográfica.
    @param times Índice de tiempo con las fechas/hora para las que calcular la irradiancia.
    @param data DataFrame con los datos meteorológicos necesarios (DNI, GHI, DHI).

    @return irradiance_on_module['poa_global'] La irradiancia global sobre el plano del módulo (W/m²).
    """
    solar_position = loc.get_solarposition(times)
    surface_azimuth = 180
    surface_tilt = 30
    irradiance_on_module = irradiance.get_total_irradiance(
        surface_tilt, surface_azimuth,
        solar_position['zenith'], solar_position['azimuth'],
        data['DNI'], data['GHI'], data['DHI']
    )
    return irradiance_on_module['poa_global']


def calculate_irradiance_with_tilt_azimuth(loc, times, data, tilt, azimuth):
    """
    @brief Calcula la irradiancia sobre el módulo solar tomando en cuenta la inclinación y la orientación especificadas.

    @param loc Objeto Location de pvlib, que contiene la ubicación geográfica.
    @param times Índice de tiempo con las fechas/hora para las que calcular la irradiancia.
    @param data DataFrame con los datos meteorológicos necesarios (DNI, GHI, DHI).
    @param tilt Inclinación del panel solar en grados.
    @param azimuth Orientación del panel solar en grados.

    @return irradiance_on_module['poa_global'] La irradiancia global sobre el plano inclinado (W/m²).
    """
    # Obtener la posición solar en los tiempos proporcionados
    solar_position = loc.get_solarposition(times)

    # Calcular la irradiancia sobre el módulo usando los parámetros de inclinación y orientación proporcionados
    irradiance_on_module = irradiance.get_total_irradiance(
        tilt, azimuth,
        solar_position['zenith'], solar_position['azimuth'],
        data['dni'], data['ghi'], data['dhi']
    )

    return irradiance_on_module['poa_global']

def calculate_cell_temperature(poa_global, temp_air, wind_speed):
    """
    @brief Calcula la temperatura de la célula del panel solar usando el modelo SAPM.

    @param poa_global Irradiancia global sobre el panel solar (W/m²).
    @param temp_air Temperatura ambiente (°C).
    @param wind_speed Velocidad del viento (m/s).

    @return temperatura de la célula del panel solar (°C).
    """
    a = -3.47
    b = -0.0594
    deltaT = 3
    return sapm_cell(
        poa_global=poa_global,
        temp_air=temp_air,
        wind_speed=wind_speed,
        a=a,
        b=b,
        deltaT=deltaT
    )

def calculate_ac_power(poa_global, temp_cell):
    """
    @brief Calcula la potencia de corriente alterna (AC) generada por el sistema fotovoltaico.

    @param poa_global Irradiancia global sobre el panel solar (W/m²).
    @param temp_cell Temperatura de la célula del panel solar (°C).

    @return potencia en corriente alterna (W).
    """
    module_params = {'pdc0': 300, 'gamma_pdc': -0.003}
    inverter_params = {'pdc0': 300}
    system = PVSystem(
        surface_tilt=30,
        surface_azimuth=180,
        module_parameters=module_params,
        inverter_parameters=inverter_params
    )
    dc_power = system.pvwatts_dc(poa_global, temp_cell)
    return pvwatts(dc_power, 300)


def simulate_cleaning_effect(times, data):
    """
    @brief Simula el efecto de los limpiadores sobre la irradiancia de los paneles solares, considerando factores como viento, temperatura y tiempo.

    @param times Índice de tiempo con las fechas/hora para simular el efecto de limpieza.
    @param data DataFrame con los datos meteorológicos necesarios (temperatura, viento).

    @return cleaning_factor Factor de limpieza ajustado que modifica la irradiancia (valor entre 0 y 1).
    """
    # Eliminar la parte de precipitación
    # Solo utilizamos el viento, la temperatura y el tiempo para el efecto de los limpiadores

    wind_factor = np.clip(data['wspd'] / 10, 0, 1)  # Aumento del 0 al 100% según la velocidad del viento
    temp_factor = np.clip(1 - (data['temp'] - 20) / 40, 0, 1)  # Disminuye eficiencia con altas temperaturas
    time_factor = np.clip(np.sin(np.linspace(0, 2 * np.pi, len(times))), 0, 1)  # Ciclo de suciedad

    # Combinamos los factores para obtener el factor total de limpieza
    cleaning_factor = 1 - (0.3 * (wind_factor + temp_factor + time_factor) / 3)

    # Aseguramos que el factor esté en el rango [0, 1]
    cleaning_factor = np.clip(cleaning_factor, 0, 1)

    return cleaning_factor

