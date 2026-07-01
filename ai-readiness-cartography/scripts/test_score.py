#!/usr/bin/env python3
"""score.py 회귀 테스트 — docs/ 위키 + CLAUDE.md 를 제대로 읽는지 검증.

실제 detail-page 레포에서 발견된 스코어러 사각지대를 픽스처로 재현한다:
  - C: docs/agent/ADR.md 같은 '파일형' tribal store 미검출 (docs/adr/ 디렉토리만 봄)
  - D: docs/dev/ARCHITECTURE.md 를 아키텍처 문서로 미인정 (루트/docs 직속만 봄)
  - E1: context 참조 검증의 오탐 4종
        · bash/트리 fence 안의 예시 경로를 실제 참조로 오인
        · .claude/… 처럼 앞에 점이 붙은 경로에서 점을 떨어뜨림
        · phases/index.json 의 확장자를 .js 로 절단
  - discovery: _handoff_unzip 같은 '_' 아티팩트 디렉토리를 모듈/컨텍스트로 포함

pytest 또는 `python test_score.py` 로 실행.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import score as sc  # noqa: E402


def _mk(root: Path, rel: str, body: str = "") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


# ---------------------------------------------------------------------------
# C. Tribal Knowledge — docs/agent/ADR.md (파일형 store) 를 인정해야 한다
# ---------------------------------------------------------------------------
def test_c_detects_file_based_adr_store():
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        _mk(repo, "CLAUDE.md", "# root\n")
        _mk(repo, "src/app.py", "x = 1\n")
        _mk(repo, "docs/agent/ADR.md", "# ADR-001 결정 기록\n")
        _mk(repo, "docs/agent/RULES.md", "# 불변 규칙\n")
        _mk(repo, "docs/LOG.md", "- 변경 로그\n")

        modules = sc.find_core_modules(repo)
        c = sc.score_c(modules, repo)

        assert c.evidence["adr"] is True, "docs/agent/ADR.md 를 tribal store 로 인정해야 함"
        assert c.sub_scores["C_Q5_TribalStore"] == 4, "store 존재 시 Q5 만점"


# ---------------------------------------------------------------------------
# D. Cross-Module Dependency — docs/dev/ARCHITECTURE.md 를 인정해야 한다
# ---------------------------------------------------------------------------
def test_d_detects_nested_architecture_doc():
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        _mk(repo, "CLAUDE.md", "# root\n")
        _mk(repo, "docs/dev/ARCHITECTURE.md", "# 아키텍처\n프론트→백엔드\n")

        d_cat = sc.score_d(repo, [repo / "CLAUDE.md"])

        assert d_cat.evidence["architecture_doc"] is True, "docs/dev/ARCHITECTURE.md 인정 필요"
        assert d_cat.score >= 6, "아키텍처 문서 존재 시 최소 6점"


def test_d_credits_sequence_or_flow_doc_as_visual_map():
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        _mk(repo, "CLAUDE.md", "# root\n")
        _mk(repo, "docs/dev/ARCHITECTURE.md", "# 아키텍처\n")
        _mk(repo, "docs/dev/SEQUENCE_DIAGRAM.md", "# Sequence\n사용자→App→API\n")

        d_cat = sc.score_d(repo, [repo / "CLAUDE.md"])

        # ARCHITECTURE(+6) + 시퀀스/데이터플로우 문서(+3, mermaid 등가)
        assert d_cat.score >= 9, "시퀀스/데이터플로우 문서는 시각적 의존도 표현으로 가점"


# ---------------------------------------------------------------------------
# E1. Reference accuracy — fence/점경로/확장자 오탐이 없어야 한다
# ---------------------------------------------------------------------------
def test_e1_no_false_positive_refs():
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        # 실제로 존재하는 대상들
        _mk(repo, ".claude/commands/harness.md", "# harness\n")
        _mk(repo, "phases/index.json", "{}\n")
        _mk(repo, "src/app.py", "x = 1\n")

        # 모두 '존재하는' 대상을 가리키는 까다로운 참조들 — 하나도 broken 이면 안 된다.
        claude = "\n".join([
            "# 프로젝트",
            "- Read order: `phases/index.json` 을 본다.",          # 인라인, .json 절단 오탐
            "- 자세히는 `.claude/commands/harness.md` 참고.",       # 앞 점 탈락 오탐
            "",
            "```bash",
            "docker build -t x .   # (Render, Dockerfile/render.yaml)",  # fence 안 예시
            "```",
            "",
            "```",
            "tree:",
            "  .claude/",
            "  ├── hooks/tdd-guard.sh",                             # fence 안 트리
            "```",
            "",
        ])
        _mk(repo, "CLAUDE.md", claude)

        e = sc.score_e(repo, [repo / "CLAUDE.md"])

        assert e.evidence["ref_broken"] == 0, (
            f"false positive 0건이어야 하는데 {e.evidence['ref_broken']}건 검출됨"
        )
        assert e.sub_scores["E1_RefAccuracy"] == 5, "오탐 없으면 정확도 만점"


# ---------------------------------------------------------------------------
# discovery — '_' 아티팩트 디렉토리는 모듈/컨텍스트에서 제외
# ---------------------------------------------------------------------------
def test_underscore_artifact_dirs_excluded():
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        _mk(repo, "src/app.py", "x = 1\n")
        _mk(repo, "_handoff_unzip/vendor/thing.py", "y = 2\n")
        _mk(repo, "_handoff_unzip/README.md", "# 남의 프로젝트\n참조: apps/web/x.css\n")

        modules = sc.find_core_modules(repo)
        ctx = sc.find_all_context_files(repo)

        assert all(not m.rel.startswith("_") for m in modules), \
            "'_' 아티팩트 디렉토리는 핵심 모듈이 아님"
        assert all("_handoff_unzip" not in str(p) for p in ctx), \
            "'_' 아티팩트 디렉토리의 README 는 컨텍스트로 세지 않음"


# ---------------------------------------------------------------------------
# 회귀 방지 — 진짜 hallucinated path 는 여전히 잡아야 한다
# ---------------------------------------------------------------------------
def test_e1_still_catches_real_hallucination():
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        _mk(repo, "CLAUDE.md", "설정은 `src/config/settings.py` 에 있다.\n")  # 미존재
        e = sc.score_e(repo, [repo / "CLAUDE.md"])
        assert e.evidence["ref_broken"] == 1, "존재하지 않는 인라인 경로는 broken 으로 잡아야 함"


if __name__ == "__main__":
    import traceback

    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
        except Exception:
            failed += 1
            print(f"ERROR {t.__name__}:\n{traceback.format_exc()}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
