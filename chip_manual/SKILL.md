---
name: chip-manual
description: Query MCU/chip reference manuals for register definitions, bit fields, addresses, peripheral configurations (I2C/SPI/UART/CAN timing), metering algorithms, calibration procedures, electrical characteristics, and pin configurations.
allowed-tools:
  - Bash(*query_manual.py*)
---

# Chip Manual Query

## CRITICAL: Do NOT read manual files directly!

Always use the query script. Manual files are too large for context.

## List Available Chips

```bash
python scripts/query_manual.py --list
```

## Query Usage

```bash
python scripts/query_manual.py --chip <CHIP_NAME> "<question>"
```

## Examples

```bash
python scripts/query_manual.py --chip RN7326 "EMUCON register address"
python scripts/query_manual.py --chip RN7326 "DMA_CH_SEL register definition"
python scripts/query_manual.py --chip RN7326 "SPI configuration steps"
python scripts/query_manual.py -c V32G410 "GPIO config registers"
```

## Tips

- Use exact register names from manual (e.g. `DMA_CH_SEL` not `WAVE_CHSEL`)
- If "not found", try broader keywords or query register list first
- Common prefixes: `EMU*`, `DMA_*`, `SPL_*`, `HW_*`
