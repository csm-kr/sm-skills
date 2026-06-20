# 프레젠테이션 기획·제작 가이드 (Planner + Designer)

ppt-maker가 덱을 만들 때 따르는 품질 기준. 2025 프레젠테이션 디자인 베스트 프랙티스(아래 References)를 종합했다. **덱을 만들기 전과 마감 전에 이 문서를 기준으로 점검한다.**

## 0. 두 역할로 일한다
- **기획자(Planner)** — 슬라이드를 만들기 *전에* 메시지·청중·스토리라인·구조를 잡는다.
- **디자이너(Designer)** — 한 슬라이드씩 시각 위계·여백·시각화로 마감한다.

둘을 분리하면 "예쁜데 메시지 없는" 덱과 "내용은 있는데 안 읽히는" 덱을 둘 다 피한다.

## 1. 기획 원칙 (Planner)
1. **한 줄 메시지** — 발표 전체를 관통하는 한 문장. 모든 슬라이드가 이걸 지지하는지 본다.
2. **청중·목적** — 누구에게 무엇을 남길지 → 용어 깊이·톤 결정.
3. **스토리라인** — Why(도입) → What(전개) → So-what(종합). 길면 Chapter로 분할.
4. **One idea per slide** — 한 장에 한 주장. **제목에 "그리고/및"이 들어가면 두 장으로 쪼갠다.**
5. **3초 룰** — 청중이 3초 안에 슬라이드 핵심을 못 잡으면 아직 안 된 것.
6. **근거를 붙인다** — 주장마다 증거(실제 스샷·데이터·사례). 추상 명사만 X.
7. **1슬라이드 ≈ 1분** — 압축. 데이터는 슬라이드당 핵심 수치 하나.

## 2. 디자인 원칙 (Designer)
1. **시각 위계** — 가장 중요한 게 가장 크고 진하게. 시선 동선: 제목 → 핵심 → 근거.
2. **6×6 규칙** — 불릿 6개 이하, 줄당 6단어 이하. 문장 아닌 구(句).
3. **여백이 디자인** — 꽉 채우지 않는다(white space).
4. **dominant visual 1개** — 슬라이드당 주인공 비주얼 하나(히어로 이미지/차트/다이어그램).
5. **시각화 > 글** — 비교=표/카드, 흐름=화살표, 양=그래프, 데이터=차트.
6. **대비·일관성** — 밝은 배경+어두운 글. 폰트 크기·색을 슬라이드마다 일관되게.
7. **색은 의미로** — accent(로즈)는 강조 1~2개에만.
8. **전환 절제** — 부드럽고 목적 있게(fade fast).
9. **제목의 약속 = 본문의 비주얼** — 제목이 곡선·그래프·비교·그림을 말하면 본문에 그 시각물을 **실제로 그린다**. 예: "한 가지 곡선이 보였다" → 막대 3개가 아니라 진짜 곡선(SVG)을. 추상 막대·플레이스홀더로 때우면 약속 불이행 + 슬라이드가 비어 보인다.
10. **statement도 여백을 채운다** — 큰 한마디 슬라이드(s-statement)는 제목만 두면 아래가 휑하다. 제목을 뒷받침하는 **미니 비주얼**(곡선·역할 막대·아이콘 행)을 붙여 화면 중앙~하단을 채운다.

## 3. 이미지 정책 — "그림을 넣을지" 판단
- **사용자 원본**(스케치·필기·스샷): 원본 그대로. 생성·변형 금지(폴라로이드 프레임).
- **실제 결과물 스샷 > 클립아트**: 웹 프로젝트는 `browse`로 스샷 찍어 쓴다.
- **세로로 긴 이미지**(풀페이지 스샷·상세페이지): 폴라로이드 대신 `object-fit:cover; object-position:top` 썸네일 카드. 여러 개면 카드 그리드로 쇼케이스.
- **생성 일러스트는 보조**: 아래 둘 중 하나일 때만 1~2장 생성한다.
  - ① 비유/개념이 글보다 그림으로 더 빨리 전달된다 (예: "메멘토 같은 개발자").
  - ② 표지·섹션처럼 텍스트만으로 허전하고 무드가 필요하다.
- 생성 시 **브랜드 톤 프롬프트 고정**: `warm cream paper, hand-drawn pen sketch, minimal, rose accent (#C73463), lots of empty space, flat`. `gen_image.py`.

## 4. 마감 QA (내보내기 전)
- `browse`로 **슬라이드별 스샷** 확인(넘침·깨짐·정렬). 전환 캡처 잔상을 피하려면 먼저 `transition:'none'`으로 끈다.
  - **모든 슬라이드를 빠짐없이 캡처**할 땐 `Reveal.slide(N)` 직접 점프 대신 `Reveal.slide(0)`에서 시작해 `Reveal.next()`로 한 장씩 넘기며 캡처한다. (직접 점프는 일부 인덱스에서 present 섹션이 비는 일이 있어 백지 스샷이 나온다. 스샷이 비면 캡처가 깨진 것이지 슬라이드가 빈 게 아닐 수 있으니 파일 크기로 한 번 더 확인.)
  - 캡처마다 전환·폰트 로드를 기다리도록 0.3~0.5초 텀을 둔다(`wait --networkidle` 후 시작).
- **약속·여백 점검** — 슬라이드별 스샷에서 ① **제목이 약속한 시각물/내용을 본문이 실제로 보여주는가**(곡선이라 했으면 곡선이 있는가) ② **휑하게 비어 보이지 않는가**(특히 statement 슬라이드). 둘 중 하나라도 아니면 미니 비주얼을 보강한다(§2-9, §2-10).
- 제목 kicker 번호 순서·오타·정렬 점검.
- **PDF 페이지 수 = 슬라이드 수** 확인.
- **PDF bleed 검증(필수)** — PDF 각 페이지 위·아래에 인접 슬라이드가 비치거나 콘텐츠가 잘리면 안 된다. `scripts/verify_pdf.py deck.pdf`로 전 페이지 콘택트 시트를 만들어 **캡처로 다** 확인한다(페이지 비율 16:9도 검사). 슬라이드가 많아질수록 심해지므로 장수 늘린 뒤엔 반드시 재검증.
  - **원인·처방(템플릿에 이미 반영됨):** reveal `print-pdf`는 ① 기본 `pdfPageHeightOffset: -1`이라 `.pdf-page`가 `@page`보다 1px 작아 페이지마다 누적 어긋남(다음/이전 슬라이드 비침) → **`pdfPageHeightOffset: 0`**, ② reveal 기본 `center: true`가 `.center` 플렉스 중앙정렬과 겹쳐 print에서 콘텐츠를 아래로 밀어 잘림 → **`center: false`**(세로 정렬은 `.center`/`.s-bullets .pad`가 직접 처리). 둘 다 `Reveal.initialize`에 박혀 있어야 한다.
- **버전 올림** — 표지/푸터의 `vX.Y`를 변경할 때마다 증가시킨다.

## 5. 안티패턴 (AI slop — 피할 것)
- 모든 슬라이드가 같은 레이아웃 → 단조로움. 슬라이드 종류를 섞는다.
- 불릿 10개 덤프.
- 의미 없는 이모지·스톡 일러스트 남발.
- 추상 명사만("효율성·시너지") 구체 사례 없음.
- 제목이 라벨("개요")이고 주장이 아님.
- 세로로 긴 이미지를 가로 프레임에 욱여넣어 빈 공간이 남음.
- 제목은 곡선·그래프·그림을 약속했는데 본문엔 추상 막대·플레이스홀더만 → 약속 불이행, 슬라이드가 비어 보임(§2-9).

## References (웹, 2025)
- [Ten simple rules for effective presentation slides — PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8638955/)
- [10 Essential Design Principles — Flashdocs](https://www.flashdocs.com/post/10-design-principles-every-slide-creator-should-know)
- [One Idea Per Slide](https://conversationsoncareers.com/2026/01/one-idea-per-slide-the-rule-that-will-change-your-presentations/)
- [10 Visual Hierarchy Principles — JEG Design](https://www.jegdesign.com/design-chat/10-visual-hierarchy-principles-for-designing-a-slide-deck/)
- [Slide Deck Design: 10 Principles — Deckary](https://deckary.com/blog/slide-deck-design-tips)
