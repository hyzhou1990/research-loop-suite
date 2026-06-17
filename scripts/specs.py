import json
from pathlib import Path

import jsonschema
import yaml

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "shared" / "watch_spec.schema.json"


def _schema():
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_spec(spec):
    """Validate a watch-spec dict; raise ValueError with a clear message if invalid."""
    try:
        jsonschema.validate(spec, _schema())
    except jsonschema.ValidationError as e:
        loc = "/".join(str(p) for p in e.absolute_path) or "<root>"
        raise ValueError(f"invalid watch-spec at {loc}: {e.message}") from e
    return spec


def load_spec(path):
    """Load + validate a watch-spec YAML file. Raises ValueError on parse/shape/schema errors."""
    path = Path(path)
    try:
        spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ValueError(f"could not parse watch-spec YAML {path}: {e}") from e
    if not isinstance(spec, dict):
        raise ValueError(f"watch-spec {path} must be a YAML mapping")
    return validate_spec(spec)
