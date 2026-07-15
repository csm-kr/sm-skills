#!/usr/bin/env python3
"""Render a self-contained HTML report from scored influencer JSON."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


STATUS_ORDER = {"PASS": 0, "NEAR MATCH": 1, "FAIL": 2, "UNVERIFIED": 3}
STATUS_LABELS = {
    "PASS": "PASS",
    "NEAR MATCH": "NEAR MATCH",
    "FAIL": "FAIL",
    "UNVERIFIED": "UNVERIFIED",
}


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def youtube_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlparse(value.strip())
    host = (parsed.hostname or "").lower()
    if parsed.scheme == "https" and (
        host == "youtube.com"
        or host.endswith(".youtube.com")
        or host == "youtu.be"
        or host.endswith(".youtu.be")
    ):
        return value.strip()
    return None


def link(label: Any, url: Any) -> str:
    safe_url = youtube_url(url)
    if not safe_url:
        return esc(label)
    return (
        f'<a href="{esc(safe_url)}" target="_blank" rel="noopener noreferrer">'
        f"{esc(label)}</a>"
    )


def number(value: Any, digits: int = 0) -> str:
    if value is None:
        return "확인 불가"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return esc(value)
    if digits == 0:
        return f"{numeric:,.0f}"
    return f"{numeric:,.{digits}f}"


def subscriber_display(candidate: dict[str, Any]) -> str:
    displayed = candidate.get("subscriber_count_displayed")
    if displayed is not None and str(displayed).strip():
        return esc(displayed)
    return number(candidate.get("subscriber_count"))


def text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item).strip()]


def candidate_sort_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    status = candidate.get("status", "UNVERIFIED")
    priority = candidate.get("priority_rank")
    if isinstance(priority, (int, float)):
        priority_key = float(priority)
    else:
        priority_key = 9999.0
    weighted = candidate.get("weighted_recommendation_score")
    weighted_key = -float(weighted) if isinstance(weighted, (int, float)) else 0.0
    comments = candidate.get("comment_total")
    comments_key = -float(comments) if isinstance(comments, (int, float)) else 0.0
    return (STATUS_ORDER.get(str(status), 9), priority_key, weighted_key, comments_key)


def failure_text(candidate: dict[str, Any]) -> str:
    parts: list[str] = []
    for failure in candidate.get("failure_reasons", []):
        if not isinstance(failure, dict):
            continue
        gate = failure.get("gate", "필수 조건")
        actual = failure.get("actual")
        required = failure.get("required")
        if actual is not None and required is not None:
            parts.append(f"{gate}: 실제 {number(actual)} / 기준 {number(required)}")
        else:
            parts.append(str(failure.get("message") or gate))
    for issue in candidate.get("verification_issues", []):
        parts.append(f"검증 문제: {issue}")
    return " · ".join(parts) or "기록된 탈락 사유 없음"


def video_rows(candidate: dict[str, Any]) -> str:
    rows: list[str] = []
    videos = candidate.get("selected_videos") or candidate.get("recent_videos") or []
    for video in videos:
        if not isinstance(video, dict):
            continue
        sponsored = video.get("sponsored")
        if sponsored is True:
            ad_label = "광고 확인"
        elif sponsored is False:
            ad_label = "표시 없음"
        else:
            ad_label = "확인 불가"
        rows.append(
            "<tr>"
            f"<td>{link(video.get('title') or '제목 없음', video.get('url'))}</td>"
            f"<td>{esc(video.get('published_at') or '확인 불가')}</td>"
            f"<td class=\"num\">{number(video.get('views'))}</td>"
            f"<td class=\"num\">{number(video.get('comments'))}</td>"
            f"<td>{esc(ad_label)}</td>"
            "</tr>"
        )
    if not rows:
        return '<p class="muted">검증된 영상 기록이 없습니다.</p>'
    return (
        '<div class="table-wrap"><table class="videos"><thead><tr>'
        "<th>최근 일반 영상</th><th>게시일</th><th>조회수</th><th>댓글</th><th>광고 표시</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )


def candidate_card(candidate: dict[str, Any], rank: int | None = None) -> str:
    status = str(candidate.get("status") or "UNVERIFIED")
    title = candidate.get("channel_name") or "채널명 확인 불가"
    rank_html = f'<span class="rank">{rank}</span>' if rank is not None else ""
    narrative_items = [
        ("추천 이유", candidate.get("recommendation_reason")),
        ("예상 시청자", candidate.get("audience_summary")),
        ("상품 소개 방식", candidate.get("existing_product_style")),
        ("콘텐츠 제안", candidate.get("content_idea")),
        ("광고 경험", candidate.get("advertising_experience_evidence") or candidate.get("sponsorship_evidence")),
        ("주의점", candidate.get("cautions")),
    ]
    narrative = "".join(
        f'<div class="fact"><dt>{esc(label)}</dt><dd>{esc(value)}</dd></div>'
        for label, value in narrative_items
        if value is not None and str(value).strip()
    )
    failure = ""
    if status != "PASS":
        failure = f'<div class="failure"><strong>판정 근거</strong><br>{esc(failure_text(candidate))}</div>'
    score = candidate.get("weighted_recommendation_score")
    score_html = number(score, 1) if score is not None else "공개 근거 부족"
    return f"""
    <article class="candidate-card" id="candidate-{esc(candidate.get('channel_name') or rank or 'item')}">
      <header class="candidate-head">
        <div class="candidate-title">{rank_html}<div><h3>{link(title, candidate.get('channel_url'))}</h3><p>{esc(candidate.get('fit_summary') or candidate.get('product_relevance_evidence') or '')}</p></div></div>
        <span class="badge status-{esc(status.lower().replace(' ', '-'))}">{esc(STATUS_LABELS.get(status, status))}</span>
      </header>
      <div class="metrics">
        <div><span>구독자</span><strong>{subscriber_display(candidate)}</strong></div>
        <div><span>댓글 합계</span><strong>{number(candidate.get('comment_total'))}</strong></div>
        <div><span>평균 조회수</span><strong>{number(candidate.get('average_views'))}</strong></div>
        <div><span>댓글/조회수</span><strong>{number(candidate.get('engagement_by_views'), 3)}%</strong></div>
        <div><span>추천 점수</span><strong>{score_html}</strong></div>
      </div>
      {failure}
      <dl class="facts">{narrative}</dl>
      {video_rows(candidate)}
      <p class="checked">확인일: {esc(candidate.get('checked_at') or '확인 불가')}</p>
    </article>
    """


def summary_table(candidates: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    rank = 0
    for candidate in candidates:
        if candidate.get("status") == "PASS":
            rank += 1
            display_rank: str = str(rank)
        else:
            display_rank = "—"
        comments = candidate.get("selected_videos") or []
        comment_series = " / ".join(
            number(video.get("comments")) for video in comments if isinstance(video, dict)
        ) or "확인 불가"
        rows.append(
            "<tr>"
            f'<td class="num">{display_rank}</td>'
            f"<td>{link(candidate.get('channel_name') or '채널명 확인 불가', candidate.get('channel_url'))}</td>"
            f'<td class="num">{subscriber_display(candidate)}</td>'
            f"<td>{esc(comment_series)}</td>"
            f'<td class="num">{number(candidate.get("comment_total"))}</td>'
            f'<td class="num">{number(candidate.get("average_views"))}</td>'
            f'<td><span class="badge status-{esc(str(candidate.get("status", "UNVERIFIED")).lower().replace(" ", "-"))}">{esc(candidate.get("status", "UNVERIFIED"))}</span></td>'
            "</tr>"
        )
    return "".join(rows)


def render(payload: dict[str, Any]) -> str:
    criteria = payload.get("criteria") if isinstance(payload.get("criteria"), dict) else {}
    metadata = payload.get("report_metadata") if isinstance(payload.get("report_metadata"), dict) else {}
    raw_candidates = payload.get("candidates") if isinstance(payload.get("candidates"), list) else []
    candidates = sorted(
        [item for item in raw_candidates if isinstance(item, dict)], key=candidate_sort_key
    )
    grouped = {
        status: [candidate for candidate in candidates if candidate.get("status") == status]
        for status in STATUS_ORDER
    }
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    counts = summary.get("status_counts") if isinstance(summary.get("status_counts"), dict) else {}
    researched = metadata.get("researched_candidate_count", summary.get("candidate_count", len(candidates)))
    pass_count = counts.get("PASS", len(grouped["PASS"]))
    near_count = counts.get("NEAR MATCH", len(grouped["NEAR MATCH"]))
    try:
        other_count = max(int(researched) - int(pass_count) - int(near_count), 0)
    except (TypeError, ValueError):
        other_count = counts.get("FAIL", 0) + counts.get("UNVERIFIED", 0)
    title = metadata.get("title") or f"{criteria.get('product') or '상품'} 유튜브 인플루언서 조사"
    criteria_summary = metadata.get("criteria_summary") or (
        f"{criteria.get('market', '한국')} · 구독자 {number(criteria.get('subscriber_max'))} 이하 · "
        f"최근 {number(criteria.get('recent_video_count', 3))}개 일반 영상 · "
        f"댓글 합계 {number(criteria.get('minimum_comment_total'))} 이상"
    )
    generated_at = metadata.get("generated_at") or criteria.get("evaluation_date") or ""
    conclusion = metadata.get("conclusion") or "검증된 공개 정보와 필수 조건을 기준으로 후보를 분류했습니다."
    top_recommendations = text_list(metadata.get("top_recommendations"))
    failure_summary = text_list(metadata.get("failure_summary"))
    next_actions = text_list(metadata.get("next_actions"))
    methodology = text_list(metadata.get("methodology_notes"))
    pass_cards = "".join(candidate_card(item, index) for index, item in enumerate(grouped["PASS"], 1))
    near_cards = "".join(candidate_card(item) for item in grouped["NEAR MATCH"])
    other_cards = "".join(candidate_card(item) for status in ("FAIL", "UNVERIFIED") for item in grouped[status])

    def list_html(items: list[str], empty: str = "기록 없음") -> str:
        if not items:
            return f'<p class="muted">{esc(empty)}</p>'
        return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    :root {{ --ink:#17211b; --muted:#647067; --paper:#f5f3ea; --card:#fffdf7; --line:#dcd9ce; --green:#0d6b4c; --green2:#dff2e8; --amber:#9b5b00; --amber2:#fff0cf; --red:#9b2c2c; --red2:#fde5e1; --gray2:#eceeea; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; color:var(--ink); background:var(--paper); font-family:Inter,"Noto Sans KR","Apple SD Gothic Neo","Malgun Gothic",sans-serif; line-height:1.6; }}
    a {{ color:var(--green); text-decoration-thickness:1px; text-underline-offset:3px; }}
    .page {{ width:min(1180px, calc(100% - 32px)); margin:0 auto; }}
    .hero {{ padding:68px 0 36px; border-bottom:1px solid var(--line); background:linear-gradient(135deg,#eef6e8 0%,#f7f0df 58%,#f3e3cf 100%); }}
    .eyebrow {{ margin:0 0 8px; color:var(--green); font-weight:800; letter-spacing:.12em; font-size:.8rem; }}
    h1 {{ margin:0; max-width:850px; font-size:clamp(2rem,5vw,4.4rem); line-height:1.04; letter-spacing:-.045em; }}
    .criteria {{ max-width:900px; margin:22px 0 0; font-size:1.05rem; }} .date {{ color:var(--muted); margin-top:10px; }}
    main {{ padding:32px 0 80px; }} .kpis {{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:28px; }}
    .kpi {{ padding:18px; border:1px solid var(--line); border-radius:16px; background:rgba(255,253,247,.92); }} .kpi span {{ display:block; color:var(--muted); font-size:.82rem; }} .kpi strong {{ display:block; margin-top:3px; font-size:1.75rem; }}
    .intro, .panel {{ background:var(--card); border:1px solid var(--line); border-radius:20px; padding:24px; margin:18px 0; }}
    h2 {{ margin:42px 0 14px; font-size:1.65rem; letter-spacing:-.025em; }} h3 {{ margin:0; font-size:1.32rem; }}
    .table-wrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:14px; background:white; }} table {{ width:100%; border-collapse:collapse; min-width:760px; }} th,td {{ padding:12px 13px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }} th {{ font-size:.78rem; color:var(--muted); background:#f3f4ef; }} tr:last-child td {{ border-bottom:0; }} .num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
    .candidate-card {{ margin:16px 0; padding:24px; border:1px solid var(--line); border-radius:20px; background:var(--card); box-shadow:0 8px 30px rgba(45,54,45,.045); }}
    .candidate-head {{ display:flex; justify-content:space-between; align-items:flex-start; gap:16px; }} .candidate-title {{ display:flex; gap:14px; align-items:flex-start; }} .candidate-title p {{ margin:4px 0 0; color:var(--muted); }} .rank {{ display:grid; place-items:center; min-width:38px; height:38px; border-radius:50%; background:var(--ink); color:white; font-weight:800; }}
    .badge {{ display:inline-flex; align-items:center; padding:4px 9px; border-radius:999px; font-weight:800; font-size:.72rem; white-space:nowrap; }} .status-pass {{ color:var(--green); background:var(--green2); }} .status-near-match {{ color:var(--amber); background:var(--amber2); }} .status-fail {{ color:var(--red); background:var(--red2); }} .status-unverified {{ color:#59615c; background:var(--gray2); }}
    .metrics {{ display:grid; grid-template-columns:repeat(5,1fr); gap:8px; margin:20px 0; }} .metrics div {{ padding:12px; background:#f4f4ee; border-radius:12px; }} .metrics span {{ display:block; color:var(--muted); font-size:.75rem; }} .metrics strong {{ display:block; margin-top:2px; font-size:1rem; font-variant-numeric:tabular-nums; }}
    .facts {{ display:grid; grid-template-columns:repeat(2,1fr); gap:0 24px; margin:18px 0; }} .fact {{ padding:10px 0; border-top:1px solid var(--line); }} dt {{ color:var(--muted); font-size:.78rem; font-weight:700; }} dd {{ margin:2px 0 0; }} .failure {{ margin:14px 0; padding:12px 14px; border-left:4px solid var(--amber); background:var(--amber2); border-radius:8px; }}
    .videos table {{ min-width:680px; }} .checked,.muted {{ color:var(--muted); font-size:.86rem; }} .grid-two {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }} footer {{ border-top:1px solid var(--line); padding:26px 0 46px; color:var(--muted); font-size:.84rem; }}
    @media (max-width:850px) {{ .kpis {{ grid-template-columns:repeat(2,1fr); }} .metrics {{ grid-template-columns:repeat(2,1fr); }} .facts,.grid-two {{ grid-template-columns:1fr; }} .candidate-head {{ flex-direction:column; }} }}
    @media print {{ body {{ background:white; }} .page {{ width:100%; }} .hero {{ padding:28px 0 20px; }} .candidate-card,.panel,.intro,.kpi {{ break-inside:avoid; box-shadow:none; }} a {{ color:inherit; }} }}
  </style>
</head>
<body>
  <header class="hero"><div class="page"><p class="eyebrow">INFLUENCER RESEARCH REPORT</p><h1>{esc(title)}</h1><p class="criteria">{esc(criteria_summary)}</p><p class="date">생성·확인 기준일 {esc(generated_at)}</p></div></header>
  <main class="page">
    <section class="kpis" aria-label="조사 요약" style="grid-template-columns:repeat(4,1fr)">
      <div class="kpi"><span>조사 후보</span><strong>{number(researched)}</strong></div>
      <div class="kpi"><span>조건 통과</span><strong>{number(pass_count)}</strong></div>
      <div class="kpi"><span>근접 후보</span><strong>{number(near_count)}</strong></div>
      <div class="kpi"><span>탈락·검증 불가</span><strong>{number(other_count)}</strong></div>
    </section>
    <section class="intro"><h2 style="margin-top:0">결론</h2><p>{esc(conclusion)}</p></section>
    <h2>후보 한눈에 보기</h2><div class="table-wrap"><table><thead><tr><th>순위</th><th>채널</th><th>구독자</th><th>최근 댓글</th><th>합계</th><th>평균 조회수</th><th>판정</th></tr></thead><tbody>{summary_table(candidates)}</tbody></table></div>
    <h2>PASS 상세 분석</h2>{pass_cards or '<div class="panel muted">모든 필수 조건을 통과한 채널이 없습니다.</div>'}
    <h2>NEAR MATCH</h2>{near_cards or '<div class="panel muted">근접 후보가 없습니다.</div>'}
    <h2>FAIL / UNVERIFIED 주요 기록</h2>{other_cards or '<div class="panel muted">상세 기록에 포함한 탈락·검증 불가 후보가 없습니다.</div>'}
    <section class="grid-two"><div class="panel"><h2 style="margin-top:0">가장 추천하는 채널</h2>{list_html(top_recommendations)}</div><div class="panel"><h2 style="margin-top:0">주요 탈락 원인</h2>{list_html(failure_summary)}</div></section>
    <section class="grid-two"><div class="panel"><h2 style="margin-top:0">다음 행동</h2>{list_html(next_actions)}</div><div class="panel"><h2 style="margin-top:0">방법론·한계</h2>{list_html(methodology)}</div></section>
  </main>
  <footer><div class="page">공개된 유튜브 정보만 사용했습니다. 시청자 성별·연령은 공개 자료가 없으면 추정이며, 연락처·광고 단가·성과를 임의로 생성하지 않았습니다. 모든 수치는 보고서의 확인일 기준입니다.</div></footer>
</body>
</html>"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a self-contained influencer HTML report.")
    parser.add_argument("--input", type=Path, help="Scored JSON file; stdin when omitted")
    parser.add_argument("--output", type=Path, required=True, help="Output HTML path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        raw = args.input.read_text(encoding="utf-8-sig") if args.input else sys.stdin.read()
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        rendered = render(payload)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
