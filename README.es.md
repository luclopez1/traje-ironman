# ✈️ TRAJE VOLADOR PERSONAL — EDF + RCS

> **Diseño conceptual de un exotraje de vuelo personal para baja altitud y uso personal.**
> Desarrollado como proyecto de ingeniería abierto en 2026.

---

## 🌍 Idiomas

- 🇪🇸 [Español](docs/es/README.es.md) ← Estás aquí
- 🇬🇧 [English](README.md)

---

## 📋 Descripción del Proyecto

Este proyecto documenta el diseño conceptual completo de un traje de vuelo personal propulsado por **propulsores EDF (Electric Ducted Fan)** y un **Sistema de Control de Reacción (RCS)** para control direccional.

El traje está diseñado para:
- Uso personal recreativo
- Vuelo a baja altitud (hasta 500m)
- Vuelo a baja velocidad (hasta 100 km/h)
- Uso no militar y no combativo

---

## ⚡ Especificaciones Principales

| Parámetro | Valor |
|-----------|-------|
| **Peso total (con piloto)** | ~117.7 kg |
| **Peso traje (sin piloto)** | ~37.7 kg |
| **Peso máximo piloto** | 95 kg |
| **Empuje EDF total** | 1,400 N |
| **Potencia EDF total** | 20 kW |
| **Margen de empuje** | 21% |
| **Capacidad batería** | 20 kWh (estado sólido) |
| **Celda combustible H₂** | 3 kW continuo |
| **Autonomía (vuelo normal)** | ~1h 15min |
| **Autonomía (vuelo lento)** | ~2h 45min |
| **Velocidad crucero** | 70 km/h |
| **Velocidad máxima recomendada** | 100 km/h |
| **Velocidad máxima absoluta** | 120 km/h |
| **Altitud operativa** | 200m (máx 500m) |
| **Tiempo recarga batería** | 6h (completa) |
| **Tiempo recarga H₂** | 15 min |
| **Tiempo de ponerse el traje** | ~4 min |
| **Temperatura operativa** | -5°C a +35°C |

---

## 🗂️ Estructura del Repositorio

```
traje-volador/
│
├── README.md                    ← README principal (Inglés)
├── docs/
│   ├── en/                      ← Documentación en inglés
│   └── es/                      ← Documentación en español
│       ├── 01-estructura.md
│       ├── 02-propulsion.md
│       ├── 03-energia.md
│       ├── 04-informatica.md
│       ├── 05-apertura.md
│       ├── 06-refrigeracion.md
│       ├── 07-aterrizaje.md
│       ├── 08-emergencia.md
│       ├── 09-articulaciones.md
│       ├── 10-comunicaciones.md
│       ├── 11-piloto.md
│       └── 12-casco.md
│
├── specs/
│   ├── technical-specs.md
│   ├── weight-analysis.md
│   ├── autonomy-analysis.md
│   └── components-list.md
│
├── components/
│   └── components-list.md
```

---

## 🔧 Sistemas Diseñados

| # | Sistema | Estado |
|---|---------|--------|
| 01 | Estructura (fibra carbono + TPU) | ✅ Completo |
| 02 | Propulsión EDF (×8) + RCS (×16) | ✅ Completo |
| 03 | Energía (batería + H₂ + solar + electrolizador) | ✅ Completo |
| 04 | Informática IA (Jetson Orin + STM32) | ✅ Completo |
| 05 | Apertura/Cierre (neumático) | ✅ Completo |
| 06 | Refrigeración (líquida + ventiladores) | ✅ Completo |
| 07 | Aterrizaje (EDF gradual + amortiguadores TPU) | ✅ Completo |
| 08 | Emergencia (aterrizaje auto + rociadores agua) | ✅ Completo |
| 09 | Articulaciones (pasivas brazos + motorizadas piernas) | ✅ Completo |
| 10 | Comunicaciones (4G + WiFi + LoRa + BT) | ✅ Completo |
| 11 | Protección Piloto (mono F1 + D30) | ✅ Completo |
| 12 | Casco (UHMWPE + HUD + O₂ + cámara 4K) | ✅ Completo |

---

## ⚖️ Desglose de Peso

| Sistema | Peso |
|---------|------|
| Estructura | 6.64 kg |
| Propulsión EDF + RCS | 4.43 kg |
| Sistema energético | 13.80 kg |
| Sistema informático | 0.85 kg |
| Sistema neumático | 1.90 kg |
| Sistema refrigeración | 1.65 kg |
| Sistema aterrizaje | 1.13 kg |
| Sistema emergencia | 0.53 kg |
| Articulaciones | 3.16 kg |
| Comunicaciones | 0.16 kg |
| Protección piloto | 1.55 kg |
| Casco | 1.92 kg |
| **TOTAL (solo traje)** | **37.72 kg** |

---

## 🚀 Autonomía de Vuelo

| Modo de vuelo | Velocidad | Autonomía |
|---------------|-----------|-----------|
| Vuelo lento | 50 km/h | ~2h 45min |
| Vuelo normal | 70 km/h | ~1h 15min |
| Vuelo rápido | 90 km/h | ~1h 07min |
| Hover estático | 0 km/h | ~1h 52min |

---

## 🛡️ Características de Seguridad

- **Aterrizaje automático** si se detecta fallo en EDF
- **Rociadores de agua** para fuego o cortocircuito
- **Corte automático de energía** por zona independiente
- **Protector espalda D30** para absorción de impactos
- **SMS de emergencia** automático vía 4G al contacto
- **Alertas HUD** para todos los parámetros críticos
- **Reserva 15% batería** aplicada automáticamente

---

## 🧩 Tecnologías Clave

- **Motores EDF**: Ventiladores eléctricos encapsulados (sin hélices expuestas)
- **RCS**: Toberas de gas N₂/H₂ para control direccional en milisegundos
- **Batería estado sólido**: 20 kWh, menos degradación que Li-ion
- **Electrolizador**: Genera H₂ + O₂ del agua usando energía solar
- **Aerogel**: Aislamiento térmico entre EDF y piloto
- **D30**: Material de impacto inteligente (rígido en impacto, flexible normalmente)
- **UHMWPE**: Polietileno de ultra alto peso molecular para el casco
- **HUD Waveguide**: Pantalla holográfica en el visor
- **Jetson Orin**: Computador IA para coordinación de vuelo en tiempo real
- **Bus CAN**: Protocolo de comunicación aeronáutico entre componentes

---

## ⚠️ Aviso Legal

> Este es un **proyecto de diseño conceptual de ingeniería** con fines educativos e investigadores.
> Construir y pilotar un traje de vuelo personal requiere aprobación regulatoria,
> ingeniería profesional y pruebas de seguridad extensas.
> Los autores no fomentan actividades de vuelo no autorizadas.

---

## 📄 Licencia

Licencia MIT — Código abierto, libre de usar y modificar con atribución.

---
