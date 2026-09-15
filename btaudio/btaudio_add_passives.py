#!/usr/bin/env python3
"""Add decoupling caps, AC coupling caps, SYS_CTRL RC circuit.

Pin geometry rule (symbol y-up → screen y-down):
  screen_x = place_x + local_x
  screen_y = place_y - local_y

Device:C / Device:R pin locals (both same):
  pin1: (0,  3.81) angle=270 → screen top  (place_y - 3.81)  exits UP   → label rot=270
  pin2: (0, -3.81) angle=90  → screen bot  (place_y + 3.81)  exits DOWN → label rot=90
"""

import sys, uuid, copy
sys.path.insert(0, '/home/dan/.local/lib/python3.14/site-packages')
import sexpdata
from sexpdata import Symbol as S
from skip.sexp.util import writeTree
import skip

SCH = "/home/dan/Documents/kicad/btaudio/btaudio/btaudio.kicad_sch"

def uid():
    return str(uuid.uuid4())

PIN_HALF = 3.81   # half-length from centre to pin connection for Device:C and Device:R

# ── Step 1: sexpdata pass – update U3 input labels (PCM→AUDIO) ──────────────
print("Step 1: Updating U3 audio input labels...")
with open(SCH) as f:
    tree = sexpdata.loads(f.read())

# Remove labels "PCM_OUTL"/"PCM_OUTR" that sit at U3 INL+/INR+ positions
# U3 at (270,68): INL+ local(0,-2.54) → screen(270, 70.54)
#                 INR+ local(0,-5.08) → screen(270, 73.08)
def is_label_at(item, name, x, y, tol=0.1):
    return (isinstance(item, list) and item
            and item[0] == S('label')
            and item[1] == name
            and isinstance(item[2], list) and item[2][0] == S('at')
            and abs(float(item[2][1]) - x) < tol
            and abs(float(item[2][2]) - y) < tol)

before = len(tree)
tree = [item for item in tree
        if not is_label_at(item, 'PCM_OUTL', 270.0, 70.54)
        and not is_label_at(item, 'PCM_OUTR', 270.0, 73.08)]
removed = before - len(tree)
print(f"  Removed {removed} old U3 labels")

# Add AUDIO_L, AUDIO_R at same positions (left-side pin, rot=180)
for name, y in [('AUDIO_L', 70.54), ('AUDIO_R', 73.08)]:
    tree.append([S('label'), name,
                 [S('at'), 270.0, y, 180],
                 [S('fields_autoplaced')],
                 [S('effects'), [S('font'), [S('size'), 1.27, 1.27]],
                  [S('justify'), S('left'), S('bottom')]],
                 [S('uuid'), uid()]])

writeTree(SCH, tree)

# ── Step 2: kicad-skip pass – clone caps, add labels ────────────────────────
print("\nStep 2: Adding passives with kicad-skip...")
schem = skip.Schematic(SCH)

# Find base Device:C and Device:R to clone
base_cap = base_res = None
for s in schem.symbol:
    try:
        lib = s.lib_id.value
        if 'Device:C' in str(lib) and base_cap is None: base_cap = s
        if 'Device:R' in str(lib) and base_res is None: base_res = s
    except: pass
print(f"  Base cap: {base_cap.property.Reference.value}  base res: {base_res.property.Reference.value}")

# Reference counter – start high to avoid charging-board refs
_ref_n = {'C': 50, 'R': 50}
def next_ref(kind):
    r = f'{kind}{_ref_n[kind]}'
    _ref_n[kind] += 1
    return r

def add_label(net, x, y, rot=0):
    lbl = schem.label.new()
    lbl.value = net
    lbl.move(x, y, rot)
    for ch in lbl.children:
        if hasattr(ch, 'entity_type') and ch.entity_type == 'uuid':
            ch.value = uid()
            break

def place_cap(value, cx, cy, ref=None, rot=0):
    """Clone a Device:C, place it at (cx, cy) with given rotation."""
    if ref is None: ref = next_ref('C')
    cap = base_cap.clone()
    cap.move(cx, cy, rot)
    cap.setAllReferences(ref)
    try: cap.property.Value.value = value
    except: pass
    return cap

def place_res(value, rx, ry, ref=None, rot=0):
    """Clone a Device:R, place it at (rx, ry)."""
    if ref is None: ref = next_ref('R')
    res = base_res.clone()
    res.move(rx, ry, rot)
    res.setAllReferences(ref)
    try: res.property.Value.value = value
    except: pass
    return res

def cap_labels(net_top, net_bot, cx, cy, rot=0):
    """Add net labels at the pin connection points of a vertical cap at (cx,cy)."""
    if rot == 0:
        # pin1 screen top (cy - 3.81), pin2 screen bot (cy + 3.81)
        add_label(net_top, cx, cy - PIN_HALF, 270)
        add_label(net_bot, cx, cy + PIN_HALF,  90)
    elif rot == 90:
        # rotated 90°: pin1→left (cx-3.81,cy), pin2→right (cx+3.81,cy)
        add_label(net_top, cx - PIN_HALF, cy, 180)
        add_label(net_bot, cx + PIN_HALF, cy,   0)

def res_labels(net_top, net_bot, rx, ry):
    add_label(net_top, rx, ry - PIN_HALF, 270)
    add_label(net_bot, rx, ry + PIN_HALF,  90)

# ── AC coupling caps (1µF, vertical, between U2 and U3) ─────────────────────
# PCM_OUTL net (U2 OUTL) → cap → AUDIO_L net (U3 INL+)
# PCM_OUTR net (U2 OUTR) → cap → AUDIO_R net (U3 INR+)
# Place at x=227 (between U2 left x=200 and U3 left x=270)
# U2 OUTL screen (200, 70.70), U3 INL+ screen (270, 70.54) → y≈70.6
# U2 OUTR screen (200, 73.24), U3 INR+ screen (270, 73.08) → y≈73.2

place_cap('1µF', 227, 70.6,  'C90')
cap_labels('PCM_OUTL', 'AUDIO_L', 227, 70.6)

place_cap('1µF', 235, 73.2,  'C91')
cap_labels('PCM_OUTR', 'AUDIO_R', 235, 73.2)

print("  Added AC coupling caps C90, C91")

# ── U1 decoupling caps ───────────────────────────────────────────────────────
# U1 left pins at screen x=109.22. Place caps at x=87–96, y aligned to power pins.
# VBAT screen y=121.92, +3V3 screen y=119.38, VIN screen y=124.46

place_cap('100nF', 93, 121.92, 'C50')
cap_labels('VBAT', 'GND', 93, 121.92)

place_cap('10µF',  87, 121.92, 'C51')
cap_labels('VBAT', 'GND', 87, 121.92)

place_cap('100nF', 93, 119.38, 'C52')
cap_labels('+3V3', 'GND', 93, 119.38)

place_cap('10µF',  87, 119.38, 'C53')
cap_labels('+3V3', 'GND', 87, 119.38)

place_cap('100nF', 93, 124.46, 'C54')
cap_labels('VIN', 'GND', 93, 124.46)

print("  Added U1 decoupling C50-C54")

# ── U2 decoupling caps ───────────────────────────────────────────────────────
# U2 body bottom at screen y≈83.40. Place caps at y=97.
# AVDD  left  screen (200, 75.78)
# AGND  left  screen (200, 78.32) ← already labeled GND
# DVDD  right screen (230.48, 58)
# CPVDD left  screen (200, 58)

place_cap('100nF', 197, 97, 'C60')
cap_labels('+3V3', 'GND', 197, 97)   # AVDD bypass

place_cap('10µF',  191, 97, 'C61')
cap_labels('+3V3', 'GND', 191, 97)

place_cap('100nF', 228, 97, 'C62')
cap_labels('+3V3', 'GND', 228, 97)   # DVDD bypass

place_cap('100nF', 203, 97, 'C63')
cap_labels('+3V3', 'GND', 203, 97)   # CPVDD bypass

print("  Added U2 decoupling C60-C63")

# ── U3 decoupling caps ───────────────────────────────────────────────────────
# U3 HPVDD right screen (300.48, 68). U3 VDD top screen (287.78, 52.76).
# Place caps to the right of U3 at x=310+, y=85.

place_cap('100nF', 312, 85, 'C70')
cap_labels('+3V3', 'GND', 312, 85)   # HPVDD bypass

place_cap('10µF',  318, 85, 'C71')
cap_labels('+3V3', 'GND', 318, 85)

place_cap('100nF', 290, 62, 'C72')
cap_labels('+3V3', 'GND', 290, 62)   # VDD (top pin) bypass

print("  Added U3 decoupling C70-C72")

# ── U4 decoupling caps ───────────────────────────────────────────────────────
# U4 VIN screen (53.65, 50.73), VOUT screen (66.35, 50.73), GND screen (60, 58.35)
# Place caps below U4, y≈70

place_cap('100nF', 50, 70, 'C73')
cap_labels('VBAT', 'GND', 50, 70)    # input bypass

place_cap('100nF', 60, 70, 'C74')
cap_labels('+3V3', 'GND', 60, 70)    # output bypass

place_cap('4.7µF', 68, 70, 'C75')
cap_labels('+3V3', 'GND', 68, 70)    # output bulk cap

print("  Added U4 decoupling C73-C75")

# ── LDOO bypass (U2 pin18, 100nF to GND) ────────────────────────────────────
# LDOO screen (230.48, 63.08) – currently NC. Add cap here.
# Cap at (247, 63): pin1→+3V3? No, LDOO is an internal LDO output (bypass to GND only).
# Place cap at (247, 63.08): pin1 → LDOO net (new net), pin2 → GND
# Remove the NC at (230.48, 63.08) and add a LDOO label instead

# We'll handle the NC removal in the sexpdata pass. For now add cap+labels.
place_cap('100nF', 247, 63.08, 'C76')
cap_labels('LDOO', 'GND', 247, 63.08)

# Also add LDOO label at U2 pin18 position (230.48, 63.08) to connect
add_label('LDOO', 230.48, 63.08, 0)

print("  Added LDOO bypass cap C76")

# ── SYS_CTRL delay circuit (RC, MOSFET to add manually) ─────────────────────
# From PLAN: Vbat→R(100k)→[SYS_RC]→MOSFET_gate; C(10µF)→GND from SYS_RC
# MOSFET drain → SYS_CTRL (U1 pin13 at screen 109.22, 111.76)
# MOSFET source → GND
# Place R50 and C92 to left of U1 at x=97

place_res('100kΩ', 97, 108, 'R50')
res_labels('VBAT', 'SYS_RC', 97, 108)

place_cap('10µF', 97, 118, 'C92')
cap_labels('SYS_RC', 'GND', 97, 118)

print("  Added SYS_CTRL RC: R50 (100kΩ), C92 (10µF)")

# ── Schematic text annotations ───────────────────────────────────────────────
def add_text(txt, x, y, size=1.0):
    t = schem.text.new()
    t.value = txt
    t.move(x, y)
    try:
        t.effects.font.size.value = [size, size]
    except:
        pass

add_text("NOTE: Add 2N7002 MOSFET:\nG=SYS_RC, D=SYS_CTRL pin13, S=GND", 75, 104)
add_text("NOTE: ANT (U1 pin46): Johanson 0433AT62A0020E\n+ pi-match network (see PLAN.md)", 152, 75)
add_text("NOTE: AC coupling caps 1uF between U2 OUTL/OUTR and U3 INL+/INR+", 215, 58)
add_text("Decoupling: 100nF X5R 0402 + 10uF X5R 0805", 75, 133)

print("  Added text annotations")

# ── Save ─────────────────────────────────────────────────────────────────────
print("\nStep 3: Saving...")
schem.write(SCH)

# ── sexpdata pass: remove old LDOO NC and old PCM_OUTL NC at y<200 ──────────
print("Step 4: Removing stale NC at LDOO pin (now connected)...")
with open(SCH) as f:
    tree2 = sexpdata.loads(f.read())

def is_nc_near(item, x, y, tol=0.2):
    return (isinstance(item, list) and item and item[0] == S('no_connect')
            and isinstance(item[1], list) and item[1][0] == S('at')
            and abs(float(item[1][1]) - x) < tol
            and abs(float(item[1][2]) - y) < tol)

before = len(tree2)
# Remove NC at LDOO position (230.48, 63.08) since we added cap+label there
tree2 = [item for item in tree2 if not is_nc_near(item, 230.48, 63.08)]
removed = before - len(tree2)
print(f"  Removed {removed} stale NC(s)")

writeTree(SCH, tree2)

# ── Final verify ─────────────────────────────────────────────────────────────
print("\nVerifying final load...")
schem3 = skip.Schematic(SCH)
syms = list(schem3.symbol)
labels = list(schem3.label)
my_labels = [l for l in labels if l.at.value[1] < 200]
print(f"  Placed symbols: {len(syms)}")
print(f"  Labels (all): {len(labels)}  my section (y<200): {len(my_labels)}")
audio = [l for l in my_labels if l.value in ('AUDIO_L','AUDIO_R')]
print(f"  AUDIO_L/R labels: {len(audio)}")
c_refs = [s.property.Reference.value for s in syms
          if 'C5' in s.property.Reference.value or 'C6' in s.property.Reference.value
          or 'C7' in s.property.Reference.value or 'C9' in s.property.Reference.value]
print(f"  New cap refs: {sorted(c_refs)}")
print("\n=== DONE ===")
