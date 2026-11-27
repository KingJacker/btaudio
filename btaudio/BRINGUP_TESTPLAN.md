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

### Phase 1 (partial, multimeter only — no scope) — 2026-11-25

- Bench supply on J6 (VBAT), no USB
- At power-on: brief ~7 mV blip (on 1V8 pad?), supply current ~5 mA for ~1 s, then ~0
- Pressing SW1: no change
- Interpretation (tentative): chip attempts boot once, fails or goes dormant; 1V8 never comes up.
  Consistent with corrupted flash: on USB, VCHG presence would retrigger boot → "bootloop".
- Open: 3V3 level, SYS_CTRL (pad 13) voltage while SW1 held, RST level, long-press / held-at-power-on test,
  meter range used for current (µA range burden voltage can brown out boot).
- Follow-up: 3V3 = 3.3 V ✔ · SYS_CTRL (SW1 side) = 3.8 V while pressed, 0 V released ✔ · RST = 3.3 V ✔
- SW1 held 10 s: current stays ~0 · SW1 held during power-up: no change · 1V8 never rises (DMM)
- **Verdict: carrier board OK (power, SYS_CTRL, RST). Module does not respond to SYS_CTRL on VBAT-only.**
  Initial ~5 mA/1 s is likely PCM5102A startup → standby (no clocks), not the module.
- Next: retry at VBAT 4.1 V (battery-threshold config?), DMM MIN/MAX on 1V8; then Phase 2 (USB, `dmesg -w`, `lsusb`).
- VBAT = 4.1 V: still no boot, 1V8 ~8 mV blip for ~1 s then 0.

### Phase 2 (partial) — USB only, no battery

- VIN = 5.0 V · **1V8 = 1.8 V (chip alive, powered from VCHG)** · VBAT ≈ 180 mV, slowly decaying (charger not driving VBAT)
- **Key finding:** module silicon/PMU alive → not a hardware-dead module. VBAT-only no-boot points to firmware/config.
- **Design issue:** U5 LDO is fed from VBAT. With USB but no battery, VBAT ≈ 0 → 3V3 ≈ 0 → VDD_PADS1/3_7, DAC, amp
  unpowered while the chip core runs from VCHG. Board effectively requires a battery to function.
- Open: 3V3 on USB-only, 1V8 stability, LED pattern, Phase 3 (USB + battery), `dmesg`/`lsusb` with and without battery.
  Was a battery attached when it worked / during the config session?
- USB only (native Linux, no VM): 3V3 = 0 V · 1V8 steady 1.8 V · LEDs off (expected: LEDs fed from VBAT) · SW1 no effect
- `dmesg -w` / `lsusb`: **module never enumerates** (only internal Goodix reader reset seen). Cable data capability not yet verified.
- User confirms: **battery was connected when the board worked.** USB-only (no battery) is a non-functional state by design.
- Next: verify data cable, Phase 3 (USB + LiPo) with `dmesg -w`/`lsusb`, search `journalctl -k` for historical VID:PID of the module.
- USB-C cable verified with phone (enumerates as 0e8d:2008).

### Phase 3 (partial) — USB + bench supply on VBAT

- 3V3 = 3.3 V · LEDs off · **no USB enumeration** (`dmesg`/`lsusb` show nothing from module)
- Open: 1V8, supply current, SW1 reaction, phone visibility, `journalctl -k` history of the module's VID:PID.

### Conclusion so far (module #2)

Carrier board OK. PMU wakes on VCHG (1V8 present) but application firmware never runs in any power mode
(no LEDs, no USB, no SYS_CTRL response) → consistent with corrupted flash. Recovery only via direct SPI flash access.

Plan: (1) remove #2, open shield, ID + read flash with voltage-correct programmer, check `strings` for encryption;
(2) fit #3 per Phase 5, power from VBAT + SW1 only, no PC; (3) Phase 4 audio tests on #3;
(4) dump #3 flash with programmer → golden image to restore #1/#2.
- Phase 3 complete: 1V8 = 1.8 V · SW1 no effect · PSU current ~5 mA for 1 s then ~0 (module runs from VCHG) · not visible over BT
- **Phase 3 verdict: firmware does not run in any power mode → module #2 recoverable only via direct flash programming.**

### Module #2 opened — 2026-11-25

- Shield removed. Parts: QCC5125 (FE437JL2), 32 MHz crystal, **flash = Macronix MX25U3232F** (32 Mbit, **1.8 V**, WSON-8)
- Programmer must be **1.8 V** (CH341A + 1.8 V level-shifter adapter, or equivalent). 3.3 V will damage the chip.
- WSON-8 pinout: 1 CS# · 2 SO/IO1 · 3 WP#/IO2 · 4 GND · 5 SI/IO0 · 6 SCLK · 7 HOLD#/IO3 · 8 VCC — tie WP#/HOLD# to VCC.
- Plan: desolder flash from #2 → read twice with flashrom → compare sha256 → check `hexdump`/`strings`
  (all FF = erased; readable strings = unencrypted, cloning viable; random = likely encrypted).

### Module #3 fitted — 2026-11-25

- Powered from bench supply on J6 + SW1 (no PC): **LEDs blink, BT pairing works** → board + module #3 OK
- Audio: nothing on output (DMM Hz on audio out shows nothing), nothing audible in headphones
- Next: Phase 4 stage-by-stage with DMM (clock ≈ 1.6 V DC trick): LRCK/BCK/DATA at U2, VNEG/LDOO, DAC out C28/C29,
  AMP_EN (R12), HPVSS (C33), HP out J3. Check module label is (I2S) variant.
  If AMP_EN low: test via 1 kΩ from 3V3 to EN (not a hard short — PIO[20] may be driving low).
- Phase 4 (module #3, DMM): LRCK/BCK/DATA at U2 = mV (no I2S) · DMM Hz mode reads nothing · VNEG = 0 V (DAC in standby, no clocks)
  · LDOO = 1.9 V (DAC powered) · C28/C29 = 0 Vrms · AMP_EN = 0 V · J3 L/R = nothing
- **Verdict: no I2S output from module #3 → everything downstream idle.** Board I2S path previously produced (quiet) audio with module #1.
- Next: confirm phone A2DP "Media audio" active · module label = (I2S) variant? (else test SPK pins 34–37)
  · measure I2S directly at module castellations 3/4/5 while playing · continuity pad 3→U2-14, 4→U2-15, 5→U2-13, 54→R12.
- Module #3 label confirmed **EWM104-BT5125(I2S)** (Ebyte insists package marking "I" = I2S). LED pattern follows play/pause → A2DP streaming works.
- Hypotheses for missing I2S: (a) firmware I2S in **slave** mode (PCM5102A is slave-only → no clocks anywhere),
  (b) bad joint pads 3–5, (c) firmware actually routes to internal DAC (SPK pins 34–37).
- Next: DC at castellations 3–6 while playing · 100 k pull-up test on pad 4/5 (driven-low vs floating input)
  · AC V on 37–36 / 35–34 · continuity 3→U2-14, 4→U2-15, 5→U2-13 · ask Ebyte: master/slave, pins, format, MCLK.
- At module castellations while playing: pads 3/4/5/6 ≈ 50 mV (no activity)
- 100 k pull-up to 3V3 on pad 4 (LRCK): reads **3.0 V → pin is a floating input, not driven**
- **Conclusion (strong): module #3 firmware runs I2S as SLAVE (or I2S not enabled). PCM5102A is slave-only → no clocks → silence.**
- Next: pull-up test on pad 5 (BCK) and pad 3 (DATA) · AC V on SPK 37–36 / 35–34 · optional Pico clock-injection test
  (LRCK 48 kHz / BCK 3.072 MHz into pads 4/5 → DATA should appear if slave).
- Fix options: Ebyte master-mode firmware/config · own config change after 1.8 V flash backup (native Windows, battery attached)
  · HW: external clock master or master-capable DAC (e.g. PCM5122) in next revision.
- Correction (user recollection): module #1 most likely **also had no I2S output** (suspected wrong variant back then);
  the "very quiet audio" observation is unreliable → dropped. The config session that bricked #1/#2 was likely an attempt to fix I2S.
- Working theory: Ebyte (I2S) firmware ships with I2S slave/disabled. Fix requires config/firmware change → **flash backup first**.
- Order: Pico clock-injection test → email Ebyte with measurements → 1.8 V adapter + dump #3 (verify sha256)
  → single config change (I2S master) on native Windows with VBAT supplied. Open: which tool / setting was used in the bricking session.
- Bricking session detail: Qualcomm proprietary tools (several versions) in a Windows VM on Linux; **tools never connected,
  no config was ever changed** → brick caused by the connection attempt itself (re-enumeration under VM passthrough,
  version mismatch, or undefined power state). Unknown which — compare flash dumps of #2 (bricked) vs #3 (good) to find out.
- Likely USB debug disabled in Ebyte production firmware → Ebyte is the primary route for I2S master config / factory image.
- Rule: no Qualcomm tool on module #3 until a verified flash backup exists; then native Windows only, VBAT supplied.

### Ebyte dev board EWT104-DA10 analysis (from parts/EWM104-BT5125-PCB/EWT104-DA10_UserManual_EN_V1.1.pdf)

- I2S DAC (item 22) = **TI PCM5102A** (marking readable in product photo) — same DAC as btaudio. Header: P_VDD, P_MCK, P_BCK, P_DIN, P_SCK, P_VIO, P_GND.
- Headphone amp (item 17) = QFN, header TPA_VDD/TPA_EN → likely TPA6132A2. 3W speaker amp (item 19) SOIC-16 (≈ "ES8405", unclear).
- All peripherals connected via jumper headers; VDD_PADS switchable 3.3 V / 1.8 V; I2S_OUT jack = PCM5102A output.
- Manual: (I2S) module works out of the box via I2S_OUT → **factory I2S firmware must be I2S master** (PCM5102A is slave-only).
- Dev board routes module MCLK (pin 6) to DAC; btaudio leaves MCLK NC with PCM5102A SCK → GND (valid: PLL from BCK).
- **Revised theory:** module #3 likely carries (DAC) firmware despite (I2S) label → I2S pins unused.

### Status at end of 2026-11-25

- Ebyte insists module is (I2S). (Decisive test since done — see Phase 6.) Previously pending: **AC V on SPK pins 37–36 / 35–34 while playing 1 kHz.**
  - Signal present → wrong (DAC) firmware → send evidence to Ebyte, request replacement or I2S firmware image.
  - No signal → not simply wrong firmware → Pico clock-injection test, flash dump.
- Before reordering: prefer EWT104-DA10 dev board + (I2S) module from official Ebyte store as known-good reference.
- Order 1.8 V SPI flash adapter (needed for backup/forensics either way).

---

## HANDOFF SUMMARY (read this first when resuming)

**Hardware status**
- Carrier board verified OK: rails, SYS_CTRL (SW1 → VBAT), RST, no bridges/shorts.
- Board needs a battery/VBAT supply: U5 LDO is fed from VBAT, so USB-only → 3V3 = 0 V (I/O, DAC, amp unpowered).
- Module #1, #2: bricked during attempts to connect Qualcomm tools via Windows VM USB passthrough (tools never connected,
  nothing configured). PMU wakes on VCHG (1V8 present) but firmware never runs, no USB enumeration. #2 removed, shield off.
- Module #3: fitted, boots on VBAT + SW1, pairs, LED follows play/pause. **No I2S output**: pads 3/4/5/6 idle (~50 mV),
  pad 4 floats to 3 V with 100 k pull-up (not driven). DAC idle (VNEG 0 V), AMP_EN 0 V, no audio.
- Module flash: Macronix **MX25U3232F, 32 Mbit, 1.8 V**, small leadless package (WSON/USON — measure size before buying socket).

**Leading theory**
- Ebyte dev board (EWT104-DA10) uses the same PCM5102A (slave-only) and the (I2S) module works there out of the box
  → factory I2S firmware should be I2S master. Module #3 not driving I2S → probably **(DAC) firmware despite (I2S) label**.
  Ebyte insists it is (I2S).

**Next steps (in order)**
1. **Decisive test:** 1 kHz tone, full volume, AC V across module pins 37–36 (L) and 35–34 (R).
   Signal → wrong firmware → send evidence (photo of meter + label) to Ebyte, ask for replacement / I2S firmware image.
   No signal → Pico clock-injection test (LRCK 48 kHz, BCK 3.072 MHz into pads 4/5; watch pad 3 DATA).
2. **Buy programmer:** CH341A kit **with the 1.8 V adapter** (check the selected variant actually includes it).
   SOIC clip will NOT fit the leadless flash → desolder chip onto a breakout or use a matching WSON/USON pogo socket.
   Use `flashrom -p ch341a_spi`; read ≥2×, compare sha256. Practise on #2 first, then back up #3.
3. Analyse dumps: all FF = erased; readable `strings` = unencrypted (cloning viable); random = likely encrypted.
4. If reordering: prefer EWT104-DA10 dev board + (I2S) module from official Ebyte store as known-good reference.
5. **Never** connect Qualcomm tools to #3 before a verified flash backup; then native Windows only, VBAT supplied, no VM.

**Doc errors to fix later**
- PLAN.md TPA6132A2 gain table is wrong: real gains are –6/0/3/6 dB (G1G0 = 00/01/10/11). Board has both gain pins → GND (–6 dB).
- PLAN.md/DOC.md describe chip antenna, onboard buttons and PJ-320 jack; built board uses IPEX, button header, aux pads.
- Repo housekeeping: done (lock file and stray log removed, added to .gitignore).

**Design notes for a possible rev 2**
- Feed LDO from VBAT *or* VIN (power path) so the board works on USB without battery.
- Route module MCLK (pin 6) to PCM5102A SCK as on Ebyte dev board (optional, with 0 Ω / jumper).
- Add test pads: 1V8 (pad 22), I2S lines, AMP_EN; add jumper/0 Ω on AMP_EN; footprint for SPI flash access is not possible (inside module).
- Consider break-out of SPK pins 34–37 to pads as fallback for DAC-firmware modules.
- 2026-11-26: AVR Dragon on hand — **not usable** as SPI flash programmer (AVR-only protocols, no flashrom support).
  Options: CH341A + 1.8 V adapter kit (preferred), or Raspberry Pi `linux_spidev` + 1.8 V level shifter (e.g. TXS0108E).

---

## Phase 6 — Scope evidence for Ebyte report (module #3)

Setup: bench supply J6 3.8 V, SW1 pressed, phone connected, **1 kHz sine 0 dBFS**, phone volume max. Probe GND = J6 pin 2.
**Screenshot every capture.**

| # | What | Where | Scope | Proves | Result |
|---|---|---|---|---|---|
| 6.1 | Analog SPK outputs | pins 37/36 (L+/L−), 35/34 (R+/R−); math CH1−CH2 | 500 µs/div, 200–500 mV/div, DC | 1 kHz present → (DAC) firmware | |
| 6.2 | I2S during playback | pads 5 BCK, 4 LRCK, 3 DATA, 6 MCLK | 1 µs & 20 µs/div, 1 V/div, trig 1.6 V normal | flat = no I2S output | |
| 6.3 | I2S with 100 k pull-up to 3V3 | pads 4, 5 | as 6.2 | pin floating, not driven | |
| 6.4 | Search for I2S elsewhere | free PIO pads 27, 29, 30, 48–53 | 1 µs/div, 1 V/div | clock found → I2S remapped in firmware | |
| 6.5 | I2S at power-up | pad 5 / 4 while pressing SW1 | single, 100 ms/div | rules out brief start-then-stop | |
| 6.6 | Supplies | 1V8 (pad 22), VBAT, 3V3 during playback | 10 ms/div, AC 50 mV/div | clean power | |

Note 6.1: QCC5125 outputs may be Class-D (PWM, hundreds of kHz) → use 20 MHz BW limit / averaging, or RC filter (1 k series, 100 nF to GND).

Also collect: photo of module label, photo of fitted board, phone screenshot (connected, playing, codec from developer options).
- 2026-11-26: CSR USB-SPI adapter on hand (has 1V8 + VS voltage-select pins). Speaks CSR BlueCore SPI-debug protocol —
  **not applicable to QCC5125** (QCC51xx uses USB/TRB debug; module has no debug-SPI pins) and not a flashrom programmer,
  unless hardware is FTDI MPSSE (lsusb 0403:6014/6010/6011) → then usable via `flashrom -p ft2232_spi` at 1.8 V. lsusb = **0a12:0042 (CSR SPI Converter, CSR protocol) → not usable.** Order CH341A + 1.8 V kit.

### Phase 6 results — 2026-11-26 (Tektronix TBS1104)

- Module #3 label: "EWM104-BT5125 · Version: I · SN S5203841S00017" (photo: imgs/bringup/module3_label_fitted.jpg)
- **6.1 L channel (pins 37/36): clean 1 kHz sine** — 1.0001 kHz, ≈ 1.5 Vpp differential (≈ 0.5 Vrms), each leg ≈ 0.7 Vpp.
  Photos: imgs/bringup/scope_spk_L_37-36_math.jpg, imgs/bringup/scope_spk_L_37-36_channels.jpg
- **→ PROOF: module routes audio to internal DAC (SPK outputs) = (DAC) firmware behaviour, despite "Version: I" (I2S) label.**
- Pending for report: 6.1 R channel (35/34) · 6.2 screenshot pads 4/5 flat (Auto trigger) ideally with pin 37 on CH3 · 6.3 pull-up on pad 4.
- **6.2 I2S pads 3/4/5/6 during active playback: all flat** (100 mV/div, 1 µs/div, Auto) — imgs/bringup/scope_i2s_pads3-6_flat_playing.jpg
- 6.3: DMM result (pad 4 → 3.0 V with 100 k pull-up) used; no separate scope shot needed.
- **Report to Ebyte written: btaudio/EBYTE_REPORT.md** (fill in order number + name before sending; attach imgs/bringup photos).
- Simultaneous capture: CH4 = SPK output 1 kHz sine, CH1–CH3 = I2S pins flat — imgs/bringup/scope_simultaneous_spk_vs_i2s.jpg (added to report as key evidence)

### 2026-11-27 — Report sent

- Report (btaudio/EBYTE_REPORT.md) sent to EBYTE as a reply in the existing email thread, with scope photos attached.
- Waiting for EBYTE's answer. If none within ~1 week: open a new ticket via the EBYTE website support form, referencing the thread;
  optionally message the AliExpress seller (order ref. 3072877780089435).
- Meanwhile: order CH341A + 1.8 V adapter kit; do not connect module #3 to Qualcomm tools before a verified flash backup.
