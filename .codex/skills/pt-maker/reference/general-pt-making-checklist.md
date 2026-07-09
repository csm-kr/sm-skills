# General PT 제작/채점 체크리스트

이 체크리스트는 pt-maker의 최종 QA 게이트다. 모든 덱은 최종 산출 전 이 문서로 채점하고, 실패 항목을 수정한 뒤 다시 렌더링해야 한다.

## 사용 규칙

1. HTML/PDF를 렌더링한다.
2. contact sheet를 생성한다.
3. 표지, 섹션 시작, 도표/SVG/타임라인, 활동/퀴즈, 마지막 페이지는 full-size PNG로 확인한다.
4. agent/subagent 도구가 있으면 dedicated QA reviewer agent를 실행한다.
5. 아래 기준으로 P0/P2와 100점 점수를 기록한다.
6. P0가 하나라도 있거나 점수가 90점 미만이면 source HTML/CSS를 수정하고 다시 렌더링한다.
7. 수정 후 contact sheet와 필요한 full-size PNG를 다시 만들고 QA를 반복한다.
8. PDF/contact sheet가 통과한 뒤에만 PPTX로 export한다.

## Agent 검수 시스템

agent/subagent 도구가 있는 환경에서는 최종 산출 전 반드시 독립 QA reviewer agent를 사용한다. 이 agent는 파일을 수정하지 않고, 렌더된 결과물만 보고 판단한다.

### Agent에게 전달할 입력

- 덱의 목적/청중/발표 상황 요약.
- 최종 또는 후보 PDF.
- contact sheet 이미지.
- full-size PNG: 표지, 섹션 시작, 도표/SVG/타임라인, 활동/퀴즈, 마지막 페이지.
- 이 체크리스트.

### Agent 지시문 템플릿

```text
You are a PT QA reviewer. Review only rendered artifacts, not source code.
Use reference/general-pt-making-checklist.md as the grading standard.

Return only:
1. pt-qa-result: pass/fail
2. score: __/100
3. P0 hard fails, with page numbers and concrete visual reason
4. P2 polish candidates, with page numbers
5. required fixes
6. recheck pages

Rules:
- Any text overlap, broken Korean word/label, footer collision, cropped content,
  broken 16:9, disconnected diagram arrow, or score below 90 is fail.
- Do not suggest broad redesign unless needed to remove a P0.
- Do not edit files.
```

### 반복 루프

1. Main agent renders PDF/contact sheet.
2. QA reviewer agent returns P0/P2/score.
3. Main agent fixes the source HTML/CSS/assets.
4. Main agent rerenders PDF/contact sheet.
5. Repeat QA until `pt-qa-result: pass`, no P0, and score >= 90.
6. Export PPTX only after pass.

If no agent/subagent tool exists, record `qa-agent: unavailable` in build notes and run the same checklist manually. Do not skip the scoring loop.

## 리뷰 등급

### P0: 즉시 수정해야 하는 hard fail

- 텍스트 겹침, 카드/푸터/출처 충돌, 잘림, 16:9 깨짐, 본문 가독성 실패.
- 카드 행/열 정렬 불일치.
- 타임라인 핀, 도식 라벨, SVG 라벨 위치 어긋남.
- 반복 header/footer/page number 좌표 흔들림.
- 섹션 번호나 핵심 라벨 줄바꿈.
- 한국어 단어, 고유명사, 숫자 라벨이 중간에서 끊김.
- 주요 도표의 선/화살표가 끊기거나 대상에 애매하게 닿음.
- 마지막 페이지의 제목, 이미지, 마무리 문구, 푸터가 서로 침범.

### P2: polish 개선 후보

- hard fail은 아니지만 시각 무게가 아래로 쏠림.
- 비슷한 레이아웃이 반복되어 지루함.
- 강조 요소, 배지, 아이콘, 장식이 메시지보다 과함.
- 첫 페이지와 마지막 페이지가 연결감 없이 따로 놂.
- 이미지가 예쁘지만 슬라이드 주장과 직접 연결되지 않음.

## 1. 기획 기준

- 청중, 목적, 발표 시간, 산출물 형식이 명확한가.
- 한 슬라이드에 하나의 핵심 역할만 있는가.
- 전체 흐름이 도입 → 맥락/문제 → 근거 → 정리/행동으로 이어지는가.
- 같은 형태의 슬라이드가 반복되어 지루하지 않은가.

## 2. 시각자료 기준

- 주요 슬라이드가 텍스트만으로 끝나지 않는가.
- 이미지, 도표, 지도, 타임라인, 캡처, AI 이미지의 역할이 명확한가.
- 이미지는 슬라이드 주장과 직접 연결되는가.
- AI 이미지는 사료/증거가 아니라 보조 일러스트로 표시되는가.

## 3. 줄바꿈/정렬 기준

- 한국어 줄바꿈이 어절 단위로 되어 있는가.
- 단어 중간, 고유명사 중간, 숫자 라벨 중간에서 끊기지 않는가.
- `01`, `02`, `10` 같은 섹션 번호가 두 줄로 갈라지지 않는가.
- 제목 줄바꿈이 의미 단위에 맞는가: 주어/서술어, 원인/결과, 문제/해결, 대비/결론.
- 마지막 줄에 짧은 단어 하나만 외롭게 남지 않는가.
- 제목, 본문, 카드, 이미지의 왼쪽 기준선이 의도에 맞게 정렬되어 있는가.

## 4. 레이아웃 기준

- 텍스트, 이미지, 카드, 푸터가 겹치지 않는가.
- 카드 내부 여백이 충분한가.
- 헤더, 페이지 번호, 푸터 위치가 일관적인가.
- 이미지 영역과 텍스트 영역이 침범하지 않는가.
- 첫 페이지와 마지막 페이지가 완성도 있게 연결되는가.

## 5. 숫자/배지/아이콘 기준

- 동그라미 숫자나 배지가 본문보다 과하게 크지 않은가.
- 배지가 위아래 줄을 침범하지 않는가.
- 숫자와 아이콘이 장식이 아니라 정보 구조를 돕는가.

## 6. 도표/SVG/화살표 기준

- 선과 화살표가 실제 대상에 정확히 연결되는가.
- 화살표가 텍스트나 카드와 겹치지 않는가.
- SVG가 떠 있거나 끊긴 것처럼 보이지 않는가.
- 복잡하면 화살표 대신 번호 단계나 단순 흐름도로 바꿨는가.

## 7. 이미지 기준

- 이미지의 주제가 슬라이드 크기에서도 분명히 보이는가.
- 텍스트가 복잡한 이미지 위에 직접 올라가지 않는가.
- 인물 얼굴, 지도, 질감, 고대비 영역 위에 본문을 얹지 않았는가.
- 생성 이미지에 가짜 글자, 왜곡된 상징, 어색한 디테일이 없는가.

## 8. 최종 QA 기준

- PDF로 렌더링해 실제 보이는 상태를 확인했는가.
- contact sheet로 전체 페이지를 한눈에 점검했는가.
- 표지, 섹션 시작, 도표, 활동/퀴즈, 마지막 페이지를 큰 이미지로 확인했는가.
- PDF가 통과한 뒤에만 PPTX로 export했는가.

## 100점 채점표

- 가독성 + 한국어 줄바꿈: 20
- 정렬 + 여백: 20
- 시각자료 적합성: 20
- 도표/SVG/화살표 완성도: 15
- 슬라이드 리듬과 변주: 10
- 표지/마무리 완성도: 10
- export 검증 증거: 5

## 즉시 fail 조건

- 텍스트와 이미지가 겹침.
- 섹션 번호나 핵심 라벨이 줄바꿈됨.
- 한국어 단어가 중간에서 끊김.
- 주요 도표의 선/화살표가 끊기거나 애매함.
- 마지막 페이지의 제목/이미지/마무리 문구가 서로 침범함.
- 전체 점수 90점 미만.

## 리뷰 기록 템플릿

```text
pt-qa-result: pass/fail
score: __/100

P0 hard fails:
- page __: ...

P2 polish candidates:
- page __: ...

fixes applied:
- ...

rerendered: yes/no
contact-sheet-reviewed: yes/no
full-size-pages-reviewed: cover, section openers, diagrams/SVGs, activities/quizzes, final
pptx-export-allowed: yes/no
```
