# btaudio — Bring-up / Debug Test Plan

Goal: find out whether the "bootloop" is a **power/hardware** problem or a **firmware/config** problem,
and why audio was **very quiet** — before soldering in the last working QCC module.

Phases are ordered from harmless to riskier. Fill in the `Result` column and send it back.
**Nothing in this plan writes to any module.** Do not connect any module to a config tool or a VM.

---

## Equipment

- Multimeter (DC V, resistance, diode mode, DC current)
- Oscilloscope (2+ channels; ≥ 20 MHz is enough, ≥ 50 MHz nicer for BCK)
- Bench supply with current limit (or charged LiPo + DMM in series for current)
- 32 Ω resistors ×2 (dummy load) or the actual headphones
- Phone with a **1 kHz sine, 0 dBFS** test file (lossless if possible)
- A **native** Linux machine (no VM passthrough) for `lsusb` / `dmesg`
- Fine wire for a probe lead on U1 pad 22 (1V8)

## Probe points (reference)

| Name | Where to probe | Notes |
|---|---|---|
| VBAT | J6 pin 1 / C11 | Battery rail, feeds U1 pins 7+14, LDO U5, LED resistors |
| VIN | J2 VBUS / U1 pad 10–11 | USB 5 V → VCHG + VCHG_SENSE |
| 3V3 | C13 / C14 / C24 | LDO output → VDD_PADS, DAC, amp |
| 1V8 | U1 pad 22 (solder a wire) | Internal SMPS output — **best "is the chip alive / resetting" indicator** |
| RST | SW6 pad (U1 pad 32) | PIO[1]/RST, should idle high |
| SYS_CTRL | SW1 pad (U1 pad 13) | High only while SW1 pressed |
| LED0 / LED1 | D4 / D5 cathode side (U1 16 / 17) | Open-drain, low = LED on |
| AMP_EN | R12 (U1 pad 54 → U3 EN) | 10 k pull-down; must go high for amp to run |
| I2S BCK | U2 pin 13 | |
| I2S DATA | U2 pin 14 | |
| I2S LRCK | U2 pin 15 | |
| DAC out L/R | C28 / C29 (after 470 Ω) | PCM5102A line out, ~2.1 Vrms full scale, centered 0 V |
| HP out L/R | J3 pins 3 / 2 | TPA6132A2 output, centered 0 V; sleeve = J3 pin 1 |

**Scope ground always to board GND** (e.g. J6 pin 2 or USB shield) — never clip the probe ground onto a headphone output.

---

## Phase 0 — Unpowered checks (board with the bricked module still on it)

| # | Check | Expected | Result |
|---|---|---|---|
| 0.1 | Visual: bridges at U1 pads 13/14 (SYS_CTRL–VBAT) | none | |
| 0.2 | Visual: bridges at U1 pads 22/23 (1V8–VDD_PADS1) | none | |
| 0.3 | Visual: bridges at U1 pads 10/11/12, 8/9 | none | |
| 0.4 | SW6 (soft reset jumper) open? | open | |
| 0.5 | JP1 (GAIN0) state: open / to 3V3 / to GND | bridged one way | |
| 0.6 | JP2 (GAIN1) state: open / to 3V3 / to GND | bridged one way | |
| 0.7 | Resistance VIN → GND (both polarities) | no short (> few kΩ) | |
| 0.8 | Resistance VBAT → GND | no short | |
| 0.9 | Resistance 3V3 → GND | no short | |
| 0.10 | Resistance 1V8 (pad 22) → GND | no short | |
| 0.11 | Resistance RST (pad 32) → GND | not 0 Ω | |

Gain reference (TPA6132A2, G1 G0): `00 = –6 dB`, `01 = 0 dB`, `10 = 3 dB`, `11 = 6 dB`.
(Verified against datasheet Table 1 — PLAN.md's 6/12/18/24 dB is wrong.)

---

## Phase 1 — Bench supply on VBAT only (no USB)

Setup: supply → J6, **3.8 V, current limit 150 mA**. USB unplugged.
Scope: CH1 = 1V8 (pad 22), CH2 = VBAT. Timebase ~200 ms/div – 1 s/div, roll mode if available.

| # | Check | Expected | Result |
|---|---|---|---|
| 1.1 | Supply current before pressing SW1 | very low (µA – few mA) | |
| 1.2 | 3V3 voltage | 3.30 V ± 2 % | |
| 1.3 | 1V8 before SW1 | 0 V (module off) | |
| 1.4 | Press SW1 (~1 s) — what happens to 1V8? | rises to ~1.8 V and **stays** | |
| 1.5 | Supply current after boot (watch 30 s) | 2–25 mA, no repeating pattern | |
| 1.6 | Does 1V8 / current drop periodically? Period? | no | |
| 1.7 | RST (pad 32) during boot — any low pulses? | stays high | |
| 1.8 | LED pattern (D4/D5): describe | pairing blink | |
| 1.9 | Visible on phone as BT device? | yes | |
| 1.10 | If visible: pair + connect succeeds? | yes | |

If it boot-loops here: capture one full cycle on the scope (1V8 + VBAT) and note the period.

---

## Phase 2 — USB power only, no battery / no bench supply

Setup: J6 disconnected. USB-C from a **wall charger** (not a PC) first.
Scope: CH1 = VBAT, CH2 = 1V8. Same slow timebase.

| # | Check | Expected | Result |
|---|---|---|---|
| 2.1 | VIN at U1 pad 10 | 4.75–5.25 V | |
| 2.2 | VBAT: DC level and behaviour (stable / sawtooth / pulsing) | ? (this is the suspect) | |
| 2.3 | 1V8: stable or dropping periodically? | | |
| 2.4 | 3V3: stable? (it is fed from VBAT) | | |
| 2.5 | LED pattern | | |
| 2.6 | Visible on phone? | | |

Then the same with USB to a **native** Linux PC (not passed into a VM):

```bash
sudo dmesg -w
```

```bash
lsusb
```

| # | Check | Result |
|---|---|---|
| 2.7 | `dmesg`: does the device connect/disconnect repeatedly? Paste a few lines | |
| 2.8 | `lsusb` line for the module (VID:PID) | |
| 2.9 | `lsusb -v -d <VID>:<PID>` — paste full output (to a file) | |

---

## Phase 3 — USB + bench supply on VBAT (normal "charging" situation)

Setup: supply on J6 at 3.8 V / 150 mA limit **and** USB from a wall charger.

| # | Check | Expected | Result |
|---|---|---|---|
| 3.1 | 1V8 stable? | yes | |
| 3.2 | Supply current (may go negative/zero if charger feeds VBAT) | | |
| 3.3 | Boots / visible on phone? | yes | |

### Interpreting Phases 1–3

| Phase 1 (VBAT only) | Phase 2 (USB only) | Meaning |
|---|---|---|
| stable | loops | **Power problem** — charger-only VBAT is unstable. Module is probably *not* bricked. Always run with battery. |
| loops | loops | Firmware/config problem (or damaged module) → flash dump route |
| doesn't boot at all | doesn't boot | Check SYS_CTRL/RST behaviour, 1V8, solder joints |

---

## Phase 4 — Audio path (only on a module that boots and connects)

Setup: bench supply 3.8 V on J6 (USB optional, wall charger only).
Phone: play **1 kHz sine at 0 dBFS**, phone volume **max**, also press module Vol+ (J1) several times.
Load: 32 Ω from each HP output to sleeve (J3 pin 1), or the headphones plugged in.

| # | Check | Expected | Result |
|---|---|---|---|
| 4.1 | LRCK frequency (U2 pin 15) | 44.1 or 48 kHz | |
| 4.2 | BCK frequency (U2 pin 13) | 32/48/64 × LRCK (e.g. 3.072 MHz @ 48 k) | |
| 4.3 | BCK/LRCK/DATA high level | ~3.3 V | |
| 4.4 | DATA (U2 pin 14) toggling while playing? | yes | |
| 4.5 | AMP_EN (R12) idle vs playing | high while playing | |
| 4.6 | DAC out L / R at C28 / C29 (Vrms, DC offset) | up to ~2.1 Vrms, ~0 V DC | |
| 4.7 | HP out L / R at J3, loaded (Vrms) | ~gain × input, **≤ ~1 Vrms** (3.3 V supply; clips above) | |
| 4.8 | HP out waveform clean sine or clipped/distorted? | clean (or clipped at 0 dB gain + full scale) | |
| 4.9 | HP out DC offset | ~0 V (DirectPath) | |
| 4.10 | U3 HPVSS (C33) | ≈ –VDD (negative charge pump running) | |

Quick diagnosis:
- 4.5 low while playing → amp in shutdown, the faint audio is leakage → firmware PIO[20] config, or bodge EN to 3V3.
- 4.6 low → volume / I2S format / DAC issue (look at 4.1–4.4).
- 4.6 fine but 4.7 low → amp issue (gain jumpers 0.5/0.6, EN, HPVSS 4.10, SGND net tie).

---

## Phase 5 — Swapping in module #3 (only after Phases 0–3 are understood)

1. Remove the old module (hot air), clean pads, inspect for lifted pads.
2. With **no module**: repeat 0.7–0.9, bench supply on J6 → check 3V3, record idle current, pads 23/24 = 3.3 V, pad 13 = 0 V (VBAT only while SW1 pressed), pad 32 not shorted.
3. Solder module #3 (tack corners → align → iron + flux per pad). Inspect bridges (0.1–0.3).
4. Power **only via bench supply on J6** first → repeat Phase 1, then Phase 4.
5. **No PC / config tool on this module** until we have a flash dump strategy.

---

## Things to send back

- The filled tables above
- Scope screenshots: Phase 1 boot (1V8 + VBAT), Phase 2 VBAT behaviour, Phase 4 DAC out + HP out
- `dmesg` excerpt and `lsusb -v` output
- Which config tool was used and what was changed when the modules bricked
- The flash chip marking, if you open a bricked module's shield

---

## Results log

### Phase 0 — 2026-11-25 (board with bricked module #2 fitted)

- Gain: JP1 (G0) and JP2 (G1) both to GND → **–6 dB** (lowest; not enough to explain "very quiet")
- SW6 is fitted as a pushbutton (normally open)
- 3V3→GND: kΩ range · VBAT→GND: kΩ range · VIN→GND: MΩ range → no rail shorts
- Pad pairs: 13/14 OL · 9/10, 7/8, 8/9, 11/12, 31/32, 3/4/5 MΩ · 21/22, 22/23, 53/54 kΩ (through IC / R12, not bridges)
- ANT (46)→GND MΩ; BT RF previously confirmed working (LED behaviour, connection)
- 1V8 (pad 22) not routed on PCB; →GND MΩ · RST (pad 32)→GND kΩ (compare against an unused PIO pad)
- **Verdict: no solder bridges or shorts. Phase 0 pass.**
