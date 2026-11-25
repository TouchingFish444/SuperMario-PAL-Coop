# Super Mario Bros. PAL 双人联机

Windows 11 x64 上的双人联机启动器。项目用 PAL v3 补丁给欧版 Rev A 增加双人同屏，再通过 RetroArch 同步两人的手柄输入。马里奥和路易吉在同一关卡同时行动，主机是 P1，加入方是 P2。

## 快速开始

手头已有 `SuperMario-PAL-v3-ReadyToPlay-Win64.zip` 时，在两台电脑上分别完整解压，运行目录中的 `SuperMario-PAL-v3.exe`。启动器会自动选中随包提供的 PAL v3 ROM。

从 GitHub 克隆仓库后，需要准备自己的欧版 Rev A ROM 和模拟器运行目录。启动器支持选中原版后点击 **应用双人补丁**，自动生成并切换到 PAL v3。 [源码运行和打包](docs/architecture.md#源码运行和打包)

### 创建和加入房间

1. 两端选用同一份 PAL v3 ROM，打开 **局域网联机**。
2. P1 选择 **创建房间**，填写 TCP 端口，默认 `55435`。跨电脑时，用 `ipconfig` 查找房主当前网卡的 IPv4 地址。
3. P2 选择 **加入房间**，填写房主的 IPv4 地址和相同端口。可以先点 **测试连通性**，再点 **加入房间**。
4. P2 加入后，P1 在标题画面按 **K** 选中 `2 PLAYER GAME`，再按 **Space** 开始。两人都在各自的游戏窗口操作。

在同一台电脑双开时，P2 地址填 `127.0.0.1`。用一把键盘时，可以切换窗口焦点分别操作。测试连通性只检测 TCP 端口是否可达，ROM 和核心兼容性由 RetroArch 在加入时检查。

### 键位

| 键位 | 操作 |
| --- | --- |
| **A / D** | 左右移动 |
| **S** | 蹲下 |
| **J** | 加速，火焰形态下发射火球 |
| **K** | 跳跃，PAL v3 标题页切换玩法 |
| **Space** | 开始、暂停 |

### PAL v3 玩法范围

- **1-1 地面区域**支持两人同时行动。路易吉复用欧版移动逻辑和配色，可以顶问号砖、拾取蘑菇变大、碎砖和发射火球。两人有各自的状态和分数，并拥有无限生命。
- 方块和道具由两人共享。两人同时碰到同一个道具时，马里奥的碰撞先结算。火球击杀目前仍由原版 P1 流程记分。
- 两人共用跟随 P1 的镜头。P2 离开画面会回到 P1 附近。独立镜头、分开探索、P2 独立进管道和触发终点，以及其他关卡的双人支持仍待实现。

## 项目结构

| 路径 | 用途 |
| --- | --- |
| `launcher.py` | Windows 界面、ROM 选择、建房和加入 |
| `netplay.py`、`netplay.cfg` | ROM 匹配、IPv4 参数和 RetroArch 联机配置 |
| `bps.py` | BPS 补丁应用与校验 |
| `patches/pal/` | PAL 汇编、链接布局与补丁生成 |
| `patches/*.bps` | 当前 PAL v3 补丁，以及面向 World 版的上游 Co-op v45 补丁 |
| `build_windows.py` | Windows 启动器与便携包构建 |
| `runtime/`、`roms/`、`dist/` | 本地模拟器、ROM 和构建产物 |

双方交换带帧号的按键，在本机执行同一份 ROM。PAL 补丁负责双人规则，RetroArch 负责逐帧同步与回滚。 [架构与维护](docs/architecture.md)

感谢 Libretro 的 RetroArch 和 FCEUmm、benj-edwards 的 Co-op v45，以及 RetrolariumLab 的 PAL 汇编参考。 [RetroArch 联机机制](https://docs.libretro.com/development/retroarch/netplay/) · [Co-op v45](https://github.com/benj-edwards/NESCoopMods#super-mario-bros-co-op) · [PAL 汇编参考](https://github.com/RetrolariumLab/smb1_src/tree/eb8faad337056e074e78ec5f3b496be24e7de761)
