<div align="center">

# 🔥 SDM845 ReSukiSU Kernel

**Xiaomi SDM845 系列内核 · ReSukiSU + SUSFS 集成版**

[![Build](https://img.shields.io/github/actions/workflow/status/xiaochen301/sdm845-resukisu-kernel/build.yml?style=for-the-badge&logo=github&label=自动构建)](https://github.com/xiaochen301/sdm845-resukisu-kernel/actions)
[![Release](https://img.shields.io/github/v/release/xiaochen301/sdm845-resukisu-kernel?style=for-the-badge&logo=release)](https://github.com/xiaochen301/sdm845-resukisu-kernel/releases)
[![License](https://img.shields.io/badge/License-GPLv2-blue?style=for-the-badge)](LICENSE)
![Android](https://img.shields.io/badge/Android-14-green?style=for-the-badge)
![Kernel](https://img.shields.io/badge/Kernel-4.9.337-important?style=for-the-badge)

**LineageOS 21 (Android 14) + ReSukiSU v4.1 + SUSFS v2.1 内核级 root 隐藏 · 全自动构建**

</div>

---

## ✨ 特性

| 能力 | 说明 |
|------|------|
| 🧬 **ReSukiSU 内核集成** | KernelSU 生态最强非 GKI 方案，官方支持 3.4+ 老内核，手动 hook 全量打齐（官方 `manual_hook_check.mk` 编译期强制校验） |
| 🕵️ **SUSFS 完整内核级隐藏** | sus_path / sus_mount / sus_kstat / spoof_uname / hide symbols，内核级反检测（v2.1.0） |
| 🔄 **Zygisk 兼容** | 配合 ZygiskNext 支持 LSPosed / Shamiko / PIF 全套模块生态 |
| 🛠️ **全自动构建** | GitHub Actions 每周检测上游更新（ReSukiSU / 内核源），自动编译并发布 Release |
| 📦 **即刷即用** | 提供 `boot.img`（fastboot 直刷）与 AnyKernel3 zip 两种产物 |

## 📱 设备支持

| 设备 | 代号 | defconfig |
|------|------|-----------|
| Xiaomi Mi 8 Pro | **equuleus** | `vendor/xiaomi/equuleus_defconfig`（mi845 基础 + equuleus 定制） |

> 内核基座为 LineageOS 官方 SDM845 4.9 内核，可扩展其他 sdm845 设备（dipper/ursa 等），修改 defconfig 即可。

## 🎯 适用系统

- **LineageOS 21 (Android 14)** — 已验证 ✅
- 内核版本：`4.9.337-perf`

## 📥 下载

前往 [Releases](https://github.com/xiaochen301/sdm845-resukisu-kernel/releases) 页面获取最新构建：

- **`boot.img`** — fastboot 直刷：`fastboot flash boot boot.img`
- **`ReSukiSU-AnyKernel3.zip`** — TWRP/自定义 Recovery 刷入

> 首次刷入后安装 [SukiSU Ultra Manager](https://github.com/SukiSU-Ultra/SukiSU-Ultra/releases)（版本号与内核驱动精确匹配，无版本警告）。

## 🛠️ 本地构建

```bash
# 1. 准备工具链（AOSP clang + gcc 4.9）
git clone --depth=1 https://github.com/PixelExperience/prebuilts_clang_kernel_linux-x86_clang-r416183b.git clang
git clone --depth=1 https://github.com/PixelExperience/prebuilts_gcc_linux-x86_aarch64_aarch64-linux-android-4.9.git gcc-aarch64
git clone --depth=1 https://github.com/PixelExperience/prebuilts_gcc_linux-x86_arm_arm-linux-androideabi-4.9.git gcc-arm

# 2. 克隆内核源码 + ReSukiSU
git clone --depth=1 --branch lineage-21-ksu https://github.com/Coconutat/android_kernel_xiaomi_sdm845_lineageos_Exp.git kernel
git clone --depth=1 https://github.com/ReSukiSU/ReSukiSU.git

# 3. 应用补丁 + 集成 ReSukiSU
cd kernel
git apply ../patches/*.patch
ln -s $PWD/../ReSukiSU/kernel drivers/kernelsu

# 4. 编译（见 scripts/build-kernel.sh）
bash scripts/build-kernel.sh
```

## 🤖 自动构建机制

GitHub Actions 每周日 04:00 (UTC) 自动触发：

1. 检测 [ReSukiSU](https://github.com/ReSukiSU/ReSukiSU) 上游更新
2. 有更新 → 拉取最新内核源码 + ReSukiSU + 应用补丁 → 编译
3. 产物自动发布至 Releases（`boot.img` + AnyKernel3 zip）
4. 也可手动触发（Actions → Run workflow）

## 📂 项目结构

```
├── patches/               # 内核修改补丁（ReSukiSU hook + SUSFS 集成）
├── scripts/               # 构建脚本
├── .github/workflows/     # 自动构建流水线
└── README.md
```

## 📚 技术栈

- **内核基座**：[Coconutat/android_kernel_xiaomi_sdm845_lineageos_Exp](https://github.com/Coconutat/android_kernel_xiaomi_sdm845_lineageos_Exp) `lineage-21-ksu` 分支
- **Root 方案**：[ReSukiSU](https://github.com/ReSukiSU/ReSukiSU)（SukiSU Ultra 生态，非 GKI 专精）
- **隐藏方案**：SUSFS v2.1（内核级反检测）
- **管理器**：[SukiSU Ultra Manager](https://github.com/SukiSU-Ultra/SukiSU-Ultra)

## 🙏 致谢

- [ReSukiSU](https://github.com/ReSukiSU/ReSukiSU) — 内核 root 方案
- [SukiSU-Ultra](https://github.com/SukiSU-Ultra/SukiSU-Ultra) — SukiSU 生态
- [Coconutat](https://github.com/Coconutat) — LOS 内核维护与 ReSukiSU 4.9 集成先例
- [simonpunk/susfs4ksu](https://gitlab.com/simonpunk/susfs4ksu) — SUSFS 内核隐藏方案
- [LineageOS](https://github.com/LineageOS) — 内核基座

## 📄 License

[GPL-2.0](LICENSE) — 内核代码遵循 GPLv2 协议

---

<div align="center">

**Made with ❤️ for Xiaomi Mi 8 Pro (equuleus)**

</div>
