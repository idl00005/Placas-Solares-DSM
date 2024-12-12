import matplotlib.pyplot as plt
import pandas as pd

from GeneradorExperimento import GeneradorExperimento

# Configuración inicial
generador = GeneradorExperimento(37.787694, -3.776444, 'Europe/Madrid', 573, 15,
                                 170, '2023-01-01', '2023-12-31', '1h',
                                 'datos.xlsx', 300, -0.004, 0.96, 1.6)

# Configurar gráficos
plt.ion()  
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
fig.suptitle("Simulación de Producción de Energía")

# Configurar gráficos vacíos con límites iniciales
ax1.set_xlabel("Fecha")
ax1.set_ylabel("Energía Acumulada (kWh)")
ax1.grid(True)
line_accum, = ax1.plot([], [], 'b-', label="Energía Acumulada (kWh)")
ax1.legend()
ax1.set_xlim(generador.times[0], generador.times[-1])
ax1.set_ylim(0, 1)

ax2.set_xlabel("Semana")
ax2.set_ylabel("Energía Semanal (kWh)")
ax2.grid(True)
line_week, = ax2.plot([], [], 'b-', label="Energía Semanal (kWh)")
ax2.legend()
ax2.set_xlim(1, 52)
ax2.set_ylim(0, 1)

# Inicializar listas de datos
energy_hourly = []
cumulative_energy = []
time_data = []
weekly_energy = []
weekly_dates = []
total_energy_weekly = 0

# Definir umbral de GHI para filtrar horas sin sol (puedes ajustarlo según tus datos)
ghi_threshold = 5  # W/m², ajusta este valor según la sensibilidad que desees

pd.set_option('display.max_rows', None)  # Mostrar todas las filas
pd.set_option('display.max_columns', None)  # Mostrar todas las columnas
pd.set_option('display.width', None)  # Ajustar al ancho completo
print(generador.data)
# Ejecutar simulación y actualizar gráficos
for i, time in enumerate(generador.weather.index):
    weather_hour = generador.weather.iloc[i:i+1]

    # Filtrar horas sin irradiancia solar significativa
    if weather_hour['ghi'].values[0] > ghi_threshold:
        generador.mc.run_model(weather_hour)

        # Guardar datos actuales en kWh
        current_energy_kWh = generador.mc.results.ac.values[0] / 1000  # Convertir a kWh
        energy_hourly.append(current_energy_kWh)

        # Calcular energía acumulada
        total_energy = sum(energy_hourly)
        cumulative_energy.append(total_energy)
        time_data.append(time)

        # Acumular energía semanal
        total_energy_weekly += current_energy_kWh

        # Verificar si es lunes a las 12:00 y actualizar energía semanal
        if time.weekday() == 0 and time.hour == 12 and i > 0:
            weekly_energy.append(total_energy_weekly)
            weekly_dates.append(len(weekly_energy))
            total_energy_weekly = 0

            # Actualizar gráfica de energía semanal
            line_week.set_data(weekly_dates, weekly_energy)
            ax2.set_xlim(1, max(weekly_dates))
            ax2.set_ylim(0, max(weekly_energy) + 1)

        # Actualizar gráfica de energía acumulada
        line_accum.set_data(time_data, cumulative_energy)
        ax1.set_ylim(0, max(cumulative_energy) + 1)

        # Redibujar gráficos
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.05)

# Detener la interactividad para finalizar
plt.ioff()
plt.show()
