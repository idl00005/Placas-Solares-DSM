# Simulación de Placas Solares con PVLib

Esta aplicación en Python simula el rendimiento de placas solares bajo distintas condiciones utilizando la librería **[PVLib](https://pvlib-python.readthedocs.io/en/stable/)**.  
El objetivo es analizar cómo diferentes configuraciones y estrategias afectan la **energía generada** por las placas solares a lo largo del tiempo.

---

## 🔬 Experimentos

La aplicación realiza varios experimentos para evaluar la eficiencia y la relación coste-rendimiento de las placas solares:

1. **Ajuste del ángulo de la placa por estación vs ángulo fijo**  
   - Comparar la energía generada cuando el ángulo de la placa se ajusta según la estación frente a mantener un ángulo fijo.

2. **Limpiadores automáticos vs sin limpieza**  
   - Evaluar el impacto de utilizar sistemas de limpieza automáticos frente a no limpiar las placas.

3. **Sistema de seguimiento solar vs placa fija**  
   - Analizar los beneficios de usar un seguidor solar que sigue al sol durante el día frente a una placa en posición fija.

4. **Distintos tipos de placas solares**  
   - Comparar diferentes tipos de placas para evaluar su **rendimiento en función del coste**.

---

## 📊 Resultados

Para cada experimento, la aplicación genera **series temporales** que muestran la **energía generada a lo largo del tiempo**, permitiendo analizar:

- Variaciones diarias y estacionales en la producción de energía.  
- Diferencias entre estrategias (por ejemplo, seguimiento solar frente a placa fija).  
- Comparación de rendimiento entre distintos tipos de placas solares.  

---

## 🛠️ Tecnologías utilizadas

- **Python**  
- **PVLib** – Para modelar la radiación solar y el rendimiento de las placas.  
- **Pandas y NumPy** – Para la manipulación y análisis de datos.  
- **Matplotlib** – Para la visualización de las series de energía generada.  
