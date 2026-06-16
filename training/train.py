"""
One-time script to load DDL, glossary, and Q→SQL examples into ChromaDB.
Re-run to add new examples; existing entries are deduplicated by Vanna.

Usage:
    python training/train.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.vanna_setup import get_vanna

TRAINING_DIR = Path(__file__).parent

vn = get_vanna()

print("Loading DDL...")
vn.train(ddl=TRAINING_DIR.joinpath("ddl.sql").read_text())
print("  DDL loaded.")

print("Loading glossary...")
vn.train(documentation=TRAINING_DIR.joinpath("glossary.md").read_text())
print("  Glossary loaded.")

print("Loading Q→SQL examples...")
count = 0
for line in TRAINING_DIR.joinpath("examples.jsonl").read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    ex = json.loads(line)
    vn.train(question=ex["question"], sql=ex["sql"])
    count += 1
print(f"  {count} examples loaded.")

print("\nTraining complete. ChromaDB stored at: chroma_db/")
