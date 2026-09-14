"""C05 — 상향 의존 검출. Python(ast) / TS / C# 각각 한 케이스."""
from autodocs.features import init
from autodocs.features.checks import structure
from autodocs.foundation import Context
from autodocs.platform import fs


def _ctx(manifest, profile, root):
    return Context(manifest=manifest, snapshot=fs.scan(root), profile=profile)


def _w(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_downward_import_is_allowed(manifest, profile, tmp_path):
    init.run(manifest, tmp_path, profile)
    _w(tmp_path, "src/features/a.py", "from foundation import types\nimport platform.fs\n")
    assert structure.dependency_direction(_ctx(manifest, profile, tmp_path)) == []


def test_upward_python_import_is_violation(manifest, profile, tmp_path):
    init.run(manifest, tmp_path, profile)
    _w(tmp_path, "src/foundation/log.py", "from features import audit\n")
    out = structure.dependency_direction(_ctx(manifest, profile, tmp_path))
    assert len(out) == 1 and "L0 → L2" in out[0].message


def test_relative_python_import_resolves(manifest, profile, tmp_path):
    init.run(manifest, tmp_path, profile)
    _w(tmp_path, "src/platform/db.py", "from ..features import x\n")
    out = structure.dependency_direction(_ctx(manifest, profile, tmp_path))
    assert len(out) == 1 and "L1 → L2" in out[0].message


def test_ts_relative_and_lib_alias(manifest, tmp_path):
    from autodocs.features import profile as pm
    prof = pm.from_dict(manifest, {"name": "web", "kind": "web", "language": "typescript",
                                   "standard_version": manifest["standard"]["version"],
                                   "layout_preset": "sveltekit"})
    init.run(manifest, tmp_path, prof)
    _w(tmp_path, "src/lib/foundation/util.ts", "import { a } from '../features/a';\n")
    _w(tmp_path, "src/lib/platform/api.ts", "import { b } from '$lib/customization/b';\n")
    _w(tmp_path, "src/lib/features/ok.ts", "import { c } from '$lib/platform/api';\n")
    out = structure.dependency_direction(_ctx(manifest, prof, tmp_path))
    msgs = sorted(f.message for f in out)
    assert len(msgs) == 2 and "L0 → L2" in msgs[0] and "L1 → L3" in msgs[1]


def test_csharp_using(manifest, tmp_path):
    from autodocs.features import profile as pm
    prof = pm.from_dict(manifest, {"name": "cad-addon", "kind": "cad-addon", "language": "csharp",
                                   "standard_version": manifest["standard"]["version"],
                                   "layout_preset": "dotnet-solution"})
    init.run(manifest, tmp_path, prof)
    _w(tmp_path, "src/CadAddon.Foundation/Log.cs", "using CadAddon.Features;\nnamespace X {}\n")
    out = structure.dependency_direction(_ctx(manifest, prof, tmp_path))
    assert len(out) == 1 and "L0 → L2" in out[0].message
