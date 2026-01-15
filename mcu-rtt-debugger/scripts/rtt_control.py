#!/usr/bin/env python3
"""
RTT Log Collection Control Script

Start, stop, and manage SEGGER J-Link RTT log collection sessions.

Usage:
    # Start RTT logging
    python rtt_control.py start --device STM32F103C8 --output /tmp/rtt.log

    # Start with auto-stop after 30 seconds
    python rtt_control.py start --device STM32F103C8 --duration 30

    # Start in background mode
    python rtt_control.py start --device STM32F103C8 --background

    # Stop RTT logging
    python rtt_control.py stop

    # Check status
    python rtt_control.py status
"""

import argparse
import subprocess
import os
import sys
import signal
import time
import json
from pathlib import Path
from datetime import datetime

# Default paths
DEFAULT_LOG_PATH = "/tmp/rtt_latest.log"
PID_FILE = "/tmp/rtt_logger.pid"
SESSION_INFO_FILE = "/tmp/rtt_session.json"


def is_wsl():
    """Check if running in WSL."""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower()
    except:
        return False


def find_jlink_rtt_logger():
    """Find JLinkRTTLogger executable."""
    # Common installation paths
    search_paths = [
        "/opt/SEGGER/JLink/JLinkRTTLogger",
        "/usr/bin/JLinkRTTLogger",
        "/usr/local/bin/JLinkRTTLogger",
        os.path.expanduser("~/SEGGER/JLink/JLinkRTTLogger"),
    ]

    # WSL paths - check Windows installation
    wsl_paths = [
        "/mnt/c/Program Files/SEGGER/JLink/JLinkRTTLogger.exe",
        "/mnt/c/Program Files (x86)/SEGGER/JLink/JLinkRTTLogger.exe",
    ]

    # Check if in PATH
    import shutil
    jlink_path = shutil.which("JLinkRTTLogger")
    if jlink_path:
        return jlink_path

    # Check common paths
    for path in search_paths:
        if os.path.exists(path):
            return path

    # Check WSL paths
    if is_wsl():
        for path in wsl_paths:
            if os.path.exists(path):
                return path

    return None


def save_session_info(device, interface, speed, channel, output, pid, start_time):
    """Save session information for later reference."""
    info = {
        "device": device,
        "interface": interface,
        "speed": speed,
        "channel": channel,
        "output": output,
        "pid": pid,
        "start_time": start_time.isoformat(),
    }
    with open(SESSION_INFO_FILE, 'w') as f:
        json.dump(info, f, indent=2)


def load_session_info():
    """Load session information."""
    if not os.path.exists(SESSION_INFO_FILE):
        return None
    try:
        with open(SESSION_INFO_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def clear_session_info():
    """Clear session information."""
    for f in [SESSION_INFO_FILE, PID_FILE]:
        if os.path.exists(f):
            os.remove(f)


def is_process_running(pid):
    """Check if a process with given PID is running."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def get_running_pid():
    """Get PID of running RTT logger process."""
    if not os.path.exists(PID_FILE):
        return None
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        if is_process_running(pid):
            return pid
        # PID file exists but process is dead
        clear_session_info()
        return None
    except (ValueError, IOError):
        return None


def start_rtt(args):
    """Start RTT log collection."""
    # Check if already running
    existing_pid = get_running_pid()
    if existing_pid:
        print(f"Error: RTT logger already running (PID: {existing_pid})")
        print("Use 'stop' command to stop it first.")
        return 1

    # Find JLinkRTTLogger
    jlink_path = find_jlink_rtt_logger()
    if not jlink_path:
        print("Error: JLinkRTTLogger not found.")
        print("Please install J-Link Software and add to PATH.")
        print("Download from: https://www.segger.com/downloads/jlink/")
        return 1

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build JLinkRTTLogger command
    cmd = [
        jlink_path,
        "-Device", args.device,
        "-If", args.interface,
        "-Speed", str(args.speed),
        "-RTTChannel", str(args.channel),
        args.output
    ]

    print(f"Starting RTT logger...")
    print(f"  Device: {args.device}")
    print(f"  Interface: {args.interface}")
    print(f"  Speed: {args.speed} kHz")
    print(f"  Channel: {args.channel}")
    print(f"  Output: {args.output}")

    start_time = datetime.now()

    if args.background:
        # Run in background
        with open(args.output, 'w') as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )

        # Save PID
        with open(PID_FILE, 'w') as f:
            f.write(str(process.pid))

        save_session_info(
            args.device, args.interface, args.speed,
            args.channel, args.output, process.pid, start_time
        )

        # Wait a moment to check if process started successfully
        time.sleep(1)
        if not is_process_running(process.pid):
            print("Error: RTT logger failed to start. Check J-Link connection.")
            clear_session_info()
            return 1

        print(f"RTT logger started in background (PID: {process.pid})")

        if args.duration:
            print(f"Will auto-stop after {args.duration} seconds.")
            # Start a background timer to stop the process
            timer_cmd = f"sleep {args.duration} && python {__file__} stop"
            subprocess.Popen(timer_cmd, shell=True, start_new_session=True)

        return 0

    else:
        # Run in foreground
        try:
            with open(args.output, 'w') as log_file:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )

                # Save PID
                with open(PID_FILE, 'w') as f:
                    f.write(str(process.pid))

                save_session_info(
                    args.device, args.interface, args.speed,
                    args.channel, args.output, process.pid, start_time
                )

                print("RTT logger running. Press Ctrl+C to stop.")
                print("-" * 50)

                start = time.time()

                for line in process.stdout:
                    # Write to file
                    log_file.write(line)
                    log_file.flush()

                    # Also print to console
                    print(line, end='')

                    # Check duration limit
                    if args.duration and (time.time() - start) >= args.duration:
                        print(f"\nDuration limit ({args.duration}s) reached.")
                        break

                process.terminate()
                process.wait(timeout=5)

        except KeyboardInterrupt:
            print("\nStopping RTT logger...")
            process.terminate()
            process.wait(timeout=5)

        finally:
            clear_session_info()

        print(f"Logs saved to: {args.output}")
        return 0


def stop_rtt(args):
    """Stop RTT log collection."""
    pid = get_running_pid()

    if not pid:
        print("No RTT logger process running.")
        return 0

    print(f"Stopping RTT logger (PID: {pid})...")

    try:
        os.kill(pid, signal.SIGTERM)
        # Wait for process to terminate
        for _ in range(10):
            if not is_process_running(pid):
                break
            time.sleep(0.5)
        else:
            # Force kill if still running
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.5)
    except (OSError, ProcessLookupError):
        pass

    # Get session info before clearing
    session = load_session_info()
    clear_session_info()

    if session:
        print(f"RTT logger stopped. Logs saved to: {session.get('output', 'unknown')}")
    else:
        print("RTT logger stopped.")

    return 0


def status_rtt(args):
    """Check RTT logger status."""
    pid = get_running_pid()

    if not pid:
        print("RTT logger is not running.")
        return 0

    session = load_session_info()

    print("RTT logger is running.")
    print(f"  PID: {pid}")

    if session:
        print(f"  Device: {session.get('device', 'unknown')}")
        print(f"  Interface: {session.get('interface', 'unknown')}")
        print(f"  Speed: {session.get('speed', 'unknown')} kHz")
        print(f"  Channel: {session.get('channel', 'unknown')}")
        print(f"  Output: {session.get('output', 'unknown')}")

        start_time = session.get('start_time')
        if start_time:
            start = datetime.fromisoformat(start_time)
            duration = datetime.now() - start
            print(f"  Running for: {duration.total_seconds():.1f} seconds")

        # Check log file size
        output_path = session.get('output')
        if output_path and os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"  Log size: {size} bytes")

    return 0


def tail_log(args):
    """Tail the current log file."""
    session = load_session_info()

    if not session:
        # Try default path
        log_path = DEFAULT_LOG_PATH
    else:
        log_path = session.get('output', DEFAULT_LOG_PATH)

    if not os.path.exists(log_path):
        print(f"Log file not found: {log_path}")
        return 1

    lines = args.lines or 20

    try:
        with open(log_path, 'r') as f:
            all_lines = f.readlines()
            for line in all_lines[-lines:]:
                print(line, end='')
    except IOError as e:
        print(f"Error reading log: {e}")
        return 1

    return 0


def main():
    parser = argparse.ArgumentParser(
        description='SEGGER J-Link RTT Log Collection Control',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Start logging:
    %(prog)s start --device STM32F103C8

  Start with duration:
    %(prog)s start --device STM32F103C8 --duration 30

  Start in background:
    %(prog)s start --device STM32F103C8 --background

  Stop logging:
    %(prog)s stop

  Check status:
    %(prog)s status

  View recent logs:
    %(prog)s tail --lines 50
"""
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Start command
    start_parser = subparsers.add_parser('start', help='Start RTT log collection')
    start_parser.add_argument('--device', '-d', required=True,
                              help='MCU device name (e.g., STM32F103C8, nRF52832)')
    start_parser.add_argument('--interface', '-i', default='SWD',
                              choices=['SWD', 'JTAG'],
                              help='Debug interface (default: SWD)')
    start_parser.add_argument('--speed', '-s', type=int, default=4000,
                              help='SWD/JTAG clock speed in kHz (default: 4000)')
    start_parser.add_argument('--channel', '-c', type=int, default=0,
                              help='RTT Up Channel number (default: 0)')
    start_parser.add_argument('--output', '-o', default=DEFAULT_LOG_PATH,
                              help=f'Log output file (default: {DEFAULT_LOG_PATH})')
    start_parser.add_argument('--duration', '-t', type=int,
                              help='Auto-stop after N seconds')
    start_parser.add_argument('--background', '-b', action='store_true',
                              help='Run in background mode')
    start_parser.set_defaults(func=start_rtt)

    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop RTT log collection')
    stop_parser.set_defaults(func=stop_rtt)

    # Status command
    status_parser = subparsers.add_parser('status', help='Check RTT logger status')
    status_parser.set_defaults(func=status_rtt)

    # Tail command
    tail_parser = subparsers.add_parser('tail', help='View recent log entries')
    tail_parser.add_argument('--lines', '-n', type=int, default=20,
                             help='Number of lines to show (default: 20)')
    tail_parser.set_defaults(func=tail_log)

    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
