"""Only application preferences; no system setting is changed."""
import json
import os
from pathlib import Path


class Settings:
    def __init__(self, path=None):
        self.path = Path(path) if path else Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "uzeyir-doctor/preferences.json"
        self.language = "tr"
        self.reduced_motion = False
        try:
            data = json.loads(self.path.read_text())
            self.language = data.get("language") if data.get("language") in ("tr", "en") else "tr"
            self.reduced_motion = data.get("reduced_motion") is True
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"language": self.language, "reduced_motion": self.reduced_motion}, indent=2) + "\n")
        temporary.replace(self.path)
