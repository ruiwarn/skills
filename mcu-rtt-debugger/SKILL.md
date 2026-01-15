---
name: mcu-rtt-debugger
description: MCU online debugging skill using SEGGER J-Link RTT for automated log collection and AI-driven analysis. Use when users need to debug embedded MCU firmware, collect RTT logs, analyze runtime behavior, or get AI feedback on firmware execution status. Triggers on phrases like "start debugging", "check MCU logs", "online debug", "RTT logs", "analyze firmware", or "run tests on MCU".
---

# MCU RTT Debugger

Automated MCU debugging skill using SEGGER J-Link RTT. Enables headless log collection, analysis, and AI-driven feedback without GUI dependencies.

## Prerequisites

- **J-Link Software**: JLinkRTTLogger must be installed and in PATH
- **Hardware**: J-Link debugger connected via SWD/JTAG
- **Firmware**: Target MCU must have RTT initialized (SEGGER_RTT)

Verify installation:
```bash
which JLinkRTTLogger || echo "JLinkRTTLogger not found in PATH"
```

## Quick Start

### 1. Start RTT Log Collection

```bash
python scripts/rtt_control.py start \
  --device STM32F103C8 \
  --speed 4000 \
  --channel 0 \
  --output /tmp/rtt_latest.log
```

### 2. Wait and Collect Logs

```bash
# Run for 30 seconds, then stop
python scripts/rtt_control.py start --device STM32F103C8 --duration 30
```

### 3. Analyze Logs

```bash
python scripts/analyze_log.py /tmp/rtt_latest.log
```

## Available Scripts

### scripts/rtt_control.py

RTT log collection control. Run with `--help` for full options.

**Key Commands:**
- `start` - Start RTT log collection
- `stop` - Stop running RTT session
- `status` - Check if RTT is running

**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--device` | MCU device name (e.g., STM32F103C8) | Required |
| `--interface` | Debug interface (SWD/JTAG) | SWD |
| `--speed` | SWD clock speed in kHz | 4000 |
| `--channel` | RTT Up Channel number | 0 |
| `--output` | Log output file path | /tmp/rtt_latest.log |
| `--duration` | Auto-stop after N seconds | None (manual) |
| `--background` | Run in background mode | False |

### scripts/analyze_log.py

Log analysis and AI feedback generation. Run with `--help` for full options.

**Key Options:**
- `--last-seconds N` - Analyze only last N seconds
- `--last-lines N` - Analyze only last N lines
- `--format json|text` - Output format
- `--summary` - Generate executive summary only

## Typical Workflow

When user says: "Start online debugging for 30 seconds, check if code runs correctly"

Execute this workflow:

1. **Start RTT collection in background**
   ```bash
   python scripts/rtt_control.py start \
     --device <MCU_DEVICE> \
     --duration 30 \
     --background
   ```

2. **Wait for collection to complete** (or manually stop early)

3. **Analyze collected logs**
   ```bash
   python scripts/analyze_log.py /tmp/rtt_latest.log --summary
   ```

4. **Report findings** with structured conclusion:
   - Runtime status: PASS / FAIL / UNSTABLE
   - Error summary (if any)
   - Debugging recommendations

## Log Format Convention

For optimal AI analysis, firmware should follow the structured log format. See [references/log_format.md](references/log_format.md) for detailed specification.

**Required Prefixes:**
- `[BOOT]` - Boot/initialization messages
- `[STAT]` - Status/statistics
- `[TEST]` - Test results
- `[ERR]` - Errors
- `[ASSERT]` - Assertion failures
- `[FAULT]` - HardFault/system faults

**Recommended Key-Value Format:**
```
[TEST] name=spi_dma result=pass
[ERR] type=i2c_nack addr=0x68
[STAT] loop_hz=998 heap_free=4096
```

## Error Handling

| Scenario | Script Behavior |
|----------|-----------------|
| J-Link not connected | Exit with clear error message |
| MCU not responding | Retry 3 times, then report failure |
| RTT not initialized | Report "RTT control block not found" |
| MCU reset during logging | Attempt to re-attach automatically |

## Analysis Output Example

```json
{
  "status": "FAIL",
  "duration_seconds": 30,
  "summary": {
    "boot_detected": true,
    "tests_run": 5,
    "tests_passed": 4,
    "tests_failed": 1,
    "errors_count": 2,
    "faults_detected": false
  },
  "errors": [
    {"type": "i2c_nack", "addr": "0x68", "count": 2, "first_seen": "00:15.234"}
  ],
  "failed_tests": [
    {"name": "i2c_sensor_read", "reason": "timeout"}
  ],
  "recommendation": "I2C communication failure detected. Check I2C bus connections and pull-up resistors. Verify device at address 0x68 is powered and responding."
}
```

## Extending This Skill

Future enhancements (not in current scope):
- Auto flash firmware before debugging
- Multi-channel RTT support
- CI/HIL test integration
- Automated reset/retry cycles
