import pandas as pd
import datetime
from meteostat import Point
from pvlib.location import Location
from data_generator import (
    configure_locale, load_excel_data, create_full_year_dataframe,
    update_dataframe_with_excel_data, fetch_meteostat_data,
    calculate_irradiance_with_tilt_azimuth, calculate_cell_temperature, calculate_ac_power
)

class SolarPanelExperiment:
    def __init__(self, lat, lon, tz, alt, start, end):
        self.lat = lat
        self.lon = lon
        self.tz = tz
        self.alt = alt
        self.start = start
        self.end = end
        self.point = Point(lat, lon)
        self.loc = Location(lat, lon, tz, alt)
        self.df = load_excel_data('../datos.xlsx')
        self.data = create_full_year_dataframe(pd.date_range(start=start, end=end, freq='1h'))
        self.data = update_dataframe_with_excel_data(self.data, self.df)

    def load_and_prepare_data(self, start, end):
        # Carga los datos meteorológicos
        meteostat_info = fetch_meteostat_data(self.point, start, end)
        self.data['temp'] = meteostat_info['temp']
        self.data['wspd'] = meteostat_info['wspd']

    def apply_dirt_penalty(self, tilt, azimuth, penalty_factor):
        # Aplicar penalización a la irradiancia global (GHI) para paneles sin limpiadores
        poa_global_no_cleaned = calculate_irradiance_with_tilt_azimuth(self.loc, self.times, self.data, tilt, azimuth)
        # Asegurarse de que la penalización reduzca la irradiancia (menor irradiancia)
        poa_global_no_cleaned = poa_global_no_cleaned * (1 - penalty_factor)  # Penaliza reduciendo la irradiancia
        return poa_global_no_cleaned

    def run(self):
        acumuladorenergia_cleaned = 0
        acumuladorenergia_no_cleaned = 0

        # Ejecutar el experimento para todo el año
        print(f"\nEjecutando experimento para todo el año ({self.start}) - ({self.end})")
        self.times = pd.date_range(start=self.start, end=self.end, freq='1h')
        self.load_and_prepare_data(self.start, self.end)

        # Usar ángulos de inclinación específicos (15 y 70) y azimut de 70
        tilt_values = [15, 70]
        azimuth_value = 70  # Azimut fijo para ambos

        penalty_factor = 0.005  # Penalización inicial de suciedad

        for tilt in tilt_values:
            if self.data['GHI'].isnull().any():
                print("Cuidado: Valores NaN en GHI")
            self.data['GHI'] = self.data['GHI'].fillna(0)

            # Para los paneles con limpiadores automáticos
            poa_global_cleaned = calculate_irradiance_with_tilt_azimuth(self.loc, self.times, self.data, tilt, azimuth_value)
            temp_cell_cleaned = calculate_cell_temperature(poa_global_cleaned, self.data['temp'], self.data['wspd'])
            ac_power_cleaned = calculate_ac_power(poa_global_cleaned, temp_cell_cleaned)
            annual_energy_cleaned = ac_power_cleaned.sum() / 1000  # kWh

            # Para los paneles sin limpiadores automáticos (aplicando penalización)
            poa_global_no_cleaned = self.apply_dirt_penalty(tilt, azimuth_value, penalty_factor)
            temp_cell_no_cleaned = calculate_cell_temperature(poa_global_no_cleaned, self.data['temp'], self.data['wspd'])
            ac_power_no_cleaned = calculate_ac_power(poa_global_no_cleaned, temp_cell_no_cleaned)
            annual_energy_no_cleaned = ac_power_no_cleaned.sum() / 1000  # kWh

            # Energía generada con la optimización de ángulo y orientación
            acumuladorenergia_cleaned += annual_energy_cleaned
            acumuladorenergia_no_cleaned += annual_energy_no_cleaned

        print(f"\nEnergía generada con limpiadores durante todo el año: {acumuladorenergia_cleaned:.2f} kWh")
        print(f"Energía generada sin limpiadores durante todo el año: {acumuladorenergia_no_cleaned:.2f} kWh")
        print(f"Diferencia de energía (con vs sin limpiadores): {acumuladorenergia_cleaned - acumuladorenergia_no_cleaned:.2f} kWh")

if __name__ == "__main__":
    configure_locale()
    lat, lon, tz, alt = 37.787694, -3.776444, 'Europe/Madrid', 667
    start = datetime.datetime(2023, 1, 1)
    end = datetime.datetime(2023, 12, 31)
    experiment = SolarPanelExperiment(lat, lon, tz, alt, start, end)
    experiment.run()
