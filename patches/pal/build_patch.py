"""Build the PAL 1-1 co-op BPS overlay from the local Rev A image and new code."""

import argparse
from hashlib import sha1
from pathlib import Path
from struct import pack
import subprocess
from tempfile import TemporaryDirectory
from zlib import crc32

from bps import apply_bps


HERE = Path(__file__).resolve().parent
SOURCE_SHA1 = "ab30029efec6ccfc5d65dfda7fbc6e6489a80805"
PATCH_PATH = HERE.parent / "SuperMarioBros-PAL-Coop-1-1-v3.bps"
STUB_ADDRESS = 0xD69E
STUB_SIZE = 0x3B
PRG_START = 16
LOWER_PRG_END = PRG_START + 0x4000
PRG_END = PRG_START + 0x8000
EXPANSION_SIZE = 0x8000
# Mapper 4, vertical mirroring, 64 KiB PRG, 8 KiB CHR ROM, 8 KiB volatile
# PRG RAM and explicitly PAL timing. The graphics are copied from the input.
HEADER = bytes.fromhex("4E 45 53 1A 04 01 41 08 00 00 07 00 01 00 00 00")


def encode_bps_number(value: int) -> bytes:
    encoded = bytearray()
    while value >= 128:
        encoded.append(value & 127)
        value = (value >> 7) - 1
    encoded.append(value | 128)
    return bytes(encoded)


def signed_bps_number(value: int) -> bytes:
    return encode_bps_number((abs(value) << 1) | (value < 0))


class PatchWriter:
    def __init__(self, source: bytes):
        self.source = source
        self.commands = bytearray()
        self.target = bytearray()
        self.source_cursor = 0
        self.target_cursor = 0

    def copy_source(self, start: int, stop: int) -> None:
        if start == stop:
            return
        length = stop - start
        self.commands.extend(encode_bps_number(((length - 1) << 2) | 2))
        self.commands.extend(signed_bps_number(start - self.source_cursor))
        self.target.extend(self.source[start:stop])
        self.source_cursor = stop

    def literal(self, data: bytes) -> None:
        self.commands.extend(encode_bps_number(((len(data) - 1) << 2) | 1))
        self.commands.extend(data)
        self.target.extend(data)

    def zero_fill(self, count: int) -> None:
        self.literal(b"\0")
        if count == 1:
            return
        first_zero = len(self.target) - 1
        self.commands.extend(encode_bps_number(((count - 2) << 2) | 3))
        self.commands.extend(signed_bps_number(first_zero - self.target_cursor))
        self.target.extend(bytes(count - 1))
        self.target_cursor = len(self.target) - 1

    def finish(self) -> bytes:
        patch = (b"BPS1" + encode_bps_number(len(self.source))
                 + encode_bps_number(len(self.target)) + encode_bps_number(0)
                 + self.commands + pack("<II", crc32(self.source), crc32(self.target)))
        return patch + pack("<I", crc32(patch))


def assemble(cc65_bin: Path | None) -> tuple[bytes, dict[str, int]]:
    def executable(program: str) -> str:
        return str(cc65_bin / f"{program}.exe") if cc65_bin else program

    with TemporaryDirectory(prefix="pal-coop-build-") as temporary:
        build = Path(temporary)
        obj, binary, labels = (build / name for name in ("coop.o", "coop.bin", "coop.lbl"))
        subprocess.run([executable("ca65"), "-o", str(obj), str(HERE / "coop.s")], check=True)
        subprocess.run([
            executable("ld65"), "-C", str(HERE / "link.cfg"), "-o", str(binary),
            "-Ln", str(labels), str(obj),
        ], check=True)
        symbols = {}
        for row in labels.read_text(encoding="ascii").splitlines():
            _, address, label = row.split()
            symbols[label.removeprefix(".")] = int(address, 16)
        return binary.read_bytes(), symbols


def file_offset(address: int) -> int:
    return PRG_START + address - 0x8000


def copy_with_edits(writer: PatchWriter, start: int, stop: int, edits: dict[int, bytes]) -> None:
    for address, replacement in sorted(edits.items()):
        offset = file_offset(address)
        if offset < start or offset + len(replacement) > stop:
            raise ValueError(f"Edit ${address:04X} overlaps an earlier edit or crosses a PRG boundary")
        writer.copy_source(start, offset)
        writer.literal(replacement)
        start = offset + len(replacement)
    writer.copy_source(start, stop)


def build_patch(source: bytes, code: bytes, symbols: dict[str, int]) -> tuple[bytes, str]:
    if sha1(source).hexdigest() != SOURCE_SHA1:
        raise ValueError("需要项目支持的 Super Mario Bros. 欧版 Rev A iNES 底版")
    signatures = {
        0x8175: bytes.fromhex("20 12 82"),                # NMI calls the mode dispatcher.
        0x819D: bytes.fromhex("AD FC 06 29 10"),          # Pause reads Start from the first pad.
        0x9282: bytes.fromhex("38 AD 7A 07 F0 21"),       # Turn-taking entry point.
        0x91D9: bytes.fromhex("CE 5A 07 10 0B"),          # Decrement lives, then branch if alive.
        0xB629: bytes.fromhex("90 43"),                   # Small Mario skips the fireball loop.
        0xBCF2: bytes.fromhex("48 A9 11 AE EE 03"),       # Native block strike.
        0xC99E: bytes.fromhex("A9 00 95 0F 95 16"),       # Clear an enemy slot.
        0xDF97: bytes.fromhex("20 B8 DF DD 93 DF 60"),    # Classify a metatile.
        STUB_ADDRESS: bytes([0xFF]) * STUB_SIZE,         # Unused fixed-bank padding.
        0xFFFC: bytes.fromhex("00 80"),                  # Original reset vector.
    }
    for address, signature in signatures.items():
        offset = file_offset(address)
        if source[offset:offset + len(signature)] != signature:
            raise ValueError(f"PAL Rev A hook bytes differ at ${address:04X}")
    if symbols["reset_hook"] != STUB_ADDRESS or symbols["overlay_boot"] != 0x8000:
        raise ValueError("Unexpected linker addresses for the reset or overlay bootstrap")
    if symbols["frame_hook"] != 0x6000:
        raise ValueError("NMI wrapper is outside the WRAM overlay")
    fixed, overlay = code[:STUB_SIZE], code[STUB_SIZE:]
    if not 0 < len(overlay) <= 0x2000:
        raise ValueError("P2 code must fit in a single 8 KiB MMC3 PRG bank")

    writer = PatchWriter(source)
    writer.literal(HEADER)
    copy_with_edits(writer, PRG_START, LOWER_PRG_END, {
        0x8175: b"\x20" + pack("<H", symbols["frame_hook"]),
        0x819D: b"\x20" + pack("<H", symbols["pause_input"]),
        0x91D9: b"\xA9\x02\xEA",   # LDA #2 / NOP: always take the normal restart branch.
        0x9282: b"\x38\x60",       # SEC / RTS: carry indicates no player switch.
        0xB629: b"\x90\x39",       # Update shared fireballs even if Mario is small.
    })
    writer.literal(overlay)
    writer.zero_fill(EXPANSION_SIZE - len(overlay))
    copy_with_edits(writer, LOWER_PRG_END, PRG_END, {
        STUB_ADDRESS: fixed,
        0xFFFC: pack("<H", symbols["reset_hook"]),
    })
    writer.copy_source(PRG_END, len(source))

    patch = writer.finish()
    target = apply_bps(source, patch)
    if target != writer.target or len(target) != 16 + 0x10000 + 0x2000:
        raise ValueError("BPS output does not match the linked PAL overlay layout")
    return patch, sha1(target).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--cc65-bin", type=Path, help="Directory containing ca65.exe and ld65.exe")
    args = parser.parse_args()
    try:
        source = args.source.read_bytes()
        if sha1(source).hexdigest() != SOURCE_SHA1:
            raise ValueError("需要项目支持的 Super Mario Bros. 欧版 Rev A iNES 底版")
        code, symbols = assemble(args.cc65_bin)
        patch, target_sha1 = build_patch(source, code, symbols)
        PATCH_PATH.write_bytes(patch)
        print(f"BPS: {PATCH_PATH} ({len(patch)} bytes)")
        print(f"Patched ROM SHA-1: {target_sha1}")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
