"""Build the Windows launcher and its portable ZIP archive."""

import argparse
from hashlib import sha1
from pathlib import Path
from struct import calcsize
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from netplay import NETPLAY_CONFIG, PAL_COOP_ROM, PAL_COOP_SHA1, PAL_PATCH, PATCHES, ROOT, RUNTIME


EXE_NAME = "SuperMario-PAL-v3.exe"
PORTABLE_NAME = "SuperMario-PAL-v3-Win64"
READY_TO_PLAY_NAME = "SuperMario-PAL-v3-ReadyToPlay-Win64"
PORTABLE_CONFIG = b'config_save_on_exit = "true"\n'
NOTICES = """\
RetroArch 1.22.2 (unmodified Libretro build)
Source and license: https://github.com/libretro/RetroArch/tree/v1.22.2

FCEUmm libretro core (unmodified Libretro build)
Source and license: https://github.com/libretro/libretro-fceumm/tree/fb919fb

RetroArch's bundled interface assets retain their upstream notices.
Asset source: https://github.com/libretro/retroarch-assets

Python and Tcl/Tk are bundled by PyInstaller 6.x.
https://docs.python.org/3/license.html
https://www.tcl-lang.org/software/tcltk/license.html
https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt

The Super Mario Bros. Co-op v45 patch is from benj-edwards/NESCoopMods.
https://github.com/benj-edwards/NESCoopMods#super-mario-bros-co-op
"""


def runtime_files() -> list[Path]:
    files = [RUNTIME / "retroarch.exe", RUNTIME / "retroarch.default.cfg", RUNTIME / "qt.conf",
             RUNTIME / "cores" / "fceumm_libretro.dll", RUNTIME / "info" / "fceumm_libretro.info"]
    files.extend(sorted(RUNTIME.glob("*.dll")))
    for directory in ("assets", "autoconfig", "platforms", "licenses"):
        files.extend(path for path in sorted((RUNTIME / directory).rglob("*")) if path.is_file())
    return files


def build(*, include_rom: bool = False) -> tuple[Path, ...]:
    if sys.platform != "win32" or calcsize("P") != 8:
        raise RuntimeError("请使用 64 位 Windows Python 构建 Windows 便携版")

    root_files = [NETPLAY_CONFIG, ROOT / "README.md", ROOT / "docs" / "architecture.md"]
    root_files.extend(ROOT / "patches" / name for name in sorted({PAL_PATCH, *PATCHES.values()}))
    files = [*root_files, *runtime_files()]
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(f"打包所需文件缺失：{path}")

    rom = None
    if include_rom:
        rom = PAL_COOP_ROM.read_bytes()
        if sha1(rom).hexdigest() != PAL_COOP_SHA1:
            raise ValueError(f"即玩包需要此版本的 PAL 双人 ROM：{PAL_COOP_ROM}")

    package_name = READY_TO_PLAY_NAME if include_rom else PORTABLE_NAME
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    exe_path = ROOT / EXE_NAME
    zip_path = dist / f"{package_name}.zip"
    with TemporaryDirectory(prefix="windows-build-", dir=dist) as temporary:
        stage = Path(temporary)
        subprocess.run([
            sys.executable, "-m", "PyInstaller", "--onefile", "--windowed", "--noupx",
            "--name", Path(EXE_NAME).stem, "--distpath", str(stage),
            "--workpath", str(stage / "work"), "--specpath", str(stage), str(ROOT / "launcher.py"),
        ], cwd=ROOT, check=True)

        launcher = stage / EXE_NAME
        archive = stage / zip_path.name
        with ZipFile(archive, "w", ZIP_DEFLATED, compresslevel=4) as bundle:
            bundle.write(launcher, f"{package_name}/{EXE_NAME}")
            for path in files:
                bundle.write(path, f"{package_name}/{path.relative_to(ROOT).as_posix()}")
            relative_config = (RUNTIME / "retroarch.cfg").relative_to(ROOT).as_posix()
            bundle.writestr(f"{package_name}/{relative_config}", PORTABLE_CONFIG)
            bundle.writestr(f"{package_name}/THIRD_PARTY_NOTICES.txt", NOTICES)
            if rom is None:
                bundle.writestr(f"{package_name}/roms/", b"")
            else:
                relative_rom = PAL_COOP_ROM.relative_to(ROOT).as_posix()
                bundle.writestr(f"{package_name}/{relative_rom}", rom)

        archive.replace(zip_path)
        if include_rom:
            return (zip_path,)
        try:
            launcher.replace(exe_path)
        except PermissionError as error:
            if not exe_path.is_file():
                raise
            print(f"已生成便携包。无法替换根目录的启动器：{error}", file=sys.stderr)
            return (zip_path,)
    return exe_path, zip_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-rom", action="store_true", help="将已生成的 PAL v3 ROM 放入即玩包")
    args = parser.parse_args()
    for output in build(include_rom=args.include_rom):
        print(output)
