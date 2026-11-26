# btaudio — Audiophiles Bluetooth 5.1 Upgrade-Board für Kopfhörer

Ein Wireless-Upgrade-Modul für Kabelkopfhörer. Kein All-in-One-Kompromiss: drei dedizierte Stufen, damit
Funk, Wandlung und Verstärkung sauber getrennt bleiben.

## Architektur

```
EWM104-BT5125 (QCC5125, BT 5.1)  →[I2S]→  PCM5102A (DAC)  →[Analog]→  TPA6132A2 (Amp)  →  Kopfhörer
          Empfang                            Wandlung                     Verstärkung
```

**Stufe 1 — Empfang:** Das EBYTE-Modul EWM104-BT5125(I2S) mit Qualcomm QCC5125 empfängt das Audiosignal (aptX HD, AAC, SBC)
und gibt es rein digital über I2S weiter.

**Stufe 2 — Wandlung:** Der PCM5102A wandelt das I2S-Signal in ein analoges Line-Signal. Er läuft im PLL-Modus, ohne MCLK.

**Stufe 3 — Verstärkung:** Der TPA6132A2 treibt die Kopfhörer direkt an (DirectPath / capless), ohne Elkos im Signalweg.

## Board (rev 1)

- 4 Lagen, 51 × 22 mm
- USB-C für die Ladung (über den Lader im Modul), LiPo an einer Stiftleiste
- IPEX-Anschluss (U.FL) für eine externe Antenne
- Lötpads für das Kopfhörerkabel, Stiftleiste für externe Taster
- Verstärkung per Lötbrücken einstellbar (−6 / 0 / 3 / 6 dB)

Details zum Aufbau: [PLAN.md](PLAN.md) · Projekt-Doku: [DOC.md](DOC.md)

## Status

Platine gefertigt und bestückt, Trägerplatine verifiziert. Das gelieferte Modul („Version: I") gibt den Ton jedoch
analog an den SPK-Pins aus statt über I2S. Es verhält sich also wie die DAC-Firmware. Die Klärung mit EBYTE läuft.
Messprotokoll: [btaudio/BRINGUP_TESTPLAN.md](btaudio/BRINGUP_TESTPLAN.md) · Bericht an EBYTE: [btaudio/EBYTE_REPORT.md](btaudio/EBYTE_REPORT.md)

## Schaltplan

![Schaltplan](imgs/schematic.png)

## Platine (3D-Ansicht)

![PCB 3D-Render](imgs/btaudio.png)

## Hardware

- **BT-Modul:** EBYTE EWM104-BT5125(I2S), Qualcomm QCC5125 (Bluetooth 5.1)
- **DAC:** Texas Instruments PCM5102A
- **Amp:** Texas Instruments TPA6132A2 (DirectPath-Kopfhörerverstärker)
- **LDO:** Microchip MCP1700-3302 (3,3 V)
- **Design-Tool:** KiCad
