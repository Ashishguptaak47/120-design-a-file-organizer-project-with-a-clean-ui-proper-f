from __future__ import annotations
import argparse
import sys
from pathlib import Path
from core.organizer import FileOrganizer
from ui.app import NeatFilesApp

def run_cli(args: argparse.Namespace) -> None:
    organizer = FileOrganizer()

    if args.undo:
        manifest_path = Path(args.undo)
        print(f"Rolling back operations from {manifest_path}...")
        try:
            restored = organizer.rollback(manifest_path)
            print(f"Success: Restored {restored} files.")
        except Exception as e:
            print(f"Rollback Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    source = Path(args.source) if args.source else Path.cwd()
    target = Path(args.target) if args.target else None

    print(f"Scanning '{source}' using mode '{args.mode}'...")
    plan = organizer.build_plan(source_dir=source, target_dir=target, mode=args.mode, recursive=args.recursive)
    print(f"Identified {len(plan)} files to organize.")

    if args.dry_run:
        print("\n--- DRY RUN PREVIEW ---")
        for item in plan[:25]:
            print(f"[{item.category}] {item.src.name} -> {item.dest}")
        if len(plan) > 25:
            print(f"... and {len(plan) - 25} more items.")
        return

    if not plan:
        print("No files found to organize.")
        return

    def console_cb(idx: int, total: int, filename: str):
        if idx % 10 == 0 or idx == total:
            print(f"Progress: [{idx}/{total}] Processing {filename}")

    count, manifest = organizer.execute_plan(
        plan,
        copy_mode=args.copy,
        conflict_strategy=args.conflict,
        progress_cb=console_cb
    )
    print(f"Successfully organized {count} files.")
    print(f"Transaction manifest logged to: {manifest}")

def main():
    parser = argparse.ArgumentParser(description="NeatFiles - Clean & Safe File Organizer")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode without GUI")
    parser.add_argument("--source", "-s", type=str, help="Source folder path")
    parser.add_argument("--target", "-t", type=str, help="Target folder path (defaults to source)")
    parser.add_argument("--mode", "-m", choices=["category", "date", "extension"], default="category", help="Organization mode")
    parser.add_argument("--conflict", "-c", choices=["rename", "skip", "overwrite"], default="rename", help="File collision strategy")
    parser.add_argument("--copy", action="store_true", help="Copy files instead of moving them")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recursively process subdirectories")
    parser.add_argument("--dry-run", action="store_true", help="Simulate organization without moving files")
    parser.add_argument("--undo", type=str, help="Path to transaction log to rollback")

    # If arguments are provided other than just program name and not empty, inspect CLI intent
    if len(sys.argv) > 1:
        args = parser.parse_args()
        run_cli(args)
    else:
        app = NeatFilesApp()
        app.mainloop()

if __name__ == "__main__":
    main()
