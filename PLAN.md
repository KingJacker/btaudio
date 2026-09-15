# btaudio Schematic Plan

Bluetooth headphone adapter. Phone pairs over BT → QCC5125 decodes → I2S → PCM5102A DAC → TPA6132A2 headphone amp → 3.5mm jack.

---

## Parts

| Ref | Part | Role |
|-----|------|------|
| U1 | EWM104-BT5125 (I2S variant) | BT5.1 receiver, I2S master |
| U2 | PCM5102AQPWRQ1 | I2S DAC, stereo audio out |
| U3 | TPA6132A2RTET | DirectPath headphone amp |
| U4 | 3.3V LDO (e.g. MCP1700-3302E) | Vbat → 3.3V |
| J1 | 3.5mm TRS jack | Headphone output |
| J2 | Battery connector | LiPo cell (external) |
| — | Charging board (MCP73871) | Already designed separately |

---

## Power Architecture

```
USB-C ──► Vin (5V) ──► MCP73871 charging board ──► Vbat (3.7–4.2V LiPo)
                │                                         │
                │                                         ▼
                │                                    LDO (U4)
                │                                         │
                │                                         ▼
                │                                      3V3 rail
                │
                └──► U1 VCHG (pin 10)   [charger input, 4–6.5V]

Vbat ──► U1 VBAT (pin 14)              [module battery supply]
3V3  ──► U1 VDD_PADS1 (pin 23)         [PIO bank 1 logic voltage]
3V3  ──► U1 VDD_PADS3_7 (pin 24)       [PIO bank 3–7 logic voltage]
3V3  ──► U2 AVDD, DVDD, CPVDD
3V3  ──► U3 VDD, HPVDD
```

**Decoupling:** 100nF + 10µF on each supply rail at each IC.

**Note:** U1 pin 22 (1V8 output) — leave available as test point; not used to power VDD_PADS (keep both banks at 3.3V so I2S signals are 3.3V compatible with PCM5102A).

---

## I2S Signal Chain

```
U1 EWM104-BT5125          U2 PCM5102A
─────────────────          ───────────
I2S_SCK   (pin 5)  ──────► BCK  (pin 13)   bit clock
I2S_LRCK  (pin 4)  ──────► LRCK (pin 15)   LR clock
I2S_SDATA (pin 3)  ──────► DIN  (pin 14)   data
I2S_MCLK  (pin 6)  ──────► SCK  (pin 12)   system clock
```

---

## Audio Chain

```
U2 PCM5102A                          U3 TPA6132A2
───────────                          ────────────
OUTL (pin 6) ──[1µF]──────────────► INL+ (pin 2)
                                     INL- (pin 1) ── GND

OUTR (pin 7) ──[1µF]──────────────► INR+ (pin 3)
                                     INR- (pin 4) ── GND

                         U3 TPA6132A2              J1 3.5mm
                         ────────────              ────────
                         OUTL (pin 16) ───────────► L
                         OUTR (pin 5)  ───────────► R
                         HPVSS/PGND/SGND/EP ──────► GND sleeve
```

AC coupling caps (1µF) between PCM5102A and TPA6132A2 needed because PCM5102A uses internal charge pump; output may not be exactly 0V DC.

**TPA6132A2 gain:** G0 (pin 6) and G1 (pin 7) set gain:
- 00 = 6dB, 01 = 12dB, 10 = 18dB, 11 = 24dB
- Start with 01 (12dB). G0 and G1 can be jumper-selectable or tied.

**TPA6132A2 enable:** EN (pin 13) — pull high (3V3) through resistor. Could tie to a PIO for soft mute.

**PCM5102A control pins:**
| Pin | Name | Connect |
|-----|------|---------|
| 10 | DEMP | GND (no de-emphasis) |
| 11 | FLT | GND (normal latency filter) |
| 16 | FMT | GND (I2S format, left-justified on high) |
| 17 | XSMT | 3V3 (unmuted); or drive from PIO for soft-mute |
| 18 | LDOO | 100nF to GND (internal LDO bypass) |

---

## SYS_CTRL Circuit (U1 pin 13)

Datasheet warning: cannot pull directly to VBAT. Need delay circuit after power-on.

```
Vbat ──[R 100k]──┬── MOSFET gate
                 │
                [C 10µF]
                 │
                GND

MOSFET drain → SYS_CTRL (pin 13)
MOSFET source → GND
```

RC time constant ~1s delay before SYS_CTRL asserts. Use N-channel MOSFET (e.g. 2N7002).
Add a parallel tactile button (RESET# / manual power-on) from SYS_CTRL to GND.

---

## PIO / Button Assignments (default firmware)

| PIO | Pin | Function | Circuit |
|-----|-----|----------|---------|
| PIO[2] | 31 | Play / Vol+ | Tactile SW to GND, 10k pull-up to 3V3 |
| PIO[3] | 26 | Pause / Vol- | Tactile SW to GND, 10k pull-up to 3V3 |
| PIO[4] | 25 | Prev / BT pair | Tactile SW to GND, 10k pull-up to 3V3 |
| PIO[5] | 28 | Next / BT disc | Tactile SW to GND, 10k pull-up to 3V3 |
| PIO[20] | 54 | Amp enable | Tie to TPA6132A2 EN (via 10k) |
| PIO[21] | 53 | LED indicator | LED + 330R to GND |
| PIO[52] | 50 | LED indicator | LED + 330R to GND |

---

## LED Assignments

| Pin | Name | Function |
|-----|------|----------|
| 16 | AIO[0]/LED[0] | Status LED (power on, pairing, etc.) |
| 17 | AIO[1]/LED[1] | Second LED (optional) |

Open-drain outputs — connect LED anode to 3V3 through resistor, cathode to pin.

---

## Antenna

Pin 46 (ANT): 50Ω impedance. Either:
- PCB trace antenna (already on module — no external connection needed for onboard antenna)
- Or route to SMA connector through 50Ω trace for external antenna

Check module variant: EWM104-BT5125(I2S) has PCB trace antenna built in. If so, pin 46 may be NC or connect to a test point only.

---

## USB (pins 8, 9)

USB_DN (pin 8), USB_DP (pin 9): full-speed USB for firmware/configuration.
- Optional: break out to USB-C connector for debug/config access
- Not required for normal operation

---

## GND Pins

Pins 15, 21, 38, 44, 45, 47 — all connect to GND plane.

---

## Schematic Sheets (proposed)

| Sheet | Contents |
|-------|----------|
| Root | Block diagram, power connectors, inter-sheet refs |
| Power | LDO, decoupling, power rails, battery interface |
| BT Module | U1 with all pin connections |
| Audio | U2 (PCM5102A) + U3 (TPA6132A2) + J1 |
| Control | Buttons, LEDs, SYS_CTRL delay circuit |

---

## Finalized Decisions

| # | Decision |
|---|----------|
| 1 | **Single sheet** — enlarge sheet size later as needed |
| 2 | **MCP1700-3302E** LDO (low Iq ~1.6µA, good for battery life, SOT-23) |
| 3 | **USB debug exposed** — USB_DN/DP break out to USB-C or micro-USB connector |
| 4 | **TPA6132A2 gain: solder-tie G0/G1** — add schematic note "resolder to change gain" |
| 5 | **MIC inputs: all NC** — headphone-only use case |
| 6 | **SMD ceramic chip antenna** — Johanson 0433AT62A0020E (2.4GHz, 50Ω, 3.2×1.6mm) |

---

## Antenna Detail

Module ANT pin (46) is the RF port — module has no built-in antenna.

```
U1 ANT (pin 46) ──[50Ω trace]──► π matching network ──► Johanson 0433AT62A0020E
```

π matching network (tune at layout stage based on PCB stackup):
- Series inductor + shunt caps either side (typical: 2.2nH series, 1pF shunt)
- Leave footprints populated with 0Ω/DNP for tuning
- Ground clearance required under antenna (no copper pour under chip antenna element)

---

## Schematic Notes to Add

- Near TPA6132A2 gain pins: *"G0/G1 soldered for 12dB gain. Reflow to change: 00=6dB 01=12dB 10=18dB 11=24dB"*
- Near SYS_CTRL: *"RC delay ~1s. Do not pull directly to VBAT."*
- Near MIC pins: *"MIC1/MIC2 inputs NC — headphone-only build"*
- Near antenna: *"Tune π network for PCB stackup. No copper under antenna element."*
