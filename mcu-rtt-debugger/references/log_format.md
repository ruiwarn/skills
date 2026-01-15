# RTT Log Format Specification

Firmware-side logging conventions for optimal AI analysis.

## Overview

This document defines the structured log format that firmware should emit via RTT for automated analysis. Following these conventions enables the AI to:

- Automatically detect test pass/fail status
- Identify and categorize errors
- Detect critical faults (HardFault, WDT reset, etc.)
- Track system statistics
- Generate actionable debugging recommendations

## Log Format

### General Structure

```
[PREFIX] key1=value1 key2=value2 optional free text
```

- **Prefix**: Category tag in square brackets (required)
- **Key-Value pairs**: Space-separated, no quotes needed for simple values
- **Free text**: Optional additional context after key-value pairs

### Timestamp (Optional)

If timestamps are included, use one of these formats:

```
MM:SS.mmm [PREFIX] ...      # Relative time (minutes:seconds.milliseconds)
HH:MM:SS.mmm [PREFIX] ...   # Absolute time
```

Example:
```
00:15.234 [TEST] name=spi_loopback result=pass
```

## Required Prefixes

### [BOOT] - Boot/Initialization

Emitted when MCU boots or resets. Helps detect unexpected resets.

```c
SEGGER_RTT_printf(0, "[BOOT] reason=power_on version=1.2.3\n");
SEGGER_RTT_printf(0, "[BOOT] reason=wdt_reset\n");
SEGGER_RTT_printf(0, "[BOOT] reason=soft_reset\n");
```

**Recommended keys:**
- `reason`: power_on, wdt_reset, soft_reset, brownout, pin_reset
- `version`: Firmware version string
- `build`: Build number or date

### [STAT] - Status/Statistics

Periodic status updates for monitoring system health.

```c
SEGGER_RTT_printf(0, "[STAT] loop_hz=%d heap_free=%d\n", loop_freq, free_heap);
SEGGER_RTT_printf(0, "[STAT] cpu_load=45 temp_c=32\n");
```

**Recommended keys:**
- `loop_hz`: Main loop frequency
- `heap_free`: Free heap bytes
- `stack_free`: Free stack bytes
- `cpu_load`: CPU utilization percentage
- `uptime_s`: Seconds since boot

### [TEST] - Test Results

Used for self-test or functional test results.

```c
SEGGER_RTT_printf(0, "[TEST] name=spi_loopback result=pass\n");
SEGGER_RTT_printf(0, "[TEST] name=i2c_sensor result=fail reason=timeout\n");
SEGGER_RTT_printf(0, "[TEST] name=adc_calibration result=pass value=2048\n");
```

**Required keys:**
- `name`: Test identifier (use underscores, no spaces)
- `result`: pass, fail, skip, timeout, error

**Optional keys:**
- `reason`: Failure reason
- `expected`: Expected value
- `actual`: Actual value
- `duration_ms`: Test duration

### [ERR] - Errors

Non-fatal errors that should be logged.

```c
SEGGER_RTT_printf(0, "[ERR] type=i2c_nack addr=0x68\n");
SEGGER_RTT_printf(0, "[ERR] type=spi_timeout dev=flash\n");
SEGGER_RTT_printf(0, "[ERR] type=checksum_mismatch expected=0xAB actual=0xCD\n");
```

**Required keys:**
- `type`: Error type identifier

**Common error types:**
- `i2c_nack`: I2C device not acknowledging
- `i2c_timeout`: I2C bus timeout
- `spi_timeout`: SPI timeout
- `uart_overrun`: UART buffer overrun
- `checksum_mismatch`: Data integrity failure
- `timeout`: Generic timeout
- `invalid_param`: Invalid parameter

### [ASSERT] - Assertion Failures

Assertion failures that indicate programming errors.

```c
SEGGER_RTT_printf(0, "[ASSERT] file=main.c line=142 expr=ptr!=NULL\n");
SEGGER_RTT_printf(0, "[ASSERT] Buffer overflow detected\n");
```

**Recommended keys:**
- `file`: Source file name
- `line`: Line number
- `expr`: Failed expression
- `func`: Function name

### [FAULT] - Critical Faults

System-level faults (HardFault, etc.). These indicate critical issues.

```c
SEGGER_RTT_printf(0, "[FAULT] type=HardFault pc=0x08001234 lr=0x08005678\n");
SEGGER_RTT_printf(0, "[FAULT] type=UsageFault reason=div_by_zero\n");
SEGGER_RTT_printf(0, "[FAULT] type=StackOverflow task=main\n");
```

**Required keys:**
- `type`: Fault type (HardFault, UsageFault, BusFault, MemManage, StackOverflow, WDT)

**Recommended keys for ARM faults:**
- `pc`: Program counter
- `lr`: Link register
- `sp`: Stack pointer
- `cfsr`: Configurable Fault Status Register

## C Implementation Example

```c
#include "SEGGER_RTT.h"

// Simple macros for structured logging
#define LOG_BOOT(reason)     SEGGER_RTT_printf(0, "[BOOT] reason=%s\n", reason)
#define LOG_STAT(fmt, ...)   SEGGER_RTT_printf(0, "[STAT] " fmt "\n", ##__VA_ARGS__)
#define LOG_TEST(name, res)  SEGGER_RTT_printf(0, "[TEST] name=%s result=%s\n", name, res)
#define LOG_ERR(type, ...)   SEGGER_RTT_printf(0, "[ERR] type=%s " __VA_ARGS__ "\n", type)
#define LOG_ASSERT(msg)      SEGGER_RTT_printf(0, "[ASSERT] %s\n", msg)
#define LOG_FAULT(type, ...) SEGGER_RTT_printf(0, "[FAULT] type=%s " __VA_ARGS__ "\n", type)

// Usage examples
void example_usage(void) {
    // Boot message
    LOG_BOOT("power_on");

    // Periodic stats
    LOG_STAT("loop_hz=%d heap_free=%d", 1000, 4096);

    // Test result
    LOG_TEST("spi_flash", "pass");
    LOG_TEST("i2c_sensor", "fail reason=timeout");

    // Error
    LOG_ERR("i2c_nack", "addr=0x68");

    // Assert (typically in assert handler)
    LOG_ASSERT("file=main.c line=42");

    // Fault (typically in fault handler)
    LOG_FAULT("HardFault", "pc=0x08001234 lr=0x08005678");
}
```

## Best Practices

### DO:
- Keep log lines short (< 200 chars)
- Use consistent key names across the codebase
- Include `name` for all TEST entries
- Include `type` for all ERR entries
- Use lowercase for values (pass, fail, not PASS, FAIL)
- Use underscores for multi-word identifiers (spi_flash, not spi-flash)
- End each log line with `\n`

### DON'T:
- Include spaces in key names or values
- Use variable-length formats that make parsing difficult
- Log binary data directly
- Omit required prefixes
- Use inconsistent capitalization

## AI Analysis Behavior

The analysis script will:

1. **Detect boot events**: Multiple [BOOT] entries indicate unexpected resets
2. **Track test results**: Count pass/fail from [TEST] entries
3. **Aggregate errors**: Group [ERR] by type and count occurrences
4. **Detect critical faults**: Flag any [FAULT] or [ASSERT] as critical
5. **Calculate statistics**: Track values from [STAT] entries
6. **Generate recommendations**: Based on error patterns and fault types

### Status Determination

| Condition | Status |
|-----------|--------|
| Any [FAULT] detected | FAIL |
| Any [ASSERT] detected | FAIL |
| Any [TEST] result=fail | FAIL |
| Error count > 5 | UNSTABLE |
| Error count 1-5, tests pass | PASS (with warnings) |
| No errors, tests pass | PASS |
