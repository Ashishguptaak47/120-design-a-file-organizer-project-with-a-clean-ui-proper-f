# NeatFiles - Intelligent File Organizer

A modern, resilient desktop file organizer featuring categorized grouping, date-based sorting, collision safety, duplicate identification, and atomic transaction rollback.

## Features
- **Clean UI & CLI Modes**: Modern responsive Tkinter interface with real-time dry-run preview, alongside a scriptable command-line interface.
- **Multiple Organizing Modes**:
  - Category-based (Documents, Images, Audio, Video, Archives, Code, etc.)
  - Date-based (`YYYY/MM` creation/modification grouping)
  - Extension-based (explicit grouping per extension)
- **Conflict Resolution**:
  - `rename`: Appends an incremental index (`file (1).ext`)
  - `skip`: Preserves existing files and logs skipped items
  - `overwrite`: Replaces destination files
- **Safe Operations & Rollback**: Records every operation to a JSON transaction manifest, allowing single-click rollbacks of entire organization batches.
- **Duplicate Detection**: Identifies exact duplicate files via SHA-256 chunked hashing without moving them unnecessarily.

## Installation

Ensure Python 3.9+ is installed. No third-party GUI dependencies are required (uses standard library `tkinter`).

```bash
python -m pip install -r requirements.txt
```

## Usage

### Graphical User Interface (Default)
```bash
python main.py
```

### Command-Line Interface
```bash
# Preview organization plan (dry run)
python main.py --cli --source ./Downloads --mode category --dry-run

# Execute organization using date-based folders
python main.py --cli --source ./Downloads --target ./Organized --mode date

# Roll back previous transaction
python main.py --cli --undo logs/transaction_TIMESTAMP.json
```

## Running Tests
```bash
pytest tests/
# or
python -m unittest discover -s tests
```
