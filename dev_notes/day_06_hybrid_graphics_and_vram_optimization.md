# Day 06: Hybrid Graphics Architecture (Cross-Adapter Presentation) & VRAM Optimization

## 1. Problem: 3.5 GB Idle VRAM Overhead on RTX 5070
When inspecting idle GPU state via `nvidia-smi`, 3.5 GB of VRAM was occupied despite zero active translation models:
- `dwm.exe` (Desktop Window Manager): **1,768.9 MB**
- `thorium.exe` (Chromium browser): **620.0 MB**
- `Discord.exe` (Electron chat): **615.3 MB**
- `Antigravity IDE.exe`: **399.4 MB**
- `obs64.exe` (OBS Studio): **397.6 MB**
- `Scrcpy Studio.exe` + `scrcpy.exe` (Android mirroring): **331.1 MB**

---

## 2. Architectural Solution: WDDM Cross-Adapter Presentation
Modern Windows 11 systems with an AMD Ryzen 7 7800X3D (RDNA 2 integrated graphics) and discrete NVIDIA GeForce RTX 5070 support **Cross-Adapter Presentation**:
1. **Physical Cable Attachment**:
   - The monitor cable remains plugged exclusively into the **NVIDIA RTX 5070**.
   - This ensures games, OBS Studio, and low-latency rendering output directly to display ports at native refresh rates (144–240 Hz) without PCIe bottlenecking.
2. **2D Application Offload to AMD Radeon(TM) Graphics**:
   - Lightweight desktop tools (Discord, browser, Scrcpy) are assigned to `GpuPreference=1;` (Power Saving / iGPU) in `HKCU\Software\Microsoft\DirectX\UserGpuPreferences`.
   - The integrated AMD GPU allocates SwapChain surfaces in system RAM (DDR5 4800 MHz) and executes 2D/video rasterization.
   - Finished desktop frames are transferred across the PCIe bus directly to the RTX 5070 scan-out pipeline with negligible overhead (<0.5% PCIe utilization).
3. **DWM Transparency Disabling**:
   - In Windows 11, Mica/Acrylic blur effects force DWM to retain double-buffered blur texture layers for every overlapping window.
   - Disabling transparency (`EnableTransparency = 0`) eliminates blur passes and frees ~600–800 MB of DWM VRAM.

---

## 3. Optimization Execution Plan & Verification Evidence
1. **Step 1 (Transparency & DWM Shaders)**:
   - Disabled Windows 11 Transparency (`EnableTransparency = 0`).
   - Disabled DWM drop shadows via Win32 API (`SPI_SETDROPSHADOW = 0x1025`).
   - Disabled window minimize/maximize animation (`SPI_SETANIMATION = 0x0049`, `MinAnimate = 0`).
   - Disabled menu fade, tooltip animations, and taskbar widgets (`TaskbarDa = 0`).
   - Disabled GameDVR background recording (`HistoricalCaptureEnabled = 0`).
2. **Step 2 (Cross-Adapter iGPU Allocation)**:
   - Configured `GpuPreference=1;` in `HKCU\Software\Microsoft\DirectX\UserGpuPreferences` for:
     - `thorium.exe` (Chromium browser)
     - `Discord.exe` (Voice & chat)
     - `Scrcpy Studio.exe` + `scrcpy.exe` (Android mirroring)
     - `Antigravity IDE.exe` (Development IDE, dropped from 350 MB to 81 MB)
     - `obs64.exe` (OBS Studio Virtual Camera & Recording)
   - Created 1-Click Toggle Batch Scripts in project root:
     - [SET_OBS_GPU_AMD.bat](../SET_OBS_GPU_AMD.bat): switches OBS to AMD iGPU (frees ~360 MB VRAM)
     - [SET_OBS_GPU_NVIDIA.bat](../SET_OBS_GPU_NVIDIA.bat): switches OBS back to RTX 5070 (for 2K/4K 144Hz heavy gaming)
     - [FLUSH_DWM_ADMIN.bat](../FLUSH_DWM_ADMIN.bat): flushes DWM texture cache via Windows UAC elevation

3. **Step 3 (Multi-Monitor Topology & Physical Display Partitioning)**:
   - Discovered multi-display overhead: 3 displays active (2K Primary, 1080p, 2K N140 portable = 8.87M pixels).
   - Partitioned physical cables: Secondary 2K display moved to motherboard (AMD Radeon iGPU), primary display retained on RTX 5070.
   - DWM display swapchains on RTX 5070 dropped significantly.

4. **Step 4 (UWP Background Freezing & Software Rasterization Trimming)**:
   - **SnippingTool.exe**: Set `Disabled=1` and `DisabledByUser=1` in `HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications\Microsoft.ScreenSketch_8wekyb3d8bbwe` and offloaded to AMD iGPU. Permanently eliminated 320 MB lingering capture buffer.
   - **RadeonSoftware.exe**: Set `Disabled=1` in `BackgroundAccessApplications\AdvancedMicroDevicesInc-2.AMDRadeonSoftware_0a9344xs7nr4m`. Eliminated 85 MB headless UWP background app.
   - **Discord.exe**: Disabled Hardware Acceleration inside Discord (`--use-angle=d3d11-warp-webgl` CPU WARP mode). Eliminated 170 MB GPU allocation on RTX 5070.
   - **NVIDIA Overlay & App**: Disabled in-game overlay and closed UI window. Reclaimed ~290 MB.

5. **Architectural Deep-Dive: Cross-Adapter Staging Surfaces**:
   - Why 70-80 MB remains on RTX 5070 for apps rendered on AMD:
     When an app renders in DDR5 RAM on the AMD iGPU, but its window is positioned on the monitor connected to the RTX 5070, Windows WDDM allocates a small Direct3D 11 Shared SwapChain Texture on the RTX 5070. This texture serves as the scan-out staging surface for the physical cable. Moving the window to the monitor connected to the motherboard drops this staging surface to 0 MB.

6. **Final Measured Benchmark Results (Verification Gate)**:
   - **VRAM Initial**: **3,669 MiB (~3.67 GB)**
   - **VRAM Final**: **1,437 MiB (~1.43 GB)**
   - **Total VRAM Reclaimed**: **-2,232 MB (-2.23 GB, 88% VRAM completely free!)**
   - **Free GDDR7 VRAM**: **>10.5 GB available**.
   - **GPU Temperature**: dropped from 59°C to 50°C.
   - **GPU Idle Power Draw**: dropped from 29W to 22W.
   - Font readability (ClearType), image thumbnails, and gaming readiness remain 100% preserved.
