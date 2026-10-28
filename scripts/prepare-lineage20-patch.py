#!/usr/bin/env python3
"""Adapt the existing ReSukiSU+SUSFS patch to the SDM845 LOS20 KSU backup branch.

This is a narrow compatibility transformation for:
  Coconutat/android_kernel_xiaomi_sdm845_lineageos_Exp:lineageos-20-ksu-backup
It deliberately does not rewrite SUSFS implementation code. It removes KSU registration
hunks already present in that branch, omits the SELinux hunk whose KSU exception is
already present there, and drops two VFS umount refactor hunks that do not exist in
that older source layout. Hunk counts are recalculated after context adaptation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

OMIT_FILES = {
    # The workflow builds this file from mi845_defconfig + equuleus.config itself.
    "arch/arm64/configs/vendor/xiaomi/equuleus_defconfig",
    # The workflow adapts the old input-hook references after applying the patch;
    # omit the upstream input.c diff to avoid context mismatch on this older tree.
    "drivers/input/input.c",
    # These KSU registration lines already exist on lineageos-20-ksu-backup.
    "drivers/Kconfig",
    "drivers/Makefile",
    # This branch already carries the equivalent KSU SELinux bypass code and CONFIG_KSU=y.
    "security/selinux/hooks.c",
}
GUARD_ADAPT_FILES = {
    "drivers/input/input.c",
    "fs/exec.c",
    "fs/read_write.c",
}
SKIP_NAMESPACE_HUNKS = (
    "static inline bool may_mandlock",
    "static int can_umount",
)
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)$")


def file_path(section: str) -> str | None:
    match = re.search(r"(?m)^diff --git a/(.+?) b/(.+?)\s*$", section)
    return match.group(2) if match else None


def adapt_section(section: str) -> str | None:
    path = file_path(section)
    if path is None:
        return section
    if path in OMIT_FILES:
        return None

    lines = section.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith("@@ "):
            out.append(line)
            i += 1
            continue

        header = line
        i += 1
        body: list[str] = []
        while i < len(lines) and not lines[i].startswith("@@ ") and not lines[i].startswith("diff --git "):
            body.append(lines[i])
            i += 1

        if path == "fs/namespace.c" and (
            any(marker in header for marker in SKIP_NAMESPACE_HUNKS)
            or any(any(marker in item for marker in SKIP_NAMESPACE_HUNKS) for item in body)
        ):
            continue

        if path in GUARD_ADAPT_FILES:
            # The LOS20 KSU backup branch has these old KernelSU hook declarations
            # unguarded. Remove only old-side/context #ifdef/#endif lines; additions
            # prefixed with '+' remain intact, including the new sys_read hook guard.
            body = [
                item for item in body
                if not (
                    item[:1] in (" ", "-")
                    and item[1:].strip() in ("#ifdef CONFIG_KSU", "#endif")
                )
            ]

        counts_old = sum(1 for item in body if item.startswith((" ", "-")))
        counts_new = sum(1 for item in body if item.startswith((" ", "+")))
        match = HUNK_RE.match(header)
        if not match:
            raise ValueError(f"Unsupported unified-diff hunk header: {header}")
        old_start, new_start, tail = match.groups()
        out.append(f"@@ -{old_start},{counts_old} +{new_start},{counts_new} @@{tail}")
        out.extend(body)

    return "\n".join(out) + "\n"


def main() -> int:
    if len(sys.argv) != 3:
        print(f"Usage: {Path(sys.argv[0]).name} INPUT.patch OUTPUT.patch", file=sys.stderr)
        return 2

    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    raw = source.read_text(encoding="utf-8")
    sections = re.split(r"(?m)(?=^diff --git a/)", raw)
    result: list[str] = []
    removed_files: list[str] = []
    skipped_hunks = 0
    adjusted_sections = 0

    for section in sections:
        if not section.strip():
            continue
        path = file_path(section)
        if path in OMIT_FILES:
            removed_files.append(path or "(unknown)")
            continue
        # Count and report skipped namespace refactor hunks for review.
        if path == "fs/namespace.c":
            before = sum(1 for line in section.splitlines() if line.startswith("@@ "))
            after_section = adapt_section(section) or ""
            after = sum(1 for line in after_section.splitlines() if line.startswith("@@ "))
            skipped_hunks += before - after
            result.append(after_section)
            continue
        adapted = adapt_section(section)
        if adapted is not None:
            if path in GUARD_ADAPT_FILES:
                adjusted_sections += 1
            result.append(adapted)

    prepared = "".join(result)
    # Ensure the adapted file is still a non-empty Git unified diff.
    if not prepared.startswith("diff --git ") or "diff --git a/fs/susfs.c b/fs/susfs.c" not in prepared:
        raise RuntimeError("Prepared patch failed structural sanity checks")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(prepared, encoding="utf-8")
    print(f"Prepared patch: {destination} ({len(prepared)} bytes)")
    print("Removed redundant/base-specific sections: " + ", ".join(removed_files))
    print(f"Adapted hook sections: {adjusted_sections}; skipped incompatible umount refactor hunks: {skipped_hunks}")
    print("Next step must run git apply --check before applying the patch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
