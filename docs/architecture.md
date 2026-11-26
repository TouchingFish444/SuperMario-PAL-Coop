# 架构与维护

## 游戏逻辑

PAL v5 使用欧版 Rev A 原版作为底版。BPS 复用底版的程序和图形，在 MMC3 扩展区域加入 6502 汇编。启动时把补丁代码复制到卡带 RAM，从而在原版 PRG 保持映射时调用原版例程。生成的 ROM 使用 PAL 时序。

原版每帧先更新马里奥。补丁随后读取第二手柄，暂存马里奥的角色变量，把路易吉的状态放入原版移动例程使用的地址，计算后再恢复马里奥。顶砖调用原版方块处理例程，道具使用同一对象缓冲区。路易吉的状态、分数和绘制由补丁维护。

双人更新以原版的游戏模式、区域指针和入场状态为准。原版正在装载新区时暂停路易吉的位置更新，原版进入可操作状态后，在新区域入口附近恢复路易吉。形态和分数跨区域保存。路易吉也可触发原版的进管道、旗杆和城堡斧头脚本，由脚本带两人进入下一区域。所有关卡复用原版的区域表和地图。

| 欧版 Rev A CPU 地址 | 用途 |
| --- | --- |
| `$8E5C`、`$06FD` | 读取两只手柄，保存 P2 输入 |
| `$8175`、`$8212` | 游戏模式调用与补丁帧更新入口 |
| `$819D`、`$91D9`、`$9282` | 双手柄暂停、无限生命和关闭轮流切换 |
| `$D69E` 至 `$D6D8` | 配置扩展卡带并切换程序 bank |
| `$B329`、`$85DC`、`$EE1E` | 原版移动、路易吉配色及角色图块表 |
| `$BCF2`、`$DF97`、`$C99E` | 顶砖、方块分类和道具对象删除 |
| `$9C03`、`$0750` | 原版装载区域指针，补丁据此检测换场景 |
| `$DDD6`、`$DEF0`、`$DE49`、`$DE16` | 原版横向管道、纵向管道、旗杆和城堡斧头入口 |
| `$CE0E` | 用原版计算的火棒各段位置检测路易吉受伤 |
| `$AF93`、`$AFC4` | 计算共享镜头可前进的距离，再调用原版滚屏 |
| `$C122` | 城堡迷宫回环时一起平移两名玩家和镜头的坐标 |
| `$B629` | 让原版例程继续更新两人共用的火球槽位 |
| `$0500`、`$05D0` | 随现有滚屏更新的两页地形碰撞数据 |

正常玩法用领先者的位置带动镜头，单帧最多前进 4 像素，并给后方玩家保留 8 像素的左侧余量。抵达余量时先等后方玩家移动，双方继续受画面边界约束。城堡迷宫的原版回环会使两人的世界坐标和镜头一起平移。单人模式和原版入场、结束演出继续走原版滚屏流程。

独立镜头需要把关卡更新和视野分开。两端仍可同步手柄，但确定性的游戏模拟必须同时维护两名玩家附近的地形与敌人，再由各自的渲染端选择跟随的角色。只把两端的 NES 滚屏设成不同位置，会让原版引擎更新不同的关卡区域。

## 联机

启动器通过 IPv4 传入端口和连接角色，调用 RetroArch 1.22.2 和 FCEUmm 核心。两边从一致的游戏状态开始，交换每帧手柄输入，各自在本机计算角色、碰撞和得分。RetroArch 会在迟到的输入与预测有差异时回滚重算。房主负责监听连接和协调初始同步。

项目的联机配置每 60 帧检查一次模拟状态。PAL v5 联机使用新的卡带 RAM，配置停用自动读档、自动应用作弊和自动加载输入重映射，减少两端启动状态的差异。两台电脑应使用相同的生成 ROM 和核心 DLL。 [RetroArch 联机协议](https://docs.libretro.com/development/retroarch/netplay/#behavior)

## 源码运行和打包

### 准备环境

- Windows x64，Python 3.10 或更新版本。构建启动器额外需要 PyInstaller，重建 PAL 汇编补丁需要 cc65 的 `ca65.exe` 和 `ld65.exe`。
- 将 RetroArch 1.22.2 Windows x64 便携包解压到 `runtime/RetroArch-Win64/`。将 `fceumm_libretro.dll` 放进其 `cores/`，将 `fceumm_libretro.info` 放进 `info/`。优先从已验证的便携包复制整个运行目录，保持两个联机端的核心一致。 [RetroArch 1.22.2 Windows x64 文件](https://buildbot.libretro.com/stable/1.22.2/windows/x86_64/) · [FCEUmm fb919fb 源码](https://github.com/libretro/libretro-fceumm/tree/fb919fb) · [Libretro 核心信息文件](https://github.com/libretro/libretro-core-info/blob/master/fceumm_libretro.info)
- 将欧版 Rev A iNES ROM 放进 `assets/roms/`。支持的完整文件 CRC32 为 `7D5FAA58`，SHA-1 为 `ab30029efec6ccfc5d65dfda7fbc6e6489a80805`。World iNES 或 NES 2.0 输入会走 `patches/upstream/` 中的 Co-op v45 补丁。

### 常用命令

```powershell
py -3 -m app.netplay prepare ".\assets\roms\0000超级玛丽.nes"
py -3 -m app.launcher
```

默认生成 `roms/SuperMarioBros-PAL-Coop-v5.nes`。它的 SHA-1 是 `cfb8b0ee0c4d6447d11af9641f282dbec2d41d51`。

| 命令 | 用途 |
| --- | --- |
| `py -3 -m app.netplay host` | 创建房间，使用默认端口 |
| `py -3 -m app.netplay join 192.168.1.23` | 加入房主的 IPv4 地址 |
| `py -3 -m app.netplay local` | 在一个进程里用两只手柄游玩 |

IPv4 联机命令支持 `--port`、`--rom`、`--runtime` 和 `--log`。启动时输出 ROM 与模拟器核心的 SHA-256，可用于两端核对。使用 World v45 时，标题菜单选择键为 **右 Shift**。

```powershell
py -3 -m pip install "PyInstaller>=6,<7"
py -3 -m tools.build_windows
py -3 -m tools.build_windows --include-rom
```

普通构建更新 `bin/SuperMario.exe` 和 `dist/SuperMario-Win64.zip`。当本地启动器正在运行时，可以从本次生成的便携包运行新启动器。即玩构建把已生成的双人 ROM 加入 `dist/SuperMario-ReadyToPlay-Win64.zip`。两种 ZIP 都可完整解压后从包目录运行 `SuperMario.exe`。

## 维护补丁

```powershell
py -3 -m patches.pal.build_patch ".\assets\roms\0000超级玛丽.nes" --cc65-bin "C:\Tools\cc65\bin"
```

构建脚本校验 PAL 底版及关键指令的字节，再用该底版验证生成的 BPS。修改汇编后的补丁与输出 ROM 应一起检查。发布新补丁时，同步更新汇编构建脚本的输出文件名和 `app/netplay.py` 中的文件名及 SHA-1。 [PAL 汇编符号参考](https://github.com/RetrolariumLab/smb1_src/tree/eb8faad337056e074e78ec5f3b496be24e7de761)

## 旧版本归档

当前 EXE 和 ZIP 使用固定路径，重复构建会更新这些文件。发布新版前，如需保留旧发行包，可把它连同对应的生成 ROM、BPS 放进 `archive/<版本>/`。需要运行旧版时，解压归档中的即玩包。

Git 跟踪源码、文档、配置和维护中的 BPS。素材目录、生成 ROM、模拟器运行目录、本地构建产物和归档由工作区管理。

## 发布即玩包

每个新版本更新 `app/netplay.py` 的 `PAL_RELEASE_TAG` 和 ROM SHA-1，准备对应的 BPS 和生成后的 ROM，并在 `docs/releases/<版本号>.md` 写版本说明。提交并推送到 GitHub 默认分支后，在有运行环境和 ROM 的 Windows 工作区执行以下命令。

```powershell
py -3 -m tools.publish_release --repo TouchingFish444/SuperMario-PAL-Coop
```

发布工具生成含 ROM 的即玩包，上传为对应 GitHub Release 的附件，校验 ZIP 的 SHA-256 后发布。公开仓库的发行版可直接下载，Git 仓库历史仍只记录源码、补丁、配置和文档。 [最新发行版](https://github.com/TouchingFish444/SuperMario-PAL-Coop/releases/latest)
