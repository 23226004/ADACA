"""4차 검증(A1~A4, C#, _pascal, validate 타입) 회귀."""
import copy

import pytest

from autodocs.features import init, layout
from autodocs.features import profile as pm
from autodocs.features.checks import structure
from autodocs.foundation import Context, ManifestInvalid, Severity
from autodocs.platform import fs, imports, manifest_schema


def _ctx(manifest, profile, root):
    return Context(manifest=manifest, snapshot=fs.scan(root, manifest["scan"]), profile=profile)


def _w(root, rel, text=""):
    p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding="utf-8")


def _errors(out):
    return [f for f in out if f.severity == Severity.ERROR]


def _prof(manifest, **kw):
    base = {"name": "demo", "kind": "cli", "language": "python", "standard_version": manifest["standard"]["version"]}
    return pm.from_dict(manifest, {**base, **kw})


def test_root_relative_absolute_import_is_resolved(manifest, tmp_path):
    """A1: import src.demo.features / from src import ..."""
    prof = _prof(manifest, layout_preset="python-package")
    init.run(manifest, tmp_path, prof)
    _w(tmp_path, "src/demo/features/__init__.py")
    _w(tmp_path, "src/demo/foundation/a.py", "import src.demo.features\n")
    out = _errors(structure.dependency_direction(_ctx(manifest, prof, tmp_path)))
    assert len(out) == 1 and "L0 → L2" in out[0].message


def test_esm_js_extension_maps_to_ts(manifest, tmp_path):
    """A2: '../features/a.js' 가 실제로는 a.ts"""
    prof = _prof(manifest, language="typescript", layout_preset="sveltekit")
    init.run(manifest, tmp_path, prof)
    _w(tmp_path, "src/lib/features/a.ts")
    _w(tmp_path, "src/lib/foundation/u.ts", "import { a } from '../features/a.js';\n")
    out = _errors(structure.dependency_direction(_ctx(manifest, prof, tmp_path)))
    assert len(out) == 1 and "L0 → L2" in out[0].message


def test_ts_bare_specifier_is_never_a_layer(manifest, tmp_path):
    """A4: generic+TS 에서 'platform' 은 npm 패키지. src/ 접두 경로형은 해석."""
    prof = _prof(manifest, language="typescript", layout_preset="generic")
    init.run(manifest, tmp_path, prof)
    _w(tmp_path, "src/features/x.ts")
    _w(tmp_path, "src/platform/api.ts")
    _w(tmp_path, "src/foundation/a.ts", "import platform from 'platform';\nimport { x } from 'features';\nimport { y } from 'src/features/x';\n")
    out = _errors(structure.dependency_direction(_ctx(manifest, prof, tmp_path)))
    assert len(out) == 1 and "L0 → L2" in out[0].message and "src/features/x" in out[0].message


def test_tsx_and_vue_are_source(manifest, tmp_path):
    prof = _prof(manifest, language="typescript", layout_preset="generic")
    init.run(manifest, tmp_path, prof)
    _w(tmp_path, "src/features/Comp.tsx")
    _w(tmp_path, "src/foundation/a.tsx", "import Comp from '../features/Comp';\n")
    assert len(_errors(structure.dependency_direction(_ctx(manifest, prof, tmp_path)))) == 1


def test_csharp_one_line_and_inline_namespace_usings():
    scan = imports.extract(__import__("pathlib").PurePosixPath("a.cs"),
                           "using System; using CadAddon.Features;\nnamespace X { using CadAddon.Platform; }\nusing var s = File.Open(p);\n", "csharp")
    assert set(scan.refs) == {"System", "CadAddon.Features", "CadAddon.Platform"}


def test_pascal_keeps_internal_caps(manifest):
    prof = _prof(manifest, name="CadAddon", language="csharp", layout_preset="dotnet-solution")
    assert layout.layer_dirs(manifest, prof)["L2"] == "src/CadAddon.Features"
    prof2 = _prof(manifest, name="my-API", language="csharp", layout_preset="dotnet-solution")
    assert layout.layer_dirs(manifest, prof2)["L2"] == "src/MyAPI.Features"


@pytest.mark.parametrize("mutate,needle", [
    (lambda m: m["structure"]["top_level"].__setitem__("docs/", None), "top_level"),
    (lambda m: m["compliance"].__setitem__("pointer_max_lines", "30"), "pointer_max_lines"),
    (lambda m: m["structure"]["presets"]["generic"]["layer_dirs"].__setitem__("L0", 5), "layer_dirs"),
    (lambda m: m["standard"].__setitem__("version", 1.0), "version"),
    (lambda m: m["project_profile"]["schema"]["has_api"].__setitem__("default", "false"), "default"),
    (lambda m: m["docs"]["types"]["readme"].__setitem__("sections", "프로젝트 목적"), "sections"),
    (lambda m: m["compliance"]["code_detection"].__setitem__("source_dirs", "src"), "source_dirs"),
    (lambda m: m["compliance"]["states"]["new"].__setitem__("next", None), "next"),
])
def test_validate_catches_type_errors(manifest, mutate, needle):
    m = copy.deepcopy(manifest); m.pop("_dir", None); mutate(m)
    with pytest.raises(ManifestInvalid) as e:
        manifest_schema.validate(m)
    assert needle in str(e.value)
