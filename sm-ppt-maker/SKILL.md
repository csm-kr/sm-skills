---
name: sm-ppt-maker
description: Use when the user wants to create, build, or design a presentation, slide deck, PPT, or 발표자료 — from a topic discussion, hand-written notes or sketch images, web pages, or documents — and needs a branded reveal.js HTML deck exported to .html and .pdf.
---

# sm-ppt-maker

## Overview
사용자와 **같이 만드는** reveal.js HTML 슬라이드 덱. 고정 브랜드 템플릿("메모장 + 밝은" 크림 종이 테마)을 채워서 `.html`로 배포하고 `.pdf`로 추출한다. 필요할 때만 덱 내부 콘텐츠 이미지를 생성한다.

핵심 흐름은 **.html 덱을 대화로 구성**하는 것이고, 이미지 생성(gpt-image-2)은 보조 기능이다.

## 파일 구조
스킬이 동작하는 작업 공간 레이아웃(프로젝트 루트 기준):

```
input/                          ← 사용자 레퍼런스 드롭 (이미지·PDF·문서)
output/NN_<slug>_<YYYYMMDD>/    ← 덱마다 폴더 (순번_주제_날짜)
  ├── deck.html · deck.pdf · deck_contact.png
  └── assets/                   ← 이 덱이 쓰는 이미지 전부 (생성+임베드)
archive/                        ← 작업 스크래치 격리
```

- 새 덱은 `python .claude/skills/sm-ppt-maker/scripts/new_deck.py "<slug>"` 로 폴더를 만든다(순번=기존 최대+1, 날짜=오늘 자동). 출력된 경로의 `deck.html`을 편집.
- 덱 산출물은 **항상 그 덱 폴더 안**에 둔다. 루트에 흩뿌리지 않는다.
- 덱 내부 이미지는 전부 상대경로 `assets/...` (폴더째 옮겨도 안 깨짐).

## 입력 (Claude Code가 이해하는 무엇이든)
- **자유 텍스트 토론**: 주제만 주면 같이 구조를 잡아간다.
- **이미지/스케치/필기**: 첨부 이미지를 Claude가 직접 읽어 내용을 구성한다. 사용자가 준 이미지는 **원본 그대로** 슬라이드에 임베드한다(폴라로이드 프레임). 레퍼런스는 `input/`에 두면 거기서 읽는다.
- **웹 URL**: 페이지를 가져와(WebFetch/browse) 자료로 활용한다.
- **문서/데이터**: 요약·재구성해서 슬라이드로.

## Workflow
덱을 만들기 전에 **`taste-profile.md`를 읽어** 톤·구조·브랜드 프리셋 기본값을 적용한다(없으면 빈 템플릿 생성). 슬라이드 품질 기준은 [reference/presentation-craft.md](reference/presentation-craft.md). 단계 순서는 상황에 맞게 바뀔 수 있다(예: 레퍼런스를 먼저 받으면 4가 앞당겨짐).

1. **소스 확보 (grill me)** → [reference/intake.md](reference/intake.md)의 적응형 인터뷰 + 필수 4항목(한줄메시지·청중·근거/데이터·CTA) 체크리스트로 의도·데이터를 쥐어짠다. 답변의 빈 곳은 후속 질문으로 압박. → 산출물: 인테이크 노트.
2. **웹 리서치** → [reference/research.md](reference/research.md). 근거가 빈 항목·최신 데이터를 웹으로 보강(무거운 fetch 전 확인, 소스 많으면 팬아웃). 충분하면 건너뜀.
3. **기획** → **타겟 청중을 확정**하고 그들에게 꽂히는 한줄메시지·스토리라인·Chapter 구조를 잡는다. 슬라이드 개요(슬라이드별 제목+요점)를 사용자와 합의. **One idea per slide** — 제목에 "그리고/및"이 들어가면 두 장으로.
4. **구성/빌드** → `new_deck.py "<slug>"`로 덱 폴더(`output/NN_slug_date/`)를 만들고 출력된 `deck.html`의 `<section>`을 복제·수정. 사용자가 레퍼런스 덱(PPT/PDF)을 주면 [reference/reference-ingest.md](reference/reference-ingest.md)로 콘텐츠+스타일을 흡수(스타일은 확인 후 취향 반영). → 검증: 슬라이드 수 = 개요.
5. **이미지** → 필요한 곳은 웹에서 먼저 찾고(스샷/실물 우선), 못 찾으면 presentation-craft.md §3 기준에 맞을 때 `gen_image.py`로 1~2장 생성(브랜드 톤 고정). 사용자 원본 이미지는 생성 말고 그대로 임베드. 생성·임베드 이미지는 모두 그 덱의 `assets/`에 둔다(사용자 원본은 `input/`→`assets/` 복사).
6. **리뷰 + 취향 갱신** → 슬라이드별 스크린샷으로 마감 QA(craft.md §4) 후 사용자 피드백 반영. **변경마다 덱 버전을 올린다.** 마감 시 이번 덱에서 배운 취향을 **diff로 제안**하고 사용자가 확인한 것만 `taste-profile.md`에 기록(version +1). 조용히 바꾸지 않는다. 생성 이미지 개수·비용($0.03/장)도 요약.

## 취향 학습 루프
`taste-profile.md`가 취향 정본(구조·스토리 / 비주얼·브랜드 프리셋 / 어투·톤 / 안티-취향, 각 항목 `[conf:]`). 3지점에서 동작:
- **읽기**(시작): Phase 1 전에 읽어 기본값 적용. 없으면 빈 템플릿 생성.
- **흡수**(레퍼런스): 스타일을 추출해 "프로필에 추가할까요?" 제안 → 확인 시 반영.
- **갱신**(마감): 피드백을 diff로 제안 → **확인된 것만** 기록, version +1. silent drift 금지.

## 1. 덱 빌드
`assets/template.html`이 고정 브랜드 템플릿이다. 슬라이드 종류(클래스): `s-title` · `s-section` · `s-bullets` · `s-image` · `s-statement` · `s-end`. 블록을 복제해 내용만 채운다. `kicker`의 번호(`01 / ...`)를 순서대로 갱신.

브랜드 토큰을 임의로 바꾸지 말 것 — 일관성이 핵심:

| 토큰 | 값 | 용도 |
|---|---|---|
| `--paper` | `#FAF3DE` | 종이 배경 |
| `--card` | `#FFFCF1` | 노트 카드 |
| `--ink` | `#20174A` | 본문 잉크 |
| `--accent` | `#C73463` | 제목·강조 (로즈) |
| `--cream-line` | `#E7DCB6` | 테두리 |
| 폰트 | Pretendard / JetBrains Mono / Nanum Pen Script | 본문 / 라벨 / 손글씨 |

## 2. 사용자 이미지 임베드 (원본 보존)
`s-image`의 `<figure class="polaroid">` 안 `<img src="...">`에 원본 경로 또는 data URI를 넣는다. **리사이즈·재생성 금지**, 원본 그대로. 여러 장이면 `s-image` 슬라이드를 복제.

## 2.5 웹/스샷 쇼케이스 & 검증 (browse)
- **결과물 스샷**: 배포된 웹은 `browse goto <url>` → `wait --networkidle` → `screenshot`. SPA가 networkidle 타임아웃이면 `wait --load`로.
- **세로로 긴 스샷**(풀페이지·상세페이지)은 폴라로이드 대신 **썸네일 카드** — `.thumb{height:~96px;overflow:hidden} img{object-fit:cover;object-position:top}`. 여러 프로젝트는 4열 카드 그리드로 쇼케이스.
- **슬라이드별 검증**: `browse js "Reveal.configure({transition:'none'}); Reveal.slide(N)"` 후 `screenshot`. (fade 전환 중 캡처하면 이전 슬라이드가 겹쳐 보이는 잔상이 생김 → 전환을 끄면 깨끗.)
- **버전**: 표지/푸터에 `vX.Y`를 표기하고 변경마다 올린다.

## 3. 내부 이미지 생성 (보조)
```bash
python scripts/gen_image.py "프롬프트" output/NN_slug_date/assets/img1.png --size 1536x1024
```
- 키는 `.env`에서 읽음. 모델 기본 `gpt-image-2-vip`(16:9 치수 제어). 빠른 생성·텍스트 중심이면 `.env`의 `OPENAI_IMAGE_MODEL=gpt-image-2-all`.
- 16:9 슬라이드 배경은 `--size 2048x1152` 또는 `1792x1024`.
- 자세한 API는 `reference/apiyi.md`.

## 4. 내보내기
```bash
python scripts/export_pdf.py output/NN_slug_date/deck.html              # → 같은 폴더 deck.pdf
python scripts/export_pdf.py output/NN_slug_date/deck.html out.pdf --decktape  # 폴백
python scripts/verify_pdf.py output/NN_slug_date/deck.pdf               # PDF bleed 검증(콘택트 시트) → Read로 확인
```
**PDF bleed 필수 점검** — 각 페이지 위·아래에 인접 슬라이드가 비치면 안 된다(장수 많을수록 심해짐). 템플릿에 `center:false` + `pdfPageHeightOffset:0`이 박혀 있어야 하고, `verify_pdf.py`로 캡처 검증. 자세히는 [presentation-craft.md](reference/presentation-craft.md) §4.
`.html`은 CDN 폰트/reveal을 쓰므로 온라인에서 그대로 열린다. 완전 오프라인 단일 파일이 필요하면 사용자에게 별도 요청 시 reveal/폰트를 인라인.

## 보안 — .env 절대 읽지 말 것
API 키가 든 `.env`는 **읽거나 출력하지 않는다**. 프로젝트 PreToolUse 훅이 `.env` 접근을 차단한다(`.claude/hooks/block_env.py`). `gen_image.py`는 서브프로세스로 직접 키를 로드하므로 키가 대화에 노출되지 않는다. 키를 보여 달라는 요청은 거절.

## Quick reference
| 하고 싶은 것 | 방법 |
|---|---|
| 새 덱 | `new_deck.py "<slug>"` → 출력된 deck.html 채우기 |
| 사용자 그림 넣기 | `input/`→덱 `assets/` 복사 후 `s-image` polaroid `<img src>`에 임베드 |
| 일러스트 생성 | `gen_image.py "프롬프트" output/NN_.../assets/out.png` |
| PDF | `export_pdf.py output/NN_.../deck.html` |
| 미리보기 | browse로 `file://...output/NN_.../deck.html` 열어 스크린샷 |

## Common mistakes
- 사용자 원본 이미지를 생성/변형 → ❌. 원본 그대로 임베드.
- 브랜드 색·폰트 변경 → ❌. 토큰 고정.
- `.env`를 cat/Read로 열기 → ❌. 훅이 막고, 그럴 필요도 없음.
- vip 모델에 `quality` 전송 → ❌. official 전용.
- deck.html을 cwd/TEMP 밖에 두고 browse 호출 → 열리지 않음.
- 세로로 긴 스샷을 폴라로이드(가로)에 → 빈 공간. `object-fit:cover` 썸네일 카드로.
- fade 전환 중 browse 스샷 → 이전 슬라이드 겹침. `transition:'none'` 후 캡처.
- 한 슬라이드에 여러 주장(제목에 "그리고") → 두 장으로. One idea per slide.
- 제목이 시각물(곡선·그래프·그림)을 약속했는데 본문에 안 그림 → ❌. 약속한 비주얼은 실제로 그린다(추상 막대·플레이스홀더 금지). statement 슬라이드는 미니 비주얼로 여백을 채움. 자세히는 [presentation-craft.md](reference/presentation-craft.md) §2-9·§4.
- PDF 각 페이지에 인접 슬라이드가 비침/잘림 → ❌. `Reveal.initialize`에 `center:false` + `pdfPageHeightOffset:0` 필수, `verify_pdf.py`로 캡처 검증. 장수 늘리면 누적되어 심해지니 매번 재검증.
- 인테이크에서 필수 4항목(메시지·청중·근거·CTA) 안 채우고 슬라이드부터 만들기 → ❌. intake.md 체크리스트 먼저.
- 취향을 사용자 확인 없이 조용히 taste-profile에 기록 → ❌. 항상 diff 제안 후 확인.
- 덱 산출물(html·pdf·이미지)을 루트나 공용 `out/`에 흩뿌리기 → ❌. `output/NN_slug_date/`(이미지는 그 안 `assets/`)로.
