import datetime
import matplotlib.pyplot as plt
from GeneradorExperimento import GeneradorExperimento
from OtrosCalculos import calculate_irradiance_with_tilt_azimuth, calculate_cell_temperature, calculate_ac_power
import random

def apply_dirt_penalty(poa_global, cumulative_penalty):
    """
    @brief Aplica una penalización a la irradiancia debido a la suciedad acumulada en el panel.

    @param poa_global Irradiancia global en el plano del panel.
    @param cumulative_penalty Penalización acumulada debido a la suciedad.

    @return Irradiancia ajustada con la penalización por suciedad.
    """
    return poa_global * (1 - cumulative_penalty)

def determine_season(date):
    """
    @brief Determina la estación del año según la fecha proporcionada.

    @param date Fecha para determinar la estación.

    @return Nombre de la estación ('Invierno', 'Primavera', 'Verano', 'Otoño').
    """
    if date >= datetime.datetime(date.year, 12, 21) or date < datetime.datetime(date.year, 3, 21):
        return 'Invierno'
    elif date >= datetime.datetime(date.year, 3, 21) and date <= datetime.datetime(date.year, 6, 20):
        return 'Primavera'
    elif date >= datetime.datetime(date.year, 6, 21) and date <= datetime.datetime(date.year, 9, 20):
        return 'Verano'
    else:
        return 'Otoño'

def simulate_rain(cumulative_penalty, season):
    """
    @brief Simula la reducción de la penalización acumulada debido a eventos de lluvia, dependiendo de la estación del año.

    @param cumulative_penalty Penalización acumulada.
    @param season Estación del año en la que ocurre la lluvia.

    @return Penalización acumulada ajustada después de la lluvia.
    """
    rain_reduction_factors = {
        'Invierno': 0.5,
        'Primavera': 0.3,
        'Verano': 0.1,
        'Otoño': 0.4
    }
    reduction = rain_reduction_factors[season] * cumulative_penalty
    return max(cumulative_penalty - reduction, 0)

def run_experiment(lat, lon, tz, alt, start, end, pdc0, gamma_pdc, eta_inv_nom, area):
    """
    @brief Simula un experimento de producción energética, considerando la limpieza automática de los paneles y la penalización por suciedad.

    @param lat Latitud de la ubicación geográfica.
    @param lon Longitud de la ubicación geográfica.
    @param tz Zona horaria de la ubicación.
    @param alt Altitud de la ubicación.
    @param start Fecha de inicio del experimento.
    @param end Fecha de fin del experimento.
    @param pdc0 Potencia nominal del panel (W).
    @param gamma_pdc Coeficiente de temperatura del panel.
    @param eta_inv_nom Eficiencia nominal del inversor.
    @param area Área del panel (m^2).

    @return Tres listas: fechas, energía acumulada con limpiadores automáticos, y energía acumulada sin limpiadores.
    """
    generador = GeneradorExperimento(lat, lon, tz, alt, 0, 0, start, end, '1h', pdc0 , eta_inv_nom)

    tilt = 25
    azimuth = 200

    total_energy_with_cleaning = 0
    total_energy_without_cleaning = 0

    energy_with_cleaning = []
    energy_without_cleaning = []
    times = []

    seasonal_penalty_factors = {
        'Invierno': 0.001,
        'Primavera': 0.005,
        'Verano': 0.01,
        'Otoño': 0.002
    }

    seasonal_rain_probabilities = {
        'Invierno': 0.3,
        'Primavera': 0.2,
        'Verano': 0.1,
        'Otoño': 0.2
    }

    # Inicializamos el penalizador acumulativo
    cumulative_penalty = 0
    current_day = None

    # Iteramos a través de todo el periodo de tiempo, calculando energía cada hora
    for date in generador.times:
        # Verificamos si cambió el día
        if current_day != date.date():
            current_day = date.date()

            # Determinamos la estación para la fecha actual
            season = determine_season(date)

            # Incrementamos la penalización acumulativa según la estación
            cumulative_penalty += seasonal_penalty_factors[season]

            # Simulamos eventos de lluvia según la probabilidad de la estación
            if random.random() < seasonal_rain_probabilities[season]:
                cumulative_penalty = simulate_rain(cumulative_penalty, season)

        # Calcular la irradiancia con limpiadores automáticos
        poa_global_with_cleaning = calculate_irradiance_with_tilt_azimuth(generador.site, [date], generador.weather, tilt, azimuth)
        temp_cell_with_cleaning = calculate_cell_temperature(poa_global_with_cleaning, generador.weather['temp_air'], generador.weather['wind_speed'])
        ac_power_with_cleaning = calculate_ac_power(poa_global_with_cleaning, temp_cell_with_cleaning)

        # Sumamos la energía producida con limpiadores automáticos
        total_energy_with_cleaning += ac_power_with_cleaning.sum() / 1000  # kWh
        energy_with_cleaning.append(total_energy_with_cleaning)

        # Aplicamos la penalización acumulativa a la irradiancia para el caso sin limpiadores
        poa_global_no_cleaned = apply_dirt_penalty(poa_global_with_cleaning, cumulative_penalty)

        temp_cell_no_cleaned = calculate_cell_temperature(poa_global_no_cleaned, generador.weather['temp_air'], generador.weather['wind_speed'])
        ac_power_no_cleaned = calculate_ac_power(poa_global_no_cleaned, temp_cell_no_cleaned)

        # Sumamos la energía producida sin limpiadores
        total_energy_without_cleaning += ac_power_no_cleaned.sum() / 1000  # kWh
        energy_without_cleaning.append(total_energy_without_cleaning)

        times.append(date)

    return times, energy_with_cleaning, energy_without_cleaning

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
times, energy_with_cleaning, energy_without_cleaning = run_experiment(lat, lon, tz, alt, start, end, pdc0, gamma_pdc, eta_inv_nom, area)

# Generamos el gráfico
plt.figure(figsize=(10, 6))
plt.plot(times, energy_with_cleaning, label='Con limpiadores')
plt.plot(times, energy_without_cleaning, label='Sin limpiadores')
plt.xlabel('Fecha')
plt.ylabel('Energía acumulada (kWh)')
plt.title('Producción de energía a lo largo del tiempo')
plt.legend()
plt.grid(True)
plt.show()
