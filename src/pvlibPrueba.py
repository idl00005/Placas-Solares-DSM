from pvlib.location import Location
loc = Location(lat, lon, tz, alt)
times = pd.date_range('2023-01-01', '2023-12-31', freq='1h', tz=tz)
solar_position = loc.get_solarposition(times)