import datetime
from GeneradorExperimento import GeneradorExperimento
from data_generator import calculate_irradiance_with_tilt_azimuth, calculate_cell_temperature, calculate_ac_power


def apply_dirt_penalty(poa_global, penalty_factor):
    return poa_global * (1 - penalty_factor)


def determine_season(date):
    """Función que determina la estación basada en la fecha"""
    if date >= datetime.datetime(date.year, 12, 21) or date < datetime.datetime(date.year, 3, 21):  # Invierno
        return 'Invierno'
    elif date >= datetime.datetime(date.year, 3, 21) and date <= datetime.datetime(date.year, 6, 20):  # Primavera
        return 'Primavera'
    elif date >= datetime.datetime(date.year, 6, 21) and date <= datetime.datetime(date.year, 9, 20):  # Verano
        return 'Verano'
    else:  # Otoño
        return 'Otoño'


def run_experiment(lat, lon, tz, alt, start, end, pdc0, gamma_pdc, eta_inv_nom, area):
    generador = GeneradorExperimento(lat, lon, tz, alt, 0, 0, start, end, '1h', pdc0 , eta_inv_nom)

    tilt = 25
    azimuth = 200

    total_energy_with_cleaning = 0
    total_energy_without_cleaning = 0

    seasonal_penalty_factors = {
        'Invierno': 0.001,  # Baja penalización en invierno
        'Primavera': 0.005,  # Mayor penalización en primavera
        'Verano': 0.01,      # Penalización más alta en verano
        'Otoño': 0.002      # Penalización moderada en otoño
    }

    # Iteramos a través de todo el periodo de tiempo, calculando energía cada hora
    for date in generador.times:
        # Determinamos la estación para la fecha actual
        season = determine_season(date)

        # Aplicamos la penalización de acuerdo con la estación
        penalty_factor = seasonal_penalty_factors[season]

        # Calcular la irradiancia con limpiadores automáticos
        poa_global_with_cleaning = calculate_irradiance_with_tilt_azimuth(generador.site, [date], generador.weather, tilt, azimuth)
        temp_cell_with_cleaning = calculate_cell_temperature(poa_global_with_cleaning, generador.weather['temp_air'], generador.weather['wind_speed'])
        ac_power_with_cleaning = calculate_ac_power(poa_global_with_cleaning, temp_cell_with_cleaning)

        # Sumamos la energía producida con limpiadores automáticos
        total_energy_with_cleaning += ac_power_with_cleaning.sum() / 1000  # kWh

        # Aplicamos la penalización a la irradiancia para el caso sin limpiadores
        poa_global_no_cleaned = apply_dirt_penalty(poa_global_with_cleaning, penalty_factor)

        temp_cell_no_cleaned = calculate_cell_temperature(poa_global_no_cleaned, generador.weather['temp_air'], generador.weather['wind_speed'])
        ac_power_no_cleaned = calculate_ac_power(poa_global_no_cleaned, temp_cell_no_cleaned)

        # Sumamos la energía producida sin limpiadores
        total_energy_without_cleaning += ac_power_no_cleaned.sum() / 1000  # kWh

    return total_energy_with_cleaning, total_energy_without_cleaning


if __name__ == "__main__":
    # Parámetros del experimento
    lat = 38.732602
    lon = -9.116373
    tz = 'Europe/Lisbon'
    alt = 10
    start = datetime.datetime(2023, 1, 1)
    end = datetime.datetime(2023, 12, 31)
    pdc0 = 300
    gamma_pdc = -0.004
    eta_inv_nom = 0.96
    area = 1.6

    # Ejecutamos el experimento para todo el año
    total_energy_with_cleaning, total_energy_without_cleaning = run_experiment(lat, lon, tz, alt, start, end, pdc0,
                                                                               gamma_pdc, eta_inv_nom, area)

    # Imprimimos los resultados
    print(f"Energía generada con limpiadores automáticos: {total_energy_with_cleaning:.2f} kWh")
    print(f"Energía generada sin limpiadores: {total_energy_without_cleaning:.2f} kWh")
    print(
        f"Diferencia de energía (con vs sin limpiadores): {total_energy_with_cleaning - total_energy_without_cleaning:.2f} kWh")
