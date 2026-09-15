
***

# Projekt-Dokumentation: Audiophiles Bluetooth 5.1 Kopfhörer-Modul

## 1. Projektübersicht & Architektur
Das Ziel dieses Projekts ist die Entwicklung eines eigenen Carrier-Boards (Trägerplatine), um einen alten Kopfhörer mit modernem Bluetooth 5.1 auszustatten. Anstatt diskrete Bluetooth-SoCs zu verwenden (die oft hinter NDAs versteckt oder schwer zu löten sind), wird ein **System-on-Module (SoM)** Ansatz gewählt.

Um die höchste Audioqualität ohne störendes Hintergrundrauschen (oft durch das RF-Signal verursacht) zu erreichen, nutzt das Design eine strikt getrennte, audiophile Architektur:
**Bluetooth-Modul (Digital I2S) $\rightarrow$ Separater I2S-DAC $\rightarrow$ Dedizierter Kopfhörerverstärker.**

## 2. Die Wahl des Bluetooth-Moduls: EBYTE EWM104-BT5125(I2S)
Nach der Analyse des Datenblattes fiel die Wahl auf das EBYTE-Modul basierend auf dem **Qualcomm QCC5125** Chip.
*   **Warum QCC5125?** Unterstützt echtes Stereo, Bluetooth 5.1 und High-End-Codecs wie aptX-HD und LDAC. (Der günstigere QCC3040 ist bei diesem Hersteller nur für Mono/TWS konfiguriert).
*   **Warum die I2S-Variante?** Das Modul gibt ein rein digitales I2S-Signal aus. Die (DAC)-Variante des Moduls würde ein differentielles Analogsignal ausgeben, was zwingend einen externen Differenzverstärker erfordern würde und anfälliger für Rauschen ist.
*   **Vorteil:** Das Modul bringt bereits einen Laderegler für den Li-Po-Akku mit!

## 3. Die drei Kern-Blöcke der Schaltung

### 3.1 Die Audio-Stufe ("DirectPath / Capless")
*   **DAC (TI PCM5102A):** Wandelt das digitale I2S-Signal in ein sauberes analoges Line-Signal. Generiert seinen Systemtakt (MCLK) intern und benötigt nur wenige externe Bauteile.
*   **Verstärker (TI TPA6132A2 / MAX97220):** Liefert den nötigen Strom für typische 32-Ohm Kopfhörertreiber, um einen satten Bass zu garantieren.
*   *Architektur-Vorteil:* Beide ICs besitzen interne Charge-Pumps zur Erzeugung einer negativen Versorgungsspannung. Dadurch entfallen große DC-Blocking-Kondensatoren am Audioausgang, die den Klang verfälschen würden.

### 3.2 Stromversorgung & USB-C
*   Der Akku wird direkt an den `VBAT`-Pin des EBYTE-Moduls angeschlossen.
*   Die 5V-Spannung der USB-C Buchse geht an den `VCHG`-Pin des Moduls (internes BMS lädt den Akku).
*   Für die modernen USB-C Power Delivery Netzteile müssen die Pins `CC1` und `CC2` der Buchse über jeweils einen **$5.1\,\text{k}\Omega$ Widerstand auf GND** gezogen werden.
*   Ein extrem rauscharmer LDO-Regler macht aus der schwankenden Akkuspannung (3.0 - 4.2V) perfekte **3.3V** für den Audio-DAC und den Verstärker.

### 3.3 Hochfrequenz (RF) & Antennendesign
Das EBYTE-Modul besitzt keine integrierte Antenne (Stamp-Hole).
*   Vom Modul-Pin `ANT` wird eine exakt **$50\,\Omega$ impedanzkontrollierte Leiterbahn** zu einer SMD-Keramikantenne geroutet.
*   In Serie wird ein $0\,\Omega$ Widerstand als Brücke / Platzhalter für ein mögliches Matching-Netzwerk platziert.

---

## 4. Bill of Materials (BOM) / Stückliste

| Kategorie | Bauteil / Funktion | Empfohlene(r) Typ(en) / Partnummer | Bauform | Stk. | Anmerkung / Aufgabe im Schaltplan |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Funk / Core** | **Bluetooth SoM** | EBYTE EWM104-BT5125(I2S) | Stamp Hole | 1 | Das Gehirn; liefert digitales Audio (I2S) & lädt den Akku. |
| | **Keramik-Antenne** | Johanson 2450AT18A100E *oder* Yageo | SMD 0603/1206 | 1 | 2.4 GHz Chip-Antenne (vermeidet komplexes PCB-Antennendesign). |
| | **RF-Matching** | $0\,\Omega$ Widerstand | SMD 0603 | 1 | Brücke in Serie zwischen Modul-Pin `ANT` und Antenne. |
| **Audio** | **I2S Audio-DAC** | **Texas Instruments PCM5102A** | TSSOP-20 | 1 | Wandelt I2S (digital) exzellent in analoges Line-Signal um. |
| | **Kopfhörer-Amp** | **TI TPA6132A2** *oder* **Maxim MAX97220** | WQFN / TDFN | 1 | Capless-Verstärker; liefert den nötigen Strom für satte Bässe. |
| | **Audio-Buchse** | 3.5mm Klinkenbuchse (z.B. PJ-320D) | SMD oder THT | 1 | Optional; Kopfhörerkabel können auch direkt verlötet werden. |
| **Power** | **USB-C Buchse** | 6-Pin oder 16-Pin Type-C | SMD | 1 | Ladeanschluss; 5V gehen an Pin 10 (`VCHG`) des Moduls. |
| | **PD-Widerstände** | $5.1\,\text{k}\Omega$ Widerstand | SMD 0603 | 2 | Zwingend an `CC1` & `CC2` (gegen GND) für USB-C Erkennung. |
| | **Li-Po Akku** | 3.7V, ca. 300 - 500 mAh mit BMS | JST-Stecker | 1 | Spannungsquelle; an Pin 14 (`VBAT`) und `GND`. |
| | **3.3V LDO-Regler** | TI TPS7A2033 *oder* MIC5219-3.3YM5 | SOT-23-5 | 1 | Rauscharme 3.3V für DAC, Amp & IO-Signale. |
| **Interface** | **Taster**| Standard Tactile Switch (Drucktaster) | SMD | 4 | Play/Pause, Vol+, Vol- und Power/Pairing. |
| | **Status LEDs** | LED Rot & LED Blau | SMD 0603 | 2 | Für Systemstatus. |
| | **LED-Widerstände** | ca. $470\,\Omega$ bis $1\,\text{k}\Omega$ | SMD 0603 | 2 | Strombegrenzung für die LEDs. |
| **Passiv*** | **Kondensatoren 1** | $100\,\text{nF}$ ($0.1\,\mu\text{F}$), MLCC, X5R/X7R | SMD 0603 | ~ 8 | Decoupling: Jeder IC braucht einen nah am VCC-Pin! |
| | **Kondensatoren 2** | $1\,\mu\text{F}$ und $2.2\,\mu\text{F}$, MLCC, X5R/X7R | SMD 0603 | ~ 5 | Für die internen Charge-Pumps von DAC und Verstärker. |
| | **Kondensatoren 3** | $10\,\mu\text{F}$, MLCC, X5R/X7R | SMD 0603 | ~ 3 | Ein- und Ausgang des 3.3V LDO-Reglers. |

*\*Tipp: Standard R/C-Bauteile am besten als komplettes "0603 SMD Resistor/Capacitor Book" bestellen.*

---

## 5. Goldene Regeln für das PCB-Layout

1.  **Kupferfreie Zone (Antenne):** Weder auf dem Top-Layer noch auf den inneren Lagen oder dem Bottom-Layer darf Kupfer (weder Masse noch Signale) unter der Antenne verlaufen. Am besten platziert man die Keramikantenne ganz am Rand der Platine ("Overhang").
2.  **Massekonzept (Grounding):** Es handelt sich um ein Mixed-Signal-Board. Halte den digitalen Funkt-Teil (Bluetooth) physisch auf der Leiterplatte getrennt vom analogen Teil (DAC-Ausgang & Verstärker). Achte auf eine solide und durchgängige Massefläche (Ground Plane) für den HF-Teil.
3.  **Decoupling:** Die $100\,\text{nF}$ Kondensatoren müssen so nah wie physikalisch möglich an die Versorgungspins (VCC/VDD) der jeweiligen ICs platziert werden.
4.  **Lötbarkeit:** Das EBYTE-Modul (Stamp-Hole), TSSOP und SOT-23 lassen sich von Hand mit dem Lötkolben löten. Für QFN-Packages (Verstärker) wird **Lötpaste und Heißluft** (Hot Air Station) benötigt.

