# Project documentation: Bluetooth 5.1 headphone module

## 1. Overview & architecture
The goal of this project is a custom carrier board that adds Bluetooth 5.1 to an old pair of wired headphones.
Instead of a discrete Bluetooth SoC (often behind NDAs or hard to solder), it uses a **system-on-module (SoM)**.

For the best audio quality without background noise (often caused by the RF signal), the architecture keeps the stages
strictly separate:
**Bluetooth module (digital, I2S) → separate I2S DAC → dedicated headphone amplifier.**

The board (rev 1) is described in [PLAN.md](PLAN.md); measurement results are in
[btaudio/BRINGUP_TESTPLAN.md](btaudio/BRINGUP_TESTPLAN.md).

## 2. The Bluetooth module: EBYTE EWM104-BT5125(I2S)
*   **Why the QCC5125?** True stereo, Bluetooth 5.1 and high-end codecs such as aptX HD. The cheaper QCC3040 is
    configured for mono/TWS only by this manufacturer.
*   **Why the I2S variant?** It outputs the audio purely digitally over I2S. The (DAC) variant outputs a differential
    analog signal, which would need an external differential amplifier and is more prone to noise.
*   **Bonus:** the module has a built-in LiPo battery charger.
*   **On-module flash:** Macronix MX25U3232F, 32 Mbit, **1.8 V**. Reading or writing it requires a 1.8 V programmer.
*   **Caution (bring-up):** the delivered modules marked "Version: I" output audio on the analog SPK pins, while the
    I2S pins stay high-impedance. They behave like the DAC firmware.
    See [btaudio/EBYTE_REPORT.md](btaudio/EBYTE_REPORT.md).
*   **Caution (configuration):** two modules stopped working after connection attempts with the Qualcomm tools through
    USB passthrough into a Windows VM. Before any configuration attempt, back up the flash, work only on native
    Windows, and keep VBAT connected.

## 3. The three core blocks

### 3.1 Audio stage (DirectPath / capless)
*   **DAC (TI PCM5102A):** converts I2S into an analog line signal (up to about 2.1 Vrms). SCK is tied to GND, so the
    DAC derives its system clock from BCK with its PLL. The module must be the I2S master. The output has an
    RC filter (470 Ω / 2.2 nF).
*   **Amplifier (TI TPA6132A2):** supplies the current for 16–32 Ω headphones. The input is AC-coupled with 1 µF.
    Gain is selected with solder jumpers JP1/JP2: **−6 / 0 / 3 / 6 dB**, built at −6 dB.
    It is enabled by the module's PIO[20] (AMP_EN, 10 k pull-down).
*   *Architecture advantage:* both ICs generate their negative supply with an internal charge pump. This removes the
    large DC-blocking capacitors at the headphone output.

### 3.2 Power & USB-C
*   The battery (pin header J6) connects directly to the module's `VBAT` (pin 14) and `VBAT_SENSE` (pin 7).
*   The 5 V from the USB-C receptacle goes to `VCHG` (pin 10) and `VCHG_SENSE` (pin 11). The module charges the battery itself.
*   `CC1` and `CC2` each have **5.1 kΩ to GND**, so USB-C chargers supply 5 V.
*   An LDO (**MCP1700-3302**) makes 3.3 V from the battery voltage for the module's I/O pins, the DAC and the amplifier.
*   **Rev 1 limitation:** the LDO is fed from VBAT only. Without a battery there is no 3.3 V, and the circuit does not
    work even on USB.

### 3.3 RF & antenna
The EBYTE module has no built-in antenna.
*   A 50 Ω trace runs from the `ANT` pin (46) through a 0 Ω resistor (L1) to an **IPEX (U.FL) connector** for an
    external antenna.
*   Two unpopulated shunt positions (C17, C18) allow π-matching if needed.

### 3.4 Controls
*   **SW1:** button from VBAT to `SYS_CTRL` (power on). Press briefly only; never tie it permanently to VBAT.
*   **SW6:** reset (RST/PIO[1] to GND).
*   **J1:** pin header for external buttons on PIO[2] (Play/Vol+), PIO[3] (Pause/Vol−) and PIO[4] (Previous/Pairing).
*   **LEDs D4/D5:** on AIO[0]/AIO[1], powered from VBAT through 1 kΩ.

---

## 4. Bill of materials (as built)

| Category | Part | Type | Package | Qty | Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RF / core** | Bluetooth SoM | EBYTE EWM104-BT5125(I2S) | Stamp hole | 1 | Receiver, I2S output, battery charger |
| | Antenna connector | IPEX / U.FL (A-1JB) | SMD | 1 | External 2.4 GHz antenna |
| | RF matching | 0 Ω (L1) + 2× NC (C17, C18) | 0402 | 3 | Series bridge / optional π network |
| **Audio** | I2S DAC | TI PCM5102AQPWRQ1 | TSSOP-20 | 1 | I2S → analog |
| | Headphone amp | TI TPA6132A2RTET | WQFN-16 | 1 | Capless headphone amplifier |
| | Audio connection | Solder pads (J3) | – | 1 | Headphone cable L / R / ground |
| **Power** | USB-C receptacle | HRO TYPE-C-31-M-12 (16 pin) | SMD | 1 | Charging, USB to the module |
| | CC resistors | 5.1 kΩ (R4, R5) | 0805 | 2 | USB-C detection |
| | Battery connector | Pin header 1×02 (J6) | 2.54 mm | 1 | LiPo 3.7 V |
| | 3.3 V LDO | Microchip MCP1700-3302 | SOT-23 | 1 | 3.3 V for I/O, DAC, amp |
| **Controls** | Power button | TS-1088 (SW1) | SMD | 1 | SYS_CTRL |
| | Reset | Button on solder-jumper footprint (SW6) | SMD | 1 | RST/PIO[1] |
| | Button connector | Pin header 1×04 (J1) | 2.54 mm | 1 | External buttons PIO[2–4] |
| | Gain select | 3-pad solder jumper (JP1, JP2) | SMD | 2 | TPA6132A2 G0/G1 |
| | Status LEDs | LED (D4, D5) | 0805 | 2 | System status |
| | LED resistors | 1 kΩ (R14, R15) | 0805 | 2 | Current limiting |
| **Passives** | Output filter | 470 Ω (R10, R11) + 2.2 nF (C28, C29) | 0805 | 4 | RC filter at the DAC output |
| | Amp enable | 10 kΩ pull-down (R12) | 0805 | 1 | AMP_EN |
| | Capacitors | 1 µF ×7, 100 nF ×5, 2.2 µF ×4 | 0805 | 16 | Coupling, charge pumps, decoupling |
| | Capacitors | 10 µF ×5 | 1206 | 5 | Bulk: VBAT, 3V3, LDOO |

Full list: `btaudio/btaudio.csv` · Interactive BOM: `btaudio/bom/ibom.html`

---

## 5. Golden rules for the PCB layout

1.  **Antenna:** keep the 50 Ω trace from the module to the IPEX connector short. Don't route other signals under the
    module's RF area or along the trace.
2.  **Grounding:** this is a mixed-signal board. Keep the radio section (Bluetooth) physically separate from the
    analog section (DAC output, amplifier). Give the RF section a continuous ground plane.
3.  **Decoupling:** place the 100 nF capacitors as close as possible to the ICs' supply pins.
4.  **Solderability:** the EBYTE module (stamp hole), TSSOP and SOT-23 can be soldered with an iron. The amplifier's QFN
    needs **solder paste and hot air**. Solder the module quickly and with flux; long hot-air reflow can shift the
    parts under its shield.
