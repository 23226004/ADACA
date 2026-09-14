"""manifest 와 코드가 어긋나지 않는지 — 선언된 check 는 모두 구현되어야 하고, 템플릿은 모두 존재해야 한다."""
from pathlib import Path

from autodocs.features.checks import REGISTRY


def test_every_manifest_check_is_implemented(manifest):
    declared = {c["name"] for c in manifest["compliance"]["checks"]}
    assert declared <= set(REGISTRY), declared - set(REGISTRY)


def test_every_doc_template_exists(manifest):
    base = Path(manifest["_dir"])
    missing = [s["template"] for s in manifest["docs"]["types"].values() if not (base / s["template"]).is_file()]
    assert not missing, missing


def test_layer_ids_match_presets(manifest):
    ids = {l["id"] for l in manifest["structure"]["layers"]}
    for name, preset in manifest["structure"]["presets"].items():
        assert set(preset["layer_dirs"]) == ids, name
