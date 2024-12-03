from data_generator import (
    configure_locale, load_excel_data, create_full_year_dataframe,
    update_dataframe_with_excel_data, fetch_meteostat_data,
    calculate_irradiance, calculate_cell_temperature, calculate_ac_power
)
import pandas as pd
import datetime
from meteostat import Point
from pvlib.location import Location

def main():
    configure_locale()
    lat, lon, tz, alt = 37.787694, -3.776444, 'Europe/Madrid', 667
    loc = Location(lat, lon, tz, alt)
    times = pd.date_range(start='2023-01-01', end='2023-12-31', freq='1h')
    df = load_excel_data('../datos.xlsx')
    data = create_full_year_dataframe(times)
    data = update_dataframe_with_excel_data(data, df)
    location = Point(lat, lon)
    start = datetime.datetime(2023, 1, 1)
    end = datetime.datetime(2023, 12, 31)
    meteostat_info = fetch_meteostat_data(location, start, end)
    data['temp'] = meteostat_info['temp']
    data['wspd'] = meteostat_info['wspd']
    poa_global = calculate_irradiance(loc, times, data)
    temp_cell = calculate_cell_temperature(poa_global, data['temp'], data['wspd'])
    ac_power = calculate_ac_power(poa_global, temp_cell)
    annual_energy = ac_power.sum() / 1000
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.expand_frame_repr', False)
    print(data)
    print(f"Energía anual generada: {annual_energy:.2f} kWh")

if __name__ == "__main__":
    main()