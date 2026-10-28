name: Build ReSukiSU Kernel (Android 13 / equuleus)

on:
  workflow_dispatch:
  schedule:
    # Forks may need to enable scheduled workflows; manual Run workflow works independently.
    - cron: '0 4 * * 0'

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      KERNEL_BRANCH: lineageos-20-ksu-backup
      KERNEL_REPO: Coconutat/android_kernel_xiaomi_sdm845_lineageos_Exp
      RESUKISU_REPO: ReSukiSU/ReSukiSU
      DEVICE: equuleus

    steps:
      - name: Checkout build scripts
        uses: actions/checkout@v4

      - name: Install build dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y bc bison build-essential cpio device-tree-compiler flex git libelf-dev libssl-dev lz4 python3 zip

      - name: Download toolchain
        run: |
          git clone --depth=1 https://github.com/PixelExperience/prebuilts_clang_kernel_linux-x86_clang-r416183b.git clang
          git clone --depth=1 https://github.com/PixelExperience/prebuilts_gcc_linux-x86_aarch64_aarch64-linux-android-4.9.git gcc-aarch64
          git clone --depth=1 https://github.com/PixelExperience/prebuilts_gcc_linux-x86_arm_arm-linux-androideabi-4.9.git gcc-arm

      - name: Clone Android 13 kernel base
        run: |
          git clone --depth=1 --single-branch --branch "$KERNEL_BRANCH" "https://github.com/$KERNEL_REPO.git" kernel
          cd kernel
          grep -q '^VERSION = 4' Makefile
          grep -q '^PATCHLEVEL = 9' Makefile
          grep -q '^SUBLEVEL = 337' Makefile
          test -s arch/arm64/configs/vendor/xiaomi/equuleus.config
          echo "Kernel source commit: $(git rev-parse HEAD)"

      - name: Clone ReSukiSU
        run: git clone --depth=1 "https://github.com/$RESUKISU_REPO.git" resukisu

      - name: Prepare LOS20-compatible patch
        run: |
          python3 -m py_compile scripts/prepare-lineage20-patch.py
          python3 scripts/prepare-lineage20-patch.py \
            patches/0001-resukisu-susfs-sdm845.patch \
            "$RUNNER_TEMP/lineage20-resukisu-susfs.patch"

      - name: Apply patch and configure equuleus
        run: |
          cd kernel
          git apply --check "$RUNNER_TEMP/lineage20-resukisu-susfs.patch"
          git apply "$RUNNER_TEMP/lineage20-resukisu-susfs.patch"
          python3 - <<'PY'
          from pathlib import Path

          p = Path("drivers/input/input.c")
          s = p.read_text()
          old_decl = "extern bool ksu_input_hook __read_mostly;"
          new_decl = "extern struct static_key_true ksu_is_input_hook_enabled;"
          old_cond = "if (unlikely(ksu_input_hook))"
          new_cond = "if (static_branch_unlikely(&ksu_is_input_hook_enabled))"
          jump_include = "#include <linux/jump_label.h>"
          include_anchor = "#include <linux/input/mt.h>"

          if s.count(old_decl) != 1 or s.count(old_cond) != 1:
              raise SystemExit("ERROR: input hook source does not match expected layout")
          s = s.replace(old_decl, new_decl, 1)
          s = s.replace(old_cond, new_cond, 1)
          if jump_include not in s:
              if s.count(include_anchor) != 1:
                  raise SystemExit("ERROR: cannot locate input header include anchor")
              s = s.replace(include_anchor, include_anchor + "\n" + jump_include, 1)
          p.write_text(s)
          print("Updated input hook and jump-label include successfully")
          PY
          test ! -e drivers/kernelsu
          ln -s "$GITHUB_WORKSPACE/resukisu/kernel" drivers/kernelsu

          cat arch/arm64/configs/vendor/xiaomi/mi845_defconfig > arch/arm64/configs/vendor/xiaomi/${DEVICE}_defconfig
          cat arch/arm64/configs/vendor/xiaomi/${DEVICE}.config >> arch/arm64/configs/vendor/xiaomi/${DEVICE}_defconfig
          cat >> arch/arm64/configs/vendor/xiaomi/${DEVICE}_defconfig <<'EOF'
          # ReSukiSU + SUSFS: KSU_SUSFS is a mutually exclusive KSU hooking choice on this tree.
          CONFIG_KSU=y
          CONFIG_KSU_SUSFS=y
          EOF

      - name: Configure and verify required options
        run: |
          cd kernel
          export PATH="$GITHUB_WORKSPACE/clang/bin:$PATH"
          export CLANG_TRIPLE=aarch64-linux-gnu-
          export CROSS_COMPILE="$GITHUB_WORKSPACE/gcc-aarch64/bin/aarch64-linux-android-"
          export CROSS_COMPILE_ARM32="$GITHUB_WORKSPACE/gcc-arm/bin/arm-linux-androideabi-"
          export LLVM=1 LLVM_IAS=1
          export AR=llvm-ar NM=llvm-nm OBJCOPY=llvm-objcopy OBJDUMP=llvm-objdump STRIP=llvm-strip

          make O=out ARCH=arm64 vendor/xiaomi/${DEVICE}_defconfig CC=clang

          echo "===== KSU configuration ====="
          grep -E '^(CONFIG_KSU|CONFIG_KSU_[A-Z0-9_]+|# CONFIG_KSU_[A-Z0-9_]+ is not set)' out/.config || true

          if ! grep -qx 'CONFIG_KSU=y' out/.config; then
            echo "ERROR: CONFIG_KSU is not enabled"
            exit 1
          fi

          if ! grep -qx 'CONFIG_KSU_SUSFS=y' out/.config; then
            echo "ERROR: CONFIG_KSU_SUSFS is not enabled"
            exit 1
          fi

          echo "KSU and KSU_SUSFS configuration checks passed."

      - name: Build kernel
        run: |
          cd kernel
          export PATH="$GITHUB_WORKSPACE/clang/bin:$PATH"
          export CLANG_TRIPLE=aarch64-linux-gnu-
          export CROSS_COMPILE="$GITHUB_WORKSPACE/gcc-aarch64/bin/aarch64-linux-android-"
          export CROSS_COMPILE_ARM32="$GITHUB_WORKSPACE/gcc-arm/bin/arm-linux-androideabi-"
          export LLVM=1 LLVM_IAS=1
          export AR=llvm-ar NM=llvm-nm OBJCOPY=llvm-objcopy OBJDUMP=llvm-objdump STRIP=llvm-strip
          make -j"$(nproc)" O=out ARCH=arm64 CC=clang
          test -s out/arch/arm64/boot/Image.gz-dtb
          ls -lh out/arch/arm64/boot/Image.gz-dtb

      - name: Package equuleus AnyKernel3 ZIP
        run: |
          git clone --depth=1 https://github.com/osm0sis/AnyKernel3.git anykernel3
          rm -rf anykernel3/.git
          cp kernel/out/arch/arm64/boot/Image.gz-dtb anykernel3/Image.gz-dtb
          grep -q '^device.name1=' anykernel3/anykernel.sh
          sed -i 's/^device.name1=.*/device.name1=equuleus/' anykernel3/anykernel.sh
          sed -i 's/^supported.versions=.*/supported.versions=13/' anykernel3/anykernel.sh
          (cd anykernel3 && zip -qr9 "$GITHUB_WORKSPACE/ReSukiSU-equuleus-AnyKernel3.zip" . -x '*.git*')
          unzip -t ReSukiSU-equuleus-AnyKernel3.zip
          sha256sum ReSukiSU-equuleus-AnyKernel3.zip

      - name: Upload ZIP artifact
        uses: actions/upload-artifact@v4
        with:
          name: ReSukiSU-equuleus-Android13-AnyKernel3
          path: ReSukiSU-equuleus-AnyKernel3.zip
          if-no-files-found: error
          retention-days: 14
