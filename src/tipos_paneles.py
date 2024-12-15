import datetime
from GeneradorExperimento import GeneradorExperimento
from data_generator import calculate_irradiance_with_tilt_azimuth, calculate_cell_temperature, calculate_ac_power

def simulate_panel_performance(panel_type, lat, lon, tz, alt, start, end, tilt, azimuth):

    # Características específicas de cada tipo de panel
    panel_specs = {
        'monocristalino': {'efficiency': 0.20, 'gamma_pdc': -0.003, 'area': 1.6},
        'policristalino': {'efficiency': 0.17, 'gamma_pdc': -0.004, 'area': 1.6},
        'película delgada': {'efficiency': 0.12, 'gamma_pdc': -0.0025, 'area': 1.6},
    }

    if panel_type not in panel_specs:
        raise ValueError(f"Tipo de panel no válido: {panel_type}")

    specs = panel_specs[panel_type]
    pdc0 = specs['efficiency'] * specs['area'] * 1000  # Potencia nominal en W
    gamma_pdc = specs['gamma_pdc']
    area = specs['area']
    eta_inv_nom = 0.96

    # Crear el generador de experimentos
    generador = GeneradorExperimento(lat, lon, tz, alt, 0, 0, start, end, '1h', pdc0, eta_inv_nom)

    total_energy = 0

    for date in generador.times:
        # Calcular la irradiancia
        poa_global = calculate_irradiance_with_tilt_azimuth(generador.site, [date], generador.weather, tilt, azimuth)
        # Ajustar la irradiancia según la eficiencia del panel
        poa_global_adjusted = poa_global * specs['efficiency']
        # Calcular la temperatura de la célula
        temp_cell = calculate_cell_temperature(poa_global_adjusted, generador.weather['temp_air'], generador.weather['wind_speed'])
        # Calcular la potencia AC
        ac_power = calculate_ac_power(poa_global_adjusted, temp_cell)
        # Acumular energía total
        total_energy += ac_power.sum() / 1000  # Convertir a kWh

    return total_energy


def run_panel_comparison_experiment(lat, lon, tz, alt, start, end, tilt, azimuth):

    panel_types = ['monocristalino', 'policristalino', 'película delgada']
    results = {}

    for panel_type in panel_types:
        energy = simulate_panel_performance(panel_type, lat, lon, tz, alt, start, end, tilt, azimuth)
        results[panel_type] = energy

    return results


if __name__ == "__main__":
    # Configuración del experimento
    lat = 38.732602
    lon = -9.116373
    tz = 'Europe/Lisbon'
    alt = 10
    start = datetime.datetime(2023, 1, 1)
    end = datetime.datetime(2023, 12, 31)
    tilt = 25
    azimuth = 200

    # Ejecutar experimento
    results = run_panel_comparison_experiment(lat, lon, tz, alt, start, end, tilt, azimuth)

    # Mostrar resultados
    print("Resultados del experimento de comparación de paneles:")
    for panel_type, energy in results.items():
        print(f"Tipo de panel: {panel_type.capitalize()}, Energía generada: {energy:.2f} kWh")
