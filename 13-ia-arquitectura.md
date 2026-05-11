# 🤖 ARQUITECTURA DE IA — TRAJE VOLADOR EDF+RCS

---

## Principio fundamental

```
PILOTO SIEMPRE TIENE CONTROL TOTAL
La IA es autónoma SOLO cuando
el piloto lo activa explícitamente.

Botón físico en el traje:
MANUAL ←→ ASISTIDO ←→ AUTÓNOMO
```

---

## Arquitectura en 4 capas

```
┌─────────────────────────────────────┐
│  CAPA 4: DECISIÓN DE ALTO NIVEL    │
│  (Jetson Orin - IA principal)      │
│  • Rutas automáticas               │
│  • Esquivar obstáculos             │
│  • Aprendizaje del piloto          │
│  • Gestión energía inteligente     │
├─────────────────────────────────────┤
│  CAPA 3: CONTROL DE VUELO          │
│  (Jetson Orin - tiempo real)       │
│  • Estabilización continua         │
│  • Fusión de sensores              │
│  • Control de postura              │
│  • Gestión de emergencias          │
├─────────────────────────────────────┤
│  CAPA 2: CONTROL DE MOTORES        │
│  (STM32 - microsegundos)           │
│  • PID por cada EDF                │
│  • Control RCS                     │
│  • Feedback de encoders            │
│  • Protección sobrecalentamiento   │
├─────────────────────────────────────┤
│  CAPA 1: HARDWARE                  │
│  (Sensores + Actuadores)           │
│  • IMU, GPS, LIDAR, cámaras        │
│  • 8 EDF + 16 RCS                  │
│  • Articulaciones motorizadas      │
│  • Todos los sensores              │
└─────────────────────────────────────┘
```

---

## Capa 2 — Control de motores (STM32)

### Algoritmo PID por EDF

```
PID = Proporcional + Integral + Derivativo

Error = RPM_deseadas - RPM_actuales
        ↓
P: salida += Kp × error
I: salida += Ki × suma_errores
D: salida += Kd × (error - error_anterior)
        ↓
Señal PWM → Motor EDF → Encoder → ciclo <1ms

PARÁMETROS INICIALES:
Kp = 0.8
Ki = 0.2
Kd = 0.1
```

### Control RCS

```
BANG-BANG CONTROL:
Si error_ángulo > umbral → tobera ON
Si error_ángulo < umbral → tobera OFF

Duración pulso: 5-50ms
Frecuencia: hasta 200Hz
Umbral: ±2° de inclinación
```

---

## Capa 3 — Control de vuelo (Jetson)

### Fusión de sensores — Filtro de Kalman Extendido

```
Combina IMU + GPS + Barómetro + LIDAR
→ Estimación óptima de posición
→ Estimación óptima de velocidad
→ Estimación óptima de orientación
→ Salida a 100Hz
```

### Bucle principal de estabilización (100Hz)

```
1. Leer estado actual (Kalman)
2. Comparar con estado deseado
3. Calcular correcciones necesarias
4. Distribuir entre EDF y RCS
5. Enviar órdenes a STM32
6. Repetir cada 10ms
```

### Control de postura — 6 grados de libertad

| Eje | Control | Sistema |
|-----|---------|---------|
| X adelante/atrás | Inclinación EDF | EDF |
| Y izquierda/derecha | Diferencial EDF | EDF |
| Z arriba/abajo | Potencia total EDF | EDF |
| Roll (rodar) | EDF izq vs der | EDF |
| Pitch (cabecear) | EDF delante vs atrás | EDF |
| Yaw (girar) | Toberas laterales | RCS |

---

## Capa 4 — IA de alto nivel (Jetson)

### Módulo 1: Esquivar obstáculos

```
Cámaras ×4 → YOLO v8 → Detección tiempo real
→ Estima distancia y trayectoria
→ Si objeto a <10m: calcula maniobra evasiva
→ Ejecuta y avisa piloto en HUD

Tiempo de reacción: <100ms
Velocidad procesamiento: 60fps a 1080p
```

### Módulo 2: Rutas automáticas

```
Algoritmo: A* modificado para 3D

1. Piloto marca destino en HUD o App
2. IA descarga mapa de la zona (4G)
3. Calcula ruta evitando:
   → Zonas restringidas (aeropuertos)
   → Edificios y obstáculos conocidos
   → Zonas de mal tiempo
4. Sigue la ruta automáticamente
5. Recalcula si aparece obstáculo

MODOS:
• Más rápida (consume más batería)
• Más eficiente (maximiza autonomía)
• Más segura (más altura, más margen)
```

### Módulo 3: Aprendizaje del piloto

```
Red neuronal recurrente (LSTM)
→ Analiza los últimos 10 vuelos
→ Detecta patrones del piloto
→ Ajusta parámetros automáticamente

APRENDE:
• Velocidad habitual en curvas
• Altitud preferida
• Maniobras frecuentes
• Zonas que suele visitar

PRIVACIDAD:
Todo el aprendizaje es LOCAL en el Jetson
Nunca sale del traje
```

### Módulo 4: Gestión energía inteligente

```
MONITORIZA:
• Batería restante
• Consumo actual
• Distancia al origen
• Condiciones de viento
• H₂ disponible

MODO AHORRO AUTOMÁTICO (batería <40%):
→ Reduce velocidad máxima a 60 km/h
→ Optimiza potencia EDF
→ Activa H₂ si no estaba activo
→ Notifica al piloto en HUD
```

---

## Modo autónomo completo

### Activación (triple seguridad)

```
1. Botón físico en muñeca izquierda
2. Confirmación vocal: "MODO AUTO"
3. Confirmación HUD: clic en SÍ
```

### Capacidades en modo autónomo

```
✅ Seguir ruta programada
✅ Mantener altitud constante
✅ Esquivar obstáculos
✅ Aterrizar automáticamente
✅ Gestionar energía óptimamente
✅ Volver al origen si batería baja
✅ Llamar a emergencias si piloto inconsciente
```

### Desactivación automática

```
→ Batería <20%
→ Fallo de sensor crítico
→ Zona restringida detectada
→ Condiciones meteorológicas malas
→ Piloto mueve cualquier extremidad
```

---

## Detección piloto inconsciente

```
MONITORIZACIÓN CONTINUA:
• Pulsómetro: ritmo cardíaco normal
• Acelerómetro: movimiento corporal
• Seguimiento ocular: ojos abiertos
• Voz: responde a preguntas

PROTOCOLO:

30s sin respuesta:
→ "¿Estás bien?" por altavoz
→ Vibración en el traje

45s sin respuesta:
→ Descenso suave automático
→ Llamada al contacto de emergencia

60s sin respuesta:
→ Aterrizaje de emergencia inmediato
→ SMS con GPS al contacto
→ Llamada automática al 112
```

---

## Stack tecnológico

| Categoría | Tecnología |
|-----------|-----------|
| Sistema operativo Jetson | Ubuntu 22.04 |
| Sistema operativo STM32 | FreeRTOS |
| Lenguaje IA | Python 3.11 |
| Lenguaje control | C++ |
| Middleware | ROS2 Humble |
| Detección objetos | YOLO v8 |
| Visión artificial | OpenCV |
| Inferencia IA | TensorFlow Lite |
| Fusión sensores | FilterPy (Kalman) |
| Control PID | simple-pid |
| Matemáticas | NumPy / SciPy |
| Aprendizaje | LSTM (Keras) |

---

## Nodos ROS2

| Nodo | Función |
|------|---------|
| `/sensor_fusion_node` | Lee sensores, aplica Kalman, publica estado |
| `/flight_controller_node` | Estabilización, calcula correcciones |
| `/motor_manager_node` | Distribuye comandos a STM32s |
| `/obstacle_detection_node` | Procesa cámaras con YOLO |
| `/route_planner_node` | Planifica rutas A*, gestiona waypoints |
| `/pilot_learning_node` | Entrena LSTM, ajusta parámetros |
| `/energy_manager_node` | Optimiza consumo, gestiona H₂ y solar |
| `/emergency_node` | Monitoriza piloto, gestiona emergencias |
| `/hud_manager_node` | Formatea datos para el HUD |

---

## Archivos a programar en Claude Code

```
src/
├── sensor_fusion_node.py
├── flight_controller_node.py
├── motor_manager_node.py
├── obstacle_detection_node.py
├── route_planner_node.py
├── pilot_learning_node.py
├── energy_manager_node.py
├── emergency_node.py
└── hud_manager_node.py
```

---

*Traje Volador EDF+RCS — Arquitectura IA — 2026*
