#!/usr/bin/env python3
"""
Restructure a SnapEDA/Ultra Librarian KiCad download into clean format.

Usage: python restructure_kicad_part.py <folder>

Nested (pass wrapper dir):
  LIB_PARTNAME/
    PARTNAME/
      KiCad/  <- kicad files
      3D/     <- 3d models
      Altium/ Allegro/ ... (discarded)
  -> new sibling PARTNAME/ created, LIB_PARTNAME/ deleted

Flat (pass part dir directly):
  PARTNAME/
    KiCad/  <- kicad files
    3D/     <- 3d models
    Altium/ Allegro/ ... (discarded)
  -> restructured in-place

After (both cases):
  PARTNAME/
    *.kicad_sym *.lib *.mod *.dcm *.kicad_mod
    3D/
"""

import sys
import shutil
from pathlib import Path

KICAD_EXTS = {'.kicad_sym', '.lib', '.mod', '.dcm', '.kicad_mod'}


def restructure(lib_path: Path) -> None:
    lib_path = lib_path.resolve()

    if not lib_path.is_dir():
        print(f"Error: '{lib_path}' is not a directory")
        sys.exit(1)

    flat = (lib_path / "KiCad").is_dir()

    if flat:
        part_name = lib_path.name
        part_dir = lib_path
        kicad_dir = lib_path / "KiCad"
    else:
        subdirs = [p for p in lib_path.iterdir() if p.is_dir()]
        if not subdirs:
            print(f"Error: no subdirectory found in '{lib_path}'")
            sys.exit(1)
        part_dir = subdirs[0]
        part_name = part_dir.name
        kicad_dir = part_dir / "KiCad"
        if not kicad_dir.is_dir():
            print(f"Error: no KiCad/ folder found in '{part_dir}'")
            sys.exit(1)

    if flat:
        print(f"Part:   {part_name}")
        print(f"Mode:   flat (in-place)")
        print(f"Dir:    {lib_path}")
    else:
        output_dir = lib_path.parent / part_name
        if output_dir.exists():
            print(f"Error: '{output_dir}' already exists — move or delete it first")
            sys.exit(1)
        print(f"Part:   {part_name}")
        print(f"From:   {lib_path}")
        print(f"To:     {output_dir}")
        print(f"Delete: {lib_path}")

    answer = input("Proceed? [y/N] ").strip().lower()
    if answer != "y":
        print("Aborted.")
        sys.exit(0)

    if flat:
        for f in kicad_dir.iterdir():
            if f.is_file():
                shutil.move(str(f), str(lib_path / f.name))
        kicad_dir.rmdir()
        for item in list(lib_path.iterdir()):
            if item.is_dir() and item.name != "3D":
                shutil.rmtree(str(item))
            elif item.is_file() and item.suffix not in KICAD_EXTS:
                item.unlink()
    else:
        three_d_dir = part_dir / "3D"
        output_dir = lib_path.parent / part_name
        output_dir.mkdir()
        for f in kicad_dir.iterdir():
            if f.is_file():
                shutil.move(str(f), str(output_dir / f.name))
        if three_d_dir.is_dir():
            shutil.move(str(three_d_dir), str(output_dir / "3D"))
        shutil.rmtree(str(lib_path))

    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python restructure_kicad_part.py <folder>")
        sys.exit(1)

    restructure(Path(sys.argv[1]))
