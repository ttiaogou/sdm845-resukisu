#!/bin/bash
# ============================================================
# ReSukiSU + SUSFS 内核构建脚本（equuleus / SDM845 / LOS21）
#
# 前置条件（仓库根目录下）：
#   kernel/     - LineageOS SDM845 内核源码（lineage-21-ksu 分支）
#   resukisu/   - ReSukiSU 源码
#   clang/      - AOSP clang 工具链（clang-r416183b）
#   gcc-aarch64/ - aarch64 gcc 4.9 交叉编译器
#   gcc-arm/    - arm gcc 4.9 交叉编译器
#
# 用法：bash scripts/build-kernel.sh
# ============================================================
set -e

# 仓库根目录（脚本所在位置的上一级）
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DEVICE=${DEVICE:-equuleus}

# ============ [1/4] defconfig 准备 ============
echo "=== [1/4] defconfig 准备 ==="
cd "$ROOT/kernel"
# 若 equuleus_defconfig 不存在则从 mi845 合成
if [ ! -f arch/arm64/configs/vendor/xiaomi/equuleus_defconfig ]; then
  echo "合成 equuleus_defconfig..."
  cat arch/arm64/configs/vendor/xiaomi/mi845_defconfig > arch/arm64/configs/vendor/xiaomi/equuleus_defconfig
  cat arch/arm64/configs/vendor/xiaomi/equuleus.config >> arch/arm64/configs/vendor/xiaomi/equuleus_defconfig
fi

# 追加 ReSukiSU 配置（带 susfs，全手动 hook）
cat >> arch/arm64/configs/vendor/xiaomi/equuleus_defconfig << 'EOF'
# ReSukiSU + SUSFS
CONFIG_KSU=y
CONFIG_KSU_MANUAL_HOOK=y
# CONFIG_KSU_MANUAL_HOOK_AUTO_SETUID_HOOK is not set
# CONFIG_KSU_MANUAL_HOOK_AUTO_INITRC_HOOK is not set
# CONFIG_KSU_MANUAL_HOOK_AUTO_INPUT_HOOK is not set
CONFIG_KSU_SUSFS=y
CONFIG_SUSFS=y
EOF
echo "KSU 配置已追加"

# ============ [2/4] make defconfig ============
echo "=== [2/4] make defconfig ==="
export PATH="$ROOT/clang/bin:$PATH"
export CLANG="$ROOT/clang/bin/clang"
export GCC_A64="$ROOT/gcc-aarch64/bin/aarch64-linux-android-"
export GCC_ARM="$ROOT/gcc-arm/bin/arm-linux-androideabi-"
export LLVM=1 LLVM_IAS=1
export AR=llvm-ar NM=llvm-nm OBJCOPY=llvm-objcopy OBJDUMP=llvm-objdump STRIP=llvm-strip

make O=out ARCH=arm64 CC=clang CLANG_TRIPLE=aarch64-linux-gnu- \
  CROSS_COMPILE="$GCC_A64" CROSS_COMPILE_ARM32="$GCC_ARM" \
  vendor/xiaomi/equuleus_defconfig

grep -E "CONFIG_KSU|CONFIG_SUSFS" out/.config | head -10

# ============ [3/4] 编译内核 ============
echo "=== [3/4] 编译内核 ==="
make -j"$(nproc)" O=out ARCH=arm64 CC=clang CLANG_TRIPLE=aarch64-linux-gnu- \
  CROSS_COMPILE="$GCC_A64" CROSS_COMPILE_ARM32="$GCC_ARM"

# ============ [4/4] 产物 ============
echo "=== [4/4] 产物 ==="
ls -lh out/arch/arm64/boot/Image.gz-dtb
echo "BUILD_DONE"
