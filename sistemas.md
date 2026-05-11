# 🔧 SISTEMAS DEL TRAJE — DOCUMENTACIÓN COMPLETA

---

## 01 · ESTRUCTURA

**Material principal:** Fibra de carbono + TPU + Aerogel
**Peso:** 6.64 kg

La estructura sigue un diseño de capas:
- Exterior: fibra de carbono 2-3mm
- Intermedio: aerogel 12mm (aislamiento térmico EDF)
- Interior: padding TPU personalizado al piloto

Diseñada específicamente para integrar los 8 propulsores EDF y los 4 paneles solares sin interferencia térmica entre sistemas.

---

## 02 · PROPULSIÓN EDF + RCS

**Propulsores:** 8 EDF brushless distribuidos lateralmente
**Control:** 16 toberas RCS de N₂/H₂
**Potencia total:** 20 kW
**Peso:** 4.43 kg

Los propulsores están distribuidos simétricamente para evitar interferencia térmica. Ningún propulsor está directamente encima o debajo de otro. El sistema RCS proporciona control instantáneo en milisegundos para los 6 grados de libertad.

---

## 03 · ENERGÍA

**Fuentes:** Batería estado sólido + Celda H₂ + Solar + Electrolizador
**Capacidad total:** 23.1 kWh disponibles
**Peso:** 13.80 kg

El electrolizador convierte agua en H₂ + O₂ usando energía solar, generando combustible de forma continua. El O₂ generado también sirve para el sistema de respiración del casco.

---

## 04 · SISTEMA INFORMÁTICO

**Cerebro:** NVIDIA Jetson Orin (275 TOPS)
**Respaldo:** Raspberry Pi 5
**Control tiempo real:** 14× STM32
**Protocolo:** Bus CAN aeronáutico
**Peso:** 0.85 kg

El Jetson coordina todos los sistemas. Los STM32 controlan cada motor y tobera independientemente con respuesta en milisegundos.

---

## 05 · APERTURA Y CIERRE

**Sistema:** Mixto (torso por espalda + extremidades independientes)
**Cierre:** Neumático con juntas de silicona
**Tiempo ponerse:** ~4 minutos
**Peso:** 1.90 kg

El cierre neumático usa el mismo compresor para todas las secciones. Cada sección tiene válvula de emergencia manual accesible sin herramientas.

---

## 06 · REFRIGERACIÓN

**EDF:** Circuito líquido (agua destilada)
**Piloto:** 2 ventiladores 40mm
**Electrónica:** Aerogel pasivo
**Peso:** 1.65 kg

Diseñado para uso personal a baja altitud. Sin sistemas complejos innecesarios. El aire de vuelo a 60 km/h enfría el radiador de forma natural.

---

## 07 · ATERRIZAJE

**Tipo:** Mixto (descenso vertical + caminar al tocar)
**Frenado:** EDF reducen gradualmente + amortiguadores TPU
**Velocidad impacto:** <0.5 m/s
**Peso:** 1.13 kg

El LIDAR mide la altura continuamente. El Jetson reduce la potencia EDF de forma gradual y proporcional. Al tocar suelo, los STM32 mantienen los EDF de pantorrillas al 5-10% durante los primeros pasos para aliviar el peso.

---

## 08 · EMERGENCIAS

**Avería:** Aterrizaje automático con EDF restantes
**Fuego:** Corte energía + rociadores agua + alerta
**Detección:** <50 ms
**Peso:** 0.53 kg

Los rociadores usan el tanque de agua del electrolizador. El corte de energía es por zonas independientes para no afectar al vuelo. Un STM32 dedicado funciona independientemente del Jetson.

---

## 09 · ARTICULACIONES

**Brazos:** Pasivas (rótulas y bisagras)
**Piernas:** Motorizadas en caderas y rodillas (30-40 Nm)
**Peso:** 3.16 kg

Las articulaciones motorizadas reducen el esfuerzo de caminar con 42 kg de traje. En vuelo se ponen en modo libre para no consumir batería.

---

## 10 · COMUNICACIONES

**Canales:** 4G/5G + WiFi + LoRa + Bluetooth
**GPS:** Diferencial (precisión ±10cm)
**Audio:** DSP con cancelación de ruido EDF
**Peso:** 0.16 kg

El Jetson gestiona automáticamente el canal óptimo según disponibilidad. Streaming 4K en tiempo real a base tierra.

---

## 11 · PROTECCIÓN PILOTO

**Interior:** Mono lycra/kevlar estilo F1
**Espalda:** Protector D30 12mm
**Caderas:** Relleno EVA 15mm
**Manos:** Guantes técnicos kevlar
**Peso:** 1.55 kg

El D30 es un material inteligente: blando en condiciones normales, se endurece en <1ms al impacto. Pulsómetro y sensor temperatura integrados para monitorización continua.

---

## 12 · CASCO

**Material:** UHMWPE + Kevlar
**Visor:** Policarbonato electrocromático 5mm
**HUD:** Waveguide holográfico 1080p
**O₂:** Tanque 0.5L + electrolizador continuo
**Cámara:** 4K 60fps 120°
**Peso:** 1.92 kg

El HUD muestra altitud, velocidad, batería, H₂, temperatura EDF, GPS y alertas. Control por seguimiento ocular. El O₂ se activa automáticamente a partir de 2000m de altitud.

---

*Traje Volador EDF+RCS — Proyecto conceptual 2026*
