"""Prepare a local NES ROM and launch a direct IPv4 RetroArch session."""

import argparse
import ctypes
from enum import Enum, auto
from hashlib import sha1, sha256
from ipaddress import IPv4Address
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from bps import apply_bps


FROZEN = getattr(sys, "frozen", False)
ROOT = Path(sys.executable if FROZEN else __file__).resolve().parent
RUNTIME = ROOT / "runtime" / "RetroArch-Win64"
NETPLAY_CONFIG = ROOT / "netplay.cfg"
DEFAULT_ROM = ROOT / "roms" / "SuperMarioBrosCoop-v45.nes"
PAL_COOP_ROM = ROOT / "roms" / "SuperMarioBros-PAL-Coop-1-1-v3.nes"
DEFAULT_PORT = 55435
TARGET_SHA1 = "9fc49680f445066c4f54ab87e63893110a5eb6d0"
PAL_ORIGINAL_SHA1 = "ab30029efec6ccfc5d65dfda7fbc6e6489a80805"
PAL_COOP_SHA1 = "f4c9f0e86f29b5661318e1c4473d4c471d7948b3"
PAL_COOP_V2_SHA1 = "8568b3cbae8faa09401d4f06b48e299a7faa8fc1"
PAL_COOP_V1_SHA1 = "01bcb374ef1d560b02944f32c0820fb9ccfa7997"
PAL_PATCH = "SuperMarioBros-PAL-Coop-1-1-v3.bps"
PATCHES = {
    "ea343f4e445a9050d4b4fbac2c77d0693b1d0922": "SuperMarioBrosCoop-v45.bps",
    "33d23c2f2cfa4c9efec87f7bc1321ce3ce6c89bd": "SuperMarioBrosCoop-v45-nes2header.bps",
}
ORIGINAL_PAYLOADS = {
    "facee9c577a5262dbe33ac4930bb0b58c8c037f7": "World 原版",
    "0c4992fc08d2278697339d3b48066e7b5f943598": "欧版 Rev A 原版",
}


class RomKind(Enum):
    PAL_COOP = auto()
    COOP = auto()
    PATCHABLE = auto()
    ORIGINAL = auto()
    UNKNOWN = auto()


def preferred_coop_rom() -> Path:
    return PAL_COOP_ROM if PAL_COOP_ROM.is_file() else DEFAULT_ROM


def read_nes_rom(rom: Path) -> bytes:
    if not rom.is_file():
        raise ValueError(f"找不到 ROM：{rom}")
    data = rom.read_bytes()
    if rom.suffix.lower() != ".nes" or len(data) <= 16 or data[:4] != b"NES\x1a":
        raise ValueError(f"请选择带 iNES 或 NES 2.0 文件头的 .nes 文件：{rom.name}")
    return data


def describe_rom(rom: Path) -> tuple[RomKind, str]:
    data = read_nes_rom(rom)
    digest = sha1(data).hexdigest()
    if digest == PAL_COOP_SHA1:
        return RomKind.PAL_COOP, "PAL v3 · 1-1 地面双人同屏，共享镜头"
    if digest == PAL_COOP_V2_SHA1:
        return RomKind.PAL_COOP, "PAL v2 · 1-1 地面双人同屏，共享镜头"
    if digest == PAL_COOP_V1_SHA1:
        return RomKind.COOP, "PAL v1 · 1-1 地面双人同屏，共享镜头"
    if digest == TARGET_SHA1:
        return RomKind.COOP, "Co-op v45 · 两人同屏，同时操作"
    if digest == PAL_ORIGINAL_SHA1:
        return RomKind.PATCHABLE, "欧版 Rev A 原版 · 应用 PAL 补丁后可在 1-1 双人同屏"
    if digest in PATCHES:
        return RomKind.PATCHABLE, "World 原版 · 应用补丁后可同屏联机"
    original = ORIGINAL_PAYLOADS.get(sha1(data[16:]).hexdigest())
    if original:
        return RomKind.ORIGINAL, f"{original} · 双人轮流。请选择同屏版或补丁支持的原版。"
    return RomKind.UNKNOWN, "玩法未识别。请使用已确认支持双人同屏的 ROM。"


def prepare(source_path: Path) -> Path:
    source = source_path.read_bytes()
    digest = sha1(source).hexdigest()
    if digest == PAL_ORIGINAL_SHA1:
        patch_name, output, target_sha1 = PAL_PATCH, PAL_COOP_ROM, PAL_COOP_SHA1
    elif digest in PATCHES:
        patch_name, output, target_sha1 = PATCHES[digest], DEFAULT_ROM, TARGET_SHA1
    else:
        raise ValueError("需要支持的 Super Mario Bros. 欧版 Rev A 或 World 原版 ROM")

    patched = apply_bps(source, (ROOT / "patches" / patch_name).read_bytes())
    if sha1(patched).hexdigest() != target_sha1:
        raise ValueError("生成的 ROM 与项目记录的双人版 SHA-1 不一致")

    output.parent.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as staging:
        ready = Path(staging) / output.name
        ready.write_bytes(patched)
        # Windows rename publishes the complete file and fails if the name already exists.
        try:
            ready.rename(output)
        except FileExistsError:
            if output.read_bytes() != patched:
                raise ValueError(f"已有同名文件，请先移走后重试：{output}") from None

    return output


def session_arguments(
    action: str, port: int | None, address: IPv4Address | None,
) -> tuple[list[str], str]:
    if action == "local":
        return [], "本地双人 · 手柄 1 / 2"
    if port is None or not 1 <= port <= 65535:
        raise ValueError("请输入 1–65535 之间的 TCP 端口")
    options = ["--port", str(port)]
    if action == "host":
        return [*options, "--host", "--nick", "P1"], f"主机 P1 · TCP {port}"
    if action == "join" and address is not None:
        return [*options, "--connect", str(address), "--nick", "P2"], f"客机 P2 · {address}:{port}"
    raise ValueError("加入联机房间需要主机 IPv4 地址")


def start_emulator(
    action: str, rom: Path, port: int | None = None, *, address: IPv4Address | None = None,
    runtime: Path = RUNTIME, log: Path | None = None, report: bool = False,
) -> subprocess.Popen:
    options, role = session_arguments(action, port, address)
    rom = rom.resolve()
    rom_data = read_nes_rom(rom)
    digest = sha1(rom_data).hexdigest()
    expected = {DEFAULT_ROM: TARGET_SHA1, PAL_COOP_ROM: PAL_COOP_SHA1}.get(rom)
    if expected is not None and digest != expected:
        raise ValueError("准备目录中的 ROM 与对应的双人补丁不一致")

    runtime = runtime.resolve()
    frontend = runtime / "retroarch.exe"
    core = runtime / "cores" / "fceumm_libretro.dll"
    for path in (frontend, core, NETPLAY_CONFIG):
        if not path.is_file():
            raise ValueError(f"找不到运行文件：{path}。请检查 README 中的运行环境说明")

    command = [str(frontend), "--appendconfig", str(NETPLAY_CONFIG), "--no-patch",
               "-L", str(core), *options]
    if action != "local" and digest == PAL_COOP_SHA1:
        command.extend(["--sram-mode", "noload-nosave"])
    if log:
        command.extend(["--verbose", "--log-file", str(log.resolve())])
    command.append(str(rom))

    if report:
        print(f"ROM SHA-256：{sha256(rom_data).hexdigest()}", flush=True)
        print(f"FCEUmm SHA-256：{sha256(core.read_bytes()).hexdigest()}", flush=True)
        print(role, flush=True)

    if not FROZEN:
        return subprocess.Popen(command, cwd=runtime)

    # RetroArch is a separate native application. It needs its own DLLs,
    # including its own zlib, ahead of libraries extracted by PyInstaller.
    set_dll_directory = ctypes.WinDLL("kernel32", use_last_error=True).SetDllDirectoryW
    set_dll_directory.argtypes = (ctypes.c_wchar_p,)
    if not set_dll_directory(None):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return subprocess.Popen(command, cwd=runtime)
    finally:
        set_dll_directory(sys._MEIPASS)


def port_number(value: str) -> int:
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("请输入整数端口号") from None
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("TCP 端口范围为 1–65535")
    return port


def ipv4_address(value: str) -> IPv4Address:
    try:
        address = IPv4Address(value)
    except ValueError:
        raise argparse.ArgumentTypeError("请输入 IPv4 地址，例如 192.168.1.23") from None
    if address.is_unspecified or address.is_multicast or int(address) == 0xFFFFFFFF:
        raise argparse.ArgumentTypeError("请输入主机的单播 IPv4 地址")
    return address


def main() -> int:
    parser = argparse.ArgumentParser(description="NES 双人同屏 IPv4 联机")
    actions = parser.add_subparsers(dest="action", required=True)
    prepare_parser = actions.add_parser("prepare", help="对本地原版 ROM 应用双人补丁")
    prepare_parser.add_argument("source", type=Path)
    local = actions.add_parser("local", help="本机使用两只手柄游玩")
    host = actions.add_parser("host", help="创建房间，作为 P1")
    join = actions.add_parser("join", help="通过 IPv4 加入房间，作为 P2")
    join.add_argument("address", type=ipv4_address)
    for action in (host, join):
        action.add_argument("--port", type=port_number, default=DEFAULT_PORT)
    for action in (local, host, join):
        action.add_argument("--rom", type=Path, default=preferred_coop_rom())
        action.add_argument("--runtime", type=Path, default=RUNTIME)
        action.add_argument("--log", type=Path)

    args = parser.parse_args()
    try:
        if args.action == "prepare":
            rom = prepare(args.source)
            print(f"双人 ROM：{rom}")
            print(f"ROM SHA-256：{sha256(rom.read_bytes()).hexdigest()}")
            return 0
        with start_emulator(args.action, args.rom, getattr(args, "port", None), address=getattr(args, "address", None),
                            runtime=args.runtime, log=args.log, report=True) as emulator:
            return emulator.wait()
    except (OSError, ValueError) as error:
        parser.exit(1, f"错误：{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
