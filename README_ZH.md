# 实时语音中英翻译与字幕生态系统（Windows 快速上手与操作指南）

[![Release](https://img.shields.io/github/v/release/Sonatko/all_translete_online?color=blue&label=最新发布版本%20Release)](https://github.com/Sonatko/all_translete_online/releases)
[![Platform](https://img.shields.io/badge/操作系统-Windows%2010%20%2F%2011%20x64-blue.svg)](https://microsoft.com)

**[English & Русский (README.md)](README.md)** | **[简体中文指南 (README_ZH.md)](README_ZH.md)**

本项目为 Windows 桌面端打造的低延迟、高性能实时双向翻译系统，专为电竞游戏（CS2 / 无畏契约 / 战地）、Discord 跨国语音开黑、实时直播听译与桌面屏幕即时翻译设计。无需手动配置复杂环境，提供一键免安装便携版。

---

## 🌟 核心功能一览

1. **Stage 1: 实时系统声音与麦克风双语字幕 (LiveTranslate)**
   - 捕捉游戏、Discord、浏览器视频的声音，毫秒级转写并翻译。
   - 屏幕置顶双行悬浮字幕（原声 + 译文），支持中/英/日/俄。
   - **自动化语言适配**：在中文系统上，目标语言自动配置为**中文 (ZH)**！
   - **黄金控制方案**：`F9` 一键静音/隐藏字幕，双击鼠标滚轮锁定穿透，按住滚轮自由拖拽。
2. **Stage 2: 屏幕圈选与剪贴板即时翻译 (OverTranslate Portable)**
   - 游戏非选中文本截图翻译（快捷键 `Ctrl + Alt + A`）。
   - 单词/句子双击 `Ctrl + C + C` 悬浮词典解析。
   - **全自动本地化**：在中文 Windows 上，翻译目标语言自动切换为 **`ZH-CN`**，界面自动适配为简体中文！
3. **Stage 3: 实时中译英语音同传与声音克隆 (Voice Studio)**
   - 麦克风说话（中文） ➔ 毫秒级识别与地道翻译 ➔ 以你自己的声音音色播报出流利英文！
   - 支持直连游戏麦克风与 Discord（通过虚拟声卡 VB-Cable 或 Topping 硬件 Loopback）。
   - 内置 7 秒个人声音克隆向导，快速录制生成专属音色！

---

## 🚀 方式一：下载即用（免安装便携版，最推荐）

适合小白与不想配置 Python 环境的任何用户：

1. 在 GitHub 页面右侧 **Releases** 中下载最新版压缩包：  
   👉 **`TranslationEcosystem-v0.3.5-Windows-x64.zip`**
2. 解压到电脑任意英文路径（例如 `D:\TranslationEcosystem`，**路径切勿包含中文字符**）。
3. 双击运行根目录下的 **`START.bat`**。  
   - 脚本会自动检测并配置隔离运行环境，无需系统预装 Python、Git 或管理员权限。
   - 启动后将直接打开**三语控制中心（Universal Hub）**。

---

## 🛠 方式二：源码克隆与极速部署（开发者）

如果您使用 Git 克隆了源码：

```bash
# 1. 克隆仓库（国内加速镜像）
git clone https://ghproxy.net/https://github.com/Sonatko/all_translete_online.git
cd all_translete_online

# 2. 启动系统（自动配置清华大学镜像源并注入完整依赖）
START.bat
```

---

## 🔄 项目更新与自愈修复（一键无感升级）

当仓库更新代码或新增特性时，无需手动执行繁琐命令行：

### 方案 A（最推荐）：控制台界面内一键更新（In-App 1-Click Update）
在 **控制台（Hub）** 窗口顶部标题栏右侧，设有版本状态按钮：
- 当发现 GitHub 新版本时，按钮将高亮显示：**`✨ 发现新版本`**。
- 直接在软件界面内点击该按钮，系统将自动优雅停止后台任务、拉取最新代码、同步补丁并自动重启软件，完全无需打开黑窗口。

### 方案 B：直接运行 `START.bat`
即使您通过 Git 命令行仅执行了 `git pull`，直接双击 **`START.bat`** 也会在 0.3 秒内触发极速自愈审计，自动补全最新补丁并应用中文化配置！开发者亦可使用 `scripts\update.bat` 命令行脚本。

---

## 📥 国内一键下载 AI 神经网络模型

为了避免仓库体积臃肿，AI 神经网络模型（ASR 识别、MT 翻译、TTS 语音合成）在首次使用前需要下载：

### 方法 A（推荐，命令行自动下载）
1. 打开 `scripts` 文件夹，双击运行 **`download_models_china.bat`**。
2. 脚本将通过国内高速镜像（hf-mirror.com）自动下载中文流水线全套模型：
   - **SenseVoice-Small INT8**（阿里通义多语种识别，~230 MB）
   - **Opus-MT ZH➔EN INT8**（低延迟中译英模型，~150 MB）
   - **Pocket-TTS 24kHz**（英文神经语音克隆模型，~210 MB）
3. 终端打印 `[SUCCESS]` 后按任意键退出即可。

### 方法 B（在软件界面内下载）
1. 运行 `START.bat`，在控制中心启动 **Stage 3: Voice Studio**。
2. 切换至顶部第 2 个选项卡 **「Модели и Управление памятью / 模型与内存管理」**。
3. 勾选 **`🇨🇳 国内镜像加速 (China Mirror: hf-mirror.com)`**。
4. 点击蓝色按钮 **`📥 一键下载所需模型`**，界面将实时显示下载进度与真实 MB/s 速度。
5. 下载完成后点击 **`⚡ Загрузить в память (Load in RAM)`**，所有状态灯变为绿色即可！

---

## 🎮 黄金控制方案与常用快捷键（Golden Controls）

| 组件 | 功能 | 快捷键 / 手势 | 作用说明 |
| :--- | :--- | :--- | :--- |
| **Stage 1 字幕** | **总开关** | **`F9`** | 同步切换字幕显示/隐藏，并启停后台系统音频监听。 |
| **Stage 1 字幕** | **鼠标穿透** | **双击鼠标滚轮 (`2x MMB`)** | 在字幕条上快速双击滚轮，开启鼠标点击穿透（玩游戏不挡视线和点击）。 |
| **Stage 1 字幕** | **移动字幕** | **按住滚轮拖拽 (`MMB Drag`)** | 按住鼠标滚轮即可把字幕拖动到屏幕任意位置，自动保存坐标。 |
| **Stage 2 识图** | **截图翻译** | **`Ctrl + Alt + A`** | 框选屏幕任意区域，就地识别游戏/图片里的外语并替换为中文。 |
| **Stage 2 识图** | **即时查词** | **`Ctrl + C + C`** | 选中任意文字连按两次 Ctrl+C，弹出上下文语法与生词解析。 |
| **Stage 2 识图** | **就地替换** | **`Ctrl + Alt + C`** | 在输入框内选中文字直接翻译替换。 |
| **Stage 3 同传** | **语音说话** | **`Shift + 按住鼠标滚轮`** | 按住说话（中文），说完松开，系统即刻在游戏中播报流利英文语音！ |

---

## 🎙 游戏与 Discord 音频设置（虚拟麦克风对接）

如果您没有 Topping 硬件声卡，请配合免费虚拟声卡软件 **VB-CABLE** 使用：
1. 运行 `scripts\install_vbcable.bat` 安装虚拟驱动。
2. 在 CS2 / 无畏契约 / Discord 中：将输入设备（麦克风）设置为 **`CABLE Output (VB-Audio Virtual Cable)`**。
3. 在 Stage 3 控制台中：将输出设备设置为 **`CABLE Input (VB-Audio Virtual Cable)`**。
4. 完成！现在你在游戏里按下开麦键，队友听到的就是你克隆音色的流利英文！

---

## 🛑 停止运行与退出

双击根目录下的 **`STOP.bat`**：  
瞬间彻底退出所有后台翻译组件，释放声卡占用与内存。
