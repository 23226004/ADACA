"""PROP-001 A: root 밖으로 쓰기/읽기 불가 — manifest·profile·CLI 어느 출처든."""
import copy

import pytest

from autodocs.features import init
from autodocs.foundation import PathEscape, norm_rel
from autodocs.platform import fs, standard


@pytest.mark.parametrize("bad", ["../x", "a/../../x", "/etc/passwd", "C:/x", "a\x00b", "..", "a/.."])
def test_norm_rel_rejects_escapes(bad):
    with pytest.raises(PathEscape):
        norm_rel(bad)


@pytest.mark.parametrize("ok,expect", [("a/b", "a/b"), ("./a//b/", "a/b"), ("a\\b", "a/b"), ("", "")])
def test_norm_rel_normalizes(ok, expect):
    assert norm_rel(ok) == expect


def test_manifest_doc_path_escape_is_rejected(manifest, profile, tmp_path):
    m = copy.deepcopy(manifest)
    m["docs"]["types"]["readme"]["path"] = "../../pwned.md"
    with pytest.raises(PathEscape):
        init.run(m, tmp_path, profile)
    assert not (tmp_path.parent / "pwned.md").exists()


def test_manifest_layer_dir_escape_is_rejected(manifest, profile, tmp_path):
    m = copy.deepcopy(manifest)
    m["structure"]["presets"]["generic"]["layer_dirs"]["L0"] = "../../pwned-dir"
    with pytest.raises(PathEscape):
        init.run(m, tmp_path, profile)


def test_manifest_pointer_file_absolute_is_rejected(manifest, profile, tmp_path):
    m = copy.deepcopy(manifest)
    m["adapters"]["claude"]["pointer_file"] = str(tmp_path.parent / "outside.md")
    with pytest.raises(PathEscape):
        init.run(m, tmp_path, profile)


def test_dangling_symlink_is_not_followed(manifest, profile, tmp_path):
    outside = tmp_path.parent / "outside-target.md"
    outside.unlink(missing_ok=True)
    (tmp_path / "CLAUDE.md").symlink_to(outside)
    with pytest.raises(PathEscape):
        init.run(manifest, tmp_path, profile)
    assert not outside.exists()


def test_symlinked_dir_component_is_rejected(manifest, tmp_path):
    outside = tmp_path.parent / "outside-dir"
    outside.mkdir(exist_ok=True)
    (tmp_path / "docs").symlink_to(outside, target_is_directory=True)
    with pytest.raises(PathEscape):
        fs.safe_path(tmp_path, "docs/x.md")


def test_template_outside_standard_dir_is_rejected(manifest, profile, tmp_path):
    m = copy.deepcopy(manifest)
    m["docs"]["types"]["readme"]["template"] = "/etc/hostname"
    with pytest.raises(PathEscape):
        init.run(m, tmp_path, profile)
    m["docs"]["types"]["readme"]["template"] = "../ref/x.md"
    with pytest.raises(PathEscape):
        standard.template_path(m, m["docs"]["types"]["readme"]["template"])


def test_project_name_cannot_traverse(manifest, tmp_path):
    from autodocs.features import profile as pm
    prof = pm.from_dict(manifest, {"name": "../../pwn", "kind": "cli", "language": "python",
                                   "standard_version": manifest["standard"]["version"],
                                   "layout_preset": "python-package"})
    res = init.run(manifest, tmp_path, prof)
    assert all(".." not in p for p in res.created)
    assert (tmp_path / "src/pwn/foundation").is_dir()      # 정제된 이름만 경로에 쓰인다


def test_snapshot_read_and_has_file_agree(manifest, profile, tmp_path):
    """22번: has_file 은 True 인데 read 는 크래시하던 불일치 — 이제 둘 다 같은 정규화를 쓴다."""
    init.run(manifest, tmp_path, profile)
    snap = fs.scan(tmp_path)
    assert snap.has_file("./README.md") and snap.read("README.md/").startswith("#")
    with pytest.raises(PathEscape):
        snap.has_file("/README.md")
    with pytest.raises(PathEscape):
        snap.read("/README.md")
