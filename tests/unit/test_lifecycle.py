"""new → init → compliant, legacy → adopt → plan 생성. 엔진의 핵심 시나리오."""
from autodocs.features import adopt, audit, init
from autodocs.foundation import State


def test_empty_dir_is_new(manifest, tmp_path):
    assert audit.run(manifest, tmp_path).state == State.NEW


def test_init_makes_compliant(manifest, profile, tmp_path):
    res = init.run(manifest, tmp_path, profile)
    assert "docs/api/openapi.yaml" in res.created          # has_api=True → 조건부 문서 생성
    assert "docs/database/database.md" not in res.created  # has_database=False → 생성 안 함
    rep = audit.run(manifest, tmp_path)
    assert rep.state == State.COMPLIANT, rep.findings


def test_init_never_overwrites(manifest, profile, tmp_path):
    (tmp_path / "README.md").write_text("mine", encoding="utf-8")
    res = init.run(manifest, tmp_path, profile)
    assert "README.md" in res.skipped
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == "mine"


def test_code_without_marker_is_legacy(manifest, tmp_path):
    (tmp_path / "app.py").write_text("print('hi')", encoding="utf-8")
    assert audit.run(manifest, tmp_path).state == State.LEGACY


def test_adopt_writes_plan_listing_unclassified(manifest, profile, tmp_path):
    (tmp_path / "app.py").write_text("print('hi')", encoding="utf-8")
    (tmp_path / "util").mkdir()
    (tmp_path / "util" / "x.py").write_text("", encoding="utf-8")
    res, plan_rel = adopt.run(manifest, tmp_path, profile)
    plan = (tmp_path / plan_rel).read_text(encoding="utf-8")
    assert "`app.py`" in plan and "`util/x.py`" in plan
    assert audit.run(manifest, tmp_path).state == State.COMPLIANT  # 구조·문서는 이미 충족


def test_missing_required_doc_is_partial(manifest, profile, tmp_path):
    init.run(manifest, tmp_path, profile)
    (tmp_path / "docs/requirements/requirements.md").unlink()
    rep = audit.run(manifest, tmp_path)
    assert rep.state == State.PARTIAL
    assert any(f.check_id == "C01" and "requirements" in f.message for f in rep.findings)
