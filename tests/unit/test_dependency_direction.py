"""C05 — 의존성 방향. 해석된 경로가 실제로 존재할 때만 계층으로 인정한다 (D-02)."""
import copy

from autodocs.features import init
from autodocs.features import profile as pm
from autodocs.features.checks import structure
from autodocs.foundation import Context, Severity
from autodocs.platform import fs


def _ctx(manifest, profile, root):
    return Context(manifest=manifest, snapshot=fs.scan(root, manifest["scan"]), profile=profile)


def _w(root, rel, text=""):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _py(manifest, tmp_path, preset="python-package"):
    prof = pm.from_dict(manifest, {"name": "demo", "kind": "cli", "language": "python",
                                   "standard_version": manifest["standard"]["version"], "layout_preset": preset})
    init.run(manifest, tmp_path, prof)
    return prof


def _errors(findings):
    return [f for f in findings if f.severity == Severity.ERROR]


# --- Python (python-package preset: src/demo/<layer>) -------------------------
def test_downward_import_is_allowed(manifest, tmp_path):
    prof = _py(manifest, tmp_path)
    _w(tmp_path, "src/demo/foundation/types.py")
    _w(tmp_path, "src/demo/platform/fs.py")
    _w(tmp_path, "src/demo/features/a.py", "from demo.foundation import types\nimport demo.platform.fs\nfrom ..platform import fs\n")
    assert _errors(structure.dependency_direction(_ctx(manifest, prof, tmp_path))) == []


def test_upward_python_import_is_violation_once_per_layer(manifest, tmp_path):
    prof = _py(manifest, tmp_path)
    _w(tmp_path, "src/demo/features/audit.py")
    _w(tmp_path, "src/demo/foundation/log.py", "from demo.features import audit\nimport demo.features.audit\n")
    out = _errors(structure.dependency_direction(_ctx(manifest, prof, tmp_path)))
    assert len(out) == 1 and "L0 → L2" in out[0].message


def test_relative_from_import_names_are_resolved(manifest, tmp_path):
    """#8: `from .. import features` 의 names 도 해석한다."""
    prof = _py(manifest, tmp_path)
    _w(tmp_path, "src/demo/features/__init__.py")
    _w(tmp_path, "src/demo/platform/db.py", "from .. import features\n")
    out = _errors(structure.dependency_direction(_ctx(manifest, prof, tmp_path)))
    assert len(out) == 1 and "L1 → L2" in out[0].message


def test_stdlib_name_is_not_a_layer(manifest, tmp_path):
    """#7: `import platform` 은 src/demo/platform 이 아니라 stdlib. python-package 에서는 충돌하지 않는다."""
    prof = _py(manifest, tmp_path)
    _w(tmp_path, "src/demo/foundation/a.py", "import platform\nimport features\nfrom features import x\n")
    assert _errors(structure.dependency_direction(_ctx(manifest, prof, tmp_path))) == []


def test_nonexistent_target_is_ignored(manifest, tmp_path):
    prof = _py(manifest, tmp_path)
    _w(tmp_path, "src/demo/foundation/a.py", "from demo.features.ghost import x\n")   # features/ghost 없음 → 무시가 아니라...
    # 존재 확인은 접두사로 내려가며 한다: demo.features.ghost → demo/features (존재) → L2 로 인정
    out = _errors(structure.dependency_direction(_ctx(manifest, prof, tmp_path)))
    assert len(out) == 1
    _w(tmp_path, "src/demo/foundation/b.py", "from nowhere.features import x\n")     # import_root 아래에 없음 → 외부 패키지
    out = _errors(structure.dependency_direction(_ctx(manifest, prof, tmp_path)))
    assert len(out) == 1


def test_generic_preset_with_python_warns(manifest, tmp_path):
    prof = _py(manifest, tmp_path, preset="generic")
    out = structure.layer_dirs_present(_ctx(manifest, prof, tmp_path))
    assert any(f.severity == Severity.WARNING and "권장하지 않음" in f.message for f in out)


def test_allowed_edges_come_from_manifest(manifest, tmp_path):
    m = copy.deepcopy(manifest)
    m["structure"]["dependency_rules"]["allowed"] = [{"from": "L0", "to": ["L2"]}, {"from": "L2", "to": []}]
    prof = _py(m, tmp_path)
    _w(tmp_path, "src/demo/features/x.py")
    _w(tmp_path, "src/demo/foundation/a.py", "from demo.features import x\n")   # 이제 허용
    _w(tmp_path, "src/demo/features/b.py", "from demo.foundation import a\n")   # 이제 금지
    out = _errors(structure.dependency_direction(_ctx(m, prof, tmp_path)))
    assert len(out) == 1 and "L2 → L0" in out[0].message


# --- 파싱 실패·미지원 언어는 INFO -------------------------------------------------
def test_syntax_error_and_unsupported_language_are_info(manifest, tmp_path):
    prof = _py(manifest, tmp_path)
    _w(tmp_path, "src/demo/foundation/bad.py", "def (:\n")
    _w(tmp_path, "src/demo/foundation/x.java", "import demo.features.X;\n")
    _w(tmp_path, "src/demo/foundation/nul.py", "import os\x00\n")
    out = structure.dependency_direction(_ctx(manifest, prof, tmp_path))
    infos = [f for f in out if f.severity == Severity.INFO]
    assert len(infos) == 3 and not _errors(out)


# --- TypeScript / SvelteKit ------------------------------------------------------
def test_ts_relative_alias_side_effect_and_comments(manifest, tmp_path):
    prof = pm.from_dict(manifest, {"name": "web", "kind": "web", "language": "typescript",
                                   "standard_version": manifest["standard"]["version"], "layout_preset": "sveltekit"})
    init.run(manifest, tmp_path, prof)
    _w(tmp_path, "src/lib/features/a.ts")
    _w(tmp_path, "src/lib/customization/b.ts")
    _w(tmp_path, "src/lib/platform/api.ts")
    _w(tmp_path, "src/lib/foundation/util.ts", "import { a } from '../features/a';\n")          # 상대: L0→L2
    _w(tmp_path, "src/lib/platform/svc.ts", "import '$lib/customization/b';\n")                # side-effect + alias: L1→L3
    _w(tmp_path, "src/lib/features/ok.ts", "import { c } from '$lib/platform/api';\n"           # 하향: OK
                                           "// import x from '../customization/b';\n"           # 주석: 무시
                                           "/* import y from '$lib/customization/b' */\n"
                                           "import { p } from 'platform';\n")                    # npm 패키지: 무시
    _w(tmp_path, "src/routes/+page.ts", "import { z } from '$lib/features/a';\n")             # 진입점은 계층 밖: 무시
    out = _errors(structure.dependency_direction(_ctx(manifest, prof, tmp_path)))
    msgs = sorted(f.message for f in out)
    assert len(msgs) == 2 and "L0 → L2" in msgs[0] and "L1 → L3" in msgs[1]


# --- C# -----------------------------------------------------------------------------
def test_csharp_using_forms(manifest, tmp_path):
    prof = pm.from_dict(manifest, {"name": "cad-addon", "kind": "cad-addon", "language": "csharp",
                                   "standard_version": manifest["standard"]["version"], "layout_preset": "dotnet-solution"})
    init.run(manifest, tmp_path, prof)
    _w(tmp_path, "src/CadAddon.Features/Foo.cs")
    _w(tmp_path, "src/CadAddon.Foundation/Log.cs",
       "global using CadAddon.Features;\nusing Feat = CadAddon.Features.Foo;\n// using CadAddon.Features.Bar;\nnamespace X {}\n")
    _w(tmp_path, "src/CadAddon.Platform/Db.cs", "using System.IO;\nusing CadAddon.Foundation;\n")   # 하향 + 외부: OK
    out = _errors(structure.dependency_direction(_ctx(manifest, prof, tmp_path)))
    assert len(out) == 1 and "L0 → L2" in out[0].message and "Log.cs" in out[0].path
