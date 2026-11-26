"""Apply and verify a BPS patch against a caller-supplied ROM."""

from io import BytesIO
from struct import unpack
from zlib import crc32


def apply_bps(source: bytes, patch: bytes) -> bytes:
    if len(patch) < 19 or patch[:4] != b"BPS1":
        raise ValueError("补丁文件不是有效的 BPS 文件")

    source_crc, target_crc, patch_crc = unpack("<III", patch[-12:])
    if crc32(patch[:-4]) != patch_crc:
        raise ValueError("BPS 补丁校验失败")
    if crc32(source) != source_crc:
        raise ValueError("原版 ROM 与 BPS 补丁要求的版本不匹配")

    commands = BytesIO(patch[4:-12])

    def read(count: int) -> bytes:
        data = commands.read(count)
        if len(data) != count:
            raise ValueError("BPS 补丁数据不完整")
        return data

    def number() -> int:
        value, scale = 0, 1
        for _ in range(9):
            byte = read(1)[0]
            value += (byte & 0x7F) * scale
            if byte & 0x80:
                return value
            scale <<= 7
            value += scale
        raise ValueError("BPS 数值超出支持范围")

    if number() != len(source):
        raise ValueError("原版 ROM 长度不匹配")
    target_size = number()
    read(number())  # Optional metadata precedes the commands.

    target = bytearray()
    source_offset = target_offset = 0
    while len(target) < target_size:
        command = number()
        action, length = command & 3, (command >> 2) + 1
        end = len(target) + length
        if end > target_size:
            raise ValueError("BPS 指令超出目标 ROM 长度")

        match action:
            case 0:  # SourceRead uses the current output position.
                if end > len(source):
                    raise ValueError("BPS 指令超出原版 ROM 长度")
                target.extend(source[len(target):end])
            case 1:  # TargetRead copies bytes stored in the patch.
                target.extend(read(length))
            case 2 | 3:  # SourceCopy and TargetCopy use separate relative cursors.
                encoded = number()
                offset = -(encoded >> 1) if encoded & 1 else encoded >> 1
                if action == 2:
                    source_offset += offset
                    stop = source_offset + length
                    if source_offset < 0 or stop > len(source):
                        raise ValueError("BPS 引用超出原版 ROM 范围")
                    target.extend(source[source_offset:stop])
                    source_offset = stop
                else:
                    target_offset += offset
                    if not 0 <= target_offset < len(target):
                        raise ValueError("BPS 引用尚未生成的目标数据")
                    # Bytewise copying also allows a command to repeat its own output.
                    for _ in range(length):
                        target.append(target[target_offset])
                        target_offset += 1

    if commands.read(1) or crc32(target) != target_crc:
        raise ValueError("生成的 ROM 未通过 BPS 校验")
    return bytes(target)
