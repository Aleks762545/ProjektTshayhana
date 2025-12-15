import yaml, os
from pathlib import Path

_cfg_path = Path(__file__).resolve().parents[1] / 'config.yaml'
if not _cfg_path.exists():
    _cfg_path = Path('config.yaml')

with open(_cfg_path, 'r', encoding='utf-8') as f:
    settings = yaml.safe_load(f)
# ensure paths exist
os.makedirs(os.path.dirname(settings['database']['sqlite_path']), exist_ok=True)
os.makedirs(settings['vector']['persist_dir'], exist_ok=True)
