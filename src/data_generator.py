# data_generator.py
import locale
import pandas as pd
from meteostat import Point, Hourly
from pvlib.inverter import pvwatts
from pvlib.location import Location
from pvlib import irradiance
from pvlib.temperature import sapm_cell
from pvlib.pvsystem import PVSystem
import datetime

def configure_locale():
    locale.setlocale(locale.LC_TIME, 'es_ES.utf8')

def load_excel_data(file_path):
    df = pd.read_excel(file_path)
    df['Hora'] = df['Tiempo'].str.extract(r'a las (\d{1,2}:\d{2})', expand=False)
    df[['Dia', 'Mes']] = df['Tiempo'].str.extract(r'(\d+) \((.*?)\)', expand=True)
    df['Fecha'] = df['Dia'] + ' ' + df['Mes']
    df['Fecha'] = df['Fecha'].str.replace('de ', '', regex=False).str.strip()
    df['Fecha Completa'] = df['Fecha'] + ' ' + df['Hora']
    df['Fecha Completa'] = df['Fecha Completa'].str.replace(r'^\d+\s', '', regex=True)
    df['Tiempo'] = pd.to_datetime(df['Fecha Completa'], format='%d %B %H:%M', errors='coerce', dayfirst=True).apply(lambda x: x.replace(year=2023) if pd.notnull(x) else x)
    df = df.dropna(subset=['Tiempo'])
    df.rename(columns={
        'Radiación Global (kJ/m2)': 'GHI',
        'Radiación Difusa (kJ/m2)': 'DHI',
        'Radiación Directa (kJ/m2)': 'DNI'
    }, inplace=True)
    df.set_index('Tiempo', inplace=True)
    return df

def create_full_year_dataframe(times):
    return pd.DataFrame(0.0, index=times, columns=['GHI', 'DHI', 'DNI', 'temp', 'wspd'])

def update_dataframe_with_excel_data(data, df):
    data.update(df)
    return data

def fetch_meteostat_data(location, start, end):
    meteostat_info = Hourly(location, start, end)
    return meteostat_info.fetch()

def calculate_irradiance(loc, times, data):
    solar_position = loc.get_solarposition(times)
    surface_azimuth = 180
    surface_tilt = 30
    irradiance_on_module = irradiance.get_total_irradiance(
        surface_tilt, surface_azimuth,
        solar_position['zenith'], solar_position['azimuth'],
        data['DNI'], data['GHI'], data['DHI']
    )
    return irradiance_on_module['poa_global']

def calculate_cell_temperature(poa_global, temp_air, wind_speed):
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