import datetime
from pvlib.solarposition import get_solarposition
from GeneradorExperimento import GeneradorExperimento
from data_generator import calculate_irradiance_with_tilt_azimuth, calculate_cell_temperature, calculate_ac_power

def calculate_tracking_angles(date, location):
    """
    Calcula ángulos dinámicos para el seguimiento solar basado en la posición solar.
    """
    solar_position = get_solarposition(date, location['latitude'], location['longitude'])

    # Calcular inclinaciones y azimuts dinámicos
    tilt = 90 - solar_position['apparent_elevation'].clip(lower=0)  # Evita inclinaciones negativas
    azimuth = solar_position['azimuth']

    return tilt, azimuth



def simulate_tracking_performance(lat, lon, tz, alt, start, end, panel_type, is_tracking):
    """
    Simula la producción energética para sistemas fijos o con seguimiento.
    """
    specs = {'efficiency': 0.20, 'gamma_pdc': -0.003, 'area': 1.6}  # Características del panel monocristalino
    pdc0 = specs['efficiency'] * specs['area'] * 1000
    gamma_pdc = specs['gamma_pdc']
    area = specs['area']
    eta_inv_nom = 0.96

    generador = GeneradorExperimento(lat, lon, tz, alt, 0, 0, start, end, '1h', pdc0, eta_inv_nom )

    total_energy = 0

    for date in generador.times:
        location = {'latitude': lat, 'longitude': lon}
        if is_tracking:
            tilt, azimuth = calculate_tracking_angles(date, location)
        else:
            tilt, azimuth = 25, 200  # Ángulo fijo

        # Calcular la irradiancia
        poa_global = calculate_irradiance_with_tilt_azimuth(generador.site, [date], generador.weather, tilt, azimuth)
        poa_global_adjusted = poa_global * specs['efficiency']
        temp_cell = calculate_cell_temperature(poa_global_adjusted, generador.weather['temp_air'], generador.weather['wind_speed'])
        ac_power = calculate_ac_power(poa_global_adjusted, temp_cell)

        total_energy += ac_power.sum() / 1000  # Convertir a kWh

    return total_energy


def run_tracking_experiment(lat, lon, tz, alt, start, end):
    """
    Compara la producción energética entre sistemas fijos y con seguimiento solar.
    """
    fixed_energy = simulate_tracking_performance(lat, lon, tz, alt, start, end, "monocristalino", is_tracking=False)
    tracking_energy = simulate_tracking_performance(lat, lon, tz, alt, start, end, "monocristalino", is_tracking=True)

    return fixed_energy, tracking_energy


if __name__ == "__main__":
    # Parámetros del experimento
    lat = 38.732602
    lon = -9.116373
    tz = 'Europe/Lisbon'
    alt = 10
    start = datetime.datetime(2023, 1, 1)
    end = datetime.datetime(2023, 12, 31)

    # Ejecutar experimento
    fixed_energy, tracking_energy = run_tracking_experiment(lat, lon, tz, alt, start, end)

    # Resultados
    print(f"Energía generada con sistema fijo: {fixed_energy:.2f} kWh")
    print(f"Energía generada con seguimiento solar: {tracking_energy:.2f} kWh")
    print(f"Diferencia de energía: {tracking_energy - fixed_energy:.2f} kWh")
