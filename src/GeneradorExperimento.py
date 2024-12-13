import locale
import pandas as pd
from meteostat import Hourly, Point
import numpy as np

from pvlib.location import Location
from pvlib import pvsystem, modelchain
from pvlib.solarposition import get_solarposition
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

from data_generator import calculate_irradiance_with_tilt_azimuth


def configure_locale():
    locale.setlocale(locale.LC_TIME, 'es_ES.utf8')

def obterer_datos_excel():
    file_path = 'datos2.csv'

    raw_data = pd.read_csv(file_path, sep=',', skiprows=0, header=0, low_memory=False)

    # Renombramos las columnas con los nombres correctos basándonos en el formato proporcionado
    raw_data.columns = [
        "ObservationTime(LST)",
        "Global Horizontal Irradiance (GHI) W/m2",
        "Direct Normal Irradiance (DNI) W/m2",
        "AmbientTemperature (deg C)",
        "WindSpeed (m/s)",
        "Wind Direction (degrees)",
        "Wind-Speed 100m (m/s)",
        "Wind Direction 100m (degrees)",
        "WindGust (m/s)",
        "Relative Humidity (%)",
        "Liquid Precipitation (kg/m2)",
        "Solid Precipitation (kg/m2)",
        "Snow Depth (m)",
        "Clear Sky GHI",
        "Clear Sky DNI",
        "Clear Sky DHI",
        "IrradianceObservationType",
        "LeadTime",
        "DataVersion",
        "ObservationTime(GMT)",
        "Diffuse Horizontal Irradiance (DIF) W/m2",
        "AmbientTemperatureObservationType",
        "WindSpeedObservationType",
        "Albedo",
        "Particulate Matter 10 (mug/m3)",
        "Particulate Matter 2.5 (mug/m3)"
    ]
    try:
        raw_data['ObservationTime(LST)'] = pd.to_datetime(raw_data['ObservationTime(LST)'], format='%m/%d/%Y %H:%M',
                                                          dayfirst=True)
    except ValueError as e:
        print(f"Error al convertir fechas: {e}")
        raise

    # Establecer la columna de tiempo como índice
    # inplace=True modifica el DataFrame original estableciendo esta columna como índice
    raw_data.set_index('ObservationTime(LST)', inplace=True)

    # Seleccionar las columnas de interés
    # Estas son las columnas específicas que queremos extraer del conjunto de datos
    columns_of_interest = [
        'Global Horizontal Irradiance (GHI) W/m2',  # Irradiancia horizontal global
        'Direct Normal Irradiance (DNI) W/m2',  # Irradiancia directa normal
        'AmbientTemperature (deg C)',  # Temperatura ambiente en grados Celsius
        'WindSpeed (m/s)'  # Velocidad del viento en metros por segundo
    ]
    data_filtered = raw_data[columns_of_interest]

    # Renombrar las columnas para simplificar el acceso
    data_filtered = data_filtered.rename(columns={
        'Global Horizontal Irradiance (GHI) W/m2': 'ghi',
        'Direct Normal Irradiance (DNI) W/m2': 'dni',
        'AmbientTemperature (deg C)': 'temp',
        'WindSpeed (m/s)': 'wspd'
    })
    return data_filtered

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


def obtener_dhi(weather, times, site):
    solar_position = get_solarposition(times, site.latitude, site.longitude)
    weather['solar_zenith'] = solar_position['zenith']

    # Calculamos dhi si faltan datos
    weather['dhi'] = weather['ghi'] - weather['dni'] * solar_position['zenith'].apply(
        lambda z: max(0, np.cos(np.radians(z))))

    # Asegurarse de que dhi no sea negativo
    weather['dhi'] = weather['dhi'].clip(lower=0)
    return weather


class GeneradorExperimento:
    def __init__(self, lat, lon, tz, alt, tilt, azimuth,start,end, frecuencia, pdc0, gamma_pdc, eta_inv_nom, area):
        configure_locale()
        self.site = Location(lat, lon, tz, alt)
        self.tilt = tilt
        self.azimuth = azimuth
        self.times = pd.date_range(start=start, end=end, freq=frecuencia)
        self.data = obterer_datos_excel()
        self.weather = self.data.loc[(self.data.index >= start) & (self.data.index <= end), ['ghi', 'dni']].copy()
        self.weather = obtener_dhi(self.weather, self.data.index, self.site)
        self.weather['temp_air'] = self.data['temp']
        self.weather['wind_speed'] = self.data['wspd']
        self.mc = crear_modelo(tilt, azimuth, pdc0, gamma_pdc, eta_inv_nom, self.site, area)

    def set_tilt(self, tilt):
        self.tilt = tilt
        self.mc.system.surface_tilt = tilt

    def set_azimuth(self, azimuth):
        self.azimuth = azimuth
        self.mc.system.surface_azimuth = azimuth
        

