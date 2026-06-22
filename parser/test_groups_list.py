import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from parser.group_finder import find_group_id

print(
    find_group_id("ИСИб-22-1")
)