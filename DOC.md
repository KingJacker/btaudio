# Projekt-Dokumentation: Audiophiles Bluetooth 5.1 Kopfhörer-Modul

## 1. Projektübersicht & Architektur
Ziel des Projekts ist eine eigene Trägerplatine, die einen alten Kabelkopfhörer mit Bluetooth 5.1 ausstattet.
Statt eines diskreten Bluetooth-SoCs (oft hinter NDAs versteckt oder schwer zu löten) kommt ein **System-on-Module (SoM)** zum Einsatz.

Für die beste Audioqualität ohne Hintergrundrauschen (oft vom RF-Signal verursacht) ist die Architektur strikt getrennt:
**Bluetooth-Modul (digital, I2S) → separater I2S-DAC → dedizierter Kopfhörerverstärker.**

Der Aufbau der Platine (rev 1) ist in [PLAN.md](PLAN.md) beschrieben, die Messergebnisse in
[btaudio/BRINGUP_TESTPLAN.md](btaudio/BRINGUP_TESTPLAN.md).

## 2. Das Bluetooth-Modul: EBYTE EWM104-BT5125(I2S)
*   **Warum QCC5125?** Echtes Stereo, Bluetooth 5.1 und High-End-Codecs wie aptX HD. Der günstigere QCC3040 ist bei
    diesem Hersteller nur für Mono/TWS konfiguriert.
*   **Warum die I2S-Variante?** Sie gibt das Audiosignal rein digital über I2S aus. Die (DAC)-Variante liefert ein
    differentielles Analogsignal, das einen externen Differenzverstärker bräuchte und anfälliger für Rauschen ist.
*   **Vorteil:** Das Modul hat einen Laderegler für den LiPo-Akku eingebaut.
*   **Flash im Modul:** Macronix MX25U3232F, 32 Mbit, **1,8 V**. Auslesen und Beschreiben geht nur mit einem 1,8-V-Programmer.
*   **Achtung (Bring-up):** Die gelieferten Module mit der Aufschrift „Version: I" geben den Ton an den analogen
    SPK-Pins aus, die I2S-Pins bleiben hochohmig. Sie verhalten sich also wie die DAC-Firmware.
    Siehe [btaudio/EBYTE_REPORT.md](btaudio/EBYTE_REPORT.md).
*   **Achtung (Konfiguration):** Zwei Module wurden beim Verbindungsversuch mit den Qualcomm-Tools über USB-Passthrough
    in eine Windows-VM unbrauchbar. Vor jedem Konfigurationsversuch den Flash sichern, nur unter nativem Windows
    arbeiten, VBAT angeschlossen.

## 3. Die drei Kern-Blöcke der Schaltung

### 3.1 Audio-Stufe (DirectPath / capless)
*   **DAC (TI PCM5102A):** Wandelt I2S in ein analoges Line-Signal (bis ca. 2,1 Vrms). SCK liegt auf GND, der DAC
    erzeugt seinen Systemtakt also per PLL aus BCK. Das Modul muss I2S-Master sein. Am Ausgang sitzt ein
    RC-Filter (470 Ω / 2,2 nF).
*   **Verstärker (TI TPA6132A2):** Liefert den Strom für 16–32-Ω-Kopfhörer. Der Eingang ist über 1 µF angekoppelt.
    Die Verstärkung wird per Lötbrücken JP1/JP2 gewählt: **−6 / 0 / 3 / 6 dB**, gebaut mit −6 dB.
    Freigabe über PIO[20] des Moduls (AMP_EN, 10 k Pull-down).
*   *Architektur-Vorteil:* Beide ICs erzeugen ihre negative Versorgung mit einer internen Charge-Pump. Dadurch
    entfallen die großen DC-Blocking-Kondensatoren am Kopfhörerausgang.

### 3.2 Stromversorgung & USB-C
*   Der Akku (Stiftleiste J6) hängt direkt an `VBAT` (Pin 14) und `VBAT_SENSE` (Pin 7) des Moduls.
*   Die 5 V der USB-C-Buchse gehen an `VCHG` (Pin 10) und `VCHG_SENSE` (Pin 11). Das Modul lädt den Akku selbst.
*   `CC1` und `CC2` der Buchse liegen über je **5,1 kΩ an GND**, damit USB-C-Netzteile 5 V liefern.
*   Ein LDO (**MCP1700-3302**) macht aus der Akkuspannung 3,3 V für die I/O-Pins des Moduls, den DAC und den Verstärker.
*   **Einschränkung rev 1:** Der LDO hängt nur an VBAT. Ohne Akku gibt es keine 3,3 V, und die Schaltung funktioniert
    auch an USB nicht.

### 3.3 Hochfrequenz (RF) & Antenne
Das EBYTE-Modul hat keine integrierte Antenne.
*   Vom Pin `ANT` (46) führt eine 50-Ω-Leiterbahn über einen 0-Ω-Widerstand (L1) zu einem **IPEX-Anschluss (U.FL)**
    für eine externe Antenne.
*   Zwei unbestückte Shunt-Plätze (C17, C18) erlauben bei Bedarf ein π-Matching.

### 3.4 Bedienung
*   **SW1:** Taster von VBAT an `SYS_CTRL` (Einschalten). Nur kurz drücken; nie dauerhaft an VBAT legen.
*   **SW6:** Reset (RST/PIO[1] an GND).
*   **J1:** Stiftleiste für externe Taster an PIO[2] (Play/Vol+), PIO[3] (Pause/Vol−) und PIO[4] (Zurück/Pairing).
*   **LEDs D4/D5:** an AIO[0]/AIO[1], versorgt aus VBAT über 1 kΩ.

---

## 4. Stückliste (as built)

| Kategorie | Bauteil | Typ | Bauform | Stk. | Aufgabe |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Funk / Core** | Bluetooth-SoM | EBYTE EWM104-BT5125(I2S) | Stamp Hole | 1 | Empfang, I2S-Ausgang, Akku-Lader |
| | Antennenanschluss | IPEX / U.FL (A-1JB) | SMD | 1 | Externe 2,4-GHz-Antenne |
| | RF-Matching | 0 Ω (L1) + 2× NC (C17, C18) | 0402 | 3 | Serienbrücke / optionales π-Netz |
| **Audio** | I2S-DAC | TI PCM5102AQPWRQ1 | TSSOP-20 | 1 | I2S → analog |
| | Kopfhörer-Amp | TI TPA6132A2RTET | WQFN-16 | 1 | Capless-Kopfhörerverstärker |
| | Audio-Anschluss | Lötpads (J3) | – | 1 | Kopfhörerkabel L / R / Masse |
| **Power** | USB-C-Buchse | HRO TYPE-C-31-M-12 (16 Pin) | SMD | 1 | Laden, USB an das Modul |
| | CC-Widerstände | 5,1 kΩ (R4, R5) | 0805 | 2 | USB-C-Erkennung |
| | Akku-Anschluss | Stiftleiste 1×02 (J6) | 2,54 mm | 1 | LiPo 3,7 V |
| | 3,3-V-LDO | Microchip MCP1700-3302 | SOT-23 | 1 | 3,3 V für I/O, DAC, Amp |
| **Bedienung** | Power-Taster | TS-1088 (SW1) | SMD | 1 | SYS_CTRL |
| | Reset | Taster auf Lötbrücken-Footprint (SW6) | SMD | 1 | RST/PIO[1] |
| | Tasteranschluss | Stiftleiste 1×04 (J1) | 2,54 mm | 1 | Externe Taster PIO[2–4] |
| | Gain-Wahl | Lötbrücke, 3 Pads (JP1, JP2) | SMD | 2 | TPA6132A2 G0/G1 |
| | Status-LEDs | LED (D4, D5) | 0805 | 2 | Systemstatus |
| | LED-Widerstände | 1 kΩ (R14, R15) | 0805 | 2 | Strombegrenzung |
| **Passiv** | Ausgangsfilter | 470 Ω (R10, R11) + 2,2 nF (C28, C29) | 0805 | 4 | RC-Filter am DAC-Ausgang |
| | Amp-Enable | 10 kΩ Pull-down (R12) | 0805 | 1 | AMP_EN |
| | Kondensatoren | 1 µF ×7, 100 nF ×5, 2,2 µF ×4 | 0805 | 16 | Kopplung, Charge-Pumps, Decoupling |
| | Kondensatoren | 10 µF ×5 | 1206 | 5 | Bulk: VBAT, 3V3, LDOO |

Vollständige Liste: `btaudio/btaudio.csv` · Interaktive Stückliste: `btaudio/bom/ibom.html`

---

## 5. Goldene Regeln für das PCB-Layout

1.  **Antenne:** Die 50-Ω-Leitung vom Modul zum IPEX-Anschluss kurz halten. Unter dem Antennenbereich des Moduls und der
    Leitung kein fremdes Signal führen.
2.  **Massekonzept:** Mixed-Signal-Board. Den Funkteil (Bluetooth) räumlich vom Analogteil (DAC-Ausgang, Verstärker) trennen.
    Für den HF-Teil eine durchgehende Massefläche vorsehen.
3.  **Decoupling:** Die 100-nF-Kondensatoren so nah wie möglich an die Versorgungspins der ICs setzen.
4.  **Lötbarkeit:** Das EBYTE-Modul (Stamp Hole), TSSOP und SOT-23 lassen sich mit dem Lötkolben löten. Für das QFN des
    Verstärkers braucht man **Lötpaste und Heißluft**. Beim Modul kurz und mit Flussmittel löten; langes Heißluft-Reflow
    kann die Bauteile unter dem Schirmblech verschieben.
