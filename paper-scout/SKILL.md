---
name: paper-scout
description: 웹에서 detection·feature-extraction·generative-detection 관련 논문/자료를 찾아 **핵심 contribution 을 구조화(contribution card)** 해서 뽑아온다. 설계 토론에서 어떤 주장·아이디어의 근거(선행연구·수치·메커니즘)를 확보해야 할 때 사용. "이 방식 선행연구 있나", "이 contribution 뭐가 새로운지", "근거 찾아와" 류 요청에 발동.
---

# paper-scout

설계 토론의 **근거 보급책**. 웹을 뒤져 논문/자료를 찾고, 각 자료에서 **핵심 contribution 만** 구조화해 돌려준다.
요약이 목적이 아니라 **"무엇이 새롭고, 왜 통하고, 우리(fm-det)에 적용 가능한가"** 를 뽑는 게 목적이다.

## 절차

1. **질문 고정** — 토론에서 검증하려는 게 무엇인지 한 줄로 적는다.
   (예: "feature upsampler 가 dense prediction 성능을 실제로 올렸나?", "generative/flow 기반 detector 의 선행연구와 한계는?")

2. **검색 fan-out** — `WebSearch` 로 2~4개 쿼리. arXiv·paperswithcode·저자 블로그·공식 repo 를 노린다.
   - 핵심어 + 연도 + "arxiv" / "object detection" / "feature upsampling" 식으로 변주.
   - SOTA 만 보지 말고 **반례·실패 보고·후속 비판** 도 한 쿼리 할당.

3. **원문 확보** — 상위 자료를 `WebFetch` 로 가져온다. 초록·method·실험표 위주. 접근 안 되면 추정하지 말고 그 사실을 적는다.

4. **contribution card 추출** — 자료당 아래 카드 한 장. **숫자는 원문에 있는 값만** (없으면 "미보고").

   ```
   ### <짧은 제목> (<저자/연도>) — <링크>
   - 문제:        <이 논문이 푸는 문제 1줄>
   - 핵심 아이디어: <한 문장. 가장 중요한 것 하나>
   - 메커니즘:    <어떻게 동작하는가. 왜 통하는지의 인과 1~2줄>
   - 결과:        <데이터셋/지표/수치 — 원문값. baseline 대비 Δ>
   - 무엇이 새로운가: <기존과의 차이점, 진짜 novelty>
   - 한계/반례:   <저자/후속이 인정한 약점, 안 통하는 조건>
   - fm-det 연관:  <우리 구조(VOC flow-matching detector, box compiler, ViT/AnyUp feat)에 적용 가능성·충돌점>
   ```

5. **종합 한 단락** — 카드들을 가로질러: 합의된 사실 / 논쟁 중인 점 / fm-det 에 대한 함의 / 아직 비어있는 근거(미확인) 를 구분해 적는다.

## 규칙

- **출처 없는 수치·주장 금지.** 모든 핵심 주장에 링크. 못 찾았으면 "근거 미확보" 라고 정직하게.
- SOTA 자랑이 아니라 **메커니즘과 반례** 를 우선한다. 토론은 반례로 단단해진다.
- 깊은 다중출처 교차검증이 필요하면 `deep-research` 스킬로 위임해도 된다(이 스킬은 빠른 근거 확보용).
- 결과는 한국어, 논문 제목·용어·코드는 원어 그대로.
