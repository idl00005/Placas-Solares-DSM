import locale
import pandas as pd
from meteostat import Hourly, Point

from pvlib.location import Location
from pvlib import pvsystem, modelchain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS



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
        'Radiación Global (kJ/m2)': 'ghi',
        'Radiación Difusa (kJ/m2)': 'dhi',
        'Radiación Directa (kJ/m2)': 'dni'
    }, inplace=True)
    df.set_index('Tiempo', inplace=True)
    return df

def create_full_year_dataframe(times, ruta_excel, lat, lon, start, end):
    df = load_excel_data(ruta_excel)
    data = pd.DataFrame(0.0, index=times, columns=['ghi', 'dhi', 'dni', 'temp', 'wspd'])
    data.update(df)
    meteostat_info = Hourly(Point(lat,lon), pd.to_datetime(start), pd.to_datetime(end)).fetch()
    data['temp'] = meteostat_info['temp']
    data['wspd'] = meteostat_info['wspd']
    return data

def crear_modelo(tilt, azimuth, pdc0, gamma_pdc, eta_inv_nom, site, area):
    temp_model_params = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
    module_params = {
        'Name': 'Generic Module',
        'pdc0': pdc0,
        'gamma_pdc': gamma_pdc,
        'area' : area
    }

    system = pvsystem.PVSystem(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        module_parameters=module_params,
        inverter_parameters={'pdc0': pdc0, 'eta_inv_nom': eta_inv_nom},
        temperature_model_parameters=temp_model_params
    )
    return modelchain.ModelChain(system, site, aoi_model="physical", spectral_model="no_loss")


class GeneradorExperimento:
    def __init__(self, lat, lon, tz, alt, tilt, azimuth,start,end, frecuencia, ruta_excel, pdc0, gamma_pdc, eta_inv_nom, area):
        configure_locale()
        self.site = Location(lat, lon, tz, alt)
        self.tilt = tilt
        self.azimuth = azimuth
        self.times = pd.date_range(start=start, end=end, freq=frecuencia)
        self.data = create_full_year_dataframe(self.times,ruta_excel, lat, lon, start, end)
        self.weather = self.data[['ghi', 'dhi', 'dni']].copy()
        self.weather['temp_air'] = self.data['temp']
        self.weather['wind_speed'] = self.data['wspd']
        self.mc = crear_modelo(tilt, azimuth, pdc0, gamma_pdc, eta_inv_nom, self.site, area)

