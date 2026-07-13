#!/usr/bin/env python3
"""Tests for numbered project initialization and input readiness checks."""

from __future__ import annotations

import contextlib
from datetime import datetime, timedelta, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import re
import sys
import tempfile
import threading
import unittest
from pathlib import Path

from build_plan_review import build as build_plan_review
from check_project import check
from comfyui_receipt import (
    connected_receipt,
    project_relative_file,
    receipt_id_for,
    workflow_receipt,
    write_receipt,
)
from init_project import choose_number, initialize, prepare
from normalize_pages import (
    build_parser,
    find_pages,
    normalize_with_pillow,
    pad_to_target_ratio,
)
from pillow_runtime import load_pillow, runtime_site_packages
from run_overlay_copy import wrap_text
from validate_pages import image_size, validate
from validate_asset_map import validate as validate_asset_map
from validate_generation_gate import (
    validate as validate_generation_gate,
    validate_approval_records,
    validate_comfy_receipt,
)
from validate_motion import validate as validate_motion
from validate_plan import validate as validate_plan
from validate_production_docs import validate as validate_production_docs


COMPLETE_PRODUCT_INFO = """# 상품 정보

프로젝트 번호: 001
상품명: 테스트 텀블러
카테고리: 주방용품
브랜드명: 없음
가장 중요한 기능적 구매 이유와 근거: 사용자 입력의 휴대하기 쉬운 크기
1. 휴대하기 쉬운 크기
2. 단순한 사용 방법
3. 세척하기 편한 구조
타깃 고객: 출퇴근 직장인
대표 불편: 일회용 컵 사용이 번거로움
사용 상황: 사무실과 이동 중
사용 방법: 음료를 담아 사용
구성품: 텀블러 본체와 뚜껑
판매 구성 수량: 본체 1개와 뚜껑 1개
소재/재질: 스테인리스
색상: 흰색
사이즈: 미제공
실측값: 미제공
실측 사진 상태: 미제공
중량: 미제공
제조국: 미제공
관리/세탁/보관 방법: 사용 후 세척
주의사항: 뜨거운 음료 사용 시 주의
경쟁 제품 대비 검증된 차별점: 별도 근거 없음
강조할 분위기: 깔끔하고 실용적
객관적인 수치/인증/시험 정보: 없음
사용하면 안 되는 표현: 100%, 완벽, 최고
"""

COMPLETE_WEB_RESEARCH = """# 웹 리서치

프로젝트 번호: 001
조사일: 2026-07-13
조사 상태: 완료
동일 제품 결론: 검색 결과 없음

| 유형 | 검색어 | URL 또는 검색 결과 없음 | 동일성 | 출처 | 확인한 내용 | 기획 사용 범위 | 제외할 주장 | ASSET_ID |
|---|---|---|---|---|---|---|---|---|
| 동일 제품 | 테스트 텀블러 모델명 | 검색 결과 없음 | M0 | E4 | 동일 제품 미확인 | 결과 없음 기록 | 모든 상품 사실 | - |
| 유사 제품 | 흰색 휴대용 텀블러 | https://example.com/similar | M3 | E4 | 카테고리 구성 | 장면 아이디어만 | 기능·수치 | - |
| 상세 구조 | 텀블러 상세페이지 A | https://example.com/a | M3 | E4 | 훅과 장점 카드 | 구조만 | 상품 사실 | - |
| 상세 구조 | 텀블러 상세페이지 B | https://example.com/b | M3 | E4 | 디테일 캡션 | 구조만 | 상품 사실 | - |
| 상세 구조 | 패션 상세페이지 C | https://example.com/c | M3 | E4 | 타이포 계층 | 구조만 | 상품 사실 | - |
"""

COMPLETE_DETAIL_PAGE_ANALYSIS = """# 상세페이지 비교 분석

## 비교한 페이지

- https://example.com/a
- https://example.com/b
- https://example.com/c

## 공통 패턴

1. 훅 다음에 설명과 카드가 이어진다.
2. 디테일마다 캡션이 있다.
3. 같은 타이포 계층을 유지한다.
"""


def write_complete_research(root: Path, project_no: str = "001") -> None:
    output_root = root / "outputs" / project_no
    output_root.joinpath("web-research.md").write_text(
        COMPLETE_WEB_RESEARCH.replace("프로젝트 번호: 001", f"프로젝트 번호: {project_no}"),
        encoding="utf-8",
    )
    output_root.joinpath("detail-page-analysis.md").write_text(
        COMPLETE_DETAIL_PAGE_ANALYSIS,
        encoding="utf-8",
    )


COMPLETE_PROMPT_SET = """# image_gen 프롬프트 세트

프로젝트 번호: 001

## SOURCE_ROLES

- RAW_PRIMARY A01을 제품 정체성의 기준으로 사용한다.
- REF_*는 추상 원리만 제공하고 상품 사실로 사용하지 않는다.

## R2P_LINEAGE

- 모든 장은 asset-map.md의 RAW_ASSET_IDS, REF_PRINCIPLE_IDS, PROOF_ID와 CLAIM_BOUNDARY를 그대로 사용한다.
- 승인되지 않은 기능·수치·구성·카피를 추가하지 않는다.

## COPY_SYSTEM

- 정확한 카피: fact-ledger.md의 EYEBROW, H1, BODY, CARD·CHIP·CAPTION, CTA만 직접 조판한다.
- 축약·의역·누락·추가를 금지하고 장마다 하나의 고유 구매 질문만 답한다.

## TYPOGRAPHY_SYSTEM

- 800x2400 원본, H1 96px, BODY 36px, LABEL·CAPTION 최소 32px를 사용한다.
- 모든 장은 같은 한국어 산세리프 계열과 같은 위계를 유지한다.

## FUNCTION_PRIORITY

- 기능과 근거를 디자인 무드보다 먼저 배치한다.
- 근거보다 강한 효능·성능·수치·보장 표현을 만들지 않는다.

## DESIGN_SYSTEM

- 제품 원본 색·형태·부품·라벨을 보존한다.
- 레퍼런스의 제품, 문구, 수치, 로고, 고유 그래픽은 복제하지 않는다.
- 각 장은 3~6개의 세로 정보 구역과 충분한 모바일 여백을 사용한다.

## 선정 장수 프롬프트와 실행 기록

| 장 | ROLE_ID | INFO_ID | 독점 정보 | raw 출력 |
|---:|---|---|---|---|
| 01 | PROBLEM_HOOK | I01 | 불편과 기능 답 | `outputs/001/raw/page-01.png` |
| 02 | PRODUCT_INTRO | I02 | 상품 정체 | `outputs/001/raw/page-02.png` |
| 03 | FEATURE_EVIDENCE | I03 | 기능 근거 | `outputs/001/raw/page-03.png` |
| 04 | FIT_SIZE | I04 | 실측 | `outputs/001/raw/page-04.png` |
| 05 | MATERIAL_SPEC | I05 | 소재 | `outputs/001/raw/page-05.png` |
| 06 | HOW_TO_USE | I06 | 사용법 | `outputs/001/raw/page-06.png` |
| 07 | USE_CASE_CTA | I07 | 사용 장면과 CTA | `outputs/001/raw/page-07.png` |
"""

COMPLETE_FONT_PLAN = """# 폰트·조판 계획

프로젝트 번호: 001
최종 조판 방식: IMAGE_GEN_DIRECT 우선, 승인된 실패 장만 FIXED_TEXT_LAYER

## 정지 이미지 조판 경로

- 승인 카피를 image_gen에 직접 전달한다.
- 동일 장 2회 실패 뒤 사용자 승인 시에만 FIXED_TEXT_LAYER로 전환한다.
- GIF·영상은 항상 FIXED_TEXT_LAYER를 사용한다.

## 폰트 잠금

- 주 한글 서체: Apple SD Gothic Neo
- 대체 서체: Nanum Gothic
- 사용 가능한 굵기: 500, 600, 700, 800
- 폰트 경로 또는 조판 환경: macOS 시스템 폰트 또는 설치 확인한 대체 폰트
- 라이선스·배포 확인: 폰트 파일은 결과물에 포함하지 않음
- 프로젝트 중 서체 혼용: 금지

## 800x2400 조판 토큰

| 역할 | 크기 | 굵기 | 행간 | 최대 줄 |
|---|---:|---:|---:|---:|
| H1 | 96px | 800 | 1.10 | 2줄 |
| H2 | 56px | 700 | 1.20 | 2줄 |
| BODY | 36px | 500 | 1.50 | 3줄 |
| LABEL·CAPTION | 최소 32px | 600 | 1.30 | 2줄 |
| CTA | 40px | 700 | 1.20 | 2줄 |

- 좌우 안전 여백 56px, 상하 안전 여백 80px, 카드 안쪽 여백 32px 이상.
- 본문이 넘치면 글자를 줄이지 않고 문장을 줄이거나 구역을 나눈다.
- 같은 의미의 카피를 다른 장에서 반복하지 않는다.

## 영상 고정 텍스트 레이어

- 승인 카피는 실제 폰트 레이어로 한 번 조판하고 모든 프레임에 고정한다.
- 생성 모델이 한글 글리프를 프레임마다 다시 만들지 않게 한다.
- 제품 물리 라벨은 원본 텍스처로 보존한다.

## 한글 QA

- 자모 분리, 오탈자, 조사, 띄어쓰기, 숫자, 단위와 줄바꿈을 승인 원문과 대조한다.
- 100% 원본 크기와 모바일 축소 크기에서 모두 읽고 32px 미만 정보 문구를 금지한다.
- 영상은 시작·중간·종료 프레임의 글자 위치와 형태가 같은지 확인한다.
"""


def write_complete_production_docs(root: Path, project_no: str = "001") -> None:
    output_root = root / "outputs" / project_no
    output_root.joinpath("prompt-set.md").write_text(
        COMPLETE_PROMPT_SET.replace("프로젝트 번호: 001", f"프로젝트 번호: {project_no}")
        .replace("outputs/001/", f"outputs/{project_no}/"),
        encoding="utf-8",
    )
    output_root.joinpath("font-plan.md").write_text(
        COMPLETE_FONT_PLAN.replace("프로젝트 번호: 001", f"프로젝트 번호: {project_no}"),
        encoding="utf-8",
    )

COMPLETE_PLAN_GATE = """# 근거 기반 가변 장수·비중복 기획 게이트

프로젝트 번호: 001
검증 상태: 완료

## 장수 결정 게이트

목표 장수: 7
정보 단위 수: 7
선정 장수: 7
장수 결정 근거: 확인된 기능·상품 정체·실측·소재·사용법·관리 정보를 서로 다른 장에 배정
삭제·병합 역할: 독립 요약 CTA를 마지막 사용 장면 장에 병합
장수 결정 상태: 완료

## 기능 우선 게이트

핵심 기능 소구: 휴대하기 쉬운 크기
기능 근거 Fact ID: F01
기능이 답하는 구매 불편: 부피가 큰 용기를 이동할 때 번거로움
디자인 보조 소구: 없음
기능 우선 적용 장: 01, 02
기능 없음 사유: 없음
기능 우선 상태: 완료

| 장 | ROLE_ID | 역할 | 필수 모듈 | 고유 구매 질문 | PRIMARY_FACT | INFO_ID | ADVANTAGE_ID | 필수 시각 증거 | H1 핵심어 | SHOT_ID | SCENE_ID | LAYOUT_ID | 다음 장과 연결 | 모션 역할 |
|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | PROBLEM_HOOK | 문제 후킹 | H1+BODY+PROBLEM_SCENE | 불편은 무엇인가 | F01 | I01 | - | 문제 상황 한 컷 | 불편 공감 | SHOT01 | SCENE01 | LAYOUT01 | 상품 소개로 | 정지 |
| 02 | PRODUCT_INTRO | 상품 메인 소개 | PRODUCT_NAME+HERO+CORE_ADVANTAGES | 어떤 상품인가 | F02 | I02 | A1+A2+A3 | 제품 히어로 | 상품 정체 | SHOT02 | SCENE02 | LAYOUT02 | 기능 근거로 | 정지 |
| 03 | FEATURE_EVIDENCE | 핵심 기능과 근거 | FEATURE+EVIDENCE+BOUNDARY | 기능 근거는 무엇인가 | F03 | I03 | A1 | 기능 근거와 허용 범위 | 기능 확인 | SHOT03 | SCENE03 | LAYOUT03 | 실측으로 | 정지 |
| 04 | FIT_SIZE | 착용감·실측 사이즈 | FIT+SIZE_DIAGRAM+MEASUREMENTS | 실제 크기는 얼마인가 | F04 | I04 | A2 | 자를 댄 실측 도식 | 실측 안내 | SHOT04 | SCENE04 | LAYOUT04 | 소재로 | 영상 |
| 05 | MATERIAL_SPEC | 소재·제품 사양 | MATERIAL+SPEC+DETAIL | 어떤 소재인가 | F05 | I05 | A3 | 소재 확대와 사양 표 | 소재 정보 | SHOT05 | SCENE05 | LAYOUT05 | 사용법으로 | GIF |
| 06 | HOW_TO_USE | 사용 방법 | STEP_BY_STEP+USE_SCENE | 어떻게 사용하는가 | F06 | I06 | - | 사용 순서 세 단계 | 사용 방법 | SHOT06 | SCENE06 | LAYOUT06 | 활용로 | 정지 |
| 07 | USE_CASE_CTA | 사용 장면·구매 안내 | USE_CASES+CAPTIONS+CTA | 어디에서 사용하는가 | F07 | I07 | - | 사용 장면과 구매 안내 | 활용 선택 | SHOT07 | SCENE07 | LAYOUT07 | 종료 | 영상 |
"""

COMPLETE_FACT_LEDGER = """# 사실·카피 원장

프로젝트 번호: 001

## allowed facts

| Fact ID | 허용 사실 | 근거 | 사용 범위 |
|---|---|---|---|
| F01 | 휴대하기 쉬운 크기 | 사용자 입력 | 기능 소개 |
| F02 | 테스트 텀블러 상품 정체 | 사용자 입력 | 상품 소개 |
| F03 | 기능 근거 범위 | 사용자 입력 | 기능 설명 |
| F04 | 사용자 제공 크기 | 사용자 입력 | 실측 안내 |
| F05 | 스테인리스 소재 | 사용자 입력 | 소재 정보 |
| F06 | 음료를 담아 사용 | 사용자 입력 | 사용 방법 |
| F07 | 사무실과 이동 중 사용 | 사용자 입력 | 사용 장면 |

## approved copy manifest

| 장 | 설득 목적 | 후킹 각도 | EYEBROW | H1 | BODY | CARD·CHIP·CAPTION | CTA | 근거 Fact ID | 읽는 순서 |
|---:|---|---|---|---|---|---|---|---|---|
| 01 | 문제 공감 | 불편 | 시작 | 불편을 확인하세요 | 불편한 상황입니다 | 상황 카드 | 없음 | F01 | 제목부터 |
| 02 | 상품 소개 | 정체 | 상품 | 테스트 상품 | 상품 소개입니다 | 제품 카드 | 없음 | F02 | 제목부터 |
| 03 | 기능 근거 | 기능 | 근거 | 기능을 확인하세요 | 근거 범위입니다 | 기능 카드 | 없음 | F03 | 제목부터 |
| 04 | 실측 | 크기 | 실측 | 크기를 확인하세요 | 사용자 제공 크기입니다 | 치수 카드 | 없음 | F04 | 제목부터 |
| 05 | 소재 | 사양 | 소재 | 소재를 확인하세요 | 소재 정보입니다 | 소재 카드 | 없음 | F05 | 제목부터 |
| 06 | 사용법 | 순서 | 사용 | 순서를 확인하세요 | 음료를 담아 씁니다 | 순서 카드 | 없음 | F06 | 제목부터 |
| 07 | 사용 장면 | 활용 | 활용 | 어디에서 쓰나요 | 사무실과 이동 중입니다 | 장면 카드 | 지금 확인하세요 | F07 | 제목부터 |

## forbidden claims

- 근거 없는 효능
"""

APPROVED_GENERATION_GATE = """# 사용자 검토·생성 게이트

프로젝트 번호: 001
기획 리뷰 HTML: `plan-review.html`
기획 검토 상태: 승인
사용자 승인 기록: 2026-07-13 · APPROVE_PLAN · ANSWER=1
승인한 기획 소스 해시: SOURCE_DIGEST
승인한 리뷰 HTML 해시: REVIEW_DIGEST
제작 범위: STATIC_ONLY
선정 모션 ID: 해당 없음
환경 선택 기록: 2026-07-13 · SELECT_ENV · SCOPE=STATIC_ONLY · MOTION=NONE · COMFY=NOT_REQUIRED
ComfyUI 상태: NOT_REQUIRED
ComfyUI 증빙 JSON: 해당 없음
정적 이미지 생성 승인: 승인
GIF·영상 생성 승인: 해당 없음
최종 생성 승인 기록: 2026-07-13 · APPROVE_EXECUTION · SCOPE=STATIC_ONLY · MOTION=NONE · COMFY=NOT_REQUIRED
"""


def write_complete_asset_map(root: Path, project_no: str = "001") -> Path:
    asset_path = root / "inputs" / project_no / "original-images" / "front.png"
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_bytes(b"fixture")
    digest = hashlib.sha256(b"fixture").hexdigest()
    page_rows = []
    stages = ("NOTICE", "UNDERSTAND", "VERIFY", "FIT", "VERIFY", "USE", "DECIDE")
    modes = (
        "COMPOSITE_LAYOUT",
        "COMPOSITE_LAYOUT",
        "COMPOSITE_LAYOUT",
        "USER_DECLARATION",
        "COMPOSITE_LAYOUT",
        "COMPOSITE_LAYOUT",
        "AI_ILLUSTRATION",
    )
    for number, (stage, mode) in enumerate(zip(stages, modes), start=1):
        page_rows.append(
            f"| {number:02d} | I{number:02d} | {stage} | A01 | NONE | P{number:02d} | F{number:02d} | {mode} | "
            f"페이지 {number}만의 독점 구매 답 | 페이지 {number}을 지우면 해당 답이 사라짐 | F{number:02d} 범위를 넘는 주장 금지 |"
        )
    proof_rows = "\n".join(
        f"| P{number:02d} | F{number:02d} | {'SPEC' if number in {1,4,5} else 'CONTEXT'} | USER_DECLARED_SPEC | PRODUCT_INFO,A01 | USER_CONFIRMED | 현재 테스트 SKU | F{number:02d} 문구 범위 | 수치·성능 확대 금지 | APPROVED |"
        for number in range(1, 8)
    )
    content = f"""# R2P 자산·근거·페이지 계보

프로젝트 번호: {project_no}
검증 상태: 완료

## A. Asset Registry

| ASSET_ID | ROLE | ORIGIN | PATH_OR_URL | PRODUCT_MATCH | SOURCE_GRADE | SHA256 | OBSERVABLE_FACTS | ALLOWED_USE | FORBIDDEN_TRANSFER | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|
| A01 | RAW_PRIMARY | USER | inputs/{project_no}/original-images/front.png | USER | USER | {digest} | 흰색 텀블러 외형 | 제품 정체성과 관찰 구조 | 보이지 않는 성능·수치 | READY |

## B. Evidence Ledger

| PROOF_ID | FACT_IDS | CLAIM_CLASS | EVIDENCE_TYPE | SOURCE_ASSET_IDS | STRENGTH | SKU_OPTION_SCOPE | ALLOWED_COPY | FORBIDDEN_EXPANSION | STATUS |
|---|---|---|---|---|---|---|---|---|---|
{proof_rows}

## C. Reference Principle Ledger

| REF_PRINCIPLE_ID | REFERENCE_ASSET_ID | REFERENCE_TYPE | ABSTRACT_PRINCIPLE | TARGET_PAGE_IDS | DO_NOT_COPY | STATUS | REJECTION_REASON |
|---|---|---|---|---|---|---|---|

## D. Page Source Contract

| 장 | INFO_ID | DECISION_STAGE | RAW_ASSET_IDS | REF_PRINCIPLE_IDS | PROOF_ID | PRIMARY_FACT_IDS | PROOF_MODE | EXCLUSIVE_GAIN | DROP_TEST | CLAIM_BOUNDARY |
|---:|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(page_rows)}
"""
    output_path = root / "outputs" / project_no / "asset-map.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def write_verified_real_demo(root: Path, project_no: str = "001") -> Path:
    Image, _, _, _ = load_pillow(install=True)
    evidence_path = root / "inputs" / project_no / "evidence" / "motion-01.gif"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    first = Image.new("RGB", (64, 64), "white")
    second = Image.new("RGB", (64, 64), "black")
    first.save(
        evidence_path,
        save_all=True,
        append_images=[second],
        duration=250,
        loop=0,
        format="GIF",
    )
    digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    asset_path = root / "outputs" / project_no / "asset-map.md"
    asset_text = asset_path.read_text(encoding="utf-8")
    asset_lines = asset_text.splitlines()
    for index, line in enumerate(asset_lines):
        if line.startswith("| A01 |"):
            asset_lines.insert(
                index + 1,
                f"| A02 | RAW_DEMO | USER | inputs/{project_no}/evidence/motion-01.gif | USER | USER | {digest} | 실제 두 프레임 시연 | 실사 동작 증거 | 성능 일반화 | READY |",
            )
            break
    else:
        raise AssertionError("asset fixture is missing A01")
    asset_path.write_text("\n".join(asset_lines) + "\n", encoding="utf-8")

    video_path = root / "outputs" / project_no / "video-plan.md"
    video_text = video_path.read_text(encoding="utf-8")
    video_text = video_text.replace(
        "- 증명 상태: PENDING_CAPTURE", "- 증명 상태: VERIFIED", 1
    ).replace(
        "- 실사 원본 클립 경로: PENDING_CAPTURE",
        f"- 실사 원본 클립 경로: inputs/{project_no}/evidence/motion-01.gif",
        1,
    )
    video_path.write_text(video_text, encoding="utf-8")
    return evidence_path


def approved_gate_for(review_path: Path, base: str = APPROVED_GENERATION_GATE) -> str:
    review_text = review_path.read_text(encoding="utf-8")
    match = re.search(r'data-source-digest="([0-9a-f]{64})"', review_text)
    if not match:
        raise AssertionError("review HTML is missing data-source-digest")
    review_digest = hashlib.sha256(review_path.read_bytes()).hexdigest()
    return base.replace("SOURCE_DIGEST", match.group(1)).replace(
        "REVIEW_DIGEST", review_digest
    )


def gate_for_selection(
    review_path: Path,
    scope: str,
    motion_ids: tuple[str, ...] = (),
    comfy: str = "NOT_REQUIRED",
    motion_approval: str = "해당 없음",
) -> str:
    text = approved_gate_for(review_path)
    selected_value = ", ".join(sorted(motion_ids)) if motion_ids else "해당 없음"
    motion_token = ",".join(sorted(motion_ids)) if motion_ids else "NONE"
    replacements = {
        "제작 범위": scope,
        "선정 모션 ID": selected_value,
        "환경 선택 기록": (
            "2026-07-13 · SELECT_ENV · "
            f"SCOPE={scope} · MOTION={motion_token} · COMFY={comfy}"
        ),
        "ComfyUI 상태": comfy,
        "GIF·영상 생성 승인": motion_approval,
        "최종 생성 승인 기록": (
            "2026-07-13 · APPROVE_EXECUTION · "
            f"SCOPE={scope} · MOTION={motion_token} · COMFY={comfy}"
        ),
    }
    for label, value in replacements.items():
        text = re.sub(
            rf"^{re.escape(label)}:[^\n]*$",
            f"{label}: {value}",
            text,
            flags=re.MULTILINE,
        )
    return text

COMPLETE_MOTION_PLAN = """# GIF·영상·ComfyUI 모션 계획

프로젝트 번호: 001
가장 영상이 필요한 소구점: 실제 제품으로 세 가지 한정 과업을 연속 시연한다

## 모션 후보 7요소 점수

| 순위 | MOTION_ID | 후보·대상 장 | 형식 | CAPTURE_MODE | 동작 필요성 | 주장 안전성 | 전환 관련성 | 제작 실행성 | 제품 안정성 | 고유 소구 선명도 | 실증 후킹력 | 총점 | 판정 |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | motion-01 | 세 과업 시연 / 05 | 영상 | REAL_DEMO | 18 | 20 | 19 | 18 | 18 | 17 | 17 | 127 | TOP1 |
| 2 | motion-02 | 구조 설명 / 06 | GIF | AI_ILLUSTRATION | 14 | 20 | 14 | 19 | 18 | 13 | 5 | 103 | 보조 |
| 3 | motion-03 | 촬영 보류 / 09 | 영상 | NO_PROOF_HOOK | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 20 | 보류 |
"""

COMPLETE_VIDEO_PLAN = """# 영상·GIF TOP3 스토리보드

프로젝트 번호: 001

## motion-01 — TOP1

- CAPTURE_MODE: REAL_DEMO
- 증명 상태: PENDING_CAPTURE
- 검증할 구매 의심: 제품을 착용한 손으로 세 가지 한정 과업을 수행하는 모습이 보이는가
- 허용 주장: 촬영된 세 과업과 열린 손가락 구조만 설명
- 도전 조건·과업: 같은 손으로 휴대폰 스와이프, 카드 집기, 지퍼 열기
- 통제 조건: 동일 제품, 동일 모델, 동일 손, 동일 카메라
- 판정 기준: 세 동작의 시작과 완료가 화면에 각각 보임
- 실사 원본 클립 경로: PENDING_CAPTURE
- 편집 정책: 세 과업은 원테이크로 촬영하고 결과를 가리는 합성 금지

## motion-02 — TOP2

- CAPTURE_MODE: AI_ILLUSTRATION
- 증명 상태: DEMO_ONLY
- 검증할 구매 의심: 엄지 홀의 위치가 어디인가
- 허용 주장: 엄지 홀 위치를 이해하기 위한 연출
- 도전 조건·과업: 해당 없음
- 통제 조건: 해당 없음
- 판정 기준: 해당 없음
- 실사 원본 클립 경로: 해당 없음
- 편집 정책: AI 연출임을 내부 원장에 표시

## motion-03 — TOP3

- CAPTURE_MODE: NO_PROOF_HOOK
- 증명 상태: PENDING_CAPTURE
- 검증할 구매 의심: 해당 없음
- 허용 주장: 없음
- 도전 조건·과업: 없음
- 통제 조건: 없음
- 판정 기준: 없음
- 실사 원본 클립 경로: PENDING_CAPTURE
- 편집 정책: 없음
"""


class ProjectWorkflowTest(unittest.TestCase):
    def test_initialize_and_choose_next_number(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, output_root = initialize(root, 1)
            self.assertTrue((input_root / "product-info.md").is_file())
            self.assertTrue((input_root / "original-images").is_dir())
            self.assertTrue((input_root / "evidence").is_dir())
            self.assertTrue((input_root / "web-confirmed").is_dir())
            self.assertTrue((output_root / "raw" / "retries").is_dir())
            self.assertTrue((output_root / "final").is_dir())
            for filename in (
                "web-research.md",
                "detail-page-analysis.md",
                "fact-ledger.md",
                "asset-map.md",
                "plan-gate.md",
                "generation-gate.md",
                "prompt-set.md",
                "qa-report.md",
                "motion-plan.md",
                "font-plan.md",
                "video-plan.md",
            ):
                self.assertTrue((output_root / filename).is_file())
            font_plan = (output_root / "font-plan.md").read_text(encoding="utf-8")
            for font_contract in (
                "image_gen 프롬프트에 직접",
                "2회 실패",
                "사용자 승인",
                "GIF·영상",
                "FIXED_TEXT_LAYER",
            ):
                self.assertIn(font_contract, font_plan)
            prompt_set = (output_root / "prompt-set.md").read_text(encoding="utf-8")
            for heading in (
                "## SOURCE_ROLES",
                "## R2P_LINEAGE",
                "## COPY_SYSTEM",
                "## TYPOGRAPHY_SYSTEM",
                "## FUNCTION_PRIORITY",
                "## DESIGN_SYSTEM",
            ):
                self.assertIn(heading, prompt_set)
            generation_gate = (output_root / "generation-gate.md").read_text(
                encoding="utf-8"
            )
            for gate_field in (
                "기획 검토 상태: 미승인",
                "승인한 기획 소스 해시:",
                "승인한 리뷰 HTML 해시:",
                "선정 모션 ID: 미선택",
                "ComfyUI 상태: 미확인",
                "ComfyUI 증빙 JSON: 미제공",
                "최종 생성 승인 기록:",
                "comfyui_receipt.py probe",
                "comfyui_receipt.py workflow",
            ):
                self.assertIn(gate_field, generation_gate)
            video_plan = (output_root / "video-plan.md").read_text(encoding="utf-8")
            self.assertIn("ComfyUI 상태: 미확인", video_plan)
            self.assertIn("가장 영상이 필요한 소구점", video_plan)
            self.assertIn("motion-03", video_plan)
            motion_plan = (output_root / "motion-plan.md").read_text(encoding="utf-8")
            for score_name in (
                "동작 필요성",
                "주장 안전성",
                "전환 관련성",
                "제작 실행성",
                "제품 안정성",
                "고유 소구 선명도",
                "실증 후킹력",
            ):
                self.assertIn(score_name, motion_plan)
            plan_gate = (output_root / "plan-gate.md").read_text(encoding="utf-8")
            for count_label in (
                "목표 장수",
                "정보 단위 수",
                "선정 장수",
                "장수 결정 근거",
                "삭제·병합 역할",
                "장수 결정 상태: 미완료",
                "INFO_ID",
            ):
                self.assertIn(count_label, plan_gate)
            for functional_label in (
                "핵심 기능 소구",
                "기능 근거 Fact ID",
                "기능이 답하는 구매 불편",
                "디자인 보조 소구",
                "기능 우선 적용 장",
                "기능 없음 사유",
                "기능 우선 상태: 미완료",
            ):
                self.assertIn(functional_label, plan_gate)
            self.assertEqual(choose_number(root, None), 2)
            with self.assertRaises(FileExistsError):
                choose_number(root, 1)
            with self.assertRaisesRegex(ValueError, "between 1 and 999"):
                initialize(root, 0)

    def test_validate_motion_accepts_real_demo_and_rejects_ai_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "motion-plan.md").write_text(
                COMPLETE_MOTION_PLAN, encoding="utf-8"
            )
            (output_root / "video-plan.md").write_text(
                COMPLETE_VIDEO_PLAN, encoding="utf-8"
            )
            report = validate_motion(root, "001")
            self.assertTrue(report["ok"], report["errors"])

            ai_top1 = COMPLETE_MOTION_PLAN.replace(
                "| 1 | motion-01 | 세 과업 시연 / 05 | 영상 | REAL_DEMO |",
                "| 1 | motion-01 | 세 과업 시연 / 05 | 영상 | AI_ILLUSTRATION |",
            )
            (output_root / "motion-plan.md").write_text(ai_top1, encoding="utf-8")
            (output_root / "video-plan.md").write_text(
                COMPLETE_VIDEO_PLAN.replace(
                    "- CAPTURE_MODE: REAL_DEMO", "- CAPTURE_MODE: AI_ILLUSTRATION", 1
                ),
                encoding="utf-8",
            )
            rejected = validate_motion(root, "001")
            self.assertFalse(rejected["ok"])
            self.assertTrue(
                any("cannot exceed 5" in error for error in rejected["errors"]),
                rejected["errors"],
            )

    def test_validate_motion_rejects_legacy_five_axis_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            legacy = """# 모션 계획

가장 영상이 필요한 소구점: 구조 설명

| 후보 | 동작 필요성 | 주장 안전성 | 전환 관련성 | ComfyUI 실행성 | 제품 안정성 | 총점 |
|---|---:|---:|---:|---:|---:|---:|
| 엄지 홀 | 19 | 20 | 20 | 18 | 15 | 92 |
"""
            (output_root / "motion-plan.md").write_text(legacy, encoding="utf-8")
            (output_root / "video-plan.md").write_text(
                COMPLETE_VIDEO_PLAN, encoding="utf-8"
            )
            report = validate_motion(root, "001")
            self.assertFalse(report["ok"])
            self.assertTrue(
                any("7-axis table" in error for error in report["errors"]),
                report["errors"],
            )

    def test_validate_motion_accepts_explicit_no_proof_hook(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            no_proof_motion = """# 모션 계획

가장 영상이 필요한 소구점: NO_PROOF_HOOK

| 순위 | MOTION_ID | 후보·대상 장 | 형식 | CAPTURE_MODE | 동작 필요성 | 주장 안전성 | 전환 관련성 | 제작 실행성 | 제품 안정성 | 고유 소구 선명도 | 실증 후킹력 | 총점 | 판정 |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | motion-01 | 실사 조건 없음 | 정지 | NO_PROOF_HOOK | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 20 | 보류 |
"""
            no_proof_video = """# 영상 계획

실사 촬영 필요: 예

## motion-01 — TOP1 보류

- CAPTURE_MODE: NO_PROOF_HOOK
"""
            (output_root / "motion-plan.md").write_text(
                no_proof_motion, encoding="utf-8"
            )
            (output_root / "video-plan.md").write_text(
                no_proof_video, encoding="utf-8"
            )
            report = validate_motion(root, "001")
            self.assertTrue(report["ok"], report["errors"])

    def test_plan_gate_rejects_blank_template_and_accepts_complete_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            blank_report = validate_plan(root, "001")
            self.assertFalse(blank_report["ok"])
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            complete_report = validate_plan(root, "001")
            self.assertTrue(complete_report["ok"], complete_report["errors"])
            self.assertEqual(len(complete_report["rows"]), 7)
            self.assertEqual(
                complete_report["page_count_decision"]["선정 장수"], "7"
            )
            self.assertEqual(
                complete_report["function_priority"]["핵심 기능 소구"],
                "휴대하기 쉬운 크기",
            )

    def test_asset_lineage_rejects_blank_template_and_accepts_complete_map(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            blank = validate_asset_map(root, "001")
            self.assertFalse(blank["ok"])

            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            write_complete_asset_map(root)
            complete = validate_asset_map(root, "001")
            self.assertTrue(complete["ok"], complete["errors"])
            self.assertEqual(len(complete["pages"]), 7)

    def test_local_web_asset_requires_research_url_and_asset_id_backlink(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            write_complete_research(root)
            asset_path = write_complete_asset_map(root)
            reference_path = (
                root / "inputs" / "001" / "real-references" / "reference.jpg"
            )
            reference_path.write_bytes(b"downloaded-reference")
            digest = hashlib.sha256(reference_path.read_bytes()).hexdigest()
            asset_text = asset_path.read_text(encoding="utf-8").replace(
                "| A01 | RAW_PRIMARY | USER | inputs/001/original-images/front.png",
                "| A02 | REF_PHOTO | WEB | inputs/001/real-references/reference.jpg | M3 | E4 | "
                f"{digest} | 밝은 여백 | 사진 무드만 | 제품·카피 전이 금지 | READY |\n"
                "| A01 | RAW_PRIMARY | USER | inputs/001/original-images/front.png",
            )
            asset_path.write_text(asset_text, encoding="utf-8")

            missing_link = validate_asset_map(root, "001")
            self.assertFalse(missing_link["ok"])
            self.assertTrue(
                any("direct URL row and ASSET_ID" in error for error in missing_link["errors"]),
                missing_link["errors"],
            )

            research_path = output_root / "web-research.md"
            research_path.write_text(
                research_path.read_text(encoding="utf-8").replace(
                    "| 상세 구조 | 텀블러 상세페이지 A | https://example.com/a | M3 | E4 | 훅과 장점 카드 | 구조만 | 상품 사실 | - |",
                    "| 상세 구조 | 텀블러 상세페이지 A | https://example.com/a | M3 | E4 | 훅과 장점 카드 | 구조만 | 상품 사실 | A02 |",
                ),
                encoding="utf-8",
            )
            linked = validate_asset_map(root, "001")
            self.assertTrue(linked["ok"], linked["errors"])

    def test_web_asset_links_require_unambiguous_rows_and_direct_image_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            write_complete_research(root)
            asset_path = write_complete_asset_map(root)

            reference_root = root / "inputs" / "001" / "real-references"
            first_path = reference_root / "reference-a.jpg"
            second_path = reference_root / "reference-b.jpg"
            first_path.write_bytes(b"downloaded-reference-a")
            second_path.write_bytes(b"downloaded-reference-b")
            first_sha = hashlib.sha256(first_path.read_bytes()).hexdigest()
            second_sha = hashlib.sha256(second_path.read_bytes()).hexdigest()
            asset_path.write_text(
                asset_path.read_text(encoding="utf-8").replace(
                    "| A01 | RAW_PRIMARY | USER | inputs/001/original-images/front.png",
                    "| A02 | REF_PHOTO | WEB | inputs/001/real-references/reference-a.jpg | M3 | E4 | "
                    f"{first_sha} | 밝은 여백 A | 사진 무드만 | 제품·카피 전이 금지 | READY |\n"
                    "| A03 | REF_PHOTO | WEB | inputs/001/real-references/reference-b.jpg | M3 | E4 | "
                    f"{second_sha} | 밝은 여백 B | 사진 무드만 | 제품·카피 전이 금지 | READY |\n"
                    "| A01 | RAW_PRIMARY | USER | inputs/001/original-images/front.png",
                ),
                encoding="utf-8",
            )

            research_path = output_root / "web-research.md"
            base_research = research_path.read_text(encoding="utf-8")
            ambiguous = base_research.replace(
                "| 상세 구조 | 텀블러 상세페이지 A | https://example.com/a | M3 | E4 | 훅과 장점 카드 | 구조만 | 상품 사실 | - |",
                "| 상세 구조 | 텀블러 상세페이지 A | https://cdn.example.com/photo.jpg | M3 | E4 | 훅과 장점 카드 | 구조만 | 상품 사실 | A02,A03 |",
            )
            research_path.write_text(ambiguous, encoding="utf-8")
            ambiguous_report = validate_asset_map(root, "001")
            self.assertFalse(ambiguous_report["ok"])
            self.assertTrue(
                any(
                    "exactly one ASSET_ID per canonical source row" in error
                    for error in ambiguous_report["errors"]
                ),
                ambiguous_report["errors"],
            )

            shared_direct_image = base_research.replace(
                "| 상세 구조 | 텀블러 상세페이지 A | https://example.com/a | M3 | E4 | 훅과 장점 카드 | 구조만 | 상품 사실 | - |",
                "| 상세 구조 | 텀블러 상세페이지 A | https://cdn.example.com/photo.jpg | M3 | E4 | 훅과 장점 카드 | 구조만 | 상품 사실 | A02 |",
            ).replace(
                "| 상세 구조 | 텀블러 상세페이지 B | https://example.com/b | M3 | E4 | 디테일 캡션 | 구조만 | 상품 사실 | - |",
                "| 상세 구조 | 텀블러 상세페이지 B | https://cdn.example.com/photo.jpg | M3 | E4 | 디테일 캡션 | 구조만 | 상품 사실 | A03 |",
            )
            research_path.write_text(shared_direct_image, encoding="utf-8")
            shared_report = validate_asset_map(root, "001")
            self.assertFalse(shared_report["ok"])
            self.assertTrue(
                any(
                    "different local SHA256 assets cannot share one direct image URL"
                    in error
                    for error in shared_report["errors"]
                ),
                shared_report["errors"],
            )

            repeated_html_page = shared_direct_image.replace(
                "https://cdn.example.com/photo.jpg", "https://example.com/listing"
            )
            research_path.write_text(repeated_html_page, encoding="utf-8")
            repeated_page_report = validate_asset_map(root, "001")
            self.assertTrue(repeated_page_report["ok"], repeated_page_report["errors"])

    def test_local_asset_roles_require_dedicated_input_folders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            write_complete_research(root)
            research_path = output_root / "web-research.md"
            research_path.write_text(
                research_path.read_text(encoding="utf-8").replace(
                    "| 상세 구조 | 텀블러 상세페이지 A | https://example.com/a | M3 | E4 | 훅과 장점 카드 | 구조만 | 상품 사실 | - |",
                    "| 상세 구조 | 텀블러 상세페이지 A | https://example.com/a | M3 | E4 | 훅과 장점 카드 | 구조만 | 상품 사실 | A02 |",
                ),
                encoding="utf-8",
            )
            asset_path = write_complete_asset_map(root)
            misplaced = root / "inputs" / "001" / "original-images" / "web.jpg"
            misplaced.write_bytes(b"web-match")
            digest = hashlib.sha256(misplaced.read_bytes()).hexdigest()
            asset_path.write_text(
                asset_path.read_text(encoding="utf-8").replace(
                    "| A01 | RAW_PRIMARY | USER | inputs/001/original-images/front.png",
                    "| A02 | WEB_MATCH | WEB | inputs/001/original-images/web.jpg | M2 | E3 | "
                    f"{digest} | 웹 외형 | 외형 보조 | 기능 전이 금지 | READY |\n"
                    "| A01 | RAW_PRIMARY | USER | inputs/001/original-images/front.png",
                ),
                encoding="utf-8",
            )
            rejected = validate_asset_map(root, "001")
            self.assertFalse(rejected["ok"])
            self.assertTrue(
                any("web-confirmed" in error for error in rejected["errors"]),
                rejected["errors"],
            )

            correct = root / "inputs" / "001" / "web-confirmed" / "web.jpg"
            misplaced.replace(correct)
            asset_path.write_text(
                asset_path.read_text(encoding="utf-8").replace(
                    "inputs/001/original-images/web.jpg",
                    "inputs/001/web-confirmed/web.jpg",
                ),
                encoding="utf-8",
            )
            accepted = validate_asset_map(root, "001")
            self.assertTrue(accepted["ok"], accepted["errors"])

    def test_local_asset_role_root_rejects_dotdot_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            asset_path = write_complete_asset_map(root)
            escaped = root / "inputs" / "001" / "evidence" / "escaped.png"
            escaped.write_bytes(b"escaped-raw-primary")
            digest = hashlib.sha256(escaped.read_bytes()).hexdigest()
            asset_path.write_text(
                asset_path.read_text(encoding="utf-8")
                .replace(
                    "inputs/001/original-images/front.png",
                    "inputs/001/original-images/../evidence/escaped.png",
                )
                .replace(hashlib.sha256(b"fixture").hexdigest(), digest),
                encoding="utf-8",
            )

            report = validate_asset_map(root, "001")
            self.assertFalse(report["ok"])
            self.assertTrue(
                any("canonical role root" in error for error in report["errors"]),
                report["errors"],
            )

    def test_local_asset_role_root_rejects_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            asset_path = write_complete_asset_map(root)
            target = root / "inputs" / "001" / "evidence" / "linked.png"
            target.write_bytes(b"linked-raw-primary")
            link = root / "inputs" / "001" / "original-images" / "linked.png"
            link.symlink_to(target)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            asset_path.write_text(
                asset_path.read_text(encoding="utf-8")
                .replace("inputs/001/original-images/front.png", str(link))
                .replace(hashlib.sha256(b"fixture").hexdigest(), digest),
                encoding="utf-8",
            )

            report = validate_asset_map(root, "001")
            self.assertFalse(report["ok"])
            self.assertTrue(
                any("canonical role root" in error for error in report["errors"]),
                report["errors"],
            )

    def test_local_asset_rejects_symlinked_canonical_role_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            original_root = root / "inputs" / "001" / "original-images"
            evidence_root = root / "inputs" / "001" / "evidence"
            (original_root / ".gitkeep").unlink()
            original_root.rmdir()
            original_root.symlink_to(evidence_root, target_is_directory=True)
            write_complete_asset_map(root)

            report = validate_asset_map(root, "001")
            self.assertFalse(report["ok"])
            self.assertTrue(
                any(
                    "canonical role root contains a symlink" in error
                    for error in report["errors"]
                ),
                report["errors"],
            )

    def test_asset_lineage_rejects_reference_as_product_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            asset_path = write_complete_asset_map(root)
            invalid = asset_path.read_text(encoding="utf-8").replace(
                "| A01 | RAW_PRIMARY | USER |",
                "| A01 | REF_PHOTO | USER |",
            )
            asset_path.write_text(invalid, encoding="utf-8")
            report = validate_asset_map(root, "001")
            self.assertFalse(report["ok"])
            self.assertTrue(
                any("cannot use REF_PHOTO" in error for error in report["errors"]),
                report["errors"],
            )

    def test_asset_lineage_rejects_ai_as_raw_and_copy_fact_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            asset_path = write_complete_asset_map(root)

            ai_raw = asset_path.read_text(encoding="utf-8").replace(
                "| A01 | RAW_PRIMARY | USER |",
                "| A01 | RAW_PRIMARY | AI |",
            )
            asset_path.write_text(ai_raw, encoding="utf-8")
            rejected = validate_asset_map(root, "001")
            self.assertFalse(rejected["ok"])
            self.assertTrue(
                any("ORIGIN=USER" in error for error in rejected["errors"]),
                rejected["errors"],
            )

            write_complete_asset_map(root)
            ledger_path = output_root / "fact-ledger.md"
            ledger_path.write_text(
                COMPLETE_FACT_LEDGER.replace(
                    "| 04 | 실측 | 크기 | 실측 | 크기를 확인하세요 | 사용자 제공 크기입니다 | 치수 카드 | 없음 | F04 |",
                    "| 04 | 실측 | 크기 | 실측 | 크기를 확인하세요 | 사용자 제공 크기입니다 | 치수 카드 | 없음 | F03 |",
                ),
                encoding="utf-8",
            )
            rejected = validate_asset_map(root, "001")
            self.assertFalse(rejected["ok"])
            self.assertTrue(
                any("copy manifest Fact IDs" in error for error in rejected["errors"]),
                rejected["errors"],
            )

    def test_plan_review_rejects_incomplete_research(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, output_root = initialize(root, 1)
            (input_root / "product-info.md").write_text(
                COMPLETE_PRODUCT_INFO, encoding="utf-8"
            )
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            write_complete_asset_map(root)

            with self.assertRaisesRegex(ValueError, "research/input validation failed"):
                build_plan_review(root, "001")

    def test_unknown_fact_cannot_be_smuggled_from_forbidden_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            plan_text = COMPLETE_PLAN_GATE.replace(
                "| 04 | FIT_SIZE | 착용감·실측 사이즈 | FIT+SIZE_DIAGRAM+MEASUREMENTS | 실제 크기는 얼마인가 | F04 |",
                "| 04 | FIT_SIZE | 착용감·실측 사이즈 | FIT+SIZE_DIAGRAM+MEASUREMENTS | 실제 크기는 얼마인가 | F99 |",
            )
            ledger_text = COMPLETE_FACT_LEDGER.replace(
                "| 04 | 실측 | 크기 | 실측 | 크기를 확인하세요 | 사용자 제공 크기입니다 | 치수 카드 | 없음 | F04 |",
                "| 04 | 실측 | 크기 | 실측 | 크기를 확인하세요 | 사용자 제공 크기입니다 | 치수 카드 | 없음 | F99 |",
            ).replace(
                "- 근거 없는 효능", "- 근거 없는 효능\n- F99"
            )
            (output_root / "plan-gate.md").write_text(plan_text, encoding="utf-8")
            (output_root / "fact-ledger.md").write_text(ledger_text, encoding="utf-8")
            asset_path = write_complete_asset_map(root)
            asset_path.write_text(
                asset_path.read_text(encoding="utf-8").replace("F04", "F99"),
                encoding="utf-8",
            )

            plan_report = validate_plan(root, "001")
            asset_report = validate_asset_map(root, "001")
            self.assertFalse(plan_report["ok"])
            self.assertFalse(asset_report["ok"])
            self.assertTrue(
                any("absent from the allowed-facts table" in error for error in plan_report["errors"]),
                plan_report["errors"],
            )
            self.assertTrue(
                any("unknown Fact IDs" in error for error in asset_report["errors"]),
                asset_report["errors"],
            )

    def test_production_docs_reject_unsupported_numeric_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER.replace(
                    "사용자 제공 크기입니다", "사용자 제공 크기 20cm입니다"
                ),
                encoding="utf-8",
            )
            write_complete_production_docs(root)
            report = validate_production_docs(root, "001")
            self.assertFalse(report["ok"])
            self.assertTrue(
                any("numeric/unit claims" in error for error in report["errors"]),
                report["errors"],
            )

    def test_production_docs_canonicalizes_centimeter_aliases(self) -> None:
        equivalent_pairs = (
            ("50cm", "50 센티미터"),
            ("50 센티미터", "50센치"),
            ("50센치", "50㎝"),
            ("50 CM", "50cm"),
        )
        for allowed_value, copy_value in equivalent_pairs:
            with self.subTest(allowed=allowed_value, copy=copy_value):
                with tempfile.TemporaryDirectory() as temp_dir:
                    root = Path(temp_dir)
                    _, output_root = initialize(root, 1)
                    (output_root / "plan-gate.md").write_text(
                        COMPLETE_PLAN_GATE, encoding="utf-8"
                    )
                    ledger = COMPLETE_FACT_LEDGER.replace(
                        "| F04 | 사용자 제공 크기 |",
                        f"| F04 | 전체 길이 {allowed_value} |",
                    ).replace(
                        "사용자 제공 크기입니다",
                        f"전체 길이 {copy_value}입니다",
                    )
                    (output_root / "fact-ledger.md").write_text(
                        ledger, encoding="utf-8"
                    )
                    write_complete_production_docs(root)
                    report = validate_production_docs(root, "001")
                    self.assertTrue(report["ok"], report["errors"])

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            ledger = COMPLETE_FACT_LEDGER.replace(
                "| F04 | 사용자 제공 크기 |",
                "| F04 | 전체 길이 50cm |",
            ).replace(
                "사용자 제공 크기입니다",
                "전체 길이 51 센티미터입니다",
            )
            (output_root / "fact-ledger.md").write_text(ledger, encoding="utf-8")
            write_complete_production_docs(root)
            report = validate_production_docs(root, "001")
            self.assertFalse(report["ok"])
            self.assertTrue(
                any("51cm" in error for error in report["errors"]), report["errors"]
            )

    def test_plan_gate_accepts_five_distinct_information_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            five_pages = (
                COMPLETE_PLAN_GATE.replace("목표 장수: 7", "목표 장수: 5")
                .replace("정보 단위 수: 7", "정보 단위 수: 5")
                .replace("선정 장수: 7", "선정 장수: 5")
                .replace(
                    "| 03 | FEATURE_EVIDENCE | 핵심 기능과 근거 | FEATURE+EVIDENCE+BOUNDARY | 기능 근거는 무엇인가 | F03 | I03 | A1 | 기능 근거와 허용 범위 | 기능 확인 | SHOT03 | SCENE03 | LAYOUT03 | 실측으로 | 정지 |",
                    "| 03 | FIT_STRUCTURE | 착용 구조 | FIT+STRUCTURE+DETAIL | 착용 구조는 어떻게 다른가 | F03 | I03 | A1 | 착용부 구조 확대 | 구조 확인 | SHOT03 | SCENE03 | LAYOUT03 | 실측으로 | 정지 |",
                )
                .replace(
                    "| 04 | FIT_SIZE | 착용감·실측 사이즈 | FIT+SIZE_DIAGRAM+MEASUREMENTS | 실제 크기는 얼마인가 | F04 | I04 | A2 | 자를 댄 실측 도식 | 실측 안내 | SHOT04 | SCENE04 | LAYOUT04 | 소재로 | 영상 |",
                    "| 04 | MEASURED_SIZE | 실측 사이즈 | SIZE_DIAGRAM+MEASUREMENTS | 실제 크기는 얼마인가 | F04 | I04 | A2 | 자를 댄 실측 도식 | 실측 안내 | SHOT04 | SCENE04 | LAYOUT04 | 사용 상황으로 | 영상 |",
                )
                .replace(
                    "| 05 | MATERIAL_SPEC | 소재·제품 사양 | MATERIAL+SPEC+DETAIL | 어떤 소재인가 | F05 | I05 | A3 | 소재 확대와 사양 표 | 소재 정보 | SHOT05 | SCENE05 | LAYOUT05 | 사용법으로 | GIF |",
                    "| 05 | SITUATION_USE | 사용 상황·구매 안내 | USE_SCENE+USAGE_INFO+CTA | 언제 사용하는가 | F05 | I05 | A3 | 운전 중 실제 사용 장면과 CTA | 사용 상황 | SHOT05 | SCENE05 | LAYOUT05 | 종료 | GIF |",
                )
            )
            five_pages = "\n".join(
                line
                for line in five_pages.splitlines()
                if not line.startswith("| 06 |") and not line.startswith("| 07 |")
            )
            (output_root / "plan-gate.md").write_text(five_pages, encoding="utf-8")
            report = validate_plan(root, "001")
            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(report["rows"], ["01", "02", "03", "04", "05"])

    def test_plan_gate_accepts_three_pages_when_only_three_information_units_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            three_pages = (
                COMPLETE_PLAN_GATE.replace("목표 장수: 7", "목표 장수: 3")
                .replace("정보 단위 수: 7", "정보 단위 수: 3")
                .replace("선정 장수: 7", "선정 장수: 3")
                .replace(
                    "| 03 | FEATURE_EVIDENCE | 핵심 기능과 근거 | FEATURE+EVIDENCE+BOUNDARY | 기능 근거는 무엇인가 | F03 | I03 | A1 | 기능 근거와 허용 범위 | 기능 확인 | SHOT03 | SCENE03 | LAYOUT03 | 실측으로 | 정지 |",
                    "| 03 | EVIDENCE_CTA | 객관 근거·구매 안내 | SOURCE+VERIFIED_FACT+CTA | 기능 근거는 무엇인가 | F03 | I03 | A1 | 기능 근거와 허용 범위 및 CTA | 기능 확인 | SHOT03 | SCENE03 | LAYOUT03 | 종료 | 정지 |",
                )
            )
            three_pages = "\n".join(
                line
                for line in three_pages.splitlines()
                if not any(line.startswith(f"| {number:02d} |") for number in range(4, 8))
            )
            (output_root / "plan-gate.md").write_text(
                three_pages, encoding="utf-8"
            )
            report = validate_plan(root, "001")
            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(report["rows"], ["01", "02", "03"])

    def test_plan_gate_rejects_duplicate_ownership_fields(self) -> None:
        mutations = (
            ("INFO_ID", "| F06 | I06 |", "| F06 | I05 |", "duplicate INFO_ID"),
            (
                "PRIMARY_FACT",
                "| F06 | I06 |",
                "| F05 | I06 |",
                "duplicate PRIMARY_FACT",
            ),
            (
                "question",
                "어떻게 사용하는가",
                "어떤 소재인가",
                "duplicate 고유 구매 질문",
            ),
            ("SHOT_ID", "SHOT06", "SHOT05", "duplicate SHOT_ID"),
            ("SCENE_ID", "SCENE06", "SCENE05", "duplicate SCENE_ID"),
            ("LAYOUT_ID", "LAYOUT06", "LAYOUT05", "duplicate LAYOUT_ID"),
        )
        for name, before, after, expected_error in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                _, output_root = initialize(root, 1)
                (output_root / "fact-ledger.md").write_text(
                    COMPLETE_FACT_LEDGER, encoding="utf-8"
                )
                (output_root / "plan-gate.md").write_text(
                    COMPLETE_PLAN_GATE.replace(before, after), encoding="utf-8"
                )
                report = validate_plan(root, "001")
                self.assertFalse(report["ok"])
                self.assertTrue(
                    any(expected_error in error for error in report["errors"]),
                    report["errors"],
                )

    def test_plan_gate_allows_repeated_role_with_distinct_information(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            repeated_role = COMPLETE_PLAN_GATE.replace(
                "| 06 | HOW_TO_USE | 사용 방법 | STEP_BY_STEP+USE_SCENE |",
                "| 06 | MATERIAL_SPEC | 소재·제품 사양 | MATERIAL+SPEC+DETAIL |",
            )
            (output_root / "plan-gate.md").write_text(
                repeated_role, encoding="utf-8"
            )
            report = validate_plan(root, "001")
            self.assertTrue(report["ok"], report["errors"])

    def test_plan_gate_rejects_noncontinuous_pages_and_count_mismatches(self) -> None:
        mutations = (
            ("| 06 | HOW_TO_USE", "| 08 | HOW_TO_USE", "continuous from 01"),
            ("목표 장수: 7", "목표 장수: 6", "must match 선정 장수"),
            ("선정 장수: 7", "선정 장수: 6", "does not match the 7 selected"),
            ("정보 단위 수: 7", "정보 단위 수: 8", "must equal 선정 장수"),
        )
        for before, after, expected_error in mutations:
            with self.subTest(after=after), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                _, output_root = initialize(root, 1)
                (output_root / "fact-ledger.md").write_text(
                    COMPLETE_FACT_LEDGER, encoding="utf-8"
                )
                (output_root / "plan-gate.md").write_text(
                    COMPLETE_PLAN_GATE.replace(before, after), encoding="utf-8"
                )
                report = validate_plan(root, "001")
                self.assertFalse(report["ok"])
                self.assertTrue(
                    any(expected_error in error for error in report["errors"]),
                    report["errors"],
                )

    def test_plan_gate_requires_information_plus_cta_on_last_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            no_cta = COMPLETE_PLAN_GATE.replace(
                "| 07 | USE_CASE_CTA | 사용 장면·구매 안내 | USE_CASES+CAPTIONS+CTA |",
                "| 07 | USE_CASES | 다양한 사용 장면 | USE_CASES+CAPTIONS |",
            )
            (output_root / "plan-gate.md").write_text(no_cta, encoding="utf-8")
            report = validate_plan(root, "001")
            self.assertFalse(report["ok"])
            self.assertTrue(
                any("supported *_CTA role" in error for error in report["errors"]),
                report["errors"],
            )

    def test_function_priority_rejects_unverified_fact_and_accepts_explicit_none(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )

            unverified = COMPLETE_PLAN_GATE.replace(
                "기능 근거 Fact ID: F01", "기능 근거 Fact ID: F99"
            )
            (output_root / "plan-gate.md").write_text(unverified, encoding="utf-8")
            rejected = validate_plan(root, "001")
            self.assertFalse(rejected["ok"])
            self.assertTrue(
                any("not present in fact-ledger.md" in error for error in rejected["errors"]),
                rejected["errors"],
            )

            no_function = (
                COMPLETE_PLAN_GATE.replace(
                    "핵심 기능 소구: 휴대하기 쉬운 크기", "핵심 기능 소구: 없음"
                )
                .replace("기능 근거 Fact ID: F01", "기능 근거 Fact ID: 없음")
                .replace("기능 우선 적용 장: 01, 02", "기능 우선 적용 장: 없음")
                .replace(
                    "기능 없음 사유: 없음",
                    "기능 없음 사유: 확인 가능한 기능 정보가 아직 입력되지 않음",
                )
            )
            (output_root / "plan-gate.md").write_text(no_function, encoding="utf-8")
            accepted = validate_plan(root, "001")
            self.assertTrue(accepted["ok"], accepted["errors"])

    def test_function_priority_requires_early_pages_and_primary_fact_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _, output_root = initialize(root, 1)
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            late_only = COMPLETE_PLAN_GATE.replace(
                "기능 우선 적용 장: 01, 02", "기능 우선 적용 장: 05, 06"
            )
            (output_root / "plan-gate.md").write_text(late_only, encoding="utf-8")
            rejected = validate_plan(root, "001")
            self.assertFalse(rejected["ok"])
            self.assertTrue(
                any("must include page 01" in error for error in rejected["errors"]),
                rejected["errors"],
            )

            no_ownership = COMPLETE_PLAN_GATE.replace(
                "| 01 | PROBLEM_HOOK | 문제 후킹 | H1+BODY+PROBLEM_SCENE | 불편은 무엇인가 | F01 |",
                "| 01 | PROBLEM_HOOK | 문제 후킹 | H1+BODY+PROBLEM_SCENE | 불편은 무엇인가 | F10 |",
            )
            (output_root / "plan-gate.md").write_text(no_ownership, encoding="utf-8")
            rejected = validate_plan(root, "001")
            self.assertFalse(rejected["ok"])
            self.assertTrue(
                any("must use a 기능 근거 Fact ID" in error for error in rejected["errors"]),
                rejected["errors"],
            )

    def test_comfy_receipts_require_live_probe_freshness_and_workflow_hash(self) -> None:
        class ComfyStatsHandler(BaseHTTPRequestHandler):
            os_value = "test"
            payload_override = None

            def do_GET(self) -> None:
                if self.path != "/system_stats":
                    self.send_error(404)
                    return
                response_payload = self.payload_override or {
                    "system": {"os": self.os_value},
                    "devices": [],
                }
                body = json.dumps(response_payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize(root, 1)
            server = ThreadingHTTPServer(("127.0.0.1", 0), ComfyStatsHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                endpoint = f"http://127.0.0.1:{server.server_address[1]}"
                payload = connected_receipt(endpoint, timeout=2.0)
                receipt_path = write_receipt(root, "001", payload)
                receipt_value = receipt_path.relative_to(root.resolve()).as_posix()
                self.assertEqual(
                    validate_comfy_receipt(root, "001", "CONNECTED", receipt_value),
                    [],
                )
                ComfyStatsHandler.payload_override = {"system": {"os": "test"}}
                with self.assertRaisesRegex(ValueError, "system object and devices list"):
                    connected_receipt(endpoint, timeout=2.0)
                ComfyStatsHandler.payload_override = None
                ComfyStatsHandler.os_value = "different-endpoint-identity"
                changed_identity_errors = validate_comfy_receipt(
                    root, "001", "CONNECTED", receipt_value
                )
                self.assertTrue(
                    any(
                        "endpoint identity changed" in error
                        for error in changed_identity_errors
                    ),
                    changed_identity_errors,
                )
                ComfyStatsHandler.os_value = "test"
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2.0)

            receipt_path.write_text(
                json.dumps(payload, indent=2) + "\n", encoding="utf-8"
            )
            offline_errors = validate_comfy_receipt(
                root, "001", "CONNECTED", receipt_value
            )
            self.assertTrue(
                any("live /system_stats re-probe" in error for error in offline_errors),
                offline_errors,
            )

            manual_payload = dict(payload)
            manual_payload["tool"] = "manual-self-attestation"
            manual_payload["receipt_id"] = receipt_id_for(manual_payload)
            receipt_path.write_text(
                json.dumps(manual_payload, indent=2) + "\n", encoding="utf-8"
            )
            marker_errors = validate_comfy_receipt(
                root, "001", "CONNECTED", receipt_value
            )
            self.assertTrue(
                any("approved receipt helper marker" in error for error in marker_errors),
                marker_errors,
            )

            stale_payload = dict(payload)
            stale_payload["checked_at"] = (
                datetime.now(timezone.utc) - timedelta(hours=25)
            ).isoformat(timespec="seconds")
            stale_payload["receipt_id"] = receipt_id_for(stale_payload)
            receipt_path.write_text(
                json.dumps(stale_payload, indent=2) + "\n", encoding="utf-8"
            )
            stale_errors = validate_comfy_receipt(
                root, "001", "CONNECTED", receipt_value
            )
            self.assertTrue(
                any("older than 24 hours" in error for error in stale_errors),
                stale_errors,
            )

            workflow_path = (
                root / "inputs" / "001" / "evidence" / "workflow.json"
            )
            workflow_path.write_text(
                json.dumps({"hello": "world"}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "API prompt graph|UI workflow"):
                workflow_receipt(root, "001", workflow_path.relative_to(root))
            workflow_path.write_text(
                json.dumps(
                    {
                        "nodes": [{"id": 1, "type": "KSampler"}],
                        "links": [],
                    }
                ),
                encoding="utf-8",
            )
            ui_workflow_payload = workflow_receipt(
                root, "001", workflow_path.relative_to(root)
            )
            self.assertEqual(ui_workflow_payload["workflow_kind"], "UI_WORKFLOW")
            workflow_path.write_text(
                json.dumps({"1": {"class_type": "KSampler", "inputs": {}}}),
                encoding="utf-8",
            )
            workflow_payload = workflow_receipt(
                root, "001", workflow_path.relative_to(root)
            )
            workflow_receipt_path = write_receipt(root, "001", workflow_payload)
            workflow_value = workflow_receipt_path.relative_to(root.resolve()).as_posix()
            self.assertEqual(
                validate_comfy_receipt(
                    root, "001", "WORKFLOW_PROVIDED", workflow_value
                ),
                [],
            )
            future_workflow_payload = dict(workflow_payload)
            future_workflow_payload["checked_at"] = (
                datetime.now(timezone.utc) + timedelta(days=1)
            ).isoformat(timespec="seconds")
            future_workflow_payload["receipt_id"] = receipt_id_for(
                future_workflow_payload
            )
            workflow_receipt_path.write_text(
                json.dumps(future_workflow_payload, indent=2) + "\n",
                encoding="utf-8",
            )
            future_workflow_errors = validate_comfy_receipt(
                root, "001", "WORKFLOW_PROVIDED", workflow_value
            )
            self.assertTrue(
                any(
                    "checked_at is implausibly in the future" in error
                    for error in future_workflow_errors
                ),
                future_workflow_errors,
            )
            workflow_receipt_path.write_text(
                json.dumps(workflow_payload, indent=2) + "\n", encoding="utf-8"
            )
            workflow_path.write_text(
                json.dumps({"1": {"class_type": "Changed", "inputs": {}}}),
                encoding="utf-8",
            )
            changed_errors = validate_comfy_receipt(
                root, "001", "WORKFLOW_PROVIDED", workflow_value
            )
            self.assertTrue(
                any("SHA256" in error for error in changed_errors), changed_errors
            )

    def test_comfy_project_paths_reject_symlinked_canonical_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_two_evidence = root / "inputs" / "002" / "evidence"
            project_two_evidence.mkdir(parents=True)
            (root / "outputs" / "001").mkdir(parents=True)
            (root / "outputs" / "002").mkdir(parents=True)
            workflow_path = project_two_evidence / "workflow.json"
            workflow_path.write_text(
                json.dumps({"1": {"class_type": "KSampler", "inputs": {}}}),
                encoding="utf-8",
            )
            workflow_payload = workflow_receipt(
                root, "002", workflow_path.relative_to(root)
            )
            receipt_path = write_receipt(root, "002", workflow_payload)

            project_one_evidence = root / "inputs" / "001" / "evidence"
            project_one_evidence.parent.mkdir(parents=True)
            project_one_evidence.symlink_to(
                project_two_evidence, target_is_directory=True
            )
            with self.assertRaisesRegex(ValueError, "symlink"):
                project_relative_file(
                    root,
                    "001",
                    "inputs/001/evidence/workflow.json",
                    "ComfyUI workflow",
                )
            receipt_errors = validate_comfy_receipt(
                root,
                "001",
                "WORKFLOW_PROVIDED",
                "inputs/001/evidence/" + receipt_path.name,
            )
            self.assertTrue(
                any("symlink" in error for error in receipt_errors), receipt_errors
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "inputs" / "001" / "evidence").mkdir(parents=True)
            project_two_output = root / "outputs" / "002"
            project_two_output.mkdir(parents=True)
            project_one_output = root / "outputs" / "001"
            project_one_output.parent.mkdir(parents=True, exist_ok=True)
            project_one_output.symlink_to(project_two_output, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                project_relative_file(
                    root, "001", "outputs/001/receipt.json", "ComfyUI receipt"
                )

    def test_plan_review_html_and_static_generation_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, output_root = initialize(root, 1)
            (input_root / "product-info.md").write_text(
                COMPLETE_PRODUCT_INFO, encoding="utf-8"
            )
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            write_complete_research(root)
            write_complete_production_docs(root)
            write_complete_asset_map(root)
            (output_root / "motion-plan.md").write_text(
                COMPLETE_MOTION_PLAN, encoding="utf-8"
            )
            (output_root / "video-plan.md").write_text(
                COMPLETE_VIDEO_PLAN, encoding="utf-8"
            )

            review_path = build_plan_review(root, "001")
            review_text = review_path.read_text(encoding="utf-8")
            self.assertIn('data-review-kind="coupang-detail-page-plan"', review_text)
            self.assertIn('data-page-count-decision="완료"', review_text)
            self.assertIn('data-functional-priority="완료"', review_text)
            self.assertIn('data-asset-lineage="complete"', review_text)
            self.assertRegex(review_text, r'data-source-digest="[0-9a-f]{64}"')
            self.assertIn("7장 기획 검토", review_text)
            self.assertIn("7장 주제와 구성", review_text)
            self.assertEqual(review_text.count('class="page-card"'), 7)
            self.assertIn("기능을 먼저 보는 설계", review_text)
            self.assertIn("휴대하기 쉬운 크기", review_text)
            for role_id in (
                "PROBLEM_HOOK",
                "PRODUCT_INTRO",
                "FEATURE_EVIDENCE",
                "FIT_SIZE",
                "MATERIAL_SPEC",
                "HOW_TO_USE",
                "USE_CASE_CTA",
            ):
                self.assertIn(f'data-role="{role_id}"', review_text)

            blocked = validate_generation_gate(root, "001", "static")
            self.assertFalse(blocked["ok"])
            self.assertTrue(
                any("not approved" in error for error in blocked["errors"]),
                blocked["errors"],
            )
            self.assertTrue(
                any("APPROVE_PLAN" in error for error in blocked["errors"]),
                blocked["errors"],
            )

            (output_root / "generation-gate.md").write_text(
                approved_gate_for(review_path), encoding="utf-8"
            )
            ready = validate_generation_gate(root, "001", "static")
            self.assertTrue(ready["ok"], ready["errors"])

            base_gate = approved_gate_for(review_path)
            contradictory_approval = base_gate.replace(
                "2026-07-13 · APPROVE_PLAN · ANSWER=1",
                "2026-07-13 · 사용자가 기획을 거절함",
            )
            (output_root / "generation-gate.md").write_text(
                contradictory_approval, encoding="utf-8"
            )
            rejected_approval = validate_generation_gate(root, "001", "static")
            self.assertFalse(rejected_approval["ok"])
            self.assertTrue(
                any("APPROVE_PLAN" in error for error in rejected_approval["errors"]),
                rejected_approval["errors"],
            )

            wrong_project_gate = base_gate.replace(
                "프로젝트 번호: 001", "프로젝트 번호: 999"
            )
            (output_root / "generation-gate.md").write_text(
                wrong_project_gate, encoding="utf-8"
            )
            wrong_project = validate_generation_gate(root, "001", "static")
            self.assertFalse(wrong_project["ok"])
            self.assertTrue(
                any("project number" in error for error in wrong_project["errors"]),
                wrong_project["errors"],
            )

            duplicate_field_gate = base_gate + "\n제작 범위: STATIC_ONLY\n"
            (output_root / "generation-gate.md").write_text(
                duplicate_field_gate, encoding="utf-8"
            )
            duplicate_field = validate_generation_gate(root, "001", "static")
            self.assertFalse(duplicate_field["ok"])
            self.assertTrue(
                any(
                    "exactly one '제작 범위:'" in error
                    for error in duplicate_field["errors"]
                ),
                duplicate_field["errors"],
            )

            wrong_review_name_gate = base_gate.replace(
                "기획 리뷰 HTML: `plan-review.html`",
                "기획 리뷰 HTML: `other-review.html`",
            )
            (output_root / "generation-gate.md").write_text(
                wrong_review_name_gate, encoding="utf-8"
            )
            wrong_review_name = validate_generation_gate(root, "001", "static")
            self.assertFalse(wrong_review_name["ok"])
            self.assertTrue(
                any(
                    "canonical plan-review.html" in error
                    for error in wrong_review_name["errors"]
                ),
                wrong_review_name["errors"],
            )

            free_text_motion_gate = base_gate.replace(
                "선정 모션 ID: 해당 없음",
                "선정 모션 ID: 해당 없음 · 사용자 거절",
            )
            (output_root / "generation-gate.md").write_text(
                free_text_motion_gate, encoding="utf-8"
            )
            free_text_motion = validate_generation_gate(root, "001", "static")
            self.assertFalse(free_text_motion["ok"])
            self.assertTrue(
                any(
                    "comma-separated motion-NN list" in error
                    for error in free_text_motion["errors"]
                ),
                free_text_motion["errors"],
            )

            stale_environment_approval_gate = base_gate.replace(
                "최종 생성 승인 기록: 2026-07-13 · APPROVE_EXECUTION · "
                "SCOPE=STATIC_ONLY · MOTION=NONE · COMFY=NOT_REQUIRED",
                "최종 생성 승인 기록: 2026-07-13 · APPROVE_EXECUTION · "
                "SCOPE=STATIC_ONLY · MOTION=NONE · COMFY=CONNECTED",
            )
            (output_root / "generation-gate.md").write_text(
                stale_environment_approval_gate, encoding="utf-8"
            )
            stale_environment_approval = validate_generation_gate(
                root, "001", "static"
            )
            self.assertFalse(stale_environment_approval["ok"])
            self.assertTrue(
                any(
                    "final generation approval record COMFY" in error
                    for error in stale_environment_approval["errors"]
                ),
                stale_environment_approval["errors"],
            )

            unknown_motion_gate = gate_for_selection(
                review_path,
                "STATIC_PLUS_MOTION_HANDOFF",
                ("motion-99",),
                "HANDOFF_ONLY",
                "승인",
            )
            (output_root / "generation-gate.md").write_text(
                unknown_motion_gate, encoding="utf-8"
            )
            unknown_motion = validate_generation_gate(root, "001", "static")
            self.assertFalse(unknown_motion["ok"])
            self.assertTrue(
                any(
                    "selected motion planning contract is invalid" in error
                    for error in unknown_motion["errors"]
                ),
                unknown_motion["errors"],
            )

            wrong_format_gate = gate_for_selection(
                review_path,
                "STATIC_PLUS_GIF",
                ("motion-01",),
                "NOT_REQUIRED",
                "승인",
            )
            (output_root / "generation-gate.md").write_text(
                wrong_format_gate, encoding="utf-8"
            )
            wrong_format = validate_generation_gate(root, "001", "static")
            self.assertFalse(wrong_format["ok"])
            self.assertTrue(
                any("must all declare a GIF" in error for error in wrong_format["errors"]),
                wrong_format["errors"],
            )

            ai_without_receipt_gate = gate_for_selection(
                review_path,
                "STATIC_PLUS_GIF",
                ("motion-02",),
                "NOT_REQUIRED",
                "승인",
            )
            (output_root / "generation-gate.md").write_text(
                ai_without_receipt_gate, encoding="utf-8"
            )
            ai_without_receipt = validate_generation_gate(root, "001", "static")
            self.assertFalse(ai_without_receipt["ok"])
            self.assertTrue(
                any("AI_ILLUSTRATION" in error for error in ai_without_receipt["errors"]),
                ai_without_receipt["errors"],
            )

            (output_root / "generation-gate.md").write_text(
                base_gate, encoding="utf-8"
            )

            tampered_html = review_path.read_text(encoding="utf-8").replace(
                "불편을 확인하세요", "승인 뒤 바뀐 카드", 1
            )
            review_path.write_text(tampered_html, encoding="utf-8")
            tampered = validate_generation_gate(root, "001", "static")
            self.assertFalse(tampered["ok"])
            self.assertTrue(
                any("page-card content was modified" in error for error in tampered["errors"]),
                tampered["errors"],
            )

            review_path = build_plan_review(root, "001")
            (output_root / "generation-gate.md").write_text(
                approved_gate_for(review_path), encoding="utf-8"
            )
            (output_root / "web-research.md").write_text(
                COMPLETE_WEB_RESEARCH.replace("조사 상태: 완료", "조사 상태: 미완료"),
                encoding="utf-8",
            )
            research_stale = validate_generation_gate(root, "001", "static")
            self.assertFalse(research_stale["ok"])
            self.assertTrue(
                any("research/input validation failed" in error for error in research_stale["errors"]),
                research_stale["errors"],
            )

            write_complete_research(root)
            review_path = build_plan_review(root, "001")
            (output_root / "generation-gate.md").write_text(
                approved_gate_for(review_path), encoding="utf-8"
            )
            (output_root / "prompt-set.md").write_text(
                "승인 뒤 바뀐 프롬프트", encoding="utf-8"
            )
            stale = validate_generation_gate(root, "001", "static")
            self.assertFalse(stale["ok"])
            self.assertTrue(
                any("changed after" in error for error in stale["errors"]),
                stale["errors"],
            )

    def test_approval_records_reject_future_dates(self) -> None:
        gate_fields = {
            "사용자 승인 기록": "2999-01-01 · APPROVE_PLAN · ANSWER=1",
            "환경 선택 기록": (
                "2999-01-01 · SELECT_ENV · SCOPE=STATIC_ONLY · "
                "MOTION=NONE · COMFY=NOT_REQUIRED"
            ),
            "최종 생성 승인 기록": (
                "2999-01-01 · APPROVE_EXECUTION · SCOPE=STATIC_ONLY · "
                "MOTION=NONE · COMFY=NOT_REQUIRED"
            ),
        }

        errors = validate_approval_records(
            gate_fields, "STATIC_ONLY", set(), "NOT_REQUIRED"
        )

        self.assertTrue(
            any("future in Asia/Seoul" in error for error in errors), errors
        )

    def test_approval_records_require_chronological_stage_order(self) -> None:
        gate_fields = {
            "사용자 승인 기록": "2026-07-13 · APPROVE_PLAN · ANSWER=1",
            "환경 선택 기록": (
                "2026-07-12 · SELECT_ENV · SCOPE=STATIC_ONLY · "
                "MOTION=NONE · COMFY=NOT_REQUIRED"
            ),
            "최종 생성 승인 기록": (
                "2026-07-11 · APPROVE_EXECUTION · SCOPE=STATIC_ONLY · "
                "MOTION=NONE · COMFY=NOT_REQUIRED"
            ),
        }

        errors = validate_approval_records(
            gate_fields, "STATIC_ONLY", set(), "NOT_REQUIRED"
        )

        self.assertIn(
            "approval record dates must satisfy plan <= environment <= final",
            errors,
        )

    def test_motion_generation_requires_verified_capture_and_allows_no_comfy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, output_root = initialize(root, 1)
            (input_root / "product-info.md").write_text(
                COMPLETE_PRODUCT_INFO, encoding="utf-8"
            )
            (output_root / "plan-gate.md").write_text(
                COMPLETE_PLAN_GATE, encoding="utf-8"
            )
            (output_root / "fact-ledger.md").write_text(
                COMPLETE_FACT_LEDGER, encoding="utf-8"
            )
            write_complete_research(root)
            write_complete_production_docs(root)
            write_complete_asset_map(root)
            (output_root / "motion-plan.md").write_text(
                COMPLETE_MOTION_PLAN, encoding="utf-8"
            )
            (output_root / "video-plan.md").write_text(
                COMPLETE_VIDEO_PLAN, encoding="utf-8"
            )
            review_path = build_plan_review(root, "001")
            handoff_gate = gate_for_selection(
                review_path,
                "STATIC_PLUS_MOTION_HANDOFF",
                ("motion-01",),
                "HANDOFF_ONLY",
                "승인",
            )
            (output_root / "generation-gate.md").write_text(
                handoff_gate, encoding="utf-8"
            )
            blocked = validate_generation_gate(root, "001", "motion")
            self.assertFalse(blocked["ok"])
            handoff_ready = validate_generation_gate(root, "001", "handoff")
            self.assertTrue(handoff_ready["ok"], handoff_ready["errors"])

            handoff_without_separate_approval = handoff_gate.replace(
                "GIF·영상 생성 승인: 승인",
                "GIF·영상 생성 승인: 미승인",
            )
            (output_root / "generation-gate.md").write_text(
                handoff_without_separate_approval, encoding="utf-8"
            )
            handoff_without_approval = validate_generation_gate(
                root, "001", "handoff"
            )
            self.assertFalse(handoff_without_approval["ok"])
            self.assertTrue(
                any(
                    "missing its separate approval" in error
                    for error in handoff_without_approval["errors"]
                ),
                handoff_without_approval["errors"],
            )

            connected_without_receipt = gate_for_selection(
                review_path,
                "STATIC_PLUS_VIDEO",
                ("motion-01",),
                "CONNECTED",
                "승인",
            )
            (output_root / "generation-gate.md").write_text(
                connected_without_receipt, encoding="utf-8"
            )
            blocked_connected = validate_generation_gate(root, "001", "motion")
            self.assertFalse(blocked_connected["ok"])
            self.assertTrue(
                any("evidence JSON" in error for error in blocked_connected["errors"]),
                blocked_connected["errors"],
            )

            write_verified_real_demo(root)
            review_path = build_plan_review(root, "001")
            real_capture_gate = gate_for_selection(
                review_path,
                "STATIC_PLUS_VIDEO",
                ("motion-01",),
                "NOT_REQUIRED",
                "승인",
            )
            (output_root / "generation-gate.md").write_text(
                real_capture_gate, encoding="utf-8"
            )
            motion_ready = validate_generation_gate(root, "001", "motion")
            self.assertTrue(motion_ready["ok"], motion_ready["errors"])

            motion_without_static_approval = real_capture_gate.replace(
                "정적 이미지 생성 승인: 승인",
                "정적 이미지 생성 승인: 미승인",
            )
            (output_root / "generation-gate.md").write_text(
                motion_without_static_approval, encoding="utf-8"
            )
            motion_without_static = validate_generation_gate(
                root, "001", "motion"
            )
            self.assertFalse(motion_without_static["ok"])
            self.assertTrue(
                any(
                    "static image generation is not approved" in error
                    for error in motion_without_static["errors"]
                ),
                motion_without_static["errors"],
            )

    def test_check_rejects_blank_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize(root, 1)
            report = check(root, "001")
            self.assertFalse(report["ok"])
            self.assertTrue(report["errors"])

    def test_check_accepts_complete_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, output_root = initialize(root, 1)
            (input_root / "product-info.md").write_text(
                COMPLETE_PRODUCT_INFO, encoding="utf-8"
            )
            (output_root / "web-research.md").write_text(
                COMPLETE_WEB_RESEARCH, encoding="utf-8"
            )
            (output_root / "detail-page-analysis.md").write_text(
                COMPLETE_DETAIL_PAGE_ANALYSIS, encoding="utf-8"
            )
            (input_root / "original-images" / "front.png").write_bytes(b"fixture")
            report = check(root, "001")
            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(len(report["original_images"]), 1)

    def test_check_requires_conversation_original_to_be_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, output_root = initialize(root, 1)
            (input_root / "product-info.md").write_text(
                COMPLETE_PRODUCT_INFO, encoding="utf-8"
            )
            (output_root / "web-research.md").write_text(
                COMPLETE_WEB_RESEARCH, encoding="utf-8"
            )
            (output_root / "detail-page-analysis.md").write_text(
                COMPLETE_DETAIL_PAGE_ANALYSIS, encoding="utf-8"
            )
            report = check(root, "001", conversation_original_count=1)
            self.assertFalse(report["ok"])
            self.assertTrue(
                any("persist at least one original" in error for error in report["errors"]),
                report["errors"],
            )
            self.assertEqual(report["conversation_original_count"], 1)
            self.assertFalse(report["original_images"])

    def test_check_rejects_project_without_completed_web_research(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, _ = initialize(root, 1)
            (input_root / "product-info.md").write_text(
                COMPLETE_PRODUCT_INFO, encoding="utf-8"
            )
            (input_root / "original-images" / "front.png").write_bytes(b"fixture")
            report = check(root, "001")
            self.assertFalse(report["ok"])
            self.assertTrue(
                any("web research" in error for error in report["errors"]),
                report["errors"],
            )

    def test_check_rejects_more_than_five_conversation_originals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize(root, 1)
            with self.assertRaises(ValueError):
                check(root, "001", conversation_original_count=6)

    def test_prepare_is_idempotent_and_preserves_product_info(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_root, _, created = prepare(root, 1)
            self.assertTrue(created)
            info_path = input_root / "product-info.md"
            info_path.write_text("private facts", encoding="utf-8")
            _, _, created_again = prepare(root, 1)
            self.assertFalse(created_again)
            self.assertEqual(info_path.read_text(encoding="utf-8"), "private facts")
            self.assertTrue((root / "outputs" / "001" / "font-plan.md").is_file())
            self.assertTrue((root / "outputs" / "001" / "video-plan.md").is_file())
            self.assertTrue(
                (root / "outputs" / "001" / "generation-gate.md").is_file()
            )

    def test_prepare_rejects_directories_in_required_file_slots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            product_info = root / "inputs" / "001" / "product-info.md"
            product_info.mkdir(parents=True)
            with self.assertRaisesRegex(IsADirectoryError, "expected project file"):
                prepare(root, 1)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            web_research = root / "outputs" / "001" / "web-research.md"
            web_research.mkdir(parents=True)
            with self.assertRaisesRegex(IsADirectoryError, "expected project file"):
                prepare(root, 1)

    def test_pillow_runtime_is_isolated_by_python_abi(self) -> None:
        self.assertIn(
            sys.implementation.cache_tag,
            runtime_site_packages().name,
        )

    def test_validate_rejects_truncated_png_with_claimed_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            final = Path(temp_dir)
            fake_header = (
                b"\x89PNG\r\n\x1a\n"
                + b"\x00\x00\x00\rIHDR"
                + (800).to_bytes(4, "big")
                + (2400).to_bytes(4, "big")
            )
            for number in range(1, 11):
                (final / f"page-{number:02d}.png").write_bytes(
                    fake_header + bytes([number])
                )
            report = validate(final)
            self.assertFalse(report["ok"])
            self.assertTrue(
                any(
                    "decode" in error
                    or "corrupt" in error
                    or "truncated" in error.lower()
                    for error in report["errors"]
                ),
                report["errors"],
            )

    def test_validate_rejects_non_png_final_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            final = Path(temp_dir)
            for number in range(1, 11):
                (final / f"page-{number:02d}.jpg").write_bytes(b"not an image")
            report = validate(final)
            self.assertFalse(report["ok"])
            self.assertTrue(any("unexpected" in error for error in report["errors"]))

    def test_page_count_contract_accepts_three_and_four_pages(self) -> None:
        Image, _, _, _ = load_pillow(install=True)
        for count in (3, 4):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as temp_dir:
                directory = Path(temp_dir)
                for number in range(1, count + 1):
                    Image.new(
                        "RGB",
                        (800, 2400),
                        (number * 30, number * 20, number * 10),
                    ).save(directory / f"page-{number:02d}.png", format="PNG")

                report = validate(directory)

                self.assertTrue(report["ok"], report["errors"])
                self.assertEqual(report["expected_count"], count)
                self.assertEqual(len(find_pages(directory)), count)

    def test_page_count_contract_rejects_two_and_eleven_pages(self) -> None:
        Image, _, _, _ = load_pillow(install=True)
        for count in (2, 11):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as temp_dir:
                directory = Path(temp_dir)
                for number in range(1, count + 1):
                    Image.new(
                        "RGB",
                        (800, 2400),
                        (number * 10 % 256, number * 20 % 256, number * 30 % 256),
                    ).save(directory / f"page-{number:02d}.png", format="PNG")

                report = validate(directory)

                self.assertFalse(report["ok"])
                self.assertTrue(
                    any("between 3 and 10" in error for error in report["errors"]),
                    report["errors"],
                )
                with self.assertRaisesRegex(ValueError, "between 3 and 10"):
                    find_pages(directory)

    def test_strict_decode_rejects_half_truncated_png(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "truncated.png"
            Image, _, _, _ = load_pillow(install=True)
            Image.new("RGB", (800, 2400), "white").save(path, format="PNG")
            data = path.read_bytes()
            path.write_bytes(data[: len(data) // 2])
            with self.assertRaises((OSError, ValueError)):
                image_size(path, required_format="PNG")

    def test_background_padding_preserves_full_source_on_exact_ratio_canvas(self) -> None:
        Image, ImageDraw, _, _ = load_pillow(install=True)
        source = Image.new("RGB", (100, 100), "white")
        ImageDraw.Draw(source).rectangle((25, 25, 74, 74), fill="black")

        padded = pad_to_target_ratio(source)

        self.assertEqual(padded.size, (100, 300))
        self.assertEqual(padded.width * 3, padded.height)
        self.assertEqual(padded.getpixel((50, 150)), (0, 0, 0))
        self.assertEqual(padded.getpixel((0, 0)), (255, 255, 255))

    def test_normalize_requires_explicit_ratio_policy_and_accepts_padding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.png"
            destination = root / "destination.png"
            Image, _, _, _ = load_pillow(install=True)
            Image.new("RGB", (200, 100), "white").save(source, format="PNG")

            with self.assertRaisesRegex(ValueError, "aspect ratio differs"):
                normalize_with_pillow(source, destination)

            normalize_with_pillow(
                source,
                destination,
                allow_background_pad=True,
            )
            self.assertEqual(
                image_size(destination, required_format="PNG"),
                (800, 2400),
            )

    def test_ratio_adjustment_options_are_mutually_exclusive(self) -> None:
        parser = build_parser()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(
                    [
                        "source",
                        "output",
                        "--allow-center-crop",
                        "--allow-background-pad",
                    ]
                )

    def test_wrap_text_rejects_box_narrower_than_one_glyph(self) -> None:
        class AlwaysWideDraw:
            @staticmethod
            def textlength(_text, font=None):
                return 100

        with self.assertRaises(ValueError):
            wrap_text(AlwaysWideDraw(), "승", object(), 10)


if __name__ == "__main__":
    unittest.main()
