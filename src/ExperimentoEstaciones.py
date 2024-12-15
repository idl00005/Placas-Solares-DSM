import datetime

from GeneradorExperimento import GeneradorExperimento
from data_generator import calculate_irradiance_with_tilt_azimuth, calculate_cell_temperature, calculate_ac_power


def get_optimal_tilt_and_azimuth(lat, lon, tz, alt, start, end,pdc0, gamma_pdc, eta_inv_nom, area):
    tilt_range = range(0, 91, 5)
    azimuth_range = range(0, 361, 10)

    best_tilt = 0
    best_azimuth = 0
    best_energy = 0.0

    generador = GeneradorExperimento(lat, lon, tz, alt, 0,
                                     0, start, end, '1h', pdc0, gamma_pdc, eta_inv_nom, area)

    for tilt in tilt_range:
        for azimuth in azimuth_range:

            generador.set_tilt(tilt)
            generador.set_azimuth(azimuth)
            poa_global = calculate_irradiance_with_tilt_azimuth(generador.site, generador.times, generador.weather, tilt, azimuth)
            temp_cell = calculate_cell_temperature(poa_global, generador.weather['temp_air'], generador.weather['wind_speed'])
            ac_power = calculate_ac_power(poa_global, temp_cell)
            annual_energy = ac_power.sum() / 1000

            if annual_energy > best_energy:
                best_energy = annual_energy
                best_tilt = tilt
                best_azimuth = azimuth

    return best_tilt, best_azimuth, best_energy

if __name__ == "__main__":
    acumuladorenergia = 0
    seasons = {
        'Invierno': (datetime.datetime(2022, 12, 21), datetime.datetime(2023, 3, 20)),
        'Primavera': (datetime.datetime(2023, 3, 21), datetime.datetime(2023, 6, 20)),
        'Verano': (datetime.datetime(2023, 6, 21), datetime.datetime(2023, 9, 20)),
        'Otoño': (datetime.datetime(2023, 9, 21), datetime.datetime(2023, 12, 20))
    }


    for season, (season_start, season_end) in seasons.items():
        print(f"\nEjecutando experimento para {season} ({season_start.date()} - {season_end.date()})")
        best_tilt, best_azimuth, best_energy = get_optimal_tilt_and_azimuth(38.732602, -9.116373, 'Europe/Lisbon', 10, season_start, season_end, 300, -0.004, 0.96, 1.6)
        print(f"Tilt óptimo: {best_tilt}°")
        print(f"Azimuth óptimo: {best_azimuth}°")
        print(f"Energía generada: {best_energy:.2f} kWh")
        acumuladorenergia += best_energy

    print(f"\nEjecutando experimento para toda la temporada ({seasons['Invierno'][0]})-({seasons['Verano'][1]})")
    best_tilt, best_azimuth, best_energy = get_optimal_tilt_and_azimuth(38.732602, -9.116373, 'Europe/Lisbon', 10, seasons['Invierno'][0], seasons['Verano'][1], 300, -0.004, 0.96, 1.6)
    print(f"Tilt óptimo: {best_tilt}°")
    print(f"Azimuth óptimo: {best_azimuth}°")
    print(f"Energía generada: {best_energy:.2f} kWh")
    print(f"Energía generada aplicando la optimización del ángulo y orientación por estación: {acumuladorenergia:.2f} kWh")
    print(f"Energía ganada con la optimización de ángulo y orientación: {acumuladorenergia-best_energy:.2f} kWh ")


