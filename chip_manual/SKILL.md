---
name: chip-manual
description: Query MCU/chip reference manuals for register definitions, bit fields, addresses, peripheral configurations (I2C/SPI/UART/CAN timing), metering algorithms, calibration procedures, electrical characteristics, and pin configurations.
---

# Chip Manual Query

## CRITICAL: Do NOT read manual files directly!

This skill uses Gemini API as backend. Always use the query script - never read files under `manuals/` directly, as they are too large and will overflow context.

## Supported Chips

Read `config.yaml` to check available chips and their aliases.

Or run:
```bash
python scripts/query_manual.py --list
```

## How to Use

```bash
python scripts/query_manual.py --chip <CHIP_NAME> "<question>"
```

Examples:
```bash
python scripts/query_manual.py --chip RN7326 "EMUCON register address"
python scripts/query_manual.py -c V32G410 "GPIO config registers"
```

## Response Format

```json
{
  "chip": "RN7326",
  "answer": "Answer based on manual content",
  "model": "gemini-3-flash-preview",
  "status": "success"
}
```

## Notes

- Temperature=0 for deterministic output
- Strictly based on manual content, no inference
- Returns "not found" if manual doesn't contain the answer
