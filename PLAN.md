# btaudio — As-Built Design (rev 1)

Bluetooth headphone adapter. Phone pairs over BT → EWM104-BT5125 (QCC5125) → I2S → PCM5102A DAC → TPA6132A2 headphone amp → solder pads for the headphone cable.

This file describes the board **as built and ordered** (KiCad project in `btaudio/`, production files in `btaudio/production/`).
The original design plan has been replaced. Differences from the plan are listed at the end.
Bring-up results: `btaudio/BRINGUP_TESTPLAN.md`.

---

## Board

- 4 layers (F.Cu, In1.Cu, In2.Cu, B.Cu), 51 × 22 mm
- Single schematic sheet (`btaudio/btaudio.kicad_sch`)

## Parts

| Ref | Part | Footprint | Role |
|-----|------|-----------|------|
| U1 | EBYTE EWM104-BT5125(I2S) | stamp hole, 54 pins | BT 5.1 receiver, should be I2S master |
| U2 | TI PCM5102AQPWRQ1 | TSSOP-20 | I2S DAC |
| U3 | TI TPA6132A2RTET | WQFN-16 3×3 | DirectPath (capless) headphone amp |
| U5 | Microchip MCP1700-3302 | SOT-23 | VBAT → 3.3 V LDO |
| J2 | USB-C receptacle, USB 2.0, 16 pin (HRO TYPE-C-31-M-12) | SMD | 5 V input + USB D+/D− to module |
| J6 | 1×02 pin header | 2.54 mm | LiPo battery (VBAT, GND) |
| J1 | 1×04 pin header "BTNS" | 2.54 mm | External buttons: GND, PIO[2], PIO[3], PIO[4] |
| J3 | Solder pads "Audio" (aux-pads) | custom | Headphone cable: sleeve, R, L |
| AE2 | IPEX / U.FL plug (A-1JB) | SMD | External 2.4 GHz antenna |
| SW1 | Tactile switch TS-1088 "POWER_SW" | SMD | VBAT → SYS_CTRL (power on) |
| SW6 | 2-pad footprint "SOFT RESET" (solder jumper, fitted with a pushbutton) | SMD | RST/PIO[1] → GND |
| JP1, JP2 | 3-pad solder jumpers GAIN0 / GAIN1 | SMD | TPA6132A2 gain select |
| D4, D5 | LED 0805 | SMD | Status LEDs on AIO[0] / AIO[1] |
| NT1 | Net tie | SMD | Joins SGND_TRACE (headphone sleeve) to GND |

Passives: 0805 caps and resistors, 1206 for 10 µF, 0402 for the RF match. Full list: `btaudio/btaudio.csv`, interactive BOM: `btaudio/bom/ibom.html`.

---

## Power

```
USB-C VBUS ──► VIN ──► U1 VCHG (pin 10) + VCHG_SENSE (pin 11)    [module's internal charger]
                │
               C7 1µF

LiPo (J6) ──► VBAT ──► U1 VBAT (pin 14) + VBAT_SENSE (pin 7)
                │      SW1 (power button) → U1 SYS_CTRL (pin 13)
                │      R14/R15 → LEDs
                └────► U5 MCP1700 ──► 3V3 ──► U1 VDD_PADS1 (23), VDD_PADS3_7 (24)
                                         ──► U2 CPVDD (1), AVDD (8), DVDD (20), XSMT (17)
                                         ──► U3 VDD (14)
```

- USB-C: CC1 and CC2 each have 5.1 kΩ to GND (R4, R5). D+/D− go straight to the module's USB (pins 8, 9).
- Decoupling:
  - VBAT: C4 1 µF, C8 100 nF, C11 10 µF.
  - 3V3: C5 1 µF, C13/C14/C24 100 nF, C25/C30/C31 10 µF, C34 2.2 µF.
- U1 pin 22 (1V8 output) is not connected. CHG_EXT (pin 12) is not connected.

> **Known limitation:** the LDO is fed from VBAT only. With USB but no battery, VBAT stays near 0 V, so 3V3 is off:
> VDD_PADS, the DAC and the amp are unpowered while the module core runs from VCHG. **The board only works with a battery,
> or a supply on J6.**

---

## I2S

| U1 pin | Signal | U2 pin |
|---|---|---|
| 3 | I2S_SDATA | 14 DIN |
| 4 | I2S_LRCK | 15 LRCK |
| 5 | I2S_SCK (bit clock) | 13 BCK |
| 6 | I2S_MCLK | not connected |

PCM5102A SCK (pin 12) is tied to GND, so the DAC derives its system clock from BCK with its internal PLL.
BCK must be 32, 48 or 64 × fs. The PCM5102A is slave-only, so the module must be the I2S master.

## DAC — PCM5102A (U2)

| Pin | Name | Connection |
|---|---|---|
| 1 / 8 / 20 | CPVDD / AVDD / DVDD | 3V3 |
| 2, 4 | CAPP, CAPM | C15 2.2 µF flying cap |
| 5 | VNEG | C16 2.2 µF to GND |
| 6 / 7 | OUTL / OUTR | R10 / R11 470 Ω → C28 / C29 2.2 nF to GND (output RC filter) |
| 10 | DEMP | GND (no de-emphasis) |
| 11 | FLT | GND (normal-latency filter) |
| 12 | SCK | GND (PLL from BCK) |
| 16 | FMT | GND (I2S format) |
| 17 | XSMT | 3V3 (unmuted) |
| 18 | LDOO | C26 100 nF + C27 10 µF to GND |

## Headphone amp — TPA6132A2 (U3)

```
PCM OUTL ─[470Ω]─┬─[C21 1µF]─► INL− (1)     INL+ (2) ── GND
                C28 2.2nF
PCM OUTR ─[470Ω]─┬─[C22 1µF]─► INR− (4)     INR+ (3) ── GND
                C29 2.2nF

OUTL (16) ──► J3 pin 3 (L)
OUTR (5)  ──► J3 pin 2 (R)
SGND (15) ──► J3 pin 1 (sleeve) ──[NT1]── GND
```

- The signal goes into the inverting inputs; both channels are inverted equally.
- Charge pump: C23 1 µF (CPP–CPN), C32 2.2 µF (HPVDD), C33 1 µF (HPVSS).
- **EN (13)** ← U1 PIO[20] (pin 54, "AMP_EN"), with R12 10 kΩ pull-down. The amp only runs when the firmware drives PIO[20] high.
- **Gain** (JP1 = G0, JP2 = G1; each jumper connects its pin to 3V3 or GND):

| G1 | G0 | Gain |
|---|---|---|
| 0 | 0 | −6 dB (as built: both to GND) |
| 0 | 1 | 0 dB |
| 1 | 0 | 3 dB |
| 1 | 1 | 6 dB |

At 3.3 V the output swing is about 1 Vrms. With the PCM5102A at 2.1 Vrms full scale, 0 dB or more clips at full volume.

---

## Control

| U1 pin | Function | Circuit |
|---|---|---|
| 13 SYS_CTRL | Power on | SW1 to VBAT (momentary; never tie permanently to VBAT) |
| 32 RST/PIO[1] | Reset | SW6 to GND |
| 31 PIO[2] | Play / Vol+ | J1 pin 2 (button to GND, external) |
| 26 PIO[3] | Pause / Vol− | J1 pin 3 |
| 25 PIO[4] | Prev / pairing | J1 pin 4 |
| 28 PIO[5] | Next / disconnect | **not connected** |
| 54 PIO[20] | Amp enable | U3 EN + R12 10 k pull-down |
| 16 AIO[0]/LED[0] | LED | D4 + R14 1 kΩ from VBAT |
| 17 AIO[1]/LED[1] | LED | D5 + R15 1 kΩ from VBAT |

Not connected: MIC inputs and MIC_BIAS (39–43), SPK outputs (34–37), SPDIF_IN, all other PIO/AIO.
The LEDs are powered from VBAT, so they cannot light without a battery.

## Antenna

U1 ANT (pin 46) → L1 0 Ω (series, 0402) → AE2 IPEX connector. C17 / C18 (0402) are left unpopulated as shunt positions,
for π-matching if needed. Bluetooth range was fine with an external antenna.

## GND

U1 pins 15, 21, 38, 44, 45, 47.

---

## Bring-up status (see `btaudio/BRINGUP_TESTPLAN.md`)

- Carrier board verified OK: power, SYS_CTRL, RST, no shorts or bridges.
- Module #3 boots, pairs and streams. **Audio appears on the module's analog SPK pins (34–37), while the I2S pins stay
  high-impedance.** The module behaves like the (DAC) firmware despite its "Version: I" label. Report to EBYTE:
  `btaudio/EBYTE_REPORT.md`.
- Modules #1 and #2 were bricked by connection attempts with the Qualcomm tools through Windows VM USB passthrough.
  The on-module flash is a Macronix MX25U3232F (1.8 V) and needs a 1.8 V programmer to recover.

## Changes from the original plan

| Original plan | As built |
|---|---|
| Johanson ceramic chip antenna + π network | IPEX (U.FL) connector + 0 Ω / NC match |
| 4 onboard tactile buttons with pull-ups | 1×04 header to external buttons (PIO2–4), PIO5 not connected |
| SYS_CTRL RC/MOSFET delay circuit | Momentary button SW1 to VBAT |
| 3.5 mm jack (PJ-320) | Solder pads J3 |
| Battery connector | 1×02 pin header J6 |
| TPA6132A2 gain 6/12/18/24 dB | Wrong values: real gains are −6/0/3/6 dB; built at −6 dB |
| MCLK routed to DAC | MCLK not connected, DAC SCK to GND (PLL mode) |
| Amp EN pull-up | 10 k pull-down; enabled only by PIO[20] |

## Ideas for rev 2

- Power path: feed the LDO from VBAT **or** VIN, so the board works on USB without a battery.
- Break out SPK pins 34–37 to pads, as a fallback for modules with DAC firmware.
- Optional MCLK route (pin 6 → PCM5102A SCK) via a 0 Ω resistor, as on the EBYTE EWT104-DA10 dev board.
- Test pads for 1V8 (pin 22), I2S, AMP_EN. Add a 0 Ω / jumper on AMP_EN to force the amp on.
- Connect PIO[5] to the button header.
