# MAGI OS Intelligence Module
## I-Ching Logic Kernel & Harmonic Synthesis System

---

## 🏛️ Architecture Overview

The Intelligence Module implements the **"Council of Systems"** architecture - a harmonic/parallel integration of multiple metaphysical frameworks where each system maintains sovereignty while contributing to unified wisdom.

```
┌─────────────────────────────────────────────────────────────────┐
│                    COUNCIL OF SYSTEMS                           │
├─────────────────┬───────────────────┬─────────────────────────┤
│   CARDOLOGY     │     I-CHING       │    [FUTURE SYSTEMS]     │
│   (Macro)       │     (Micro)       │    Vedic, Mayan, etc.   │
│   52-day cycle  │     ~6-day cycle  │                         │
├─────────────────┴───────────────────┴─────────────────────────┤
│              HARMONIC SYNTHESIS ENGINE                         │
│     - Elemental Resonance Calculation                          │
│     - Frequency Spectrum Unification (XP/Leveling)            │
│     - Cross-System Quest Generation                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Module Structure

```
src/app/modules/intelligence/
├── __init__.py              # Main module exports
├── iching/
│   ├── __init__.py          # I-Ching module exports
│   └── kernel.py            # I-Ching Logic Kernel (3500+ lines)
├── cardology/
│   ├── __init__.py          # Cardology module exports
│   └── kernel.py            # Cardology interface stub
└── synthesis/
    ├── __init__.py          # Synthesis module exports
    └── harmonic.py          # Harmonic Synthesis Engine
```

---

## 🔮 I-Ching Logic Kernel

### Features

| Feature | Status | Description |
|---------|--------|-------------|
| **64 Gates Complete** | ✅ | Full database with I-Ching, HD, Gene Keys |
| **Binary Representation** | ✅ | 6-bit encoding for all hexagrams |
| **Trigram Composition** | ✅ | Upper/Lower trigram breakdown |
| **Line Calculation** | ✅ | Precise 0.9375° per line |
| **Color/Tone/Base** | ✅ | Full HD sub-structure support |
| **36 Channels** | ✅ | Complete channel definitions |
| **12 Profiles** | ✅ | All profile combinations |
| **192 Incarnation Crosses** | ✅ | RAC/JXP/LAC for all gates |
| **Type Determination** | ✅ | Generator/MG/Manifestor/Projector/Reflector |
| **Gene Keys Spectrum** | ✅ | Shadow/Gift/Siddhi for XP mapping |

### Mathematical Precision

```python
# Degrees per division (derived from 360° / 64 gates)
DEGREES_PER_GATE  = 5.625      # 360/64
DEGREES_PER_LINE  = 0.9375     # 5.625/6
DEGREES_PER_COLOR = 0.15625    # 0.9375/6
DEGREES_PER_TONE  = 0.026042   # 0.15625/6
DEGREES_PER_BASE  = 0.005208   # 0.026042/5

# Zodiac Offset (Fixed Tropical)
ICHING_OFFSET = 58  # Gate 41 starts at 302° (Aquarius 2°)
```

### Core Usage

```python
from app.modules.intelligence.iching import IChingKernel, GATE_DATABASE

# Initialize kernel
kernel = IChingKernel()

# Get daily code (current Sun/Earth gates)
daily = kernel.get_daily_code()
print(f"Sun: Gate {daily.sun_activation.gate}")
print(f"Earth: Gate {daily.earth_activation.gate}")

# Calculate gate from longitude
activation = kernel.longitude_to_activation(223.25)
print(f"Gate: {activation.gate}, Line: {activation.line}")

# Get full gate info
info = kernel.get_gate_info(13)
print(f"Name: {info['iching']['name']}")
print(f"HD: {info['human_design']['name']}")
print(f"Gene Keys: {info['gene_keys']['shadow']} → {info['gene_keys']['gift']} → {info['gene_keys']['siddhi']}")
```

### Gate Database Structure

Each of the 64 gates contains:

```python
GateData(
    # Core Identity
    number=13,
    binary="111101",
    king_wen_sequence=13,
    
    # Trigram Composition
    lower_trigram="101",  # Fire
    upper_trigram="111",  # Heaven
    
    # I-Ching Layer
    iching_name="Fellowship with Men",
    iching_chinese="同人",
    iching_pinyin="Tóng Rén",
    iching_judgment="Fellowship with men in the open...",
    iching_image="Heaven together with fire...",
    
    # Human Design Layer
    hd_name="The Gate of the Listener",
    hd_keynote="The Fellowship of Humanity",
    hd_center="G",
    hd_circuit="Collective",
    hd_stream="Sharing",
    
    # Gene Keys Layer (XP SPECTRUM)
    gk_shadow="Discord",
    gk_gift="Discernment",
    gk_siddhi="Empathy",
    gk_programming_partner=7,
    gk_codon_ring="Ring of Union",
    gk_amino_acid="Valine",
    
    # Wheel Position
    wheel_index=2,
    start_degree=313.25,
    zodiac_sign="Aquarius",
    zodiac_degree=13.25,
)
```

---

## 🌐 Harmonic Synthesis Engine

### Philosophy

The Synthesis Engine treats all metaphysical systems as **equal sovereigns**:

- **Cardology** = Macro-Coordinate (52-day planetary periods)
- **I-Ching** = Micro-Coordinate (~6-day gate transits)
- **Future Systems** = Additional parallel voices

### Elemental Resonance

Cross-system resonance is calculated via elemental correspondence:

| Element | Cardology | Human Design | I-Ching |
|---------|-----------|--------------|---------|
| Fire | Clubs ♣ | Heart Center | Heaven, Thunder, Fire |
| Water | Hearts ♥ | Sacral, Solar Plexus | Water, Lake |
| Earth | Diamonds ♦ | Spleen, Root | Earth, Mountain |
| Air | Spades ♠ | Head, Ajna | Wind |
| Ether | - | Throat, G | - |

### Usage

```python
from app.modules.intelligence.synthesis import (
    CouncilOfSystems,
    IChingAdapter,
    CardologyAdapter,
)
from app.modules.intelligence.iching import IChingKernel

# Create the Council
council = CouncilOfSystems()

# Register systems
kernel = IChingKernel()
council.register_system("I-Ching", IChingAdapter(kernel))
council.register_system("Cardology", CardologyAdapter())

# Get unified synthesis
synthesis = council.synthesize()

print(f"Resonance: {synthesis.resonance_score:.2f} ({synthesis.resonance_type.value})")
print(f"Macro Theme: {synthesis.macro_theme}")
print(f"Micro Theme: {synthesis.micro_theme}")
print(f"Guidance: {synthesis.synthesis_guidance}")

# Quest suggestions for gamification
for quest in synthesis.quest_suggestions:
    print(f"  • {quest}")
```

### Cross-System Synthesis Function

```python
from app.modules.intelligence.synthesis import cross_system_synthesis

result = cross_system_synthesis(card_reading, hexagram_reading)
print(f"Resonance: {result['resonance_score']:.2f}")
print(f"Guidance: {result['synthesis_guidance']}")
```

---

## 🎮 Solo Leveling / XP Integration

The Gene Keys spectrum maps directly to gamification:

| XP Range | Frequency Band | Expression |
|----------|----------------|------------|
| 0-33% | **Shadow** | Unconscious, reactive patterns |
| 34-66% | **Gift** | Conscious, responsive expression |
| 67-100% | **Siddhi** | Transcendent, unified state |

### Example Implementation

```python
def get_expression_for_xp(gate: int, xp: int) -> str:
    """Get the current frequency expression based on XP."""
    spectrum = IChingKernel.get_gene_key_spectrum(gate)
    
    if xp < 333:
        return f"Shadow: {spectrum['shadow']}"
    elif xp < 666:
        return f"Gift: {spectrum['gift']}"
    else:
        return f"Siddhi: {spectrum['siddhi']}"

# Example: Gate 13 with 500 XP
expression = get_expression_for_xp(13, 500)
# Returns: "Gift: Discernment"
```

---

## 🔧 Integration with Existing GUTTERS

### Connecting to Your Cardology Kernel

1. **Copy your `chronos_magi_kernel.py`** to `cardology/`
2. **Update the CardologyAdapter** in `synthesis/harmonic.py`:

```python
from .cardology.chronos_magi_kernel import CardologyKernel, generate_blueprint

class CardologyAdapter:
    def __init__(self, kernel=None):
        self._kernel = kernel or CardologyKernel()
    
    def get_reading(self, dt: datetime) -> SystemReading:
        blueprint = generate_blueprint(dt.date())
        # Map to SystemReading...
```

### Using with Swiss Ephemeris

For high-fidelity planetary positions:

```python
from app.modules.intelligence.iching import IChingKernel, SwissEphemerisService

# Initialize with ephemeris
ephemeris = SwissEphemerisService("/path/to/ephe/data")
kernel = IChingKernel(ephemeris_service=ephemeris)

# Now calculations use exact planetary positions
daily = kernel.get_daily_code()
```

---

## 📊 Verification Tests

All tests pass (11/11):

| Test | Result |
|------|--------|
| Gate 41 at 302° | ✅ |
| Gate 1 at 223.25° | ✅ |
| Gate 2 at 43.25° | ✅ |
| Line 1 calculation | ✅ |
| Line 6 calculation | ✅ |
| Gate 1 binary (111111) | ✅ |
| Gate 2 binary (000000) | ✅ |
| Channel detection (64-47) | ✅ |
| Type: Reflector | ✅ |
| Type: Generator | ✅ |
| Profile 3/5 | ✅ |

---

## 📜 API Reference

### IChingKernel

| Method | Returns | Description |
|--------|---------|-------------|
| `longitude_to_activation(longitude)` | `Activation` | Convert longitude to full activation |
| `calculate_solar_gate(longitude)` | `Dict` | Get gate with semantic data |
| `get_daily_code(dt)` | `DailyCode` | Current Sun/Earth gates |
| `get_gate_info(gate_number)` | `Dict` | Complete gate information |
| `get_hexagram_binary(gate_number)` | `str` | 6-bit binary representation |
| `get_gene_key_spectrum(gate_number)` | `Dict` | Shadow/Gift/Siddhi |
| `find_channels(active_gates)` | `List[ChannelData]` | Defined channels |
| `determine_type(centers, channels)` | `str` | HD Type calculation |
| `calculate_profile(line1, line2)` | `Dict` | Profile data |

### CouncilOfSystems

| Method | Returns | Description |
|--------|---------|-------------|
| `register_system(name, adapter)` | `None` | Register a system |
| `get_reading(system_name, dt)` | `SystemReading` | Get single reading |
| `synthesize(dt)` | `HarmonicSynthesis` | Full synthesis |

---

## 🚀 Future Extensions

The architecture supports adding new systems:

```python
class VedicAdapter:
    def get_reading(self, dt: datetime) -> SystemReading:
        # Calculate Vedic position
        # Return as SystemReading
        pass

council.register_system("Vedic", VedicAdapter(), weight=1.0)
```

---

## 📝 License

For metaphysical research and consciousness development tools.
Part of the GUTTERS Project / Magi OS.

---

*"The System knows the script before you read the lines."*
