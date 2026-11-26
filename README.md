# Super Mario Bros. PAL 双人联机

Windows 11 x64 上的双人联机启动器。PAL v5 补丁给欧版 Rev A 增加跨关双人同屏，再通过 RetroArch 同步两人的手柄输入。马里奥和路易吉在同一关卡同时行动，主机是 P1，加入方是 P2。

## 快速开始

在当前工作区运行 `bin/SuperMario.exe`。另一台电脑可从最新发行版下载 `SuperMario-ReadyToPlay-Win64.zip`，完整解压后运行包内的 `SuperMario.exe`。启动器会自动选中即玩包内的双人 ROM。 [GitHub Releases](https://github.com/TouchingFish444/SuperMario-PAL-Coop/releases/latest)

从 GitHub 克隆仓库后，需要准备自己的欧版 Rev A ROM 和模拟器运行目录。可把原版 ROM 放进 `assets/roms/`，在启动器里选择它并点击 **应用双人补丁**。 [源码运行和打包](docs/architecture.md#源码运行和打包)

### 创建和加入房间

1. 两端选用同一份 PAL v5 ROM，打开 **局域网联机**。
2. P1 选择 **创建房间**，填写 TCP 端口，默认 `55435`。跨电脑时，用 `ipconfig` 查找房主当前网卡的 IPv4 地址。
3. P2 选择 **加入房间**，填写房主的 IPv4 地址和相同端口。可以先点 **测试连通性**，再点 **加入房间**。
4. P2 加入后，P1 在标题画面按 **K** 选中 `2 PLAYER GAME`，再按 **Space** 开始。两人都在各自的游戏窗口操作。

在同一台电脑双开时，P2 地址填 `127.0.0.1`。用一把键盘时，可以切换窗口焦点分别操作。测试连通性只检测 TCP 端口是否可达，ROM 和核心兼容性由 RetroArch 在加入时检查。

### 键位

| 键位 | 操作 |
| --- | --- |
| **A / D** | 左右移动 |
| **S** | 蹲下，从管口下行 |
| **W** | 向上，攀爬藤蔓 |
| **J** | 加速，火焰形态下发射火球 |
| **K** | 跳跃或游泳划水，标题页切换玩法 |
| **Space** | 开始、暂停 |

### PAL v5 跨关玩法

- 路易吉在原版八个世界的地面、地下、水下和城堡场景中使用同一套双人更新。过关、换世界和进出管道时，队伍一起切换场景，路易吉保留形态和分数。两人拥有无限生命。
- 路易吉可顶问号砖、拾取蘑菇、碎砖和发射火球，也可游泳、搭乘基础平台、爬藤、触碰旗杆或城堡斧头。路易吉发起过关或进管道时，使用原版的单人演出带队推进。
- 方块和道具由两人共享。两人同时碰到同一个道具时，马里奥的碰撞先结算。火球击杀目前仍由原版 P1 流程记分。
- 两人共用镜头，谁领先都能带动滚屏。后方玩家靠近左边缘时，镜头会停住等他跟上，普通跑动和滚屏不会重置角色位置。开场、过关、进入管道和死亡复活仍有各自的入场流程。部分原版机关（如落台和平衡台）仍由马里奥的碰撞驱动。

## 项目结构

| 路径 | 用途 |
| --- | --- |
| `app/` | 启动器、联机命令和 BPS 校验 |
| `config/` | RetroArch 联机配置 |
| `tools/` | Windows 打包入口 |
| `assets/roms/` | 下载的或自行准备的原版 ROM |
| `patches/pal/` | PAL 汇编、链接布局与补丁生成 |
| `patches/*.bps`、`patches/upstream/` | 当前 PAL 补丁和上游 World 版补丁 |
| `runtime/` | RetroArch、FCEUmm 和模拟器附带素材 |
| `roms/` | 已应用补丁的双人 ROM |
| `bin/`、`dist/` | 当前启动器和便携包 |
| `archive/` | 本机旧版本归档 |

双方交换带帧号的按键，在本机执行同一份 ROM。PAL 补丁负责双人规则，RetroArch 负责逐帧同步与回滚。 [架构与维护](docs/architecture.md)

感谢 Libretro 的 RetroArch 和 FCEUmm、benj-edwards 的 Co-op v45，以及 RetrolariumLab 的 PAL 汇编参考。 [RetroArch 联机机制](https://docs.libretro.com/development/retroarch/netplay/) · [Co-op v45](https://github.com/benj-edwards/NESCoopMods#super-mario-bros-co-op) · [PAL 汇编参考](https://github.com/RetrolariumLab/smb1_src/tree/eb8faad337056e074e78ec5f3b496be24e7de761)
