"""5단계: 잘못된 manifest 는 로드 시점에 ManifestInvalid 하나로 보고된다 (KeyError/ValueError 크래시 없음)."""
import copy

import pytest

from autodocs.foundation import ManifestInvalid
from autodocs.platform import manifest_schema


def _bad(manifest, mutate):
    m = copy.deepcopy(manifest); m.pop("_dir", None)
    mutate(m)
    with pytest.raises(ManifestInvalid) as e:
        manifest_schema.validate(m)
    return str(e.value)


def test_shipped_manifest_is_valid(manifest):
    m = copy.deepcopy(manifest); m.pop("_dir", None)
    manifest_schema.validate(m)


def test_bad_severity(manifest):
    msg = _bad(manifest, lambda m: m["compliance"]["checks"][0].__setitem__("severity", "fatal"))
    assert "severity" in msg


def test_missing_layers(manifest):
    msg = _bad(manifest, lambda m: m["structure"].pop("layers"))
    assert "layers" in msg


def test_preset_layer_mismatch(manifest):
    msg = _bad(manifest, lambda m: m["structure"]["presets"]["generic"]["layer_dirs"].pop("L3"))
    assert "layer_dirs" in msg


def test_dependency_rule_unknown_layer(manifest):
    msg = _bad(manifest, lambda m: m["structure"]["dependency_rules"]["allowed"].append({"from": "L9", "to": []}))
    assert "L9" in msg


def test_applies_to_unknown_doc(manifest):
    def mut(m):
        chk = next(c for c in m["compliance"]["checks"] if c["id"] == "C07"); chk["applies_to"] = ["ghost"]
    assert "ghost" in _bad(manifest, mut)


def test_conditional_without_when(manifest):
    assert "when" in _bad(manifest, lambda m: m["docs"]["types"]["api"].pop("when"))


def test_duplicate_check_id(manifest):
    assert "중복" in _bad(manifest, lambda m: m["compliance"]["checks"].append(dict(m["compliance"]["checks"][0])))


def test_many_errors_reported_together(manifest):
    def mut(m):
        m["structure"].pop("layers"); m["compliance"].pop("states"); m["scan"]["skip_dirs"] = "x"
    msg = _bad(manifest, mut)
    assert msg.count("\n  - ") >= 3
