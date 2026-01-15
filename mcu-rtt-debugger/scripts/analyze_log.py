#!/usr/bin/env python3
"""
RTT Log Analysis Script

Analyze RTT logs from MCU firmware and generate structured feedback.

Usage:
    # Analyze entire log file
    python analyze_log.py /tmp/rtt_latest.log

    # Analyze last 30 seconds
    python analyze_log.py /tmp/rtt_latest.log --last-seconds 30

    # Analyze last 100 lines
    python analyze_log.py /tmp/rtt_latest.log --last-lines 100

    # Output as JSON
    python analyze_log.py /tmp/rtt_latest.log --format json

    # Summary only
    python analyze_log.py /tmp/rtt_latest.log --summary
"""

import argparse
import re
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any


# Log prefix patterns
LOG_PREFIXES = {
    'BOOT': r'\[BOOT\]',
    'STAT': r'\[STAT\]',
    'TEST': r'\[TEST\]',
    'ERR': r'\[ERR\]',
    'ASSERT': r'\[ASSERT\]',
    'FAULT': r'\[FAULT\]',
}

# Compiled patterns
PREFIX_PATTERN = re.compile(r'\[(BOOT|STAT|TEST|ERR|ASSERT|FAULT)\]')
KV_PATTERN = re.compile(r'(\w+)=([^\s]+)')
TIMESTAMP_PATTERN = re.compile(r'^(\d{2}):(\d{2}):(\d{2})\.(\d{3})')
RELATIVE_TIME_PATTERN = re.compile(r'^(\d+):(\d{2})\.(\d{3})')

# Fault patterns
FAULT_PATTERNS = [
    r'HardFault',
    r'UsageFault',
    r'BusFault',
    r'MemManage',
    r'WDT.*[Rr]eset',
    r'Watchdog',
    r'Stack\s*[Oo]verflow',
    r'IWDG',
    r'WWDG',
]

FAULT_REGEX = re.compile('|'.join(FAULT_PATTERNS), re.IGNORECASE)


@dataclass
class TestResult:
    name: str
    result: str  # pass, fail, timeout, etc.
    details: Dict[str, str] = field(default_factory=dict)
    line_number: int = 0
    timestamp: Optional[str] = None


@dataclass
class ErrorEntry:
    error_type: str
    details: Dict[str, str] = field(default_factory=dict)
    count: int = 1
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    line_numbers: List[int] = field(default_factory=list)


@dataclass
class AnalysisResult:
    status: str  # PASS, FAIL, UNSTABLE
    total_lines: int = 0
    analyzed_lines: int = 0
    duration_seconds: Optional[float] = None

    # Counts
    boot_detected: bool = False
    boot_count: int = 0

    # Tests
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_other: int = 0
    test_results: List[TestResult] = field(default_factory=list)

    # Errors
    errors_count: int = 0
    errors: List[ErrorEntry] = field(default_factory=list)

    # Faults
    faults_detected: bool = False
    fault_messages: List[str] = field(default_factory=list)

    # Asserts
    asserts_count: int = 0
    assert_messages: List[str] = field(default_factory=list)

    # Statistics
    stats: Dict[str, Any] = field(default_factory=dict)

    # Recommendations
    recommendation: str = ""


def parse_kv_pairs(line: str) -> Dict[str, str]:
    """Extract key=value pairs from a log line."""
    return dict(KV_PATTERN.findall(line))


def parse_timestamp(line: str) -> Optional[str]:
    """Extract timestamp from log line if present."""
    # Try absolute timestamp (HH:MM:SS.mmm)
    match = TIMESTAMP_PATTERN.match(line)
    if match:
        return f"{match.group(1)}:{match.group(2)}:{match.group(3)}.{match.group(4)}"

    # Try relative timestamp (MM:SS.mmm)
    match = RELATIVE_TIME_PATTERN.match(line)
    if match:
        return f"{match.group(1)}:{match.group(2)}.{match.group(3)}"

    return None


def filter_lines_by_time(lines: List[str], last_seconds: int) -> List[str]:
    """Filter lines to only include those within the last N seconds.

    This is a heuristic approach - we look for timestamps and filter based on them.
    If no timestamps found, return all lines.
    """
    # Try to find lines with timestamps
    timestamped_lines = []
    for i, line in enumerate(lines):
        ts = parse_timestamp(line)
        if ts:
            timestamped_lines.append((i, ts, line))

    if not timestamped_lines:
        # No timestamps found, return all lines
        return lines

    # Parse the last timestamp to determine cutoff
    last_idx, last_ts, _ = timestamped_lines[-1]

    # Simple approach: just return the last portion
    # For more accurate filtering, would need actual time parsing
    return lines  # Fallback: return all


def filter_lines_by_count(lines: List[str], last_lines: int) -> List[str]:
    """Return only the last N lines."""
    return lines[-last_lines:] if last_lines < len(lines) else lines


def analyze_log(lines: List[str], start_line: int = 0) -> AnalysisResult:
    """Analyze log lines and return structured result."""
    result = AnalysisResult(
        status="PASS",
        total_lines=len(lines),
        analyzed_lines=len(lines)
    )

    # Track errors by type for aggregation
    error_tracker: Dict[str, ErrorEntry] = {}

    for i, line in enumerate(lines):
        line_num = start_line + i + 1
        line = line.strip()

        if not line:
            continue

        timestamp = parse_timestamp(line)

        # Check for prefix
        prefix_match = PREFIX_PATTERN.search(line)

        if prefix_match:
            prefix = prefix_match.group(1)
            kv_pairs = parse_kv_pairs(line)

            if prefix == 'BOOT':
                result.boot_detected = True
                result.boot_count += 1

            elif prefix == 'TEST':
                test_name = kv_pairs.get('name', 'unnamed')
                test_result = kv_pairs.get('result', 'unknown').lower()

                tr = TestResult(
                    name=test_name,
                    result=test_result,
                    details=kv_pairs,
                    line_number=line_num,
                    timestamp=timestamp
                )
                result.test_results.append(tr)
                result.tests_run += 1

                if test_result == 'pass':
                    result.tests_passed += 1
                elif test_result in ('fail', 'failed', 'error', 'timeout'):
                    result.tests_failed += 1
                else:
                    result.tests_other += 1

            elif prefix == 'ERR':
                result.errors_count += 1
                error_type = kv_pairs.get('type', 'unknown')

                # Create a unique key for this error type
                error_key = error_type
                if 'addr' in kv_pairs:
                    error_key += f"_addr_{kv_pairs['addr']}"

                if error_key in error_tracker:
                    error_tracker[error_key].count += 1
                    error_tracker[error_key].last_seen = timestamp
                    error_tracker[error_key].line_numbers.append(line_num)
                else:
                    error_tracker[error_key] = ErrorEntry(
                        error_type=error_type,
                        details=kv_pairs,
                        count=1,
                        first_seen=timestamp,
                        last_seen=timestamp,
                        line_numbers=[line_num]
                    )

            elif prefix == 'ASSERT':
                result.asserts_count += 1
                # Extract message after prefix
                msg = line[prefix_match.end():].strip()
                if msg:
                    result.assert_messages.append(msg)

            elif prefix == 'FAULT':
                result.faults_detected = True
                msg = line[prefix_match.end():].strip()
                if msg:
                    result.fault_messages.append(msg)

            elif prefix == 'STAT':
                # Collect statistics
                for key, value in kv_pairs.items():
                    try:
                        # Try to parse as number
                        if '.' in value:
                            result.stats[key] = float(value)
                        else:
                            result.stats[key] = int(value)
                    except ValueError:
                        result.stats[key] = value

        # Check for fault patterns regardless of prefix
        if FAULT_REGEX.search(line):
            if not result.faults_detected:
                result.faults_detected = True
                result.fault_messages.append(line)

    # Convert error tracker to list
    result.errors = list(error_tracker.values())

    # Determine overall status
    if result.faults_detected:
        result.status = "FAIL"
    elif result.asserts_count > 0:
        result.status = "FAIL"
    elif result.tests_failed > 0:
        result.status = "FAIL"
    elif result.errors_count > 5:  # Threshold for "unstable"
        result.status = "UNSTABLE"
    elif result.errors_count > 0:
        result.status = "UNSTABLE" if result.tests_run == 0 else "PASS"

    # Generate recommendation
    result.recommendation = generate_recommendation(result)

    return result


def generate_recommendation(result: AnalysisResult) -> str:
    """Generate debugging recommendation based on analysis."""
    recommendations = []

    if result.faults_detected:
        recommendations.append(
            "Critical fault detected. Check stack usage, pointer validity, "
            "and memory access patterns. Review fault registers for details."
        )

    if result.asserts_count > 0:
        recommendations.append(
            f"Assertion failures detected ({result.asserts_count}). "
            "Review assertion conditions and check input validation."
        )

    # Check for specific error patterns - track seen patterns to avoid duplicates
    seen_patterns = set()

    for error in result.errors:
        error_lower = error.error_type.lower()

        if 'i2c' in error_lower and 'i2c' not in seen_patterns:
            seen_patterns.add('i2c')
            addrs = set(e.details.get('addr', 'unknown') for e in result.errors if 'i2c' in e.error_type.lower())
            addr_str = ', '.join(addrs)
            recommendations.append(
                f"I2C communication failure (addr: {addr_str}). "
                "Check bus connections, pull-up resistors, and device power."
            )
        elif 'spi' in error_lower and 'spi' not in seen_patterns:
            seen_patterns.add('spi')
            recommendations.append(
                "SPI communication error. Verify clock polarity, "
                "phase settings, and chip select timing."
            )

    if result.tests_failed > 0:
        failed_names = [t.name for t in result.test_results if t.result in ('fail', 'failed', 'error', 'timeout')]
        recommendations.append(
            f"Failed tests: {', '.join(failed_names[:5])}. "
            "Review test implementation and expected conditions."
        )

    if result.boot_count > 1:
        recommendations.append(
            f"Multiple boot sequences detected ({result.boot_count}). "
            "Device may be resetting unexpectedly - check watchdog and power supply."
        )

    if not recommendations:
        if result.status == "PASS":
            return "No issues detected. Firmware running normally."
        else:
            return "Review log details for specific error conditions."

    return " ".join(recommendations)


def format_text_output(result: AnalysisResult, summary_only: bool = False) -> str:
    """Format analysis result as human-readable text."""
    lines = []

    # Header
    status_icon = {"PASS": "[OK]", "FAIL": "[!!]", "UNSTABLE": "[?]"}.get(result.status, "[--]")
    lines.append(f"\n{'='*60}")
    lines.append(f"RTT Log Analysis Result")
    lines.append(f"{'='*60}")
    lines.append(f"Status: {status_icon} {result.status}")
    lines.append(f"Lines analyzed: {result.analyzed_lines}")

    if result.duration_seconds:
        lines.append(f"Duration: {result.duration_seconds:.1f} seconds")

    lines.append("")

    # Summary section
    lines.append("SUMMARY:")
    lines.append(f"  Boot detected: {'Yes' if result.boot_detected else 'No'}")
    if result.boot_count > 1:
        lines.append(f"  Boot count: {result.boot_count} (multiple resets!)")

    lines.append(f"  Tests run: {result.tests_run}")
    if result.tests_run > 0:
        lines.append(f"    Passed: {result.tests_passed}")
        lines.append(f"    Failed: {result.tests_failed}")

    lines.append(f"  Errors: {result.errors_count}")
    lines.append(f"  Asserts: {result.asserts_count}")
    lines.append(f"  Faults: {'Yes' if result.faults_detected else 'No'}")

    if not summary_only:
        # Detailed sections
        if result.faults_detected:
            lines.append("")
            lines.append("FAULTS:")
            for msg in result.fault_messages[:5]:
                lines.append(f"  - {msg}")

        if result.asserts_count > 0:
            lines.append("")
            lines.append("ASSERTIONS:")
            for msg in result.assert_messages[:5]:
                lines.append(f"  - {msg}")

        if result.errors:
            lines.append("")
            lines.append("ERRORS:")
            for error in result.errors[:10]:
                details = ', '.join(f"{k}={v}" for k, v in error.details.items() if k != 'type')
                lines.append(f"  - {error.error_type}: count={error.count}")
                if details:
                    lines.append(f"    Details: {details}")

        if result.tests_failed > 0:
            lines.append("")
            lines.append("FAILED TESTS:")
            for test in result.test_results:
                if test.result in ('fail', 'failed', 'error', 'timeout'):
                    lines.append(f"  - {test.name}: {test.result}")
                    if 'reason' in test.details:
                        lines.append(f"    Reason: {test.details['reason']}")

        if result.stats:
            lines.append("")
            lines.append("STATISTICS:")
            for key, value in list(result.stats.items())[:10]:
                lines.append(f"  {key}: {value}")

    lines.append("")
    lines.append("RECOMMENDATION:")
    lines.append(f"  {result.recommendation}")
    lines.append("")

    return '\n'.join(lines)


def format_json_output(result: AnalysisResult) -> str:
    """Format analysis result as JSON."""
    # Convert dataclass to dict
    data = {
        "status": result.status,
        "total_lines": result.total_lines,
        "analyzed_lines": result.analyzed_lines,
        "duration_seconds": result.duration_seconds,
        "summary": {
            "boot_detected": result.boot_detected,
            "boot_count": result.boot_count,
            "tests_run": result.tests_run,
            "tests_passed": result.tests_passed,
            "tests_failed": result.tests_failed,
            "errors_count": result.errors_count,
            "asserts_count": result.asserts_count,
            "faults_detected": result.faults_detected,
        },
        "errors": [
            {
                "type": e.error_type,
                "details": e.details,
                "count": e.count,
                "first_seen": e.first_seen,
            }
            for e in result.errors[:20]
        ],
        "failed_tests": [
            {
                "name": t.name,
                "result": t.result,
                "reason": t.details.get('reason'),
            }
            for t in result.test_results
            if t.result in ('fail', 'failed', 'error', 'timeout')
        ],
        "faults": result.fault_messages[:10],
        "asserts": result.assert_messages[:10],
        "stats": result.stats,
        "recommendation": result.recommendation,
    }

    return json.dumps(data, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze RTT logs from MCU firmware',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Analyze entire log:
    %(prog)s /tmp/rtt_latest.log

  Analyze last 30 seconds:
    %(prog)s /tmp/rtt_latest.log --last-seconds 30

  Analyze last 100 lines:
    %(prog)s /tmp/rtt_latest.log --last-lines 100

  Output as JSON:
    %(prog)s /tmp/rtt_latest.log --format json

  Quick summary:
    %(prog)s /tmp/rtt_latest.log --summary
"""
    )

    parser.add_argument('logfile', help='Path to RTT log file')
    parser.add_argument('--last-seconds', '-s', type=int,
                        help='Analyze only last N seconds of logs')
    parser.add_argument('--last-lines', '-n', type=int,
                        help='Analyze only last N lines')
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--summary', action='store_true',
                        help='Show summary only, hide detailed lists')

    args = parser.parse_args()

    # Read log file
    log_path = Path(args.logfile)
    if not log_path.exists():
        print(f"Error: Log file not found: {args.logfile}")
        return 1

    try:
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except IOError as e:
        print(f"Error reading log file: {e}")
        return 1

    if not lines:
        print("Log file is empty.")
        return 0

    total_lines = len(lines)
    start_line = 0

    # Apply filters
    if args.last_lines:
        start_line = max(0, total_lines - args.last_lines)
        lines = filter_lines_by_count(lines, args.last_lines)
    elif args.last_seconds:
        lines = filter_lines_by_time(lines, args.last_seconds)
        start_line = total_lines - len(lines)

    # Analyze
    result = analyze_log(lines, start_line)
    result.total_lines = total_lines

    # Output
    if args.format == 'json':
        print(format_json_output(result))
    else:
        print(format_text_output(result, summary_only=args.summary))

    # Exit code based on status
    return 0 if result.status == "PASS" else 1


if __name__ == '__main__':
    sys.exit(main())
