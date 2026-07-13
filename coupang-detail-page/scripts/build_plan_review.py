#!/usr/bin/env python3
"""Build a standalone HTML review board from a project's planning documents."""

from __future__ import annotations

import argparse
import hashlib
import html
import re
import sys
from pathlib import Path

from check_project import check as check_project
from validate_asset_map import validate as validate_asset_map
from validate_motion import validate as validate_motion
from validate_production_docs import validate as validate_production_docs
from validate_plan import (
    MAX_PAGES,
    MIN_PAGES,
    normalize_project_number,
    table_rows,
    validate as validate_plan,
)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def clean_inline(value: str) -> str:
    return value.strip().replace("`", "").replace("**", "").strip()


def field(text: str, label: str, default: str = "미기록") -> str:
    match = re.search(
        rf"^{re.escape(label)}[ \t]*:[ \t]*([^\r\n]*)$", text, re.MULTILINE
    )
    if not match:
        return default
    value = clean_inline(match.group(1))
    return value or default


def markdown_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    lines = text.splitlines()
    tables: list[tuple[list[str], list[list[str]]]] = []
    index = 0
    while index + 1 < len(lines):
        header_line = lines[index].strip()
        divider_line = lines[index + 1].strip()
        if header_line.startswith("|") and divider_line.startswith("|"):
            header = [cell.strip() for cell in header_line.strip("|").split("|")]
            divider = [cell.strip() for cell in divider_line.strip("|").split("|")]
            if len(header) == len(divider) and all(
                re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in divider
            ):
                rows: list[list[str]] = []
                index += 2
                while index < len(lines) and lines[index].strip().startswith("|"):
                    cells = [
                        clean_inline(cell)
                        for cell in lines[index].strip().strip("|").split("|")
                    ]
                    if len(cells) == len(header):
                        rows.append(cells)
                    index += 1
                tables.append((header, rows))
                continue
        index += 1
    return tables


def table_with_header(
    text: str, required: set[str]
) -> tuple[list[str], list[list[str]]] | None:
    for header, rows in markdown_tables(text):
        if required.issubset(set(header)):
            return header, rows
    return None


def row_maps(text: str, required: set[str]) -> list[dict[str, str]]:
    table = table_with_header(text, required)
    if table is None:
        return []
    header, rows = table
    return [dict(zip(header, row)) for row in rows]


def section_bullets(text: str, heading: str) -> list[str]:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return []
    return [
        clean_inline(line[2:])
        for line in match.group(1).splitlines()
        if line.strip().startswith("- ")
    ]


def planning_files(skill_root: Path, project_no: str) -> dict[str, Path]:
    output_root = skill_root / "outputs" / project_no
    return {
        "plan": output_root / "plan-gate.md",
        "ledger": output_root / "fact-ledger.md",
        "asset": output_root / "asset-map.md",
        "prompt": output_root / "prompt-set.md",
        "font": output_root / "font-plan.md",
        "motion": output_root / "motion-plan.md",
        "video": output_root / "video-plan.md",
        "gate": output_root / "generation-gate.md",
        "product": skill_root / "inputs" / project_no / "product-info.md",
        "research": output_root / "web-research.md",
        "analysis": output_root / "detail-page-analysis.md",
        "output": output_root / "plan-review.html",
    }


def planning_digest(paths: dict[str, Path]) -> str:
    """Return a deterministic digest for every user-reviewed planning source."""

    keys = (
        "product",
        "research",
        "analysis",
        "plan",
        "ledger",
        "asset",
        "prompt",
        "font",
        "motion",
        "video",
    )
    digest = hashlib.sha256()
    for key in keys:
        path = paths[key]
        digest.update(key.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def read_required(paths: dict[str, Path], keys: tuple[str, ...]) -> dict[str, str]:
    missing = [str(paths[key]) for key in keys if not paths[key].is_file()]
    if missing:
        raise FileNotFoundError("missing planning files: " + ", ".join(missing))
    return {key: paths[key].read_text(encoding="utf-8") for key in keys}


def render_page_card(
    page: str, plan: list[str], copy: dict[str, str], source: dict[str, str]
) -> str:
    role_id = plan[1]
    role = plan[2]
    modules = plan[3]
    question = plan[4]
    primary_fact = plan[5]
    info_id = plan[6]
    evidence = plan[8]
    h1 = copy.get("H1", plan[9])
    eyebrow = copy.get("EYEBROW", "")
    body = copy.get("BODY", "")
    cards = copy.get("CARD·CHIP·CAPTION", "")
    cta = copy.get("CTA", "")
    metadata = f"{plan[10]} · {plan[11]} · {plan[12]}"
    copy_parts = []
    if eyebrow and eyebrow != "없음":
        copy_parts.append(f'<span class="eyebrow">{esc(eyebrow)}</span>')
    copy_parts.append(f"<h3>{esc(h1)}</h3>")
    if body and body != "없음":
        copy_parts.append(f'<p class="body-copy">{esc(body)}</p>')
    if cards and cards != "없음":
        copy_parts.append(f'<p class="chips"><strong>카드·캡션</strong> {esc(cards)}</p>')
    if cta and cta != "없음":
        copy_parts.append(f'<p class="cta"><strong>CTA</strong> {esc(cta)}</p>')
    return f"""
    <article class="page-card" data-page="{esc(page)}" data-role="{esc(role_id)}" data-info="{esc(info_id)}">
      <div class="page-top"><span class="page-no">{esc(page)}</span><div><b>{esc(role)}</b><small>{esc(role_id)} · {esc(info_id)}</small></div><span class="motion">{esc(plan[14])}</span></div>
      <div class="question"><strong>이 장이 답할 질문</strong><br>{esc(question)}</div>
      <div class="copy-block">{''.join(copy_parts)}</div>
      <dl>
        <div><dt>필수 모듈</dt><dd>{esc(modules)}</dd></div>
        <div><dt>주제·소유 사실</dt><dd>{esc(primary_fact)}</dd></div>
        <div><dt>고유 정보 단위</dt><dd>{esc(info_id)}</dd></div>
        <div><dt>필수 화면 구성</dt><dd>{esc(evidence)}</dd></div>
        <div><dt>의사결정 단계</dt><dd>{esc(source.get('DECISION_STAGE', '미기록'))}</dd></div>
        <div><dt>RAW 자산</dt><dd>{esc(source.get('RAW_ASSET_IDS', '미기록'))}</dd></div>
        <div><dt>레퍼런스 원리</dt><dd>{esc(source.get('REF_PRINCIPLE_IDS', 'NONE'))}</dd></div>
        <div><dt>증거·경계</dt><dd>{esc(source.get('PROOF_ID', '미기록'))} · {esc(source.get('PROOF_MODE', '미기록'))}<br>{esc(source.get('CLAIM_BOUNDARY', '미기록'))}</dd></div>
        <div><dt>삭제 테스트</dt><dd>{esc(source.get('DROP_TEST', '미기록'))}</dd></div>
        <div><dt>컷·장면·레이아웃</dt><dd>{esc(metadata)}</dd></div>
        <div><dt>다음 장 연결</dt><dd>{esc(plan[13])}</dd></div>
      </dl>
    </article>"""


def build(skill_root: Path, project_no: str) -> Path:
    project_no = normalize_project_number(project_no)
    paths = planning_files(skill_root, project_no)
    texts = read_required(
        paths,
        (
            "plan",
            "ledger",
            "asset",
            "prompt",
            "font",
            "motion",
            "video",
            "gate",
            "product",
            "research",
            "analysis",
        ),
    )

    project_report = check_project(skill_root, project_no)
    if not project_report["ok"]:
        raise ValueError(
            "project research/input validation failed: "
            + "; ".join(project_report["errors"])
        )
    plan_report = validate_plan(skill_root, project_no)
    if not plan_report["ok"]:
        raise ValueError(
            "plan validation failed: " + "; ".join(plan_report["errors"])
        )
    asset_report = validate_asset_map(skill_root, project_no)
    if not asset_report["ok"]:
        raise ValueError(
            "asset lineage validation failed: " + "; ".join(asset_report["errors"])
        )
    production_report = validate_production_docs(skill_root, project_no)
    if not production_report["ok"]:
        raise ValueError(
            "production document validation failed: "
            + "; ".join(production_report["errors"])
        )
    motion_report = validate_motion(skill_root, project_no)
    if not motion_report["ok"]:
        raise ValueError(
            "motion planning validation failed: "
            + "; ".join(motion_report["errors"])
        )
    source_digest = planning_digest(paths)

    plan_rows = table_rows(texts["plan"])
    ordered_pages = sorted(plan_rows, key=lambda value: int(value))
    if not MIN_PAGES <= len(ordered_pages) <= MAX_PAGES:
        raise ValueError(
            f"plan-gate.md must select {MIN_PAGES} to {MAX_PAGES} pages; found {len(ordered_pages)}"
        )
    expected_pages = [f"{number:02d}" for number in range(1, len(ordered_pages) + 1)]
    if ordered_pages != expected_pages:
        raise ValueError(
            "plan-gate.md page rows must be continuous from 01: "
            + ", ".join(ordered_pages)
        )
    short_rows = [page for page in ordered_pages if len(plan_rows[page]) < 15]
    if short_rows:
        raise ValueError(
            "plan-gate.md rows need all 15 columns including INFO_ID: "
            + ", ".join(short_rows)
        )
    page_count = len(ordered_pages)

    copy_rows = row_maps(texts["ledger"], {"장", "H1", "BODY"})
    copy_by_page = {
        f"{int(row['장']):02d}": row
        for row in copy_rows
        if row.get("장", "").isdigit() and 1 <= int(row["장"]) <= MAX_PAGES
    }
    source_rows = row_maps(
        texts["asset"],
        {
            "장",
            "INFO_ID",
            "DECISION_STAGE",
            "RAW_ASSET_IDS",
            "REF_PRINCIPLE_IDS",
            "PROOF_ID",
            "PROOF_MODE",
            "DROP_TEST",
            "CLAIM_BOUNDARY",
        },
    )
    source_by_page = {
        f"{int(row['장']):02d}": row
        for row in source_rows
        if row.get("장", "").isdigit() and 1 <= int(row["장"]) <= MAX_PAGES
    }
    fact_rows = row_maps(texts["ledger"], {"Fact ID", "허용 사실", "사용 범위"})
    motion_rows = row_maps(
        texts["motion"], {"MOTION_ID", "CAPTURE_MODE", "총점", "판정"}
    )
    if not motion_rows:
        motion_rows = row_maps(
            texts["motion"], {"후보", "대상 장", "형식", "총점", "판정"}
        )
    if not motion_rows:
        motion_rows = row_maps(
            texts["motion"], {"순위", "후보·권장 위치", "합계", "판정"}
        )

    product_name = field(texts["product"], "상품명")
    category = field(texts["product"], "카테고리")
    approval = field(texts["gate"], "기획 검토 상태", "미승인")
    scope = field(texts["gate"], "제작 범위", "미선택")
    comfy = field(texts["gate"], "ComfyUI 상태", "미확인")
    approved = approval == "승인"
    status_class = "approved" if approved else "pending"
    status_text = "사용자 기획 승인 완료" if approved else "승인 전 · 이미지/GIF/영상 생성 금지"

    page_cards = "".join(
        render_page_card(
            page,
            plan_rows[page],
            copy_by_page.get(page, {}),
            source_by_page.get(page, {}),
        )
        for page in ordered_pages
    )
    page_cards_digest = hashlib.sha256(page_cards.encode("utf-8")).hexdigest()
    production_contract = (
        "=== prompt-set.md ===\n"
        + texts["prompt"]
        + "\n=== font-plan.md ===\n"
        + texts["font"]
    )
    production_digest = hashlib.sha256(production_contract.encode("utf-8")).hexdigest()
    facts_html = "".join(
        f"<tr><td>{esc(row.get('Fact ID', ''))}</td><td>{esc(row.get('허용 사실', ''))}</td><td>{esc(row.get('사용 범위', ''))}</td></tr>"
        for row in fact_rows
    ) or '<tr><td colspan="3">기록 없음</td></tr>'
    forbidden = section_bullets(texts["ledger"], "forbidden claims")
    forbidden_html = "".join(f"<li>{esc(item)}</li>" for item in forbidden) or "<li>기록 없음</li>"
    motion_html = "".join(
        "<tr>"
        f"<td>{esc(row.get('MOTION_ID', row.get('후보', row.get('순위', ''))))}</td>"
        f"<td>{esc(row.get('후보·대상 장', row.get('대상 장', row.get('후보·권장 위치', ''))))}</td>"
        f"<td>{esc(' · '.join(value for value in (row.get('CAPTURE_MODE', ''), row.get('형식', '')) if value))}</td>"
        f"<td>{esc(row.get('총점', row.get('합계', '')))}</td>"
        f"<td>{esc(row.get('판정', ''))}</td>"
        "</tr>"
        for row in motion_rows[:3]
    ) or '<tr><td colspan="5">모션 후보를 아직 기록하지 않았습니다.</td></tr>'
    strongest_motion = field(texts["motion"], "가장 영상이 필요한 소구점")
    if strongest_motion == "미기록":
        strongest_motion = field(texts["video"], "가장 영상이 필요한 소구점")

    function_appeal = field(texts["plan"], "핵심 기능 소구")
    function_fact = field(texts["plan"], "기능 근거 Fact ID")
    function_pain = field(texts["plan"], "기능이 답하는 구매 불편")
    design_support = field(texts["plan"], "디자인 보조 소구")
    function_pages = field(texts["plan"], "기능 우선 적용 장")
    no_function_reason = field(texts["plan"], "기능 없음 사유")
    function_status = field(texts["plan"], "기능 우선 상태", "미완료")
    function_ready = function_status == "완료"
    function_status_class = "approved" if function_ready else "pending"
    function_status_text = "기능 우선 설계 완료" if function_ready else "기능 우선 설계 미완료"
    no_function_html = ""
    if function_appeal == "없음":
        no_function_html = f'<div><dt>기능 없음 사유</dt><dd>{esc(no_function_reason)}</dd></div>'

    target_pages = field(texts["plan"], "목표 장수")
    information_units = field(texts["plan"], "정보 단위 수")
    selected_pages = field(texts["plan"], "선정 장수")
    page_count_reason = field(texts["plan"], "장수 결정 근거")
    removed_roles = field(texts["plan"], "삭제·병합 역할")
    page_count_status = field(texts["plan"], "장수 결정 상태", "미완료")
    count_ready = page_count_status == "완료"
    count_status_class = "approved" if count_ready else "pending"
    count_status_text = "정보량 기반 장수 결정 완료" if count_ready else "장수 결정 미완료"

    document = f"""<!doctype html>
<html lang="ko" data-review-kind="coupang-detail-page-plan" data-project="{esc(project_no)}" data-source-digest="{esc(source_digest)}" data-render-digest="{esc(page_cards_digest)}" data-production-digest="{esc(production_digest)}" data-asset-lineage="complete">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(product_name)} · 프로젝트 {esc(project_no)} 기획 검토</title>
  <style>
    :root{{--ink:#1f2320;--muted:#667068;--paper:#f2f0e9;--card:#fff;--line:#d9ddd6;--green:#27634b;--red:#9c4034;--cream:#f8f4e8;--shadow:0 18px 45px rgba(38,48,41,.08)}}
    *{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;line-height:1.55}} .wrap{{width:min(1180px,calc(100% - 32px));margin:auto}}
    header{{padding:56px 0 34px;background:linear-gradient(145deg,#fff,var(--cream));border-bottom:1px solid var(--line)}} h1{{margin:12px 0 8px;font-size:clamp(34px,6vw,66px);letter-spacing:-.05em;line-height:1.08}} .lead{{color:var(--muted);max-width:780px}}
    .status{{display:inline-flex;padding:9px 13px;border-radius:999px;font-size:13px;font-weight:900}} .status.pending{{background:#f8ded8;color:var(--red)}} .status.approved{{background:#dcecdf;color:var(--green)}}
    .meta{{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}} .meta span{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:8px 11px;font-weight:700;font-size:13px}}
    main{{padding:42px 0 80px}} section{{margin-bottom:48px}} h2{{font-size:30px;letter-spacing:-.035em;margin:0 0 10px}} .notice{{padding:18px;border-left:5px solid var(--red);background:#fff5f2;border-radius:14px;color:#66352e}} .function-priority{{background:#172b22;color:#fff;border-radius:24px;padding:26px;box-shadow:var(--shadow)}} .function-priority h2{{margin-top:12px}} .function-priority .lead{{color:#c6d6cd}} .function-priority dl{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}} .function-priority dl div{{display:block;border:1px solid rgba(255,255,255,.14);border-radius:14px;padding:14px;background:rgba(255,255,255,.06)}} .function-priority dt{{color:#a9c7b7}} .function-priority dd{{color:#fff;font-size:15px;margin-top:4px}}
    .pages{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}} .page-card{{background:var(--card);border:1px solid var(--line);border-radius:22px;padding:22px;box-shadow:var(--shadow)}} .page-top{{display:grid;grid-template-columns:48px 1fr auto;gap:12px;align-items:center}} .page-no{{display:grid;place-items:center;width:46px;height:46px;background:var(--ink);color:#fff;border-radius:13px;font-weight:900}} .page-top b,.page-top small{{display:block}} .page-top small{{color:var(--muted);font-size:11px}} .motion{{font-size:11px;color:var(--green);font-weight:900}}
    .question{{margin:16px 0;padding:13px 14px;background:#eff5f0;border-radius:13px;color:#345344}} .copy-block{{padding:18px;border-radius:16px;background:var(--cream)}} .eyebrow{{font-size:12px;color:var(--green);font-weight:900}} h3{{font-size:26px;line-height:1.18;letter-spacing:-.035em;margin:8px 0}} .body-copy,.chips,.cta{{margin:8px 0;color:var(--muted);font-size:14px}} .cta{{color:var(--green)}} dl{{margin:16px 0 0}} dl div{{display:grid;grid-template-columns:120px 1fr;gap:12px;padding:8px 0;border-top:1px solid #edf0eb}} dt{{font-weight:850;font-size:12px}} dd{{margin:0;color:var(--muted);font-size:13px}}
    table{{width:100%;border-collapse:collapse;background:#fff;border-radius:16px;overflow:hidden}} th,td{{padding:12px 14px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}} th{{font-size:12px;background:#e9ece7}} td{{font-size:13px;color:var(--muted)}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}} .panel{{background:#fff;padding:22px;border:1px solid var(--line);border-radius:20px}} .source-contract{{max-height:560px;overflow:auto;white-space:pre-wrap;word-break:break-word;background:#17211c;color:#dce8e0;border-radius:14px;padding:18px;font-size:12px}} ul{{padding-left:20px}} code{{background:#eceeea;padding:2px 5px;border-radius:5px}} footer{{padding:24px 0 52px;color:var(--muted);font-size:12px}}
    @media(max-width:780px){{.pages,.grid,.function-priority dl{{grid-template-columns:1fr}}.page-top{{grid-template-columns:44px 1fr}}.motion{{grid-column:2}}dl div{{grid-template-columns:1fr;gap:2px}}table{{display:block;overflow-x:auto}}}}
  </style>
</head>
<body>
  <header><div class="wrap">
    <span class="status {status_class}">{esc(status_text)}</span>
    <h1>{esc(product_name)}<br>{page_count}장 기획 검토</h1>
    <p class="lead">이 문서는 이미지 생성 전에 장별 주제, 카피, 화면 구성, 비중복 설계와 모션 아이디어를 검토하기 위한 승인 보드입니다.</p>
    <div class="meta"><span>프로젝트 {esc(project_no)}</span><span>{esc(category)}</span><span>기본 800×2400 · {page_count}장</span><span>R2P 자산 계보 PASS</span><span>소스 해시 {esc(source_digest[:12])}</span><span>제작 범위 {esc(scope)}</span><span>ComfyUI {esc(comfy)}</span></div>
  </div></header>
  <main class="wrap">
    <section class="function-priority" data-page-count-decision="{esc(page_count_status)}">
      <span class="status {count_status_class}">{esc(count_status_text)}</span>
      <h2>반복 없이 {page_count}장만 선정</h2>
      <p class="lead">요청 수량을 채우는 대신 확인된 정보 단위만 남기고, 반복되는 역할은 삭제하거나 합칩니다.</p>
      <dl>
        <div><dt>목표 장수</dt><dd>{esc(target_pages)}</dd></div>
        <div><dt>정보 단위 수</dt><dd>{esc(information_units)}</dd></div>
        <div><dt>선정 장수</dt><dd>{esc(selected_pages)}</dd></div>
        <div><dt>장수 결정 근거</dt><dd>{esc(page_count_reason)}</dd></div>
        <div><dt>삭제·병합 역할</dt><dd>{esc(removed_roles)}</dd></div>
      </dl>
    </section>
    <section class="function-priority" data-functional-priority="{esc(function_status)}">
      <span class="status {function_status_class}">{esc(function_status_text)}</span>
      <h2>기능을 먼저 보는 설계</h2>
      <p class="lead">디자인은 보조로 두고, 구매자가 먼저 확인할 기능·근거·불편을 01~03장 앞부분에 연결합니다.</p>
      <dl>
        <div><dt>핵심 기능 소구</dt><dd>{esc(function_appeal)}</dd></div>
        <div><dt>기능 근거</dt><dd>{esc(function_fact)}</dd></div>
        <div><dt>기능이 답하는 구매 불편</dt><dd>{esc(function_pain)}</dd></div>
        <div><dt>디자인 보조 소구</dt><dd>{esc(design_support)}</dd></div>
        <div><dt>기능 우선 적용 장</dt><dd>{esc(function_pages)}</dd></div>
        {no_function_html}
      </dl>
    </section>
    <section><div class="notice"><strong>생성 게이트</strong><br>사용자가 이 HTML의 주제와 구성을 확정하고 <code>generation-gate.md</code>에 승인 기록을 남기기 전에는 image_gen, GIF 또는 영상 생성을 시작하지 않습니다.</div></section>
    <section><h2>{page_count}장 주제와 구성</h2><p class="lead">각 장은 고유 ROLE_ID·INFO_ID·구매 질문과 RAW·증거·레퍼런스 원리 계보를 하나씩 소유하고, 마지막 정보 장이 CTA까지 담당합니다.</p><div class="pages">{page_cards}</div></section>
    <section class="grid">
      <div class="panel"><h2>허용 사실</h2><table><thead><tr><th>ID</th><th>사실</th><th>사용 범위</th></tr></thead><tbody>{facts_html}</tbody></table></div>
      <div class="panel"><h2>금지 주장</h2><ul>{forbidden_html}</ul></div>
    </section>
    <section><h2>GIF·영상 후보 TOP3</h2><p><strong>가장 영상이 필요한 소구점:</strong> {esc(strongest_motion)}</p><table><thead><tr><th>후보</th><th>대상 장</th><th>형식</th><th>총점</th><th>판정</th></tr></thead><tbody>{motion_html}</tbody></table></section>
    <section class="panel"><h2>승인 대상 생성 프롬프트·폰트 계약 원문</h2><p class="lead">아래 원문까지 이번 승인에 포함됩니다. 승인 뒤 한 글자라도 바뀌면 소스 해시와 HTML 해시가 모두 무효화됩니다.</p><pre id="production-contract" class="source-contract">{esc(production_contract)}</pre></section>
    <section class="panel"><h2>승인 후 순서</h2><ol><li>기획 확정 응답·소스 해시·이 HTML 파일 SHA256을 <code>generation-gate.md</code>에 기록</li><li>다음 응답부터 한 질문씩 정확한 <code>motion-NN</code> ID와 지원 GIF·VIDEO 범위를 선택</li><li>REAL 촬영·ComfyUI·핸드오프 환경을 선택하고, 실행형 ComfyUI는 helper receipt로 검증</li><li>정적 승인, GIF·영상 또는 인계 승인, 최종 실행 승인을 각각 별도 기록</li><li>대상별 generation gate를 통과한 이미지 {page_count}장과 선택 모션만 생성·QA</li></ol></section>
  </main>
  <footer class="wrap">원본 문서: product-info.md · web-research.md · detail-page-analysis.md · plan-gate.md · fact-ledger.md · asset-map.md · prompt-set.md · font-plan.md · motion-plan.md · video-plan.md · generation-gate.md</footer>
</body></html>"""
    paths["output"].write_text(document, encoding="utf-8")
    return paths["output"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a per-project HTML plan review board.")
    parser.add_argument("project", help="Project number, for example 003 or 3")
    args = parser.parse_args()
    skill_root = Path(__file__).resolve().parents[1]
    try:
        output = build(skill_root, args.project)
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"PLAN_REVIEW={output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
