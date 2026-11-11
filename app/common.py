import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'configs/commands.json').read_text(encoding='utf-8'))
COMMANDS = CONFIG['commands']
LABELS = list(COMMANDS) + CONFIG['non_action_labels']
RATE = CONFIG['audio']['sample_rate_hz']
