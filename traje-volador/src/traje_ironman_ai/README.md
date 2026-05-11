# 🤖 NODOS ROS2 — Sistema de IA del Traje Volador

## Overview

Este directorio contiene los 9 nodos ROS2 que controlan la IA del traje volador EDF+RCS. Cada nodo cumple una función específica en el sistema de control jerárquico de 4 capas.

```
CAPA 4: Decisión de alto nivel    ← route_planner, pilot_learning, energy_manager
CAPA 3: Control de vuelo          ← flight_controller, obstacle_detection
CAPA 2: Control de motores        ← motor_manager
CAPA 1: Hardware                  ← sensor_fusion (Lee sensores)
```

---

## Nodos Incluidos

### 1. **sensor_fusion_node.py** — Fusión de Sensores (100 Hz)
**Función:** Filtra y fusiona datos de todos los sensores usando Filtro de Kalman Extendido.

**Entrada:**
- IMU (acelerómetro, giroscopio)
- GPS
- Barómetro
- LIDAR (altura)

**Salida:**
- `/state_estimate` — Estimación óptima de posición, velocidad, orientación

**Algoritmo:** EKF (Extended Kalman Filter) → fusiona sensores a 100 Hz

---

### 2. **flight_controller_node.py** — Control de Vuelo (100 Hz)
**Función:** Estabilización y control de 6 grados de libertad (6-DOF).

**Entrada:**
- `/state_estimate` — Estado actual del traje
- `/cmd_vel` — Comandos de velocidad del piloto/IA

**Salida:**
- `/control_output` — Comandos a 8 EDF + 16 RCS (24 valores)

**Algoritmo:** 6 controladores PID independientes
- **Pitch/Roll:** Diferencial de empuje en EDFs
- **Yaw:** Control RCS (toberas de gas)
- **Altitud:** Potencia total EDF
- **Movimiento XY:** Inclinación EDF

---

### 3. **motor_manager_node.py** — Gestor de Motores (1000 Hz)
**Función:** Distribuye comandos a microcontroladores STM32 a nivel de PWM.

**Entrada:**
- `/control_output` — Comandos del flight controller
- `/motor_feedback` — RPM, corriente, temperatura de cada motor

**Salida:**
- `/pwm_commands` — Señales PWM a 8 motores EDF
- `/rcs_commands` — Señales de disparo a 16 toberas RCS

**Algoritmo:** PID individual por motor + Bang-Bang para RCS

---

### 4. **obstacle_detection_node.py** — Detección de Obstáculos (30 Hz)
**Función:** Detección en tiempo real usando YOLO v8 (cámaras 4K).

**Entrada:**
- `/camera0...camera3/image_raw` — 4 cámaras (frontal, lateral izq/der, posterior)

**Salida:**
- `/detected_obstacles` — Lista de obstáculos en 3D
- `/threat_vector` — Vector de maniobra evasiva si hay amenaza (<10m)

**Algoritmo:** YOLO v8 → triangulación 3D con cámaras calibradas

---

### 5. **route_planner_node.py** — Planificador de Rutas (10 Hz)
**Función:** Genera rutas automáticas evitando obstáculos usando A*.

**Entrada:**
- `/goal_pose` — Destino del piloto/IA
- `/detected_obstacles` — Mapa dinámico de obstáculos

**Salida:**
- `/planned_path` — Ruta completa (lista de waypoints)
- `/next_waypoint` — Siguiente waypoint para el control de vuelo

**Algoritmo:** A* en malla 3D de 10m x 10m
- **Modos:** Safe (12 m/s), Normal (15 m/s), Fast (25 m/s)
- **Replanificación:** Si desviación > 20m

---

### 6. **pilot_learning_node.py** — Aprendizaje del Piloto (1 Hz)
**Función:** Aprende patrones de vuelo del piloto con LSTM (red neuronal).

**Entrada:**
- `/state_estimate` — Estado de vuelo
- `/cmd_vel` — Comandos del piloto

**Salida:**
- `/pilot_params` — Parámetros aprendidos (velocidad preferida, altitud, agresividad)

**Algoritmo:** LSTM recurrente sobre últimos 10 vuelos
- Detecta: velocidad habitual, altitud preferida, maniobras frecuentes
- Ajusta: parámetros de control automáticamente
- **Privacidad:** Todo local en Jetson, no sale del traje

---

### 7. **energy_manager_node.py** — Gestor de Energía (5 Hz)
**Función:** Optimiza distribución de potencia entre batería, H₂ y solar.

**Entrada:**
- `/motor_status` — Consumo de motores
- `/auxiliary_power` — Consumo de sistemas auxiliares

**Salida:**
- `/energy_status` — SOC batería, H₂, potencia consumida
- `/fuel_cell_power_request` — Comando a celda H₂
- `/electrolyzer_power_request` — Comando a electrolizador
- `/remaining_flight_time` — Tiempo de vuelo estimado

**Algoritmo:**
- Batería principal: 20 kWh (estado sólido)
- Celda H₂: 3 kW continuo (respaldo)
- Paneles solares: 100-150 W
- Electrolizador: genera H₂ del agua con solar

---

### 8. **emergency_node.py** — Gestión de Emergencias (10 Hz)
**Función:** Monitoriza piloto y ejecuta protocolos de emergencia.

**Entrada:**
- `/pilot_vitals` — Pulso, O₂, temperatura, ojos
- `/motor_status` — Detección de fallos motores

**Salida:**
- `/emergency_landing` — Comando de aterrizaje forzado
- `/home_position` — Retorno automático al origen
- `/system_alert` — Alertas críticas

**Protocolo inconsciente:**
- 0-30s: Alerta verbal + vibración "¿Estás bien?"
- 30-60s: Descenso suave automático
- 60-90s: Retorno a casa
- >90s: Aterrizaje de emergencia + 112

---

### 9. **hud_manager_node.py** — Gestor del HUD (30 Hz)
**Función:** Formatea y muestra telemetría en pantalla holográfica del casco.

**Entrada:**
- `/state_estimate` — Todos los datos de vuelo
- `/energy_status` — Batería, H₂, tiempo restante
- `/pilot_status` — Salud del piloto
- `/threat_vector` — Alertas de obstáculos

**Salida:**
- `/hud_display` — Texto formateado para visor waveguide
- `/hud_overlay` — Coordenadas AR para overlay

**Display primario:**
```
╔════════════════════════════════════════╗
║ ALT  185.3m              BAT   84%    ║
║ SPD  18.5m/s             H2    52%    ║
║ V/S  +2.1m/s             TIME  67m    ║
║                                        ║
║       CLEAR - PROCEED                  ║
║       WP: 245m  CRS: 127°              ║
╚════════════════════════════════════════╝
```

---

## Tópicos ROS2 (Message Bus)

### Tópicos de Sensores
- `/imu/data` → IMU (aceleraciones, giros)
- `/gps/fix` → GPS
- `/barometer` → Presión → Altitud
- `/lidar/height` → Altura del suelo

### Tópicos de Estado
- `/state_estimate` → Estimación fusionada (100 Hz)
- `/pose_estimate` → Solo posición
- `/flight_status` → Velocidad y rotación actual

### Tópicos de Control
- `/cmd_vel` → Comandos de velocidad
- `/control_output` → Comandos de motores (8 EDF + 16 RCS)
- `/pwm_commands` → PWM a microcontroladores
- `/rcs_commands` → Disparo de toberas RCS

### Tópicos de Percepción
- `/detected_obstacles` → Lista de obstáculos 3D
- `/threat_vector` → Vector de evasión si hay amenaza
- `/camera0...camera3/image_raw` → Video cámaras

### Tópicos de Navegación
- `/planned_path` → Ruta planificada (waypoints)
- `/next_waypoint` → Siguiente punto de ruta
- `/goal_pose` → Destino deseado

### Tópicos de Energía
- `/energy_status` → Batería, H₂, consumo
- `/remaining_flight_time` → Minutos restantes
- `/battery_warning` → Alerta batería baja

### Tópicos de Emergencia
- `/pilot_status` → Estado de salud del piloto
- `/emergency_landing` → Comando de aterrizaje forzado
- `/home_position` → Retorno automático
- `/system_alert` → Alertas críticas

### Tópicos de Aprendizaje
- `/pilot_params` → Parámetros aprendidos del piloto

### Tópicos del HUD
- `/hud_display` → Texto para mostrar en pantalla
- `/hud_overlay` → Coordenadas de AR overlay

---

## Instalación

```bash
cd traje-ironman
rosdep install --from-paths . --ignore-src -r -y
colcon build
source install/setup.bash
```

---

## Lanzamiento

### Todos los nodos (sistema completo)
```bash
ros2 launch traje_ironman_ai full_system.launch.xml
```

### Nodos individuales
```bash
# Sensor fusion
ros2 run traje_ironman_ai sensor_fusion

# Flight controller
ros2 run traje_ironman_ai flight_controller

# Motor manager
ros2 run traje_ironman_ai motor_manager

# Y así con cada nodo...
```

---

## Frecuencias y Tiempos de Actualización

| Nodo | Frecuencia | Período |
|------|-----------|---------|
| sensor_fusion | 100 Hz | 10 ms |
| flight_controller | 100 Hz | 10 ms |
| motor_manager | 1000 Hz | 1 ms |
| obstacle_detection | 30 Hz | 33 ms |
| route_planner | 10 Hz | 100 ms |
| pilot_learning | 1 Hz | 1000 ms |
| energy_manager | 5 Hz | 200 ms |
| emergency_node | 10 Hz | 100 ms |
| hud_manager | 30 Hz | 33 ms |

---

## Parámetros de Tuning (en cada nodo)

### flight_controller_node.py
```python
PID_CONTROLLERS = {
    'roll': PIDController(Kp=1.5, Ki=0.1, Kd=0.3),
    'pitch': PIDController(Kp=1.5, Ki=0.1, Kd=0.3),
    'yaw': PIDController(Kp=2.0, Ki=0.05, Kd=0.4),
    'altitude': PIDController(Kp=2.0, Ki=0.2, Kd=0.5),
}
```

### motor_manager_node.py
```python
MOTOR_MAX_RPM = 12000
MOTOR_MAX_TEMP = 85.0  # °C
MOTOR_MAX_AMP = 80.0   # A
```

### energy_manager_node.py
```python
BATTERY_WARNING = 0.30  # 30%
BATTERY_CRITICAL = 0.20  # 20%
BATTERY_EMERGENCY = 0.15  # 15%
```

---

## Diagnóstico

### Ver estado en tiempo real
```bash
# Estado de vuelo
ros2 topic echo /state_estimate

# Energía
ros2 topic echo /energy_status

# Obstáculos detectados
ros2 topic echo /detected_obstacles

# Status del piloto
ros2 topic echo /pilot_status
```

### Grabar datos de vuelo
```bash
ros2 bag record -a -o flight_data.bag
```

### Reproducir vuelo anterior
```bash
ros2 bag play flight_data.bag
```

---

## Notas de Implementación

1. **Sensor Fusion:** El Kalman Filter asume modelo de movimiento cinemático simple. Para vuelos complejos, se puede mejorar con modelo dinámico.

2. **Flight Controller:** Los PID son lineales. Se puede usar control no-lineal (como Nonlinear Dynamic Inversion) para mejor tracking en maniobras agresivas.

3. **Motor Manager:** Simula comportamiento STM32. En producción, usar driver real CAN/serial.

4. **Obstacle Detection:** Simula YOLO. Para producción, usar `torch.hub` o TensorFlow Lite.

5. **Route Planner:** A* en 3D es computacionalmente intensivo. Para espacios reales, usar RRT* o Theta*.

6. **Pilot Learning:** LSTM simulado. Para producción, usar TensorFlow/PyTorch con historial real.

7. **Energy Manager:** Modelos simplificados. Para mejor predicción, usar machine learning con datos reales.

8. **Emergency Node:** Thresholds de vitales son ejemplos. Calibrar con médicos.

---

## Referencias
- **Documentación ROS2:** https://docs.ros.org/en/humble/
- **FilterPy:** https://filterpy.readthedocs.io/
- **OpenCV:** https://docs.opencv.org/
- **YOLO v8:** https://github.com/ultralytics/ultralytics

---

*Traje Volador EDF+RCS — Sistema de IA ROS2 — 2026*
