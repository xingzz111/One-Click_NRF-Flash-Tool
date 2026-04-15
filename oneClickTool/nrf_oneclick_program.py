#!/usr/bin/env python3

import argparse
import hashlib
import os
import platform
import re
import shlex
import subprocess
import sys
import tempfile
import time
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

_BASE_DIR = None
try:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        _BASE_DIR = Path(getattr(sys, "_MEIPASS")).resolve()
    else:
        _BASE_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(_BASE_DIR))
except Exception:
    _BASE_DIR = Path(".").resolve()


_RPC_IMPORT_ERROR: Optional[BaseException] = None


def _is_rosetta_translated() -> bool:
    if sys.platform != "darwin":
        return False
    try:
        p = subprocess.run(["sysctl", "-n", "sysctl.proc_translated"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        return (p.stdout or "").strip() == "1"
    except Exception:
        return False


def _maybe_reexec_x86_64_for_rpc() -> None:
    if sys.platform != "darwin":
        return
    if os.environ.get("NRFFLASHTOOL_REEXEC_X86") == "1":
        return
    if "--no-rpc" in sys.argv:
        return
    if platform.machine().lower() != "arm64":
        return
    if _is_rosetta_translated():
        return
    exe = sys.executable
    if not exe:
        return
    os.environ["NRFFLASHTOOL_REEXEC_X86"] = "1"
    try:
        os.execvp("arch", ["arch", "-x86_64", exe] + sys.argv[1:])
    except Exception:
        return


def _get_rpc_client_wrapper():
    global _RPC_IMPORT_ERROR
    try:
        from mix.lynx.rpc.rpc_client import RPCClientWrapper  # type: ignore
        return RPCClientWrapper
    except Exception as ex:
        _RPC_IMPORT_ERROR = ex
        msg = str(ex)
        if sys.platform == "darwin" and platform.machine().lower() == "arm64":
            if "wrong architecture" in msg.lower() or "mach-o" in msg.lower():
                _maybe_reexec_x86_64_for_rpc()
        return None


# =============================================================================
# ANSI Color Codes for Beautiful CLI Output
# =============================================================================
class Colors:
    """ANSI color codes for terminal output styling.
    
    Optimized for WHITE/LIGHT terminal backgrounds.
    """
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Standard colors (dark colors work best on white background)
    BLACK = "\033[30m"   # Pure black - primary text
    RED = "\033[31m"     # Dark red - errors
    GREEN = "\033[32m"   # Dark green - success
    YELLOW = "\033[33m"  # Dark yellow - warnings
    BLUE = "\033[34m"    # Dark blue - info
    MAGENTA = "\033[35m" # Dark magenta - highlights
    CYAN = "\033[36m"    # Dark cyan - accents
    WHITE = "\033[37m"   # White

    # Bright colors (use sparingly on white bg)
    BRIGHT_BLACK = "\033[90m"   # Dark gray - very dim text
    BRIGHT_RED = "\033[91m"    # Bright red - errors
    BRIGHT_GREEN = "\033[92m"  # Bright green - success
    BRIGHT_YELLOW = "\033[93m" # Bright yellow - warnings
    BRIGHT_BLUE = "\033[94m"   # Bright blue - info
    BRIGHT_MAGENTA = "\033[95m" # Bright magenta - highlights
    BRIGHT_CYAN = "\033[96m"   # Bright cyan - accents
    BRIGHT_WHITE = "\033[97m"  # White

    # Background colors (for colored backgrounds)
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


class Style:
    """Pre-defined color styles for different output types.
    
    Optimized for WHITE/LIGHT terminal backgrounds.
    All colors are dark to ensure high contrast on white.
    """

    # Primary colors - dark, high contrast on white
    TITLE = f"{Colors.BOLD}{Colors.BLUE}"           # Dark blue for title
    HEADER = f"{Colors.BOLD}{Colors.BLUE}"          # Dark blue for headers
    SUCCESS = f"{Colors.BOLD}{Colors.GREEN}"        # Dark green for success
    ERROR = f"{Colors.BOLD}{Colors.RED}"            # Dark red for errors (NOT bright red)
    WARNING = f"{Colors.BOLD}{Colors.YELLOW}"       # Dark yellow for warnings
    INFO = f"{Colors.BOLD}{Colors.CYAN}"           # Dark cyan for info

    # Secondary colors - dark for visibility on white
    DIM_TEXT = f"{Colors.BLACK}"                    # Black for dim text (high contrast!)
    HIGHLIGHT = f"{Colors.BOLD}{Colors.BLACK}"     # Bold black for highlight
    SERIAL_NUM = f"{Colors.BOLD}{Colors.MAGENTA}"  # Dark magenta for serial
    FILE_PATH = f"{Colors.BOLD}{Colors.BLUE}"      # Dark blue for paths
    PARAM = f"{Colors.BOLD}{Colors.CYAN}"           # Dark cyan for params

    # Box drawing - black for visibility on white
    BOX_LINE = f"{Colors.BLACK}"                    # Black for box lines
    BOX_CORNER = f"{Colors.BLACK}"                 # Black for corners


def colored(text: str, style: str) -> str:
    """Apply color style to text."""
    return f"{style}{text}{Colors.RESET}"


# =============================================================================
# ASCII Art and UI Components
# =============================================================================
ASCII_LOGO = r"""
 _   _  _____   ______
| \ | | |  __ \ |  ____|
|  \| | | |__) || |__
| . ` | |  _  / |  __|
| |\  | | | \ \ | |
|_| \_| |_|  \_\|_|

 ______ _           _     _______          _
|  ____| |         | |   |__   __|        | |
| |__  | | __ _ ___| |__    | | ___   ___ | |
|  __| | |/ _` / __| '_ \   | |/ _ \ / _ \| |
| |    | | (_| \__ \ | | |  | | (_) | (_) | |
|_|    |_|\__,_|___/_| |_|  |_|\___/ \___/|_|

"""

def print_banner() -> None:
    """Print the application banner."""
    print(colored(ASCII_LOGO, Style.TITLE))
    print(colored("=" * 70, Style.BOX_LINE))
    print(colored("  One-Click J-Link Programming Tool for Nordic nRF Devices  ", Style.INFO))
    print(colored("=" * 70, Style.BOX_LINE))
    print()


def print_separator(char: str = "─", width: int = 50) -> None:
    """Print a horizontal separator line."""
    print(colored(char * width, Style.BOX_LINE))


def print_step(step_num: int, total: int, description: str) -> None:
    """Print a step indicator."""
    progress = f"[{step_num}/{total}]"
    print(f"\n{colored(progress, Style.INFO)} {colored(description, Style.HEADER)}")


def print_status(message: str, status: str = "info") -> None:
    """Print a status message with appropriate styling."""
    icons = {
        "pending": colored("○", Style.DIM_TEXT),
        "info": colored("●", Style.INFO),
        "success": colored("OK", Style.SUCCESS),
        "error": colored("XX", Style.ERROR),
        "warning": colored("!!", Style.WARNING),
        "loading": colored("...", Style.INFO),
        "spinner": colored("...", Style.INFO),
    }
    icon = icons.get(status, icons["info"])
    # Remove extra space for better alignment
    print(f"  {icon} {message}")


def print_config_table(title: str, items: list[tuple[str, str]]) -> None:
    """Print a configuration table."""
    print()
    print(colored(f"  ┌{'─' * 46}┐", Style.BOX_LINE))
    print(colored(f"  │ {title:<44} │", Style.HEADER))
    print(colored(f"  ├{'─' * 46}┤", Style.BOX_LINE))

    for key, value in items:
        print(colored(f"  │ {key:<20} │ ", Style.DIM_TEXT) + colored(value, Style.PARAM) + colored(" │", Style.DIM_TEXT))

    print(colored(f"  └{'─' * 46}┘", Style.BOX_LINE))


# =============================================================================
# Progress Animation
# =============================================================================
class Spinner:
    """Animated spinner for loading states."""

    def __init__(self, message: str):
        self.message = message
        self.frames = ["◐", "◓", "◑", "◒"]
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def _spin(self) -> None:
        idx = 0
        while self.running:
            frame = self.frames[idx % len(self.frames)]
            print(f"\r  {colored(frame, Colors.CYAN)} {self.message}...", end="", flush=True)
            idx += 1
            time.sleep(0.15)
        # Clear the line
        print(f"\r{' ' * 60}\r", end="", flush=True)

    def start(self) -> "Spinner":
        """Start the spinner animation."""
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()
        return self

    def stop(self, message: str, status: str = "success") -> None:
        """Stop the spinner and print final message."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
        status_icon = colored("✓", Style.SUCCESS) if status == "success" else colored("✗", Style.ERROR)
        print(f"  {status_icon} {message}")


# =============================================================================
# Progress Bar
# =============================================================================
class ProgressBar:
    """ASCII progress bar for long operations."""

    def __init__(self, total: int = 100, width: int = 40, prefix: str = "Progress"):
        self.total = total
        self.width = width
        self.prefix = prefix
        self.current = 0

    def update(self, current: int, prefix: Optional[str] = None) -> None:
        """Update progress bar to current value."""
        self.current = min(current, self.total)
        prefix = prefix or self.prefix
        filled = int(self.width * self.current / max(self.total, 1))
        bar = colored("█" * filled, Colors.GREEN) + colored("░" * (self.width - filled), Colors.BRIGHT_BLACK)
        percent = int(100 * self.current / max(self.total, 1))
        print(f"\r  {prefix}: │{bar}│ {percent}%", end="", flush=True)

    def complete(self, message: str = "Done") -> None:
        """Complete the progress bar."""
        self.update(self.total, message)
        print()


# =============================================================================
# Data Classes
# =============================================================================
@dataclass(frozen=True)
class JLinkEntry:
    serial: str
    line: str


# =============================================================================
# Utility Functions
# =============================================================================
def eprint(*args: object) -> None:
    """Print to stderr."""
    print(*args, file=sys.stderr)


def normalize_drag_input(raw: str) -> str:
    """Normalize drag-and-drop input from file manager."""
    s = (raw or "").strip()
    if not s:
        return ""
    try:
        parts = shlex.split(s)
        if len(parts) == 1:
            return parts[0]
    except Exception:
        pass
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1]
    return s.strip()


def resolve_firmware_path(raw: str) -> Path:
    """Resolve firmware path, supporting both files and directories."""
    p = Path(raw).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"Firmware path not exists: {p}")

    if p.is_dir():
        candidates = []
        for child in p.iterdir():
            if child.is_file() and child.suffix.lower() in {".bin", ".hex"}:
                candidates.append(child)
        candidates.sort()

        if not candidates:
            raise FileNotFoundError(f"No .bin/.hex file found in: {p}")

        if len(candidates) > 1:
            raise RuntimeError(
                f"Multiple firmware files found in directory. "
                f"Please specify one file: {', '.join(str(x) for x in candidates)}"
            )

        return candidates[0].resolve()

    if p.suffix.lower() not in {".bin", ".hex"}:
        raise RuntimeError(f"Firmware file must be .bin or .hex: {p}")

    return p.resolve()


def prompt_firmware_path() -> Path:
    """Prompt user for firmware path with beautiful UI."""
    print()
    print(colored("  ╭──────────────────────────────────────────────╮", Style.BOX_LINE))
    print(colored("  │  📁 Firmware File Selection", Style.HEADER))
    print(colored("  ├──────────────────────────────────────────────┤", Style.BOX_LINE))
    print(colored("  │  Supported formats: .bin, .hex", Style.DIM_TEXT))
    print(colored("  │  Tip: Drag and drop file or folder here!", Style.DIM_TEXT))
    print(colored("  ╰──────────────────────────────────────────────╯", Style.BOX_LINE))
    print()

    while True:
        try:
            user_input = input(colored("  ➜ FW Path: ", Style.INFO)).strip()
            if not user_input:
                print_status("Path cannot be empty. Please provide a valid path.", "warning")
                continue

            firmware = resolve_firmware_path(normalize_drag_input(user_input))
            print_status(f"Selected: {firmware.name}", "success")
            return firmware

        except FileNotFoundError as ex:
            print_status(f"File not found: {ex}", "error")
        except RuntimeError as ex:
            print_status(f"Invalid firmware: {ex}", "error")
        except KeyboardInterrupt:
            print()
            print_status("Operation cancelled by user.", "warning")
            sys.exit(0)


# =============================================================================
# J-Link Operations
# =============================================================================
def parse_jlink_entries(show_emu_output: str) -> list[JLinkEntry]:
    """Parse J-Link device entries from command output."""
    entries: list[JLinkEntry] = []
    seen: set[str] = set()

    for line in (show_emu_output or "").splitlines():
        # Try different patterns for serial number extraction
        patterns = [
            re.search(r"Serial\s*number:\s*(\d+)", line, re.IGNORECASE),
            re.search(r"S/N:\s*(\d+)", line, re.IGNORECASE),
            re.search(r"Serial\s*#\s*:\s*(\d+)", line, re.IGNORECASE),
        ]

        m = next((p for p in patterns if p), None)
        if not m:
            continue

        sn = m.group(1)
        if sn in seen:
            continue

        seen.add(sn)
        entries.append(JLinkEntry(serial=sn, line=line.strip()))

    return entries


def run_jlink_show_emu_list(jlink_exe: Path, timeout_sec: float) -> tuple[list[JLinkEntry], str]:
    """Run J-Link command to list connected devices."""
    with tempfile.NamedTemporaryFile("w", suffix=".jlink", delete=False) as f:
        f.write("ShowEmuList\nexit\n")
        cmd_file = Path(f.name)

    try:
        cmd = [str(jlink_exe), "-CommanderScript", str(cmd_file)]
        p = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout_sec, text=True
        )
        out = p.stdout or ""
        entries = parse_jlink_entries(out)
        return entries, out
    finally:
        try:
            cmd_file.unlink(missing_ok=True)
        except Exception:
            pass


def choose_jlink_interactive(entries: list[JLinkEntry]) -> str:
    """Interactive selection when multiple J-Links are detected."""
    print()
    print(colored("  ╭──────────────────────────────────────────────╮", Style.BOX_LINE))
    print(colored("  │  🔌 Multiple J-Link Devices Detected", Style.WARNING))
    print(colored("  ├──────────────────────────────────────────────┤", Style.BOX_LINE))

    for idx, entry in enumerate(entries, start=1):
        print(colored(f"  │  [{idx}] ", Style.INFO) + colored(entry.line, Style.SERIAL_NUM) + colored(" │", Style.DIM_TEXT))

    print(colored("  ╰──────────────────────────────────────────────╯", Style.BOX_LINE))
    print()

    while True:
        try:
            user_input = input(colored("  ➜ Select J-Link (1-", Style.INFO) + f"{len(entries)}): ").strip()

            if not user_input:
                continue

            if user_input.isdigit():
                n = int(user_input)
                if 1 <= n <= len(entries):
                    selected = entries[n - 1]
                    print_status(f"Selected: S/N {selected.serial}", "success")
                    return selected.serial

            # Also accept direct serial number input
            for entry in entries:
                if entry.serial == user_input:
                    print_status(f"Selected: S/N {entry.serial}", "success")
                    return entry.serial

            print_status(f"Invalid selection. Please enter 1-{len(entries)} or a valid serial number.", "error")

        except KeyboardInterrupt:
            print()
            print_status("Operation cancelled by user.", "warning")
            sys.exit(0)


def select_jlink_serial(jlink_exe: Path, timeout_sec: float, forced_serial: Optional[str]) -> str:
    """Select J-Link serial number with UI feedback."""
    if forced_serial:
        print_status(f"Using specified J-Link: S/N {forced_serial}", "info")
        return forced_serial

    spinner = Spinner("Scanning for J-Link devices")
    spinner.start()

    try:
        entries, out = run_jlink_show_emu_list(jlink_exe, timeout_sec=timeout_sec)
    except subprocess.TimeoutExpired:
        spinner.stop("Scan timed out", "error")
        raise RuntimeError("J-Link scan timed out. Please check connections.")
    except Exception as ex:
        spinner.stop(f"Scan failed: {ex}", "error")
        raise

    spinner.stop("Scan complete")

    if not entries:
        print()
        print_status("No J-Link devices found!", "error")
        print(colored("\n  Troubleshooting tips:", Style.WARNING))
        print(colored("  • Check USB connection to J-Link", Style.DIM_TEXT))
        print(colored("  • Verify J-Link drivers are installed", Style.DIM_TEXT))
        print(colored("  • Try reconnecting the J-Link", Style.DIM_TEXT))
        raise RuntimeError("No J-Link detected via ShowEmuList")

    if len(entries) == 1:
        entry = entries[0]
        print_status(f"Single J-Link found: {entry.line}", "success")
        return entry.serial

    return choose_jlink_interactive(entries)


# =============================================================================
# Script Building
# =============================================================================
def build_commander_script(
    device: str,
    interface: str,
    speed_khz: int,
    firmware: Path,
    address: str,
    do_erase: bool,
    mode: str,
    after: str,
) -> str:
    """Build J-Link commander script for flashing."""
    lines: list[str] = []
    if mode == "strict":
        lines.append("ExitOnError 1")

    fw_path = str(firmware.resolve())

    lines += [
        f"device {device}",
        f"if {interface}",
        f"speed {speed_khz}",
        "connect",
        "sleep 1000",
    ]

    if do_erase:
        lines += ["erase", "sleep 1000"]

    if firmware.suffix.lower() == ".hex":
        lines.append(f"loadfile {fw_path}")
    else:
        lines.append(f"loadfile {fw_path}, {address}")

    if after == "reset":
        lines += ["sleep 100", "r"]
    elif after == "go":
        lines += ["sleep 100", "r", "sleep 100", "g"]

    lines.append("exit")

    return "\n".join(lines) + "\n"


def format_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.2f} MB"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def intel_hex_data_bytes(path: Path) -> Optional[int]:
    try:
        total = 0
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                line = raw.strip()
                if not line or not line.startswith(":") or len(line) < 11:
                    continue
                try:
                    count = int(line[1:3], 16)
                    rec_type = int(line[7:9], 16)
                except ValueError:
                    continue
                if rec_type == 0:
                    total += count
        return total
    except Exception:
        return None


def firmware_identity(fw: Path) -> dict:
    st = fw.stat()
    info = {
        "path": str(fw.resolve()),
        "size_bytes": int(st.st_size),
        "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
        "sha256": sha256_file(fw),
    }
    if fw.suffix.lower() == ".hex":
        info["hex_data_bytes"] = intel_hex_data_bytes(fw)
    return info


def prompt_continue(question: str, default_yes: bool = True) -> bool:
    prompt = " [Y/n]: " if default_yes else " [y/N]: "
    s = input(question + prompt).strip().lower()
    if not s:
        return default_yes
    return s in {"y", "yes"}


def prompt_optional_text(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        return ""


def resolve_firmware_interactive(previous: Optional[Path], initial: Optional[str]) -> Path:
    if initial:
        return resolve_firmware_path(normalize_drag_input(initial))
    if previous is None:
        return prompt_firmware_path()
    s = normalize_drag_input(prompt_optional_text(f"FW路径(回车保持: {previous}): "))
    if not s:
        return previous
    return resolve_firmware_path(s)


def script_output_path(serial: str, out_dir: Path) -> Path:
    ts = int(time.time())
    safe_serial = re.sub(r"[^0-9A-Za-z]+", "_", str(serial))
    return out_dir / f"program_flash_{safe_serial}_{ts}.jlink"


def extract_download_file_path(jlink_out: str) -> Optional[str]:
    m = re.search(r"Downloading file \\[(.+?)\\]\\.\\.\\.", jlink_out or "", re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip()


def prompt_channel(previous: Optional[str]) -> str:
    while True:
        if previous:
            s = input(f"选择通道 32/33/34/35 (回车保持: {previous}): ").strip()
            if not s:
                return previous
        else:
            s = input("选择通道 32/33/34/35: ").strip()
        s = s.strip()
        if s in {"32", "33", "34", "35"}:
            return s
        print_status("通道输入无效，请输入 32/33/34/35", "warning")


def rpc_power_up(channel: str) -> None:
    RPCClientWrapper = _get_rpc_client_wrapper()
    if RPCClientWrapper is None:
        detail = f"{type(_RPC_IMPORT_ERROR).__name__}: {_RPC_IMPORT_ERROR}" if _RPC_IMPORT_ERROR else "unknown import error"
        raise RuntimeError("RPC client not available: " + detail)
    ip = f"169.254.1.{channel}"
    rpc = RPCClientWrapper(ip=ip, port=7801)
    rpc.call("mixdevice.reset")
    rpc.call("mixdevice.relay", "DUT_SYS_RST_0KPULLDOWN")
    rpc.call("mixdevice.relay", "SOCKET_POWER_ON_BY_DUT_PP_VSYS")
    rpc.call("mixdevice.relay", "DUT_PP_VBATT_TO_PSU_BATTERY_POS1")
    rpc.call("mixdevice.enable_battery_output", 8000, 5000)
    rpc.call("mixdevice.relay", "DUT_PP1V8_AON_TO_DMMCH0", "CONNECT")
    rpc.call("mixdevice.measureVoltageWithDMM", 'ch0', '7000mV')
    time.sleep(2)


# =============================================================================
# Result Analysis
# =============================================================================
def classify_jlink_result(log: str) -> Tuple[bool, Optional[str]]:
    """Analyze J-Link operation result with detailed error reporting."""
    lower = (log or "").lower()

    # Check if script completed
    if "script processing completed" not in lower:
        return False, "Script did not complete successfully"

    # Check for restore errors (usually non-fatal)
    restore_err = any(
        phrase in lower
        for phrase in [
            "failed to restore target",
            "ramcode never stops",
            "restore() failed",
            "ramcode-sided restore() failed",
        ]
    )

    # Check for errors in log
    for line in (log or "").splitlines():
        l = line.strip()
        ll = l.lower()

        if ll.startswith("****** error:"):
            if restore_err and ("restore" in ll or "ramcode" in ll):
                continue
            return False, l

    # Check for known failure indicators
    failure_hints = [
        ("connect failed", "Failed to connect to target"),
        ("connection failed", "Connection to target failed"),
        ("no emulators connected", "No J-Link emulators connected"),
        ("no j-link", "No J-Link found"),
        ("no device found", "No target device found"),
        ("unknown device", "Unknown device specified"),
        ("unknown command", "Unknown command in script"),
        ("target voltage too low", "Target voltage too low"),
        ("verification failed", "Flash verification failed"),
        ("verify failed", "Flash verification failed"),
        ("flash download failed", "Flash download failed"),
    ]

    for hint, message in failure_hints:
        if hint in lower:
            return False, message

    # Verify successful operations in log
    load_pos = lower.find("j-link>loadfile")
    if load_pos < 0:
        return False, "Missing loadfile command in output"

    blk = lower[load_pos:]

    checks = [
        ("downloading file" not in blk, "File download did not start"),
        (
            "flash download: total:" not in blk and "flash download: total time needed:" not in blk,
            "Missing flash download summary",
        ),
        (not re.search(r"program:\s*[\d.]+s", blk), "Missing program timing info"),
        (not re.search(r"verify:\s*[\d.]+s", blk), "Missing verify timing info"),
        ("o.k." not in blk, "Operation not confirmed as successful"),
    ]

    for failed, error_msg in checks:
        if failed:
            return False, error_msg

    # Handle restore errors (non-fatal warning)
    if restore_err:
        return True, "warning: Restore failed (non-critical)"

    return True, None


# =============================================================================
# Main Function
# =============================================================================
def main() -> int:
    """Main entry point with enhanced UI."""
    # Print banner
    print_banner()

    # Parse arguments
    parser = argparse.ArgumentParser(
        add_help=True,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=colored("One-Click J-Link Programming Tool for Nordic nRF Devices", Style.INFO),
        epilog=colored("\nExample usage:\n"
                      "  python nrf_oneclick_program.py --fw firmware.hex\n"
                      "  python nrf_oneclick_program.py ./build/output.hex --serial 123456789\n"
                      "  python nrf_oneclick_program.py --device nRF52840_xxAA --speed 4000",
                      Style.DIM_TEXT)
    )

    parser.add_argument("--fw", "--firmware", dest="fw", default=None, help="Firmware file path (.bin or .hex)")
    parser.add_argument("fw_pos", nargs="?", default=None, help="Firmware path (positional)")
    parser.add_argument("--device", default="nRF54LM20A_M33", help="Target device (default: nRF54LM20A_M33)")
    parser.add_argument("--interface", default="swd", help="Interface: swd or jtag (default: swd)")
    parser.add_argument("--speed", type=int, default=1000, help="JTAG/SWD speed in kHz (default: 1000)")
    parser.add_argument("--address", default="0x00000000", help="Flash address for .bin files (default: 0x00000000)")
    parser.add_argument("--jlink-exe", default="/Applications/SEGGER/JLink/JLinkExe", help="Path to JLinkExe")
    parser.add_argument("--serial", dest="serial", default=None, help="J-Link serial number (optional)")
    parser.add_argument("--timeout", type=float, default=50.0, help="Operation timeout in seconds (default: 50)")
    parser.add_argument("--expected", default="O.K.", help="Expected success keyword (default: O.K.)")
    parser.add_argument("--no-erase", action="store_true", default=False, help="Skip flash erase before programming")
    parser.add_argument("--script-mode", choices=["legacy", "strict"], default="legacy", help="J-Link script mode: legacy (match station) or strict (ExitOnError 1)")
    parser.add_argument("--after", choices=["none", "reset", "go"], default="none", help="After loadfile: none/reset/go (default: none)")
    parser.add_argument("--once", action="store_true", default=False, help="Program once and exit (default: keep running)")
    parser.add_argument("--script-out-dir", default=None, help="Directory to save generated .jlink scripts (default: ~/NRFFlashTool_scripts)")
    parser.add_argument("--channel", choices=["32", "33", "34", "35"], default=None, help="DUT channel (169.254.1.<channel>:7801)")
    parser.add_argument("--no-rpc", action="store_true", default=False, help="Skip pre-flash RPC power-up sequence")

    args = parser.parse_args()

    script_out_dir = Path(args.script_out_dir) if args.script_out_dir else (Path.home() / "NRFFlashTool_scripts")
    script_out_dir.mkdir(parents=True, exist_ok=True)

    jlink_exe = Path(args.jlink_exe)
    if not jlink_exe.exists():
        print_status(f"JLinkExe not found: {jlink_exe}", "error")
        print(colored("\n  Please install SEGGER J-Link or specify correct path with --jlink-exe", Style.DIM_TEXT))
        return 2

    previous_firmware: Optional[Path] = None
    previous_serial: Optional[str] = None
    previous_channel: Optional[str] = None
    initial_fw = args.fw or args.fw_pos
    first = True

    while True:
        if args.no_rpc:
            channel = args.channel or previous_channel
        else:
            channel = args.channel or prompt_channel(previous_channel)

        print_separator("═", 60)
        print(colored("  ⚙  Configuration", Style.HEADER))
        print_separator("═", 60)

        config_items = [
            ("Device", args.device),
            ("Interface", args.interface.upper()),
            ("Speed", f"{args.speed} kHz"),
            ("Timeout", f"{args.timeout}s"),
            ("Script", args.script_mode),
            ("After", args.after),
            ("JLinkExe", str(jlink_exe)),
            ("Channel", channel if channel else "-"),
            ("RPC", "Skip" if args.no_rpc else "Enable"),
        ]
        print_config_table("  ⚙  Configuration", config_items)

        print_step(1, 4, "Selecting Firmware")
        try:
            firmware = resolve_firmware_interactive(previous_firmware, initial_fw if first else None)
        except Exception as ex:
            print_status(f"Invalid firmware path: {ex}", "error")
            if args.once:
                return 2
            if not prompt_continue("继续选择FW?", default_yes=True):
                return 2
            continue

        fw_info = firmware_identity(firmware)
        fw_size = int(fw_info["size_bytes"])
        sha = str(fw_info["sha256"])
        print_status(f"FW: {fw_info['path']} ({format_bytes(fw_size)})", "success")
        print_status(f"FW mtime: {fw_info['mtime']}", "info")
        if firmware.suffix.lower() == ".hex":
            hex_bytes = fw_info.get("hex_data_bytes")
            if isinstance(hex_bytes, int):
                print_status(f"HEX data bytes: {format_bytes(hex_bytes)}", "info")
        print_status(f"FW sha256: {sha}", "info")

        print_step(2, 4, "Verifying J-Link")
        print_status(f"JLinkExe found: {jlink_exe}", "success")

        if not args.no_rpc:
            print_step(2, 4, "Powering DUT (RPC)")
            try:
                print_status(f"RPC target: 169.254.1.{channel}:7801", "info")
                rpc_power_up(channel)
                print_status("RPC power-up done", "success")
            except Exception as ex:
                print_status(f"RPC power-up failed: {ex}", "error")
                if args.once:
                    return 2
                if not prompt_continue("继续烧录下一台?", default_yes=True):
                    return 2
                previous_channel = channel
                first = False
                continue

        print_step(3, 4, "Selecting J-Link Device")
        try:
            if args.serial:
                serial = str(args.serial)
            elif previous_serial and prompt_continue(f"使用上次J-Link S/N {previous_serial}?", default_yes=True):
                serial = previous_serial
            else:
                serial = select_jlink_serial(
                    jlink_exe=jlink_exe,
                    timeout_sec=min(10.0, float(args.timeout)),
                    forced_serial=None,
                )
        except Exception as ex:
            print_status(f"J-Link selection failed: {ex}", "error")
            if args.once:
                return 2
            if not prompt_continue("继续选择J-Link?", default_yes=True):
                return 2
            continue

        print()
        print_separator("─", 60)
        print_config_table("  📋 Final Configuration", [
            ("Firmware", str(fw_info["path"])),
            ("FW File Size", format_bytes(fw_size)),
            ("FW SHA256", sha[:16]),
            ("Device", args.device),
            ("Interface", args.interface.upper()),
            ("Speed", f"{args.speed} kHz"),
            ("Erase", "No" if args.no_erase else "Yes"),
            ("Script", args.script_mode),
            ("After", args.after),
            ("Serial", serial),
            ("Channel", channel if channel else "-"),
        ])

        print_step(4, 4, "Flashing Firmware")
        print_status("Starting J-Link programming...", "info")
        print()

        script = build_commander_script(
            device=str(args.device),
            interface=str(args.interface),
            speed_khz=int(args.speed),
            firmware=firmware,
            address=str(args.address),
            do_erase=not args.no_erase,
            mode=str(args.script_mode),
            after=str(args.after),
        )

        cmd_file = script_output_path(serial, script_out_dir)
        cmd_file.write_text(script, encoding="utf-8")
        print_status(f"Saved .jlink script: {cmd_file}", "info")
        time.sleep(0.5)

        cmd = [str(jlink_exe), "-NoGui", "1", "-USB", str(serial), "-CommanderScript", str(cmd_file)]

        print(colored("  ┌─────────────────────────────────────────────────────────┐", Style.BOX_LINE))
        print(colored("  │  ", Style.BOX_LINE) + colored("Programming Flash...", Style.INFO) + colored(" " * 30 + "│", Style.BOX_LINE))
        print(colored("  └─────────────────────────────────────────────────────────┘", Style.BOX_LINE))
        print()

        # Initialize progress tracking
        progress = ProgressBar(total=100, width=50, prefix="  Flashing")
        progress.update(0)

        # Start J-Link process with real-time output capture
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        out_lines = []
        current_progress = 0

        stages = [
            ("connecting to j-link", 10),
            ("connecting to target", 15),
            ("erasing device", 30),
            ("downloading file", 45),
            ("programming flash", 75),
            ("verifying flash", 90),
            ("script processing completed", 95),
        ]

        stage_idx = 0

        # Read output line by line
        if p.stdout:
            for line in iter(p.stdout.readline, ''):
                if not line:
                    break
                out_lines.append(line)
                line_lower = line.lower().strip()

                for i, (needle, pct) in enumerate(stages):
                    if needle in line_lower:
                        if i > stage_idx:
                            stage_idx = i
                            current_progress = pct
                            progress.update(current_progress)
                            break

                if "%" in line:
                    pct_match = re.search(r"(\d+)%", line)
                    if pct_match:
                        pct_val = int(pct_match.group(1))
                        if 0 <= pct_val <= 100:
                            current_progress = max(current_progress, min(100, pct_val))
                            progress.update(current_progress)

                # Check for critical errors (ignore non-fatal restore errors)
                if "error:" in line_lower and "restore" not in line_lower and "ramcode" not in line_lower:
                    print()
                    print_status(f"J-Link error: {line.strip()}", "error")

            p.wait(timeout=float(args.timeout))

        out = "".join(out_lines)

        downloaded_path = extract_download_file_path(out)
        if downloaded_path:
            norm_downloaded = str(Path(downloaded_path).expanduser().resolve()) if Path(downloaded_path).expanduser().exists() else downloaded_path
            expected_path = str(firmware.resolve())
            print_status(f"J-Link downloaded: {norm_downloaded}", "info")
            if norm_downloaded != expected_path:
                print_status("Firmware mismatch: J-Link downloaded file is NOT the selected FW!", "error")
                print_status(f"Selected FW: {expected_path}", "error")
                if args.once:
                    return 1
                if not prompt_continue("继续烧录下一台?", default_yes=True):
                    return 1
                previous_firmware = firmware
                previous_serial = serial
                first = False
                continue

        m_aff = re.search(r"ranges affected \\((\\d+) bytes\\)", out, re.IGNORECASE)
        if m_aff:
            try:
                aff = int(m_aff.group(1))
                print_status(f"J-Link ranges affected: {format_bytes(aff)}", "info")
            except Exception:
                pass

        # Complete progress bar
        if p.returncode == 0:
            progress.update(100)
        progress.complete("")  # Don't print extra line, we'll print our own status

        # Print raw output in a styled box
        print()
        print(colored("  ", Style.SUCCESS) + colored("J-Link operation completed", "success" if p.returncode == 0 else "error"))
        print_separator("─", 60)
        print(colored("  J-Link Output:", Style.HEADER))

        # Colorize the output
        for line in out.splitlines():
            line_lower = line.lower().strip()
            # Skip non-fatal restore errors (J-Link warning that doesn't affect programming)
            if "error:" in line_lower and ("restore" in line_lower or "ramcode" in line_lower):
                print(colored(f"  {line}", Style.WARNING))
            elif "error:" in line_lower:
                print(colored(f"  {line}", Style.ERROR))
            elif "o.k." in line_lower or "success" in line_lower:
                print(colored(f"  {line}", Style.SUCCESS))
            elif "warning" in line_lower:
                print(colored(f"  {line}", Style.WARNING))
            elif line.startswith("******"):
                print(colored(f"  {line}", Style.ERROR))
            else:
                print(colored(f"  {line}", Style.DIM_TEXT))

        print_separator("─", 60)

        if p.returncode != 0:
            print()
            print_status("J-Link exited with non-zero return code", "error")
            if args.once:
                return 1
            if not prompt_continue("继续烧录下一台?", default_yes=True):
                return 1
            previous_firmware = firmware
            previous_serial = serial
            first = False
            continue

        # Analyze result
        ok, warn = classify_jlink_result(out)

        if not ok:
            print()
            print_status(f"Programming failed: {warn}", "error")
            if args.once:
                return 1
            if not prompt_continue("继续烧录下一台?", default_yes=True):
                return 1
            previous_firmware = firmware
            previous_serial = serial
            first = False
            continue

        if warn:
            print_status(f"Warning: {warn}", "warning")

        # Check expected keyword
        exp = str(args.expected or "").strip()
        if exp and exp not in out:
            print_status(f"Expected keyword '{exp}' not found in output", "error")
            if args.once:
                return 1
            if not prompt_continue("继续烧录下一台?", default_yes=True):
                return 1
            previous_firmware = firmware
            previous_serial = serial
            first = False
            continue

        # Success!
        print()
        print(colored("  ╔══════════════════════════════════════════════════════════╗", Style.SUCCESS))
        print(colored("  ║", Style.SUCCESS) + colored("              [ SUCCESS ] Programming Complete             ", Style.SUCCESS) + colored("║", Style.SUCCESS))
        print(colored("  ╚══════════════════════════════════════════════════════════╝", Style.SUCCESS))
        print()
        print_status(f"Device {args.device} programmed successfully!", "success")

        previous_firmware = firmware
        previous_serial = serial
        previous_channel = channel
        first = False
        if args.once:
            return 0
        if not prompt_continue("继续烧录下一台?", default_yes=True):
            return 0
        print()
        continue

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
