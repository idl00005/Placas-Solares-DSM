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

    def get_optimal_tilt_and_azimuth(self):
        # Rango de inclinación y orientación a probar
        tilt_range = range(0, 91, 5)  # De 0° a 90° (inclinación) con un paso de 5°
        azimuth_range = range(0, 361, 10)  # De 0° a 360° (orientación) con un paso de 10°

        best_tilt = 0
        best_azimuth = 0
        best_energy = 0.0

        # Probar todas las combinaciones de inclinación y orientación
        for tilt in tilt_range:
            for azimuth in azimuth_range:
                self.data['GHI'] = self.data['GHI'].fillna(0)  # Asegúrate de no tener NaNs
                # Llamada a la nueva función que toma en cuenta la inclinación y la orientación
                poa_global = calculate_irradiance_with_tilt_azimuth(self.loc, self.times, self.data, tilt, azimuth)
                temp_cell = calculate_cell_temperature(poa_global, self.data['temp'], self.data['wspd'])
                ac_power = calculate_ac_power(poa_global, temp_cell)
                annual_energy = ac_power.sum() / 1000  # kWh

                # Comparar la energía generada
                if annual_energy > best_energy:
                    best_energy = annual_energy
                    best_tilt = tilt
                    best_azimuth = azimuth

        return best_tilt, best_azimuth, best_energy

    def run(self):
        # Fechas para cada estación
        seasons = {
            'Primavera': (datetime.datetime(2023, 3, 21), datetime.datetime(2023, 6, 20)),
            'Verano': (datetime.datetime(2023, 6, 21), datetime.datetime(2023, 9, 20)),
            'Otoño': (datetime.datetime(2023, 9, 21), datetime.datetime(2023, 12, 20)),
            'Invierno': (datetime.datetime(2023, 12, 21), datetime.datetime(2024, 3, 20)),
        }

        # Ejecutar el experimento para cada estación
        for season, (season_start, season_end) in seasons.items():
            print(f"\nEjecutando experimento para {season} ({season_start.date()} - {season_end.date()})")
            self.times = pd.date_range(start=season_start, end=season_end, freq='1h')
            self.load_and_prepare_data(season_start, season_end)

            best_tilt, best_azimuth, best_energy = self.get_optimal_tilt_and_azimuth()
            print(f"Tilt óptimo: {best_tilt}°")
            print(f"Azimuth óptimo: {best_azimuth}°")
            print(f"Energía generada: {best_energy:.2f} kWh")

if __name__ == "__main__":
    configure_locale()
    lat, lon, tz, alt = 37.787694, -3.776444, 'Europe/Madrid', 667
    start = datetime.datetime(2023, 1, 1)
    end = datetime.datetime(2024, 3, 20)
    experiment = SolarPanelExperiment(lat, lon, tz, alt, start, end)
    experiment.run()
