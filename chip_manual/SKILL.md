---
name: chip-manual
description: |
  MCU/chip documentation query tool supporting two document types:
  1. Reference Manual (ref): Register definitions, bit fields, addresses, peripheral configs (I2C/SPI/UART/CAN timing), metering algorithms, calibration, electrical specs, pin configs
  2. API Reference (api): Driver library function interfaces, parameters, usage examples, init flows - for developing drivers from scratch
  NOTE: Not all chips have API docs. Use --list to check available document types before querying.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Chip Manual Query

## CRITICAL: Do NOT read manual files directly!

Always use the query script. Manual files are too large for context.

## IMPORTANT: Check Document Availability First!

**Not all chips have API documentation.** Before querying, check what documents are available:

```bash
# Check config.yaml or use --list to see available document types
python3 $SKILL_DIR/scripts/query_manual.py --list
```

Output will show `available_docs` for each chip. If a chip only has `ref` type, don't waste time querying `api`.

---

## Workflow: Developing a Driver from Scratch

When user needs to develop a driver for a peripheral (e.g., USART, SPI, I2C):

### Step 1: Check if API documentation exists

```bash
python3 $SKILL_DIR/scripts/query_manual.py --list
```

Look for `"type": "api"` in the chip's `available_docs`. If not available, skip to reference manual.

### Step 2: Discover available APIs for the module

```bash
# Query what API functions are available for a module
python3 $SKILL_DIR/scripts/query_manual.py -c V32G410X -t api "list all USART functions"
python3 $SKILL_DIR/scripts/query_manual.py -c V32G410X -t api "what SPI APIs are available"
python3 $SKILL_DIR/scripts/query_manual.py -c V32G410X -t api "I2C module function list"
```

### Step 3: Query specific API usage

```bash
# Query specific function usage, parameters, examples
python3 $SKILL_DIR/scripts/query_manual.py -c V32G410X -t api "USART_Init function parameters and usage"
python3 $SKILL_DIR/scripts/query_manual.py -c V32G410X -t api "how to use GPIO_SetBits"
```

### Step 4: Query hardware details from reference manual (if needed)

```bash
# Query register addresses, bit field definitions
python3 $SKILL_DIR/scripts/query_manual.py -c V32G410X "USART register addresses"
python3 $SKILL_DIR/scripts/query_manual.py -c V32G410X "GPIO port base address"
```

---

## Query Usage

```bash
python3 $SKILL_DIR/scripts/query_manual.py --chip <CHIP_NAME> [--type <TYPE>] "<question>"
```

### Document Types

| Type | Description | Use Cases |
|------|-------------|-----------|
| `ref` | Reference Manual (default) | Registers, hardware config, peripheral specs, pins |
| `api` | API Reference | Driver library functions, parameters, examples |

---

## Examples

### Query Reference Manual (registers, hardware config)

```bash
python3 $SKILL_DIR/scripts/query_manual.py --chip RN7326 "EMUCON register address"
python3 $SKILL_DIR/scripts/query_manual.py --chip RN7326 "DMA_CH_SEL register definition"
python3 $SKILL_DIR/scripts/query_manual.py -c V32G410 "GPIO config registers"
```

### Query API Reference (driver library functions)

```bash
# Discover available APIs
python3 $SKILL_DIR/scripts/query_manual.py -c V32G410X -t api "list all timer functions"

# Query specific usage
python3 $SKILL_DIR/scripts/query_manual.py -c V32G410X -t api "TMR_TimeBaseInit parameters"
python3 $SKILL_DIR/scripts/query_manual.py -c V32G410X -t api "how to configure PWM output"
```

---

## Concurrency Limit

**Maximum 3 concurrent queries.** Do NOT run more than 3 query_manual.py commands in parallel to avoid API rate limits.

---

## Tips

- **Check availability first**: Use `--list` or read `config.yaml` to confirm chip has required document type
- **Discover APIs first**: When developing drivers, query module functions before specific usage
- Use exact register/function names when possible
- If "not found", try broader keywords
- Common API prefixes: `GPIO_*`, `USART_*`, `SPI_*`, `I2C_*`, `TMR_*`, `ADC_*`, `DMA_*`
