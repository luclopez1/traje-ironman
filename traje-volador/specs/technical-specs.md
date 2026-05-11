# 📐 ESPECIFICACIONES TÉCNICAS / TECHNICAL SPECIFICATIONS

---

## PESO / WEIGHT

| Sistema | Peso |
|---------|------|
| Estructura | 6.640 kg |
| Propulsión EDF + RCS | 4.430 kg |
| Sistema energético | 13.800 kg |
| Sistema informático | 0.850 kg |
| Sistema neumático | 1.900 kg |
| Sistema refrigeración | 1.650 kg |
| Sistema aterrizaje | 1.130 kg |
| Sistema emergencia | 0.530 kg |
| Articulaciones | 3.160 kg |
| Comunicaciones | 0.160 kg |
| Protección piloto | 1.550 kg |
| Casco | 1.920 kg |
| **TOTAL TRAJE** | **37.720 kg** |
| Piloto (referencia) | 80.000 kg |
| **TOTAL CON PILOTO** | **117.720 kg** |

---

## PROPULSIÓN / PROPULSION

| Parámetro | Valor |
|-----------|-------|
| Número de propulsores EDF | 8 |
| Potencia EDF escápulas | 4 kW × 2 |
| Potencia EDF hombros | 3 kW × 2 |
| Potencia EDF cadera | 2 kW × 2 |
| Potencia EDF pantorrillas | 1 kW × 2 |
| Potencia EDF total | 20 kW |
| Empuje total | ~1,400 N |
| Peso a levantar | ~1,154 N |
| Margen empuje | 21% |
| Número toberas RCS | 16 |
| Gas RCS | N₂ + H₂ |
| Presión tanque RCS | 200-300 bar |
| Tiempo respuesta RCS | <1 ms |
| Tipo motor | Brushless EDF encapsulado |

---

## ENERGÍA / ENERGY

| Parámetro | Valor |
|-----------|-------|
| Batería principal | Estado sólido 20 kWh |
| Energía útil batería (85%) | 17 kWh |
| Reserva seguridad | 15% (3 kWh) |
| Energía disponible vuelo | 14 kWh |
| Celda combustible H₂ | 3 kW continuo |
| Duración H₂ | ~2 horas |
| Paneles solares | 4 × flexibles |
| Potencia solar total | 100-150 W |
| Eficiencia paneles | 22% |
| Electrolizador | 200-500 W |
| Producción H₂ | 0.1 g/s |
| Tanque agua | 3 litros |
| Tiempo recarga batería | 6 horas (3.3kW) |
| Tiempo recarga H₂ | 15 minutos |

---

## AUTONOMÍA / AUTONOMY

| Modo vuelo | Velocidad | EDF % | Consumo | Autonomía |
|-----------|-----------|-------|---------|-----------|
| Hover | 0 km/h | 60% | 12 kW | ~1h 52min |
| Vuelo lento | 50 km/h | 50% | 10 kW | ~2h 45min |
| Vuelo normal | 70 km/h | 70% | 14 kW | ~1h 15min |
| Vuelo rápido | 90 km/h | 85% | 17 kW | ~1h 07min |
| Vuelo máximo | 110 km/h | 100% | 20 kW | ~50 min |

**Consumo sistemas auxiliares en vuelo: ~147W**
- Informática: 74W
- Comunicaciones: 15W
- Refrigeración: 25W
- Articulaciones (vuelo): 8W
- Casco: 20W
- Emergencia espera: 5W

---

## VELOCIDAD / SPEED

| Parámetro | Valor |
|-----------|-------|
| Velocidad despegue/aterrizaje | 0-20 km/h |
| Velocidad crucero óptima | 70 km/h |
| Velocidad máxima recomendada | 100 km/h |
| Velocidad máxima absoluta | 120 km/h |
| Límite automático HUD | 110 km/h |
| Alerta HUD velocidad | 90 km/h |
| Velocidad descenso aterrizaje | <0.5 m/s |
| Velocidad descenso emergencia | <2 m/s |

---

## ALTITUD / ALTITUDE

| Parámetro | Valor |
|-----------|-------|
| Altitud operativa normal | 200 m |
| Altitud máxima recomendada | 500 m |
| Altitud máxima absoluta | 1,000 m |
| Altitud activación O₂ | >2,000 m (emergencia) |

---

## SISTEMA INFORMÁTICO / COMPUTING

| Parámetro | Valor |
|-----------|-------|
| Cerebro principal | NVIDIA Jetson Orin |
| Capacidad IA | 275 TOPS |
| RAM Jetson | 64 GB |
| Sistema respaldo | Raspberry Pi 5 |
| Microcontroladores | 14× STM32 |
| Protocolo datos | Bus CAN aeronáutico |
| Frecuencia ciclo control | 100 Hz (10ms) |
| Frecuencia ciclo RCS | 1000 Hz (1ms) |
| Consumo informática | ~74 W |
| Peso informática | 0.85 kg |

---

## ARTICULACIONES / JOINTS

| Articulación | Tipo | Torque | Rango |
|-------------|------|--------|-------|
| Hombro | Rótula esférica pasiva | — | 3 ejes |
| Codo | Bisagra pasiva | — | 0°-145° |
| Muñeca | Rótula pasiva | — | ±70°/±80° |
| Cadera | Servo motorizado | 30 Nm | 0°-90° |
| Rodilla | Servo motorizado | 40 Nm | 0°-130° |
| Tobillo | Bisagra+muelle pasiva | — | ±30°/±20° |

---

## COMUNICACIONES / COMMUNICATIONS

| Canal | Tecnología | Alcance | Uso |
|-------|-----------|---------|-----|
| Internet/Datos | 4G/5G | Global | Streaming, SMS emergencia |
| Base tierra | WiFi 802.11ac | 2 km | Telemetría baja latencia |
| Entre trajes | LoRa 868MHz | 5 km | Coordinación vuelo |
| Móvil personal | Bluetooth 5.2 | 100 m | Config, datos |
| Navegación | GPS + DGPS | Global | Posición ±10cm |
| Voz | DSP + UHF | 50 km | Comunicación directa |

---

## SEGURIDAD / SAFETY

| Parámetro | Valor |
|-----------|-------|
| Reserva batería mínima | 15% |
| Alerta batería | 30% |
| Aterrizaje forzado | 20% |
| Tiempo detección fallo EDF | <10 ms |
| Tiempo respuesta emergencia | <50 ms |
| Tiempo corte cortocircuito | <1 ms |
| Tiempo extinción fuego | 2-3 s |
| Protección impacto columna | D30 12mm |
| Material casco | UHMWPE + Kevlar |
| Resistencia impacto casco | >200 J |

---

## CASCO / HELMET

| Parámetro | Valor |
|-----------|-------|
| Material exterior | UHMWPE + Kevlar |
| Grosor exterior | 4mm |
| Peso total casco | ~1.92 kg |
| Visor | Policarbonato 5mm |
| Tipo visor | Electrocromático |
| Transmisión luz visor | 15-85% (variable) |
| HUD resolución | 1920×1080 por ojo |
| HUD tipo | Waveguide holográfico |
| Cámara | 4K 60fps, 120° |
| O₂ duración emergencia | 20 minutos |
| Activación O₂ | Automática >2000m |
| Reducción ruido | ~30 dB |
| Nivel ruido interior | ~50 dB |

---

## MATERIALES PRINCIPALES / MAIN MATERIALS

| Material | Uso | Propiedades clave |
|----------|-----|------------------|
| Fibra carbono | Estructura | 1.6 g/cm³, resistente a 150°C |
| TPU alta densidad | Articulaciones, amortiguación | Flexible, -40°C a +120°C |
| Aluminio 6061 | Soportes EDF, bloques fríos | Conduce calor lateralmente |
| Aerogel | Aislamiento térmico | Bloquea 95% del calor |
| UHMWPE | Casco exterior | Resistencia impacto >200J |
| Kevlar | Traje interior, refuerzos | Ignífugo, resistente rozadura |
| D30 | Protector espalda | Rígido en impacto, flexible normal |
| Titanio grado 5 | Articulaciones críticas | Alta resistencia, bajo peso |
| Silicona aeroespacial | Juntas neumáticas, cables | -20°C a +200°C |
| EVA alta densidad | Protectores cadera | Absorción impacto lateral |

---

*Traje Volador EDF+RCS — Proyecto conceptual 2026*
*EDF+RCS Flight Suit — Conceptual project 2026*
