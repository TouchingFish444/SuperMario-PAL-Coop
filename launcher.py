"""Windows launcher for the NES game's LAN multiplayer sessions."""

import argparse
from pathlib import Path
from queue import Empty, SimpleQueue
import socket
from threading import Thread
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from netplay import (
    DEFAULT_PORT, ROOT, RomKind, describe_rom, ipv4_address, port_number, preferred_coop_rom, prepare,
    start_emulator,
)


BACKGROUND = "#101720"
PANEL = "#192430"
FIELD = "#111A24"
BORDER = "#364A5B"
TEXT = "#F0F6FC"
MUTED = "#A8B8C8"
ACCENT = "#70E5B1"
ERROR = "#FFA298"
FONT = "Microsoft YaHei UI"
LOOPBACK = "127.0.0.1"


def default_rom() -> Path | None:
    prepared = preferred_coop_rom()
    if prepared.is_file():
        return prepared
    local_roms = [path for path in ROOT.glob("*.nes") if path.is_file()]
    return local_roms[0] if len(local_roms) == 1 else None


def check_connection(address: str, port: int, result: SimpleQueue[tuple[str, str]]) -> None:
    endpoint = f"{address}:{port}"
    try:
        with socket.create_connection((address, port), timeout=2):
            pass
    except ConnectionRefusedError:
        result.put((f"{endpoint} 拒绝连接。请确认主机已建房、端口一致。", ERROR))
    except TimeoutError:
        result.put((f"连接 {endpoint} 超时。请确认主机已建房，再检查地址和防火墙。", ERROR))
    except OSError as error:
        result.put((f"无法连接 {endpoint}。{error}", ERROR))
    else:
        result.put((f"{endpoint} 的 TCP 端口可达。加入时会校验游戏和核心。", ACCENT))


class Launcher:
    def __init__(self, root: tk.Tk, rom: Path | None, log: Path | None):
        self.root = root
        self.rom = rom
        self.log = log
        self.mode = "host"
        self.process = None
        self.prepare_buttons: list[ttk.Button] = []
        self.rom_kind: RomKind | None = None

        root.title("超级玛丽 · 联机启动器")
        root.configure(background=BACKGROUND)
        root.geometry("680x670")
        root.minsize(620, 660)
        self.configure_styles()

        self.address = tk.StringVar(value=LOOPBACK)
        self.port = tk.StringVar(value=str(DEFAULT_PORT))
        self.rom_name = tk.StringVar()
        self.rom_notice = tk.StringVar()

        content = ttk.Frame(root, padding=(32, 28, 32, 24))
        content.pack(fill="both", expand=True)
        self.home = ttk.Frame(content)
        self.lobby = ttk.Frame(content)
        self.build_home()
        self.build_lobby()
        self.set_rom(rom)
        self.show_home()

    def configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", font=(FONT, 11), background=BACKGROUND, foreground=TEXT)
        style.configure("Title.TLabel", font=(FONT, 28, "bold"))
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Panel.TFrame", background=PANEL, bordercolor=BORDER)
        style.configure("Panel.TLabel", background=PANEL)
        style.configure("PanelMuted.TLabel", background=PANEL, foreground=MUTED, font=(FONT, 10))
        style.configure("PanelTitle.TLabel", background=PANEL, font=(FONT, 12, "bold"))
        style.configure("TEntry", padding=(10, 8), fieldbackground=FIELD, foreground=TEXT,
                        insertcolor=TEXT, bordercolor=BORDER, lightcolor=FIELD, darkcolor=FIELD)
        style.map("TEntry", bordercolor=[("focus", ACCENT)])
        style.configure("TButton", background=PANEL, bordercolor=BORDER, focuscolor=ACCENT,
                        lightcolor=PANEL, darkcolor=PANEL, padding=(12, 9))
        style.map("TButton", background=[("pressed", FIELD), ("active", "#273B4B")],
                  foreground=[("disabled", MUTED)])
        style.configure("Primary.TButton", background=ACCENT, foreground=BACKGROUND,
                        bordercolor=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT,
                        font=(FONT, 11, "bold"))
        style.map("Primary.TButton", background=[("disabled", BORDER), ("pressed", "#58C89A"),
                                                 ("active", "#A0F6CC")],
                  foreground=[("disabled", TEXT)])
        style.configure("Selected.TButton", background="#23483D", foreground=ACCENT,
                        bordercolor=ACCENT, lightcolor="#23483D", darkcolor="#23483D")
        style.map("Selected.TButton", background=[("pressed", "#23483D"), ("active", "#315E51")])

    def rom_card(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Panel.TFrame", padding=16)
        card.pack(fill="x")
        card.columnconfigure(0, weight=1)
        ttk.Label(card, text="游戏 ROM", style="PanelMuted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(card, textvariable=self.rom_name, style="PanelTitle.TLabel", wraplength=330).grid(
            row=1, column=0, sticky="w", pady=(4, 0)
        )
        ttk.Button(card, text="选择 ROM", command=self.choose_rom).grid(row=0, column=1, rowspan=2, sticky="e")
        ttk.Label(card, textvariable=self.rom_notice, style="PanelMuted.TLabel", wraplength=500).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )
        apply_patch = ttk.Button(card, text="应用双人补丁", command=self.prepare_rom)
        apply_patch.grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.prepare_buttons.append(apply_patch)

    def build_home(self) -> None:
        ttk.Label(self.home, text="超级玛丽", style="Title.TLabel").pack(anchor="w")
        ttk.Label(self.home, text="双人同屏联机", style="Muted.TLabel").pack(anchor="w", pady=(3, 30))
        self.rom_card(self.home)

        menu = ttk.Frame(self.home, style="Panel.TFrame", padding=16)
        menu.pack(fill="x", pady=(18, 0))
        ttk.Button(menu, text="局域网联机", command=self.show_lobby, style="Primary.TButton").pack(
            side="right", padx=(12, 0)
        )
        ttk.Label(menu, text="双人房间", style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(menu, text="使用 IPv4 加入，双方同步手柄输入。", style="PanelMuted.TLabel",
                  wraplength=350).pack(anchor="w", pady=(5, 0))

    def build_lobby(self) -> None:
        ttk.Button(self.lobby, text="返回主页面", command=self.show_home).pack(anchor="w")
        ttk.Label(self.lobby, text="局域网联机", style="Title.TLabel").pack(anchor="w", pady=(12, 14))
        self.rom_card(self.lobby)

        tabs = ttk.Frame(self.lobby)
        tabs.pack(fill="x", pady=(16, 10))
        tabs.columnconfigure((0, 1), weight=1, uniform="modes")
        self.host_tab = ttk.Button(tabs, text="创建房间 · P1", command=lambda: self.select_mode("host"))
        self.join_tab = ttk.Button(tabs, text="加入房间 · P2", command=lambda: self.select_mode("join"))
        self.host_tab.grid(row=0, column=0, padx=(0, 4), sticky="ew")
        self.join_tab.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        form = ttk.Frame(self.lobby, style="Panel.TFrame", padding=(16, 12))
        form.pack(fill="x")
        form.columnconfigure(0, weight=1)
        self.address_field = ttk.Frame(form, style="Panel.TFrame")
        self.address_field.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Label(self.address_field, text="目标 IPv4 地址", style="PanelMuted.TLabel").pack(anchor="w")
        ttk.Entry(self.address_field, textvariable=self.address).pack(fill="x", pady=(5, 0))

        self.port_field = ttk.Frame(form, style="Panel.TFrame")
        self.port_field.grid(row=0, column=1, sticky="w")
        self.port_label = ttk.Label(self.port_field, style="PanelMuted.TLabel")
        self.port_label.pack(anchor="w")
        ttk.Entry(self.port_field, textvariable=self.port, width=10).pack(anchor="w", pady=(5, 0))

        self.form_hint = ttk.Label(form, style="PanelMuted.TLabel", wraplength=480)
        self.form_hint.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Label(self.lobby, text="A / D 移动 · S 蹲下 · J 加速 / 火球 · K 跳跃\n"
                  "Space 开始 / 暂停", style="Muted.TLabel").pack(anchor="w", pady=(9, 0))

        actions = ttk.Frame(self.lobby)
        actions.pack(fill="x", pady=(12, 0))
        self.start_button = ttk.Button(actions, style="Primary.TButton", command=self.start_session)
        self.start_button.pack(side="left")
        self.probe_button = ttk.Button(actions, text="测试连通性", command=self.test_connection)
        self.probe_status = ttk.Label(self.lobby, style="Muted.TLabel", wraplength=500)
        self.probe_status.pack(anchor="w", pady=(8, 0))
        self.session_status = ttk.Label(self.lobby, style="Muted.TLabel", wraplength=500)
        self.session_status.pack(anchor="w", pady=(4, 0))
        self.select_mode("host")

    def show_home(self) -> None:
        self.lobby.pack_forget()
        self.home.pack(fill="both", expand=True)

    def show_lobby(self) -> None:
        self.home.pack_forget()
        self.lobby.pack(fill="both", expand=True)

    def select_mode(self, mode: str) -> None:
        self.mode = mode
        joining = mode == "join"
        self.host_tab.configure(style="TButton" if joining else "Selected.TButton")
        self.join_tab.configure(style="Selected.TButton" if joining else "TButton")
        if joining:
            self.address_field.grid()
            self.port_field.grid_configure(column=1)
            self.probe_button.pack(side="left", padx=(8, 0))
            self.probe_status.pack(anchor="w", before=self.session_status, pady=(8, 0))
        else:
            self.address_field.grid_remove()
            self.port_field.grid_configure(column=0)
            self.probe_button.pack_forget()
            self.probe_status.pack_forget()
        self.port_label.configure(text="目标 TCP 端口" if joining else "监听 TCP 端口")
        self.update_form_hint()
        self.start_button.configure(text="加入房间" if joining else "创建房间")

    def update_form_hint(self) -> None:
        hint = "P2 加入后，按所选 ROM 的说明开启双人同屏。"
        if self.mode == "join":
            hint = "同机填写 127.0.0.1。加入后，等房主选择双人玩法。"
        elif self.rom_kind in (RomKind.PAL_COOP, RomKind.COOP):
            select_key = "K" if self.rom_kind == RomKind.PAL_COOP else "右 Shift"
            hint = f"P2 加入后，房主按 {select_key} 选 2 PLAYER GAME，再按 Space 开始。"
        self.form_hint.configure(text=hint)

    def choose_rom(self) -> None:
        selection = filedialog.askopenfilename(
            parent=self.root, title="选择 NES ROM", initialdir=self.rom.parent if self.rom else ROOT,
            filetypes=(("NES ROM", "*.nes"),),
        )
        if selection:
            self.set_rom(Path(selection))

    def set_rom(self, rom: Path | None) -> None:
        self.rom = rom
        self.rom_name.set(rom.name if rom else "未选择 ROM")
        self.rom_kind = None
        notice = "请选择同屏版 ROM 或支持打补丁的原版。"
        if rom is not None:
            try:
                self.rom_kind, notice = describe_rom(rom)
            except (OSError, ValueError) as error:
                notice = str(error)
        self.rom_notice.set(notice)
        for button in self.prepare_buttons:
            if self.rom_kind == RomKind.PATCHABLE:
                button.grid()
            else:
                button.grid_remove()
        self.update_form_hint()
        self.update_start_button()

    def prepare_rom(self) -> None:
        if self.rom_kind != RomKind.PATCHABLE or self.rom is None:
            return
        try:
            rom = prepare(self.rom)
        except (OSError, ValueError) as error:
            messagebox.showerror("无法应用双人补丁", str(error), parent=self.root)
            return
        self.set_rom(rom)

    def update_start_button(self) -> None:
        ready = self.process is None and self.rom_kind in (RomKind.PAL_COOP, RomKind.COOP, RomKind.UNKNOWN)
        self.start_button.state(["!disabled" if ready else "disabled"])

    def test_connection(self) -> None:
        try:
            address = str(ipv4_address(self.address.get().strip()))
            port = port_number(self.port.get().strip())
        except argparse.ArgumentTypeError as error:
            self.probe_status.configure(text=str(error), foreground=ERROR)
            return

        self.probe_button.state(["disabled"])
        self.probe_status.configure(text=f"正在测试 {address}:{port}…", foreground=MUTED)
        result = SimpleQueue()
        Thread(target=check_connection, args=(address, port, result), daemon=True).start()
        self.root.after(50, self.finish_probe, result)

    def finish_probe(self, result: SimpleQueue[tuple[str, str]]) -> None:
        try:
            message, color = result.get_nowait()
        except Empty:
            self.root.after(50, self.finish_probe, result)
            return
        self.probe_status.configure(text=message, foreground=color)
        self.probe_button.state(["!disabled"])

    def start_session(self) -> None:
        self.set_rom(self.rom)
        if self.rom is None or self.start_button.instate(["disabled"]):
            return
        try:
            port = port_number(self.port.get().strip())
            address = ipv4_address(self.address.get().strip()) if self.mode == "join" else None
            if address is None:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                    listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                    listener.bind(("0.0.0.0", port))
        except (argparse.ArgumentTypeError, ValueError) as error:
            self.session_status.configure(text=str(error), foreground=ERROR)
            return
        except OSError as error:
            self.session_status.configure(text=f"无法监听 TCP {port}。{error}", foreground=ERROR)
            return

        try:
            self.process = start_emulator(self.mode, self.rom, port, address=address, log=self.log)
        except (OSError, ValueError) as error:
            self.session_status.configure(text=f"无法启动模拟器。{error}", foreground=ERROR)
            return

        self.update_start_button()
        self.session_status.configure(text="已发起联机。请在游戏窗口确认状态，关闭游戏窗口即可退出。",
                                      foreground=MUTED)
        self.root.after(200, self.poll_session)

    def poll_session(self) -> None:
        status = self.process.poll()
        if status is None:
            self.root.after(200, self.poll_session)
            return
        if status == 0:
            self.session_status.configure(text="游戏窗口已关闭。", foreground=MUTED)
        else:
            self.session_status.configure(text=f"模拟器退出，退出码 {status}。", foreground=ERROR)
        self.process = None
        self.update_start_button()


def main() -> None:
    parser = argparse.ArgumentParser(description="NES 双人联机启动器")
    parser.add_argument("--rom", type=Path, default=default_rom())
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    root = tk.Tk()
    Launcher(root, args.rom.resolve() if args.rom else None, args.log.resolve() if args.log else None)
    root.mainloop()


if __name__ == "__main__":
    main()
