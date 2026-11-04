# 实时语音中英翻译与字幕生态系统（Windows 快速上手指南）

[English / Русский (README.md)](README.md) | **[简体中文 (README_ZH.md)](README_ZH.md)**

本项目为 Windows 桌面端打造的低延迟实时双向翻译系统，特别针对游戏（CS2 / 战地 / 无畏契约）、Discord、实时直播与跨国语音交流优化。

---

## ⚡ 为什么之前界面显示红色 `ERROR`？

在初次运行 **Stage 3: Voice Translation Studio** 时，界面中的 ASR、MT、TTS 节点可能会亮起红色的 **`ERROR`**：
1. **轻量化设计：** Git 仓库为了避免体积过大，默认不打包数个 GB 的 AI 神经网络二进制权重。
2. **语言不匹配：** 原始配置为俄语母语者的俄译英模型（Sber GigaAM），对中文语音无效。

我们已针对中国大陆网络环境部署了**全套中文 AI 管道**与**国内极速下载镜像（hf-mirror.com / ghproxy.net）**。

---

## 🚀 3 步快速配置与使用（中国用户专用）

### 第一步：一键下载模型权重（国内直连）

**方法 A（最推荐，纯鼠标操作）：**
1. 进入项目根目录下的 `scripts` 文件夹。
2. 双击运行 **`download_models_china.bat`**。
3. 终端会自动通过国内反代镜像加速下载：
   * **阿里通义 SenseVoice-Small INT8**（多语种与中文方言识别，~230 MB）
   * **Helsinki Opus-MT ZH➔EN INT8**（轻量级低延迟中译英模型，~150 MB）
   * **Kyutai Pocket-TTS 24kHz**（英文神经语音合成模型，~210 MB）
4. 下载完毕后出现 `[SUCCESS]` 即可关闭窗口。

**方法 B（软件内界面操作）：**
1. 启动 `START.bat` 并打开 **Stage 3: Voice Studio**。
2. 切换至顶部第 2 个选项卡 **「Модели и Управление памятью」（模型与内存管理）**。
3. 勾选 **`🇨🇳 国内镜像加速 (China Mirror: hf-mirror.com)`**。
4. 点击蓝色按钮 **`📥 一键下载所需模型`**，界面将实时显示下载百分比与速度（MB/s）。

---

### 第二步：选择中文流水线（ZH➔EN）

1. 进入 **Stage 3: Voice Translation Studio** 主窗口。
2. 在交互式信号链上方，点击绿色的语言切换按钮：  
   👉 **`[ 🇨🇳 中文配置 / Китайский (ZH➔EN: SenseVoice + Opus-MT) ]`**
3. 节点 2 和节点 3 将自动更新为中文识别与翻译模型。
4. 点击选项卡 2 中的 **`⚡ Загрузить в память (Load in RAM)`**，所有红色的 `ERROR` 徽章将变为绿色的 **`В ОЗУ (0 ms)`**！

---

### 第三步：在 Discord 或游戏中开麦交流

* **数据流向：**  
  你的物理麦克风 ➔ 本地 SenseVoice 实时识别中文 ➔ Opus-MT 瞬间翻成地道英文 ➔ Pocket-TTS 用自然人声将英文输出至虚拟音频线（VB-Cable）。
* **游戏 / Discord 音频设置：**  
  打开 Discord 或游戏音频设置，将**麦克风 / 输入设备（Input Device）**设置为：  
  👉 **`CABLE Output (VB-Audio Virtual Cable)`**
* **说话快捷键（Push-to-Talk）：**  
  按住 **`Shift + 鼠标中键（按下滚轮）`** 说话，说完松开，系统即刻在游戏频道中播报纯正英文！
