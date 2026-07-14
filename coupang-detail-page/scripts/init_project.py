#!/usr/bin/env python3
"""Create the next numbered Coupang detail-page input/output project."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PROJECT_PATTERN = re.compile(r"^[0-9]{3}$")
PRODUCT_INFO_TEMPLATE = """# 상품 정보

프로젝트 번호: {project_no}

## 기본 정보

상품명:
카테고리:
브랜드명:
모델명/SKU:
제품 라벨 표기:
검색 식별 키워드:
가장 중요한 기능적 구매 이유와 근거:

## 핵심 장점 3가지

1.
2.
3.

## 고객과 사용

타깃 고객:
대표 불편:
사용 상황:
사용 방법:

## 상품 사양

구성품:
판매 구성 수량: 미확인
소재/재질:
색상:
사이즈:
실측값: 미제공
실측 사진 상태: 미제공
중량:
제조국:
관리/세탁/보관 방법:
주의사항:

## 광고 근거

경쟁 제품 대비 검증된 차별점:
강조할 분위기:
객관적인 수치/인증/시험 정보: 없음
사용하면 안 되는 표현:
정적 비교 장면 기본값: 실제 비교 사진이 없으면 승인 뒤 `AI_ILLUSTRATION`으로 생성 · 실제 시험/수치/객관적 우위 근거로 사용 금지

## 실증 영상 입력

실물 샘플 촬영 가능 여부: 미확인
기존 실사 원본 클립: 없음
검증 가능한 시험 조건·과업·반복 횟수: 없음
촬영에서 확인할 판정 기준: 없음

## 입력 이미지

- 원본 상품 이미지: `original-images/`
- 실측·실사 시험 근거: `evidence/`
- 웹에서 동일·유력 판정한 보조 이미지: `web-confirmed/`
- 실제 스타일 레퍼런스: `real-references/`
"""

WEB_RESEARCH_TEMPLATE = """# 웹 리서치

프로젝트 번호: {project_no}
조사일:
조사 상태: 미완료
동일 제품 결론:

## 근거 등급

- 동일성: M1 확정 / M2 유력 / M3 유사 / M0 불일치·확인 불가
- 출처: E1 공식 / E2 신뢰 판매처 / E3 마켓플레이스·개인 판매 / E4 카테고리 자료

## 검색 기록

로컬로 저장한 웹 자산은 한 행에 정확히 한 `ASSET_ID`와 canonical 출처 URL을 연결한다. 서로 다른 로컬 SHA256 자산을 같은 direct image URL에 연결하지 않는다. 같은 HTML 상품 페이지의 여러 컷도 자산별 행으로 나누고 실제 이미지 URL 또는 파생·캡처 관계를 기록한다.

| 유형 | 검색어 | URL 또는 검색 결과 없음 | 동일성 | 출처 | 확인한 내용 | 기획 사용 범위 | 제외할 주장 | ASSET_ID |
|---|---|---|---|---|---|---|---|---|
| 동일 제품 |  |  | M0 |  |  |  |  | - |
| 유사 제품 |  |  | M3 | E4 |  |  |  | - |
| 상세 구조 |  |  | M3 |  |  | 훅·본문·카드·캡션·타이포 구조만 |  | - |
| 상세 구조 |  |  | M3 |  |  | 훅·본문·카드·캡션·타이포 구조만 |  | - |
| 상세 구조 |  |  | M3 |  |  | 훅·본문·카드·캡션·타이포 구조만 |  | - |

## 기획에 채택한 연구 인사이트

1.
2.
3.
"""

FACT_LEDGER_TEMPLATE = """# 사실·카피 원장

프로젝트 번호: {project_no}

## allowed facts

## approved copy manifest

| 장 | 설득 목적 | 후킹 각도 | EYEBROW | H1 | BODY | CARD·CHIP·CAPTION | CTA | 근거 Fact ID | 읽는 순서 |
|---|---|---|---|---|---|---|---|---|---|

## forbidden claims
"""

ASSET_MAP_TEMPLATE = """# R2P 자산·근거·페이지 계보

프로젝트 번호: {project_no}
검증 상태: 미완료

`references/r2p-planning-method.md`를 읽고 RAW와 레퍼런스를 분리한다. 폴더명만 믿지 말고 모든 자산에 역할과 해시를 부여한다. `REF_*`와 `GENERATED` 자산은 상품 사실의 근거가 될 수 없다.

## A. Asset Registry

로컬 경로는 스킬 루트 기준 상대 경로를 쓰고 실제 SHA256을 기록한다. 직접 URL만 있는 원격 자산은 SHA256에 `REMOTE`를 쓴다. 사용하지 않거나 불확실한 자산은 표에 넣지 말고 조사 문서에 제외 이유를 남긴다.

| ASSET_ID | ROLE | ORIGIN | PATH_OR_URL | PRODUCT_MATCH | SOURCE_GRADE | SHA256 | OBSERVABLE_FACTS | ALLOWED_USE | FORBIDDEN_TRANSFER | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|
| A01 | RAW_PRIMARY | USER | inputs/{project_no}/original-images/ | USER | USER |  |  | 제품 정체성 | 보이지 않는 기능·구성·치수 | READY |

허용 ROLE: `RAW_PRIMARY`, `RAW_DETAIL`, `RAW_MEASUREMENT`, `RAW_DEMO`, `WEB_MATCH`, `REF_STRUCTURE`, `REF_MOOD`, `REF_TYPO`, `REF_PHOTO`, `GENERATED`.

## B. Evidence Ledger

사용자 진술 실측처럼 사진이 없는 값은 숨기지 말고 `USER_DECLARED_SPEC`와 `USER_CONFIRMED_NO_PHOTO`로 기록한다. 원본에 보이는 개수는 `PACKAGE_VISIBLE`일 뿐 판매 수량 `PACKAGE_SALE`이 아니다.

| PROOF_ID | FACT_IDS | CLAIM_CLASS | EVIDENCE_TYPE | SOURCE_ASSET_IDS | STRENGTH | SKU_OPTION_SCOPE | ALLOWED_COPY | FORBIDDEN_EXPANSION | STATUS |
|---|---|---|---|---|---|---|---|---|---|
| P01 |  |  |  |  |  | 현재 판매 옵션 |  |  | APPROVED |

## C. Reference Principle Ledger

| REF_PRINCIPLE_ID | REFERENCE_ASSET_ID | REFERENCE_TYPE | ABSTRACT_PRINCIPLE | TARGET_PAGE_IDS | DO_NOT_COPY | STATUS | REJECTION_REASON |
|---|---|---|---|---|---|---|---|
| RP01 |  |  |  |  | 실제 문구·수치·로고·제품 기능·고유 그래픽 | USED | 없음 |

레퍼런스가 없으면 이 표의 예시 행을 삭제하고 페이지 표에서 `REF_PRINCIPLE_IDS`를 `NONE`으로 쓴다.

## D. Page Source Contract

`plan-gate.md`에서 최종 선정한 모든 장을 정확히 한 번씩 적는다. PRIMARY_FACT_IDS는 계획표와 정확히 일치해야 하고 PROOF_ID는 장마다 달라야 한다.

| 장 | INFO_ID | DECISION_STAGE | RAW_ASSET_IDS | REF_PRINCIPLE_IDS | PROOF_ID | PRIMARY_FACT_IDS | PROOF_MODE | EXCLUSIVE_GAIN | DROP_TEST | CLAIM_BOUNDARY |
|---:|---|---|---|---|---|---|---|---|---|---|
| 01 | I01 | NOTICE | A01 | RP01 | P01 |  | RAW_CROP | 이 장을 지우면 사라지는 구매 답 | 이 장을 삭제하면 구매자가 잃는 정보 | 근거보다 강한 카피 금지 |

허용 단계: `NOTICE`, `UNDERSTAND`, `VERIFY`, `FIT`, `USE`, `DECIDE`.

허용 PROOF_MODE: `RAW_CROP`, `USER_DECLARATION`, `OFFICIAL_DIAGRAM`, `REAL_DEMO`, `REAL_TEST`, `AI_ILLUSTRATION`, `COMPOSITE_LAYOUT`.

완성 뒤 `python3 scripts/validate_asset_map.py {project_no}`를 통과해야 기획 HTML을 만들 수 있다.
"""

PLAN_GATE_TEMPLATE = """# 근거 기반 가변 장수·비중복 기획 게이트

프로젝트 번호: {project_no}
검증 상태: 미완료

## 장수 결정 게이트

먼저 서로 다른 구매 정보 단위를 세고, 확인된 정보만으로 3~10장을 선정한다. 보통은 5~8장이지만 정보가 적으면 3~4장으로 끝낸다. 요청 장수를 채우기 위해 같은 장점·장면·카피를 늘리지 않는다. 독립 요약 CTA가 앞 내용을 반복하면 삭제하고, 마지막 정보 장에 CTA를 결합한다.

목표 장수:
정보 단위 수:
선정 장수:
장수 결정 근거:
삭제·병합 역할:
장수 결정 상태: 미완료

### 장수 작성 규칙

- `목표 장수`와 `선정 장수`는 근거 검토 후 확정한 같은 값으로 적는다.
- 최종 선정한 `정보 단위 수`와 `선정 장수`를 같게 맞춘다. 정보가 부족하면 장수를 줄이고, 남는 정보는 다음 프로젝트 후보로 기록한다.
- 각 장에 `I01` 같은 고유 `INFO_ID`를 하나씩 배정한다.
- 01부터 빠짐없이 연속 번호를 사용하고 최소 3장, 최대 10장만 선정한다.
- 삭제하거나 합친 역할과 이유를 `삭제·병합 역할`에 기록한다. 없으면 `없음`으로 적는다.
- 위 항목과 표를 모두 채운 뒤에만 `장수 결정 상태: 완료`로 바꾼다.

## 기능 우선 게이트

상세페이지는 디자인보다 구매자가 먼저 확인할 핵심 기능과 그 기능이 해결하는 불편을 앞세운다. 기능은 `fact-ledger.md`의 허용 사실로 확인된 것만 적는다. 확인된 기능이 없으면 임의로 만들지 말고 `핵심 기능 소구: 없음`과 구체적인 사유를 기록한다.

핵심 기능 소구:
기능 근거 Fact ID:
기능이 답하는 구매 불편:
디자인 보조 소구:
기능 우선 적용 장:
기능 없음 사유:
기능 우선 상태: 미완료

### 작성 규칙

- 기능이 있으면 `기능 근거 Fact ID`는 `fact-ledger.md`의 실제 Fact ID여야 한다.
- 기능이 있으면 `기능 우선 적용 장`에 01과 02 또는 03을 포함하고, 그중 한 장 이상은 기능 근거 Fact ID를 `PRIMARY_FACT`로 사용한다.
- 디자인·컬러·무드·스타일은 `디자인 보조 소구`로 분리하고 핵심 기능보다 앞세우지 않는다.
- 기능이 없으면 `기능 근거 Fact ID`와 `기능 우선 적용 장`을 `없음`으로 쓰고 `기능 없음 사유`를 구체적으로 작성한다.
- 모든 항목과 선정 장수 표를 작성한 뒤에만 `기능 우선 상태: 완료`로 바꾼다.

## 선택 역할·정보 소유권 표

허용된 `ROLE_ID` 중 상품에 실제로 필요한 역할만 고른다. 서로 다른 기능 근거처럼 INFO_ID·Fact·Proof가 다르면 같은 역할을 다시 쓸 수 있지만, `PRODUCT_INTRO`는 정확히 한 번만 쓴다. 첫 장은 `PROBLEM_HOOK`, 마지막 장은 새 정보와 CTA를 결합한 `*_CTA` 역할을 쓴다.

허용 역할:

- 시작·소개: `PROBLEM_HOOK`, `NEED_REASON`, `PRODUCT_INTRO`
- 상품 정보: `FEATURE_EVIDENCE`, `FIT_STRUCTURE`, `MEASURED_SIZE`, `FIT_SIZE`, `MATERIAL_SPEC`, `COMPONENTS`, `OPTIONS`, `HOW_TO_USE`, `SITUATION_COMPARE`, `NEUTRAL_COMPARE`, `RECOMMENDATION`, `USE_CASES`, `CARE_GUIDE`, `SAFETY_GUIDE`, `EVIDENCE`
- 마지막 정보+CTA: `SITUATION_USE`, `SPEC_CTA`, `GUIDE_CTA`, `USE_CASE_CTA`, `CARE_CTA`, `EVIDENCE_CTA`, `COMPONENTS_CTA`, `OPTIONS_CTA`, `SAFETY_CTA`

아래 5행은 일반적인 구성 예시다. 상품 근거에 따라 3~10행으로 역할·모듈을 바꾸고, 빈 셀 없이 작성한 뒤 `python3 scripts/validate_plan.py {project_no}`를 통과해야 생성할 수 있다.

| 장 | ROLE_ID | 역할 | 필수 모듈 | 고유 구매 질문 | PRIMARY_FACT | INFO_ID | ADVANTAGE_ID | 필수 시각 증거 | H1 핵심어 | SHOT_ID | SCENE_ID | LAYOUT_ID | 다음 장과 연결 | 모션 역할 |
|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | PROBLEM_HOOK | 문제 후킹 | H1+BODY+PROBLEM_SCENE |  |  | I01 | - |  |  |  |  |  |  |  |
| 02 | PRODUCT_INTRO | 상품 메인 소개 | PRODUCT_NAME+HERO+CORE_ADVANTAGES |  |  | I02 | A1+A2+A3 |  |  |  |  |  |  |  |
| 03 | FEATURE_EVIDENCE | 핵심 기능과 근거 | FEATURE+EVIDENCE+BOUNDARY |  |  | I03 | A1 |  |  |  |  |  |  |  |
| 04 | FIT_SIZE | 착용감·실측 사이즈 | FIT+SIZE_DIAGRAM+MEASUREMENTS |  |  | I04 | A2 |  |  |  |  |  |  |  |
| 05 | USE_CASE_CTA | 사용 장면·구매 안내 | USE_CASES+CAPTIONS+CTA |  |  | I05 | A3 |  |  |  |  |  | 종료 |  |

## 의미 중복 직접 검사

- [ ] 모든 장의 INFO_ID가 다르고, 비최종 장끼리 PRIMARY_FACT의 의미가 겹치지 않는다.
- [ ] 역할마다 구매 질문·시각 증거·실측·사용법 등 서로 다른 정보를 제공한다.
- [ ] 같은 4어절 이상 카피, 제품 크롭, 모델·의상·포즈와 지배 레이아웃을 반복하지 않는다.
- [ ] 마지막 장은 앞 장 요약만 반복하지 않고, 고유 정보와 CTA를 함께 제공한다.
"""

GENERATION_GATE_TEMPLATE = """# 사용자 검토·생성 게이트

프로젝트 번호: {project_no}
기획 리뷰 HTML: `plan-review.html`
기획 검토 상태: 미승인
사용자 승인 기록:
승인한 기획 소스 해시:
승인한 리뷰 HTML 해시:
제작 범위: 미선택
선정 모션 ID: 미선택
환경 선택 기록:
ComfyUI 상태: 미확인
ComfyUI 증빙 JSON: 미제공
정적 이미지 생성 승인: 미승인
GIF·영상 생성 승인: 미승인
최종 생성 승인 기록:

## 허용 값

- 기획 검토 상태: `미승인` / `승인`
- 제작 범위: `STATIC_ONLY` / `STATIC_PLUS_GIF` / `STATIC_PLUS_VIDEO` / `STATIC_PLUS_GIF_VIDEO` / `STATIC_PLUS_MOTION_HANDOFF`
- ComfyUI 상태: `CONNECTED` / `WORKFLOW_PROVIDED` / `HANDOFF_ONLY` / `NOT_REQUIRED`
- 정적 이미지 생성 승인: `미승인` / `승인`
- GIF·영상 생성 승인: `미승인` / `승인` / `해당 없음`

## 기록 규칙

- `plan-review.html`을 사용자에게 보여주기 전에는 `기획 검토 상태`를 승인으로 바꾸지 않는다.
- 1번 기획 확정 응답만 `YYYY-MM-DD · APPROVE_PLAN · ANSWER=1` 형식으로 `사용자 승인 기록`에 남긴다. 자유문·거절문은 무효다.
- HTML의 `data-source-digest` 64자를 `승인한 기획 소스 해시`에 그대로 기록한다.
- 승인한 `plan-review.html` 파일 자체의 SHA256을 `승인한 리뷰 HTML 해시`에 기록한다. 소스 문서나 HTML 본문이 바뀌면 승인이 자동 무효화된다.
- ComfyUI 연결을 실제로 확인하지 않았다면 `CONNECTED`로 기록하지 않는다.
- 환경 선택은 `YYYY-MM-DD · SELECT_ENV · SCOPE=<범위> · MOTION=<정렬 ID 또는 NONE> · COMFY=<상태>`, 최종 1번 실행 승인은 `YYYY-MM-DD · APPROVE_EXECUTION · SCOPE=<범위> · MOTION=<정렬 ID 또는 NONE> · COMFY=<상태>` 형식으로 각각 기록한다. 날짜는 Asia/Seoul 오늘보다 미래일 수 없고 `기획 승인 ≤ 환경 선택 ≤ 최종 승인` 순서여야 한다.
- 이 문서의 표준 필드는 각각 정확히 한 번만 유지한다. `기획 리뷰 HTML`은 정확히 `plan-review.html`, `선정 모션 ID`는 `해당 없음` 또는 중복 없는 `motion-NN` 쉼표 목록만 허용한다. 환경이 바뀌면 최종 승인을 다시 받는다.
- `CONNECTED`는 `python3 scripts/comfyui_receipt.py probe {project_no} --endpoint <http(s) URL>`이 만든 24시간 이내 receipt 경로를 `ComfyUI 증빙 JSON`에 기록하고, 실제 생성 게이트에서 같은 endpoint의 `/system_stats` live 재확인도 통과한다.
- `WORKFLOW_PROVIDED`는 프로젝트 내부의 구조가 유효한 ComfyUI API prompt graph 또는 UI workflow를 `python3 scripts/comfyui_receipt.py workflow {project_no} --workflow <path>`로 검증·해시한 receipt 경로를 기록한다. 이 상태는 `STATIC_PLUS_MOTION_HANDOFF` 전용이며 실제 렌더 완료를 뜻하지 않는다.
- `HANDOFF_ONLY`는 스토리보드·프롬프트 인계만 허용하며 GIF·영상을 생성했다고 보고하지 않는다.
- 실제 생성 직전 `python3 scripts/validate_generation_gate.py {project_no} --target static` 또는 `--target motion`을 통과해야 한다.
"""

PROMPT_SET_TEMPLATE = """# image_gen 프롬프트 세트

프로젝트 번호: {project_no}

## SOURCE_ROLES

- `RAW_PRIMARY`·`RAW_DETAIL`·`RAW_MEASUREMENT`·`RAW_DEMO`: 현재 제품의 정체성·관찰·실측·실사 동작 근거
- `WEB_MATCH`: M1/M2로 연결된 웹 보조 자산이며 RAW를 대신하지 않음
- `REF_STRUCTURE`·`REF_MOOD`·`REF_TYPO`·`REF_PHOTO`: 추상 표현 원리만 제공
- `GENERATED`: 승인 뒤 만든 출력이며 상품 사실 근거로 사용 금지

## R2P_LINEAGE

- 각 장은 `asset-map.md`의 `RAW_ASSET_IDS / REF_PRINCIPLE_IDS / PROOF_ID / PROOF_MODE / CLAIM_BOUNDARY`를 그대로 사용한다.
- RAW, WEB_MATCH, REF_*, GENERATED의 역할을 바꾸거나 서로 대체하지 않는다.
- 카피 강도는 해당 Proof보다 강할 수 없으며 승인되지 않은 수치·기능·구성·효능을 추가하지 않는다.

## COPY_SYSTEM

- 카피 매니페스트: EYEBROW / H1 / BODY / CARD·CHIP / CAPTION / CTA
- 정보 밀도: 한 장당 3~6개 세로 정보 구역, 구역마다 한 메시지
- 정확한 카피: 모든 승인 문자열을 직접 조판하고 누락·축약·의역·추가 금지

## TYPOGRAPHY_SYSTEM

- 800x2400 원본: H1 72~104px / H2 44~64px / BODY 32~40px / 라벨·캡션 최소 32px
- 선정한 모든 장에 동일한 한국어 산세리프 한 계열과 굵기 토큰

## FUNCTION_PRIORITY

- `plan-gate.md`에서 확정한 핵심 기능·구매 불편·근거 경계를 디자인 무드보다 먼저 보여준다.
- 확인된 기능이 없으면 만들지 않고, 기능명만 확인된 경우 수치·원리·성능 보장으로 확대하지 않는다.

## DESIGN_SYSTEM

- 현재 제품 RAW의 색·형태·부품·라벨·관찰 가능한 구조를 잠근다.
- REF_*의 문구·제품·수치·로고·고유 그래픽을 복제하지 않는다.
- 장별 SHOT_ID·SCENE_ID·LAYOUT_ID를 다르게 하고 같은 구매 답을 다시 말하지 않는다.

## 선정 장수 프롬프트 계약 — 승인 스냅샷

선정한 장마다 한 행을 만들고 `raw 출력 계약`은 `outputs/{project_no}/raw/page-NN.png`로 기록한다. 이 문서는 `plan-review.html`에 포함되는 승인 소스이므로 승인 뒤 시도 횟수·상태를 덮어쓰지 않는다. 실제 실행 기록은 `execution-log.md`에 남긴다.

| 장 | ROLE_ID | INFO_ID | 역할·정보 구역 | 카피 매니페스트 | RAW_ASSET_IDS | 최종 프롬프트 | raw 출력 계약 |
|---:|---|---|---|---|---|---|---|
"""

EXECUTION_LOG_TEMPLATE = """# 생성 실행 로그

프로젝트 번호: {project_no}
실행 상태: 미실행
승인한 기획 소스 해시:
승인한 리뷰 HTML 해시:

이 문서는 승인 뒤의 가변 실행 기록이다. `plan-review.html`의 승인 소스가 아니며 `prompt-set.md`를 실행 로그로 덮어쓰지 않는다.

## 장별 호출 기록

| 장 | 시도 | 도구·모드 | 참조 자산·입력 | 생성 원본 | TEXT | PRODUCT | LAYOUT | CLAIMS | 판정 | 실패·교체 사유 |
|---:|---:|---|---|---|---|---|---|---|---|---|

## 정규화·최종 파일

| 장 | 선택 raw | 정규화 방식 | 최종 파일 | 규격 | SHA256 | 판정 |
|---:|---|---|---|---|---|---|

## 실행 경계

- 승인한 기획 소스는 생성 전후 같은 SHA256을 유지한다.
- 재시도 전 결과는 `raw/retries/`에 보존한다.
- GIF·영상은 승인 범위에 포함될 때만 별도 실행 기록을 추가한다.
"""

DETAIL_PAGE_ANALYSIS_TEMPLATE = """# 상세페이지 비교 분석

프로젝트 번호: {project_no}
조사일:

## 접근 상태

- 차단된 URL과 확인하지 못한 범위를 기록한다.

## 비교한 페이지

| 페이지 | 확인한 구조 | 채택할 패턴 | 가져오지 않는 것 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

## 공통 패턴

1.
2.
3.

## 프로젝트 적용 결정

- 한 장당 3~6개 세로 정보 구역
- H1 72~104px / H2 44~64px / BODY 32~40px / 라벨·캡션 최소 32px
"""

QA_REPORT_TEMPLATE = """# 장별 QA 보고서

프로젝트 번호: {project_no}

| 장 | 시도 | TEXT | PRODUCT | LAYOUT | CLAIMS | ROLE | SOURCE_LINEAGE | UNIQUENESS | 판정 | 실패 사유 | 최종 파일 |
|---|---|---|---|---|---|---|---|---|---|---|---|

## 전체 흐름 QA

- FLOW: 01부터 선정 장수까지 연속 / ROLE_ID·INFO_ID 중복 0
- INFORMATION_COVERAGE: 각 장이 서로 다른 정보 단위와 시각 증거를 소유
- FINAL_CTA: 마지막 정보 장에 CTA 결합 / 반복 요약 전용 장 없음
- FINAL_RECHECK: 800x2400 정규화 후 TEXT·PRODUCT·LAYOUT·CLAIMS·ROLE·SOURCE_LINEAGE·UNIQUENESS 재검사

## 영상 증거 QA

- EVIDENCE: CAPTURE_MODE와 허용 주장 범위 일치
- CAPTURE_INTEGRITY: 실사 시험의 동일 SKU·조건·판정 기준·원본 경로·핵심 구간 무편집 확인
- AI_BOUNDARY: AI_ILLUSTRATION을 시험·입증·성능 증거로 표현하지 않음
- MOTION_VALIDATION: `python3 scripts/validate_motion.py {project_no}` 실행 전에는 TOP1 확정 금지
"""

MOTION_PLAN_TEMPLATE = """# GIF·영상·ComfyUI 모션 계획

프로젝트 번호: {project_no}
ComfyUI 상태: 미확인
실사 촬영 상태: PENDING_CAPTURE
모션 검증 상태: 미완료
가장 영상이 필요한 소구점:

## CAPTURE_MODE 계약

- `REAL_TEST`: 실제 판매 제품의 성능·물성·내구·작동 결과를 명시된 조건과 판정 기준으로 촬영
- `REAL_DEMO`: 실제 판매 제품의 외형·구조·착용법·한정된 과업을 촬영하며 일반 성능으로 확대하지 않음
- `AI_ILLUSTRATION`: 이해를 돕는 생성·합성 연출이며 시험·입증·성능 증거로 사용하지 않음
- `NO_PROOF_HOOK`: 안전하게 증명할 근거나 실사 조건이 없어 TOP1을 보류함

## 모션 후보 7요소 점수

각 항목은 0~20점, 총점은 140점으로 기록한다. 근거 없는 물성·효능을 암시하면 총점이 높아도 선정하지 않는다. `고유 소구 선명도`와 `실증 후킹력`이 각각 12점 미만이면 TOP1로 선정하지 않는다. `AI_ILLUSTRATION`의 실증 후킹력은 최대 5점이다.

| 순위 | MOTION_ID | 후보·대상 장 | 형식 | CAPTURE_MODE | 동작 필요성 | 주장 안전성 | 전환 관련성 | 제작 실행성 | 제품 안정성 | 고유 소구 선명도 | 실증 후킹력 | 총점 | 판정 |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | motion-01 |  |  |  |  |  |  |  |  |  |  |  |  |
| 2 | motion-02 |  |  |  |  |  |  |  |  |  |  |  |  |
| 3 | motion-03 |  |  |  |  |  |  |  |  |  |  |  |  |

## 장별 계획

| 장 | 정지/GIF/영상 | 추천 이유 | 움직임 아이디어 | 시작·끝 프레임 | 길이/FPS/루프 | 입력 경로 | 제품 불변 요소 | 상태 |
|---|---|---|---|---|---|---|---|---|
"""

FONT_PLAN_TEMPLATE = """# 폰트·조판 계획

프로젝트 번호: {project_no}
최종 조판 방식: 미확정 — 장별 시도·사용자 승인 기록 후 확정

## 정지 이미지 조판 경로

- 1차: 승인한 전체 한글 카피를 image_gen 프롬프트에 직접 넣어 한 번에 조판한다.
- 동일 장에서 한글 QA가 2회 실패하면 자동 전환하지 않고 사용자 승인을 받는다.
- 사용자 승인 시에만 실패한 정지 장을 `FIXED_TEXT_LAYER` 후편집으로 전환하고 장·시도·승인 기록을 남긴다.
- GIF·영상은 생성 글자 흔들림을 막기 위해 처음부터 항상 `FIXED_TEXT_LAYER`를 사용한다.

## 폰트 잠금

- 주 한글 서체:
- 대체 서체:
- 사용 가능한 굵기:
- 폰트 경로 또는 조판 환경:
- 라이선스·배포 확인:
- 프로젝트 중 서체 혼용: 금지

## 조판 토큰

| 형식 | 캔버스 | H1 | H2 | BODY | LABEL·CAPTION | CTA | 안전 여백 |
|---|---|---|---|---|---|---|---|
| 정지 상세페이지 | 800x2400 |  |  |  | 최소 32px |  |  |
| GIF |  |  |  |  |  |  |  |
| 세로 영상 | 1080x1920 |  |  |  |  |  |  |

## 영상 고정 텍스트 레이어

- 모션 원본 플레이트와 광고 카피 레이어를 분리한다.
- 승인 카피는 실제 폰트 레이어로 한 번 조판하고 프레임마다 재생성하지 않는다.
- 카피 위치·크기·자간·행간은 전체 클립에서 고정한다.
- 제품에 원래 붙은 물리 라벨은 원본 텍스처를 트래킹하고 새 글자로 재생성하지 않는다.

## 한글 QA

- 한글 자모·오탈자·라인 브레이크·잘림 확인
- 정지·GIF·영상의 토큰 일관성 확인
- 시작·중간·종료 프레임의 글자 위치·형태·선명도 일치 확인
"""

VIDEO_PLAN_TEMPLATE = """# 영상·GIF TOP3 스토리보드

프로젝트 번호: {project_no}
ComfyUI 상태: 미확인
실사 촬영 상태: PENDING_CAPTURE
실제 영상 생성 상태: 미실행
가장 영상이 필요한 소구점:
선정 이유:

## TOP3 요약

| 순위 | MOTION_ID | 소구점 | CAPTURE_MODE | 형식 | 삽입 위치 | 총점 | 선정 근거 |
|---:|---|---|---|---|---|---:|---|
| 1 | motion-01 |  |  |  |  |  |  |
| 2 | motion-02 |  |  |  |  |  |  |
| 3 | motion-03 |  |  |  |  |  |  |

## motion-01 — TOP1

- CAPTURE_MODE:
- 증명 상태: PENDING_CAPTURE
- 목적·구매 질문:
- 검증할 구매 의심:
- 허용 주장:
- 도전 조건·과업:
- 통제 조건:
- 판정 기준:
- 삽입 위치:
- 캔버스·길이·FPS·루프:
- 입력 경로:
- 실사 원본 클립 경로: PENDING_CAPTURE
- 편집 정책:
- 제품 불변 요소:
- 시작 프레임:
- 종료 프레임:

| 구간 | 화면·동작 | 고정 텍스트 레이어 | 전환·카메라 |
|---|---|---|---|
|  |  |  |  |

- ComfyUI 실행 프롬프트:
- 네거티브 프롬프트:
- 프레임 잠금·컨트롤:
- 산출 경로:
- QA:

## motion-02 — TOP2

- CAPTURE_MODE:
- 증명 상태: PENDING_CAPTURE
- 목적·구매 질문:
- 검증할 구매 의심:
- 허용 주장:
- 도전 조건·과업:
- 통제 조건:
- 판정 기준:
- 삽입 위치:
- 캔버스·길이·FPS·루프:
- 입력 경로:
- 실사 원본 클립 경로: PENDING_CAPTURE
- 편집 정책:
- 제품 불변 요소:

| 구간 | 화면·동작 | 고정 텍스트 레이어 | 전환·카메라 |
|---|---|---|---|
|  |  |  |  |

- ComfyUI 실행 프롬프트:
- 네거티브 프롬프트:
- 프레임 잠금·컨트롤:
- 산출 경로:
- QA:

## motion-03 — TOP3

- CAPTURE_MODE:
- 증명 상태: PENDING_CAPTURE
- 목적·구매 질문:
- 검증할 구매 의심:
- 허용 주장:
- 도전 조건·과업:
- 통제 조건:
- 판정 기준:
- 삽입 위치:
- 캔버스·길이·FPS·루프:
- 입력 경로:
- 실사 원본 클립 경로: PENDING_CAPTURE
- 편집 정책:
- 제품 불변 요소:

| 구간 | 화면·동작 | 고정 텍스트 레이어 | 전환·카메라 |
|---|---|---|---|
|  |  |  |  |

- ComfyUI 실행 프롬프트:
- 네거티브 프롬프트:
- 프레임 잠금·컨트롤:
- 산출 경로:
- QA:

## 인계 주의

- `HANDOFF_ONLY`는 기획·프롬프트·스토리보드만 완성되었고 실제 ComfyUI 실행·렌더·검수는 하지 않았다는 뜻이다.
- 모든 광고 카피는 `font-plan.md`의 실제 폰트 고정 레이어로 후합성한다. 프레임별 생성 텍스트를 사용하지 않는다.
- `PENDING_CAPTURE`는 실사 촬영 전 상태이며 결과를 상품 사실이나 PASS 카피로 승격하지 않는다.
- `AI_ILLUSTRATION`은 구조 이해용 연출이다. 실사 시험 영역을 생성형 도구로 수정한 합성물도 증거로 인정하지 않는다.
"""

OUTPUT_TEMPLATES = {
    "web-research.md": WEB_RESEARCH_TEMPLATE,
    "detail-page-analysis.md": DETAIL_PAGE_ANALYSIS_TEMPLATE,
    "fact-ledger.md": FACT_LEDGER_TEMPLATE,
    "asset-map.md": ASSET_MAP_TEMPLATE,
    "plan-gate.md": PLAN_GATE_TEMPLATE,
    "generation-gate.md": GENERATION_GATE_TEMPLATE,
    "prompt-set.md": PROMPT_SET_TEMPLATE,
    "execution-log.md": EXECUTION_LOG_TEMPLATE,
    "qa-report.md": QA_REPORT_TEMPLATE,
    "motion-plan.md": MOTION_PLAN_TEMPLATE,
    "font-plan.md": FONT_PLAN_TEMPLATE,
    "video-plan.md": VIDEO_PLAN_TEMPLATE,
}


def existing_numbers(skill_root: Path) -> set[int]:
    numbers: set[int] = set()
    for folder_name in ("inputs", "outputs"):
        base = skill_root / folder_name
        if not base.is_dir():
            continue
        for child in base.iterdir():
            if child.is_dir() and PROJECT_PATTERN.fullmatch(child.name):
                numbers.add(int(child.name))
    return numbers


def choose_number(skill_root: Path, requested: int | None) -> int:
    used = existing_numbers(skill_root)
    if requested is not None:
        if not 1 <= requested <= 999:
            raise ValueError("project number must be between 1 and 999")
        if requested in used:
            raise FileExistsError(f"project {requested:03d} already exists")
        return requested
    number = max(used, default=0) + 1
    if number > 999:
        raise ValueError("no project numbers remain in the 001-999 range")
    return number


def initialize(skill_root: Path, number: int) -> tuple[Path, Path]:
    if not 1 <= number <= 999:
        raise ValueError("project number must be between 1 and 999")
    project_no = f"{number:03d}"
    input_root = skill_root / "inputs" / project_no
    output_root = skill_root / "outputs" / project_no

    if input_root.exists() or output_root.exists():
        raise FileExistsError(f"project {project_no} already exists")

    empty_directories = (
        input_root / "original-images",
        input_root / "evidence",
        input_root / "web-confirmed",
        input_root / "real-references",
        output_root / "raw" / "retries",
        output_root / "final",
    )
    for directory in empty_directories:
        directory.mkdir(parents=True)
        (directory / ".gitkeep").touch()
    (input_root / "product-info.md").write_text(
        PRODUCT_INFO_TEMPLATE.format(project_no=project_no), encoding="utf-8"
    )
    for filename, template in OUTPUT_TEMPLATES.items():
        (output_root / filename).write_text(
            template.format(project_no=project_no), encoding="utf-8"
        )
    return input_root, output_root


def prepare(skill_root: Path, number: int) -> tuple[Path, Path, bool]:
    """Idempotently prepare a starter/runtime project without overwriting data."""

    if not 1 <= number <= 999:
        raise ValueError("project number must be between 1 and 999")
    project_no = f"{number:03d}"
    input_root = skill_root / "inputs" / project_no
    output_root = skill_root / "outputs" / project_no
    empty_directories = (
        input_root / "original-images",
        input_root / "evidence",
        input_root / "web-confirmed",
        input_root / "real-references",
        output_root / "raw" / "retries",
        output_root / "final",
    )
    for directory in empty_directories:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".gitkeep").touch(exist_ok=True)
    info_path = input_root / "product-info.md"
    if info_path.exists() and not info_path.is_file():
        raise IsADirectoryError(f"expected project file but found non-file: {info_path}")
    created = not info_path.exists()
    if created:
        info_path.write_text(
            PRODUCT_INFO_TEMPLATE.format(project_no=project_no), encoding="utf-8"
        )
    for filename, template in OUTPUT_TEMPLATES.items():
        path = output_root / filename
        if path.exists() and not path.is_file():
            raise IsADirectoryError(f"expected project file but found non-file: {path}")
        if not path.exists():
            path.write_text(template.format(project_no=project_no), encoding="utf-8")
    return input_root, output_root, created


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create inputs/NNN and outputs/NNN for a new detail-page project."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--number",
        type=int,
        help="Explicit project number from 1 to 999; default is max existing number plus one",
    )
    group.add_argument(
        "--prepare",
        type=int,
        metavar="NUMBER",
        help="Idempotently prepare an existing starter project without overwriting it",
    )
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parents[1]
    try:
        if args.prepare is not None:
            input_root, output_root, created = prepare(skill_root, args.prepare)
            print(f"PROJECT={args.prepare:03d}")
            print(f"PRODUCT_INFO={'CREATED' if created else 'PRESERVED'}")
            print(f"INPUTS={input_root}")
            print(f"OUTPUTS={output_root}")
            return 0
        number = choose_number(skill_root, args.number)
        input_root, output_root = initialize(skill_root, number)
    except (FileExistsError, OSError, ValueError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"PROJECT={number:03d}")
    print(f"INPUTS={input_root}")
    print(f"OUTPUTS={output_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
