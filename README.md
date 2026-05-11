# ✈️ PERSONAL FLIGHT SUIT — EDF + RCS

> **Conceptual design of a personal flight exosuit for low altitude and personal use.**
> Developed as an open engineering project in 2026.

---

## 🌍 Languages

- 🇪🇸 [Español](docs/es/README.es.md)
- 🇬🇧 [English](README.md) ← You are here

---

## 📋 Project Overview

This project documents the complete conceptual design of a personal flight suit powered by **Electric Ducted Fan (EDF)** propulsors and a **Reaction Control System (RCS)** for directional control.

The suit is designed for:
- Personal recreational use
- Low altitude flight (up to 500m)
- Low speed flight (up to 100 km/h)
- Non-military, non-combat purposes

---

## ⚡ Key Specifications

| Parameter | Value |
|-----------|-------|
| **Total weight (with pilot)** | ~117.7 kg |
| **Suit weight (without pilot)** | ~37.7 kg |
| **Max pilot weight** | 95 kg |
| **EDF thrust** | 1,400 N |
| **Total EDF power** | 20 kW |
| **Thrust margin** | 21% |
| **Battery capacity** | 20 kWh (solid state) |
| **H₂ fuel cell** | 3 kW continuous |
| **Flight endurance (normal)** | ~1h 15min |
| **Flight endurance (slow)** | ~2h 45min |
| **Cruise speed** | 70 km/h |
| **Max recommended speed** | 100 km/h |
| **Max absolute speed** | 120 km/h |
| **Operating altitude** | 200m (max 500m) |
| **Recharge time** | 6h (full battery) |
| **H₂ refuel time** | 15 min |
| **Donning time** | ~4 min |
| **Operating temperature** | -5°C to +35°C |

---

## 🗂️ Repository Structure

```
traje-volador/
│
├── README.md                    ← Main README (English)
├── docs/
│   ├── en/
│   │   ├── README.es.md         ← Full README (Spanish)
│   │   ├── 01-structure.md      ← Structure system
│   │   ├── 02-propulsion.md     ← EDF + RCS propulsion
│   │   ├── 03-energy.md         ← Energy system
│   │   ├── 04-computing.md      ← AI computing system
│   │   ├── 05-opening.md        ← Opening/closing system
│   │   ├── 06-cooling.md        ← Cooling system
│   │   ├── 07-landing.md        ← Landing system
│   │   ├── 08-emergency.md      ← Emergency system
│   │   ├── 09-joints.md         ← Joint system
│   │   ├── 10-comms.md          ← Communications
│   │   ├── 11-pilot.md          ← Pilot protection
│   │   └── 12-helmet.md         ← Helmet design
│   └── es/
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
│   ├── technical-specs.md       ← Full technical specifications
│   ├── weight-analysis.md       ← Detailed weight breakdown
│   ├── autonomy-analysis.md     ← Autonomy calculations
│   └── components-list.md       ← Complete components list
│
├── components/
│   └── components-list.md       ← Full BOM (Bill of Materials)
```

---

## 🔧 Systems Designed

| # | System | Status |
|---|--------|--------|
| 01 | Structure (carbon fiber + TPU) | ✅ Complete |
| 02 | EDF Propulsion (×8) + RCS (×16) | ✅ Complete |
| 03 | Energy (battery + H₂ + solar + electrolyzer) | ✅ Complete |
| 04 | AI Computing (Jetson Orin + STM32) | ✅ Complete |
| 05 | Opening/Closing (pneumatic) | ✅ Complete |
| 06 | Cooling (liquid + fans) | ✅ Complete |
| 07 | Landing (EDF gradual + TPU dampers) | ✅ Complete |
| 08 | Emergency (auto-landing + water sprinklers) | ✅ Complete |
| 09 | Joints (passive arms + motorized legs) | ✅ Complete |
| 10 | Communications (4G + WiFi + LoRa + BT) | ✅ Complete |
| 11 | Pilot Protection (F1-style suit + D30) | ✅ Complete |
| 12 | Helmet (UHMWPE + HUD + O₂ + 4K cam) | ✅ Complete |

---

## ⚖️ Weight Breakdown

| System | Weight |
|--------|--------|
| Structure | 6.64 kg |
| EDF + RCS Propulsion | 4.43 kg |
| Energy System | 13.80 kg |
| Computing System | 0.85 kg |
| Pneumatic System | 1.90 kg |
| Cooling System | 1.65 kg |
| Landing System | 1.13 kg |
| Emergency System | 0.53 kg |
| Joints | 3.16 kg |
| Communications | 0.16 kg |
| Pilot Protection | 1.55 kg |
| Helmet | 1.92 kg |
| **TOTAL (suit only)** | **37.72 kg** |

---

## 🚀 Flight Autonomy

| Flight Mode | Speed | Endurance |
|-------------|-------|-----------|
| Slow flight | 50 km/h | ~2h 45min |
| Normal flight | 70 km/h | ~1h 15min |
| Fast flight | 90 km/h | ~1h 07min |
| Static hover | 0 km/h | ~1h 52min |

---

## 🛡️ Safety Features

- **Auto-landing** if EDF failure detected
- **Water sprinkler** system for fire/short circuit
- **Automatic energy cutoff** per zone
- **D30 spine protector** for impact absorption
- **Emergency SMS** via 4G to contact
- **HUD alerts** for all critical parameters
- **15% battery reserve** enforced automatically

---

## 🧩 Key Technologies

- **EDF Motors**: Brushless electric ducted fans (no exposed propellers)
- **RCS**: N₂/H₂ gas thrusters for millisecond directional control
- **Solid-state battery**: 20 kWh, less degradation than Li-ion
- **Electrolyzer**: Generates H₂ + O₂ from water using solar power
- **Aerogel**: Thermal insulation between EDF and pilot
- **D30**: Smart impact material (rigid on impact, flexible normally)
- **UHMWPE**: Ultra-high-molecular-weight polyethylene for helmet
- **Waveguide HUD**: Holographic heads-up display
- **Jetson Orin**: AI computer for real-time flight coordination
- **CAN Bus**: Aeronautical communication protocol between components

---

## ⚠️ Disclaimer

> This is a **conceptual engineering design project** for educational and research purposes.
> Building and flying a personal flight suit requires regulatory approval,
> professional engineering, and extensive safety testing.
> The authors do not encourage unauthorized flight activities.

---

## 📄 License

MIT License — Open source, free to use and modify with attribution.

---

## 👤 Author
