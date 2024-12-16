import datetime

from GeneradorExperimento import GeneradorExperimento


def get_optimal_tilt_and_azimuth(lat, lon, tz, alt, start, end,pdc0, gamma_pdc, eta_inv_nom, area):
    """
    Calcula los ángulos de inclinación y azimut óptimos para maximizar la energía generada en función de los parámetros dados.

    @param lat: Latitud del lugar de instalación.
    @param lon: Longitud del lugar de instalación.
    @param tz: Zona horaria del lugar de instalación.
    @param alt: Altitud del lugar de instalación.
    @param start: Fecha de inicio del experimento.
    @param end: Fecha de fin del experimento.
    @param pdc0: Potencia máxima de la planta fotovoltaica (W).
    @param gamma_pdc: Coeficiente de temperatura de la potencia (1/°C).
    @param eta_inv_nom: Eficiencia nominal del inversor.
    @param area: Área del sistema fotovoltaico (m²).

    @return: Los ángulos de inclinación y azimut óptimos y la energía anual generada (kWh).
        """
    tilt_range = range(0, 91, 5)
    azimuth_range = range(0, 361, 10)

    best_tilt = 0
    best_azimuth = 0
    best_energy = 0.0

    generador = GeneradorExperimento(lat, lon, tz, alt, 0,
                                     0, start, end, '1h', pdc0, eta_inv_nom )

    for tilt in tilt_range:
        for azimuth in azimuth_range:

            generador.set_tilt(tilt)
            generador.set_azimuth(azimuth)
            ac_power = generador.calculate_ac_power()
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

    """
    Ejecuta el experimento para una estación específica y calcula los resultados correspondientes.

    @param season: Nombre de la estación (Invierno, Primavera, Verano, Otoño).
    @param season_start: Fecha de inicio de la estación.
    @param season_end: Fecha de fin de la estación.
    """
    for season, (season_start, season_end) in seasons.items():
        print(f"\nEjecutando experimento para {season} ({season_start.date()} - {season_end.date()})")
        best_tilt, best_azimuth, best_energy = get_optimal_tilt_and_azimuth(38.732602, -9.116373, 'Europe/Lisbon', 10, season_start, season_end, 300, -0.004, 0.96, 1.6)
        days_in_season = (season_end - season_start).days + 1
        print(f"days_in_season: {days_in_season}")
        average_daily_energy = best_energy / days_in_season

        # Calcular la energía generada por día
        generador = GeneradorExperimento(38.732602, -9.116373, 'Europe/Lisbon', 10, best_tilt, best_azimuth,
                                         season_start, season_end, '1h', 300, 0.96)
        desviacion_tipica_diaria = generador.calcular_desviacion_tipica()

        print(f"Tilt óptimo: {best_tilt}°")
        print(f"Azimuth óptimo: {best_azimuth}°")
        print(f"Energía generada: {best_energy:.2f} kWh")
        print(f"Energía media diaria: {average_daily_energy:.2f} kWh/día")
        print(f"Desviación típica diaria: {desviacion_tipica_diaria/1000:.2f} kWh/día")
        acumuladorenergia += best_energy

    print(f"\nEjecutando experimento para toda la temporada ({seasons['Invierno'][0]})-({seasons['Otoño'][1]})")
    best_tilt, best_azimuth, best_energy = get_optimal_tilt_and_azimuth(38.732602, -9.116373, 'Europe/Lisbon', 10, seasons['Invierno'][0], seasons['Otoño'][1], 300, -0.004, 0.96, 1.6)
    days_in_season = -(seasons['Invierno'][0] - seasons['Otoño'][1]).days + 1
    print(f"days_in_season: {days_in_season}")
    average_daily_energy = best_energy / days_in_season

    generador = GeneradorExperimento(38.732602, -9.116373, 'Europe/Lisbon', 10, best_tilt, best_azimuth,
                                     seasons['Invierno'][0], seasons['Otoño'][1], '1h', 300, 0.96)
    desviacion_tipica_diaria = generador.calcular_desviacion_tipica()

    print(f"Tilt óptimo: {best_tilt}°")
    print(f"Azimuth óptimo: {best_azimuth}°")
    print(f"Energía generada: {best_energy:.2f} kWh")
    print(f"Energía media diaria: {average_daily_energy:.2f} kWh/día")
    print(f"Desviación típica diaria: {desviacion_tipica_diaria/1000:.2f} kWh/día")
    print(f"Energía generada aplicando la optimización del ángulo y orientación por estación: {acumuladorenergia:.2f} kWh")
    print(f"Energía ganada con la optimización de ángulo y orientación en cada estación: {acumuladorenergia-best_energy:.2f} kWh ({((acumuladorenergia-best_energy)/best_energy)*100:.2f}%)")

