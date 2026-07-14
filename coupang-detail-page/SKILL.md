---
name: coupang-detail-page
description: 원본 상품과 실제 스타일 레퍼런스를 분리하고 RAW→REFERENCE→REASON→PROOF→PAGE(R2P) 계보로 쿠팡 모바일 상세페이지를 기획·생성한다. 동일·유사 상품과 공개 인기 사례를 웹 조사하되 순위·타사 기능은 현재 상품 카피로 옮기지 않는다. 디자인보다 기능·호환·실측·구성·사용법·관리·안전을 먼저 배치하고, 독점 구매 질문 수에 따라 3~10장(보통 5~8장)만 선택해 반복 비교·추천·요약을 삭제한다. plan-review.html에서 장별 카피·화면·RAW·증거·레퍼런스 원리를 먼저 검토받고, 소스 해시가 일치하는 사용자 승인 뒤에만 built-in image_gen 또는 모션을 실행·검수한다. 기본 800x2400 PNG, 폰트 계획, GIF·영상 TOP3와 선택적 ComfyUI 실행·핸드오프를 납품한다. 쿠팡 상세페이지, 여러 카테고리 상품 분석, 원본·레퍼런스 매칭, 기능·실측 우선 소구, 중복 없는 가변 장수 기획, HTML 승인, GIF·영상 스토리보드 요청에 사용한다.
---

# 쿠팡 상세페이지 근거 기반 가변 장수 생성

## 완료 계약

- 기획안이나 프롬프트에서 멈추지 않고 사용자가 승인한 장수의 최종 이미지를 실제로 생성한다.
- 기본 범위는 3~10장이며 보통 5~8장이다. `정보 단위 수 = 선정 장수`를 원칙으로 하고 10장을 목표로 내용을 늘리지 않는다.
- 각 장은 built-in `image_gen`을 별도로 호출한다. 한 장짜리 분할 콜라주나 단순 변형 여러 개로 대체하지 않는다.
- 정상 경로는 장별 한 번의 호출 안에서 제품·배경·레이아웃·타이포그래피·승인된 한국어 카피를 함께 완성하는 것이다.
- 텍스트 없는 이미지를 먼저 만들고 후편집하는 방식을 기본 경로로 사용하지 않는다.
- 결과를 장마다 직접 시각 검사하고 이상한 장만 다시 생성한다. 통과한 장은 잠근다.
- 최종 파일은 `page-01.png`부터 승인된 마지막 번호까지 빠짐없이 연속하며 기본 크기는 모두 `800x2400`이다.
- 모든 주장과 시각적 암시는 사용자 정보, 원본 또는 허용된 웹 근거에 연결한다. 비슷한 상품의 설명을 현재 상품 사실로 옮기지 않는다.
- 검증되거나 사용자가 명시적으로 확인한 기능적 구매 이유가 있으면 디자인·분위기보다 먼저 설명한다. 디자인은 기능을 대체하지 않고 이해·차별화·선호 판단을 돕는 보조 소구로 둔다.
- 각 장은 다른 장에 없는 독점 정보 단위를 최소 하나 소유한다. 새 정보 없이 기존 장점을 바꿔 말하는 비교·추천·활용·CTA 장은 삭제하거나 앞 장에 병합한다.
- 각 장의 RAW·Fact·Proof·Reference 원리·Page 연결이 `asset-map.md`에 없으면 기획 HTML을 만들지 않는다. 생성 결과와 스타일 레퍼런스는 상품 사실의 근거가 아니다.

## 시작 전에 반드시 읽을 문서

선택한 문서는 끝까지 읽은 뒤 행동한다.

- 모든 프로젝트: [references/prompt.txt](references/prompt.txt) — 사용자가 제공한 `prompt.txt`를 중복 없이 정리한 기획 기준
- 모든 프로젝트의 자산·근거·페이지 연결: [references/r2p-planning-method.md](references/r2p-planning-method.md)
- 문제 훅·가변 장수·정보 독점·증명형 영상: [references/hook-uniqueness.md](references/hook-uniqueness.md)
- 첫 실행·빈 프로젝트·사용법 요청: [references/onboarding.md](references/onboarding.md)
- 원본 또는 웹 확인 상품 이미지 사용: [references/original-images.md](references/original-images.md)
- 스타일 분석·가변 장수 구성: [references/real-references.md](references/real-references.md)
- 여러 상세페이지의 정보 밀도·후킹·모듈 패턴 분석: [references/detail-page-patterns.md](references/detail-page-patterns.md)
- 카테고리 선택·RAW 촬영·모션 참고: [references/case-studies-001-010.md](references/case-studies-001-010.md) — 2026-07-13 공개 사례 스냅샷; 수치 전이 금지
- 동일·유사 제품 조사, GIF·영상 또는 ComfyUI 기획: [references/research-motion.md](references/research-motion.md)
- 기획 HTML 검토, 사용자 승인과 정적·모션 생성 차단: [references/approval-generation.md](references/approval-generation.md)
- ComfyUI live 실행·검증된 워크플로 핸드오프 증빙: [references/comfyui-receipt-schema.md](references/comfyui-receipt-schema.md)

## 온보딩 대화 규칙

- 첫 실행에서는 저장 위치, 웹 조사, 정보 단위에 따른 장수 결정, 기획 HTML 검토·승인, ComfyUI 확인, 장별 생성, QA, `800x2400` 납품을 먼저 짧게 설명한다.
- 한 응답에 질문은 정확히 하나만 한다. 이미 확인한 내용은 다시 묻지 않는다.
- 모든 선택 질문은 번호 보기로 제시하고 마지막 보기는 항상 `N. 다른 답변하기`로 둔다.
- 추천안은 `(추천)`이라고 표시할 수 있지만 자동으로 선택하지 않는다. 제안이 맞지 않을 수 있음을 전제로 한다.
- 사용자는 번호만 답하거나 `N. 원하는 답변`으로 자유 답변을 함께 보낼 수 있다. `다른 답변하기` 번호만 오면 다음 응답에서 원하는 내용 하나만 묻는다.
- 답을 받을 때마다 저장한 값 하나를 확인하고 다음 질문 하나만 한다.
- 사진에서 관찰한 후보도 확정 사실로 저장하기 전에 번호 선택으로 확인받는다.
- 기획 승인 전에는 ComfyUI 여부를 묻지 않는다. 승인 뒤에도 한 번에 하나씩 `정확한 motion-NN 선택 → GIF·VIDEO 범위 → CAPTURE_MODE에 맞는 환경 → 정적 승인 → GIF·영상 또는 핸드오프 승인 → 최종 실행 승인` 순서로 묻는다.
- 모든 승인 질문에도 `다른 답변하기`를 포함한다. `generation-gate.md`에 사용자 응답이 기록되고 대상 검사가 통과한 뒤에만 `image_gen`, GIF·영상 렌더 또는 ComfyUI를 호출한다.

## 진행 중 멘트 규칙

사용자가 작업이 멈췄다고 느끼지 않도록 실행 과정 자체를 짧고 구체적으로 중계한다. 이 규칙은 선택 사항이 아니다.

- 도구를 처음 호출하기 전에 현재 시작 단계와 바로 다음 단계를 알린다.
- `입력 확인`, `웹 조사`, `정보 단위·장수 결정`, `HTML 검토·승인`, `생성`, `QA·재생성`, `정규화·납품`의 일곱 관문을 지날 때마다 한 번 이상 진행 상황을 알린다.
- 한 번의 업데이트에는 `완료한 것 / 현재 하는 것 / 다음 할 것`을 한두 문장으로 담는다.
- 생성 중에는 시작 전에 `N/전체 장수 생성 시작`, 결과를 저장·검수한 뒤 `N/전체 장수 결과와 PASS/RETRY`를 알린다. 여러 장을 병렬로 만들 때도 최소 두 장마다 누적 현황을 알린다.
- 재생성이 필요하면 숨기지 말고 실패 항목과 다음 시도를 즉시 알린다. 통과하지 않은 장을 완료라고 말하지 않는다.
- 진행 중 업데이트 없는 상태가 60초를 넘지 않게 한다. 오래 걸리는 호출 전에는 무엇을 기다리는지 먼저 알린다.
- 진행 멘트는 광고 문구나 장황한 작업 일지가 아니라 사용자가 결과를 예측할 수 있는 상태 보고여야 한다.

## 필수 입력

- 상품명, 카테고리, 가능하면 브랜드·모델명/SKU·라벨 표기
- 가장 중요한 기능적 구매 이유와 근거, 핵심 장점 3가지, 타깃 고객, 대표 불편, 사용 상황과 방법
- 구성품, 소재, 색상, 크기 등 확인 가능한 사양
- 검증된 차별점, 강조할 분위기, 주의사항과 금지 표현
- 객관적 수치·인증·시험 정보 또는 `없음`
- 실측 전체 길이·펼친 폭·입구 폭·커프 길이와 측정 사진 또는 `미측정`
- 판매 구성 수량이 `한 장 / 한 쌍 / 두 세트` 중 무엇인지 사용자 확인
- 실물 샘플·실사 촬영 가능 여부, 실제 시험 원본과 촬영 조건 또는 `없음`
- 제품 외형을 확인할 수 있는 원본 상품 이미지 1장 이상
- 선택 사항: 스타일·구성 참고용 실제 상세페이지 이미지 1~3장

필수 사실이 없으면 임의로 채우지 않는다. 비필수 정보는 보수적으로 생략한다. 이미지와 텍스트가 충돌하거나 정확한 외형을 확인할 원본이 없으면 한 번에 질문 하나로 확인한다.

### 기능 우선 계약

- 기획 전에 `핵심 기능 소구 / 기능 근거 Fact ID / 기능이 답하는 구매 불편 / 디자인 보조 소구 / 기능 우선 적용 장`을 확정한다.
- 기능에는 성능뿐 아니라 실제 사용 편의, 구조, 안전, 구성, 시간·노력 절감처럼 고객이 제품을 사는 실용적 이유를 포함한다.
- 확인된 기능이 있으면 01과 02 또는 03에서 기능이 답하는 구매 불편, 작동 구조와 허용 범위를 먼저 보여준다. 선정 장수가 3~4장이면 별도의 증거 장을 강제하지 않고 해당 정보 장 안에 증거와 경계를 결합한다.
- 디자인, 색, 무드, 코디는 핵심 기능을 설명한 뒤 보조 소구로 둔다. 기능이 확인됐는데 디자인만으로 01~03을 채우면 기획 실패다.
- 객관 수치가 없더라도 사용자가 직접 확정한 정성적 기능명은 그 범위 안에서 사용할 수 있다. 수치, 지속 시간, 소재 원리, 경쟁 우위나 효능 보장으로 확대하지 않는다.
- 확인 가능한 기능이 없으면 만들지 않는다. `핵심 기능 소구: 없음`과 이유를 기록하고, 구조·사용법·구성처럼 관찰 가능한 실용 정보로 대체한다. 본질이 미적 선택인 상품만 사용자 확인 뒤 디자인을 선두에 둘 수 있다.
- `plan-gate.md`의 기능 우선 상태가 완료되지 않으면 `validate_plan.py`가 실패해야 하며, `plan-review.html`은 기능 소구와 디자인 보조 소구를 장별 카드보다 먼저 보여준다.

## 프로젝트 구조

세 자리 숫자로 실행을 분리한다. 첫 프로젝트는 `001`, 다음은 `002`이며 삭제된 번호를 자동 재사용하지 않는다.

```text
coupang-detail-page/
├── workflow.html
├── inputs/
│   └── <project-no>/
│       ├── product-info.md
│       ├── original-images/
│       ├── evidence/
│       ├── web-confirmed/
│       └── real-references/
└── outputs/
    └── <project-no>/
        ├── raw/
        │   └── retries/
        ├── final/
        ├── web-research.md
        ├── detail-page-analysis.md
        ├── fact-ledger.md
        ├── asset-map.md
        ├── plan-gate.md
        ├── plan-review.html
        ├── generation-gate.md
        ├── prompt-set.md
        ├── execution-log.md
        ├── qa-report.md
        ├── font-plan.md
        ├── motion-plan.md
        └── video-plan.md
```

원본 상품 이미지는 `inputs/<project-no>/original-images/`, 실측·실사 시험은 `evidence/`, 웹 확인 보조는 `web-confirmed/`, 스타일 레퍼런스는 `real-references/`에 저장한다. `WEB_MATCH`를 `original-images/`에 둔 상태는 허용하지 않는다. 과거 자료도 생성 전에 `web-confirmed/`로 이동하고 `product-info.md`·`asset-map.md`의 경로와 실제 SHA256을 갱신한다. 실행 데이터는 Git에 커밋하지 않는다. 상품 실행 이미지를 지침용 `references/`에 넣지 않는다.

설치 직후 `python3 scripts/init_project.py --prepare 1`, 다음 프로젝트부터 `python3 scripts/init_project.py`를 사용한다. 기존 파일을 덮어쓰지 않는다. 로컬에 있는 이미지는 원본을 보존하며 표준 폴더로 복사한다.

## 작업 흐름

### 1. 입력을 검사한다

1. 프로젝트 번호를 확정하고 `product-info.md`와 네 자산 폴더를 읽는다.
2. 대화 첨부는 임시 입력으로만 센다. 원본 바이트를 `inputs/<project-no>/`의 역할별 폴더에 먼저 보존하고 `asset-map.md`에 실제 SHA256을 기록하기 전에는 기획 증거, 승인 대상 또는 생성 입력으로 사용할 수 없다. `--conversation-originals <count>`는 아직 저장하지 못한 첨부 수를 진단하는 옵션일 뿐 READY를 만들지 않는다.
3. 모든 로컬 이미지를 `view_image`로 확인한다.
4. 사용자 원본은 `RAW_PRIMARY/RAW_DETAIL`, 실측·실사 시험은 `RAW_MEASUREMENT/RAW_DEMO`, 웹 동일·유력 이미지는 `WEB_MATCH`, 스타일 자료는 `REF_*`로 분리한다.
5. 모든 자산의 실제 SHA256, 출처, M/E 등급, 관찰 사실, 허용·금지 용도를 `asset-map.md` Asset Registry에 기록한다. AI 생성본과 유사 상품은 RAW가 아니다.

#### 정적 비교 장면 기본값

- 사용자가 정성적 불편과 현재 상품의 기능·구조를 확인했지만 실제 비교 사진이 없으면, 비교 사진 업로드를 기본으로 요구하지 않는다. 승인된 정적 페이지 생성 단계에서 `image_gen`으로 일반적인 문제 상황과 현재 상품 사용 장면을 `AI_ILLUSTRATION`으로 만든다.
- 생성 비교컷은 이해용 연출이지 실제 비교 시험·상품 증거가 아니다. `asset-map.md`의 `PROOF_MODE`를 `AI_ILLUSTRATION`으로 두고 `실제 비교 시험·압박 수치·효과 보장 근거가 아님`을 `CLAIM_BOUNDARY`에 기록한다.
- 경쟁사·브랜드·고유 제품을 재현하지 않고 무브랜드 일반형만 사용한다. 상처·신체 변화·측정 장비·결과 배지·수치·`입증`, `테스트`, `더 우수` 같은 실증 표현을 넣지 않는다.
- 현재 상품은 매 호출마다 승인된 `RAW_PRIMARY`·`RAW_DETAIL`을 다시 전달해 외형을 보존한다. 생성한 일반형 비교 제품이나 이전 출력은 RAW로 승격하지 않는다.
- 실제 비교 사진은 사용자가 실증 비교를 명시적으로 원하거나 물성·성능 주장이 실제 시험을 필요로 할 때만 요청한다. AI 비교 장면도 기획 HTML 승인과 정적 생성 게이트 통과 뒤에만 만든다.

### 2. 동일 제품과 여러 유사 상세페이지를 반드시 웹 조사한다

모든 프로젝트에서 생성 전에 웹 검색을 실행한다. 결과가 없어도 검색어와 `동일 제품 확인 못함`을 `web-research.md`에 남긴다. 인터넷 접근 자체가 불가능하면 생성 준비가 완료된 것으로 보고하지 않는다.

- 동일 제품 검색: 상품명, 브랜드·모델명/SKU, 라벨의 고유 문구, 패키지와 외형 특징을 조합한다.
- 유사 제품 검색: 같은 카테고리, 사용 상황, 디자인 특성, 구매 불편 키워드를 조합한다.
- 동일성: `M1 확정`, `M2 유력`, `M3 유사`, `M0 불일치·확인 불가`.
- 출처 강도: `E1 공식`, `E2 신뢰 판매처`, `E3 마켓플레이스·개인 판매`, `E4 카테고리 자료`.
- `M1+E1/E2`의 명시 사실만 카피 후보로 제안할 수 있다.
- `M1/M2+E3`는 외형·착용 구조 보조 확인에만 사용한다.
- `M3/E4`는 문제 각도, 촬영 장면, 정보 구조와 카테고리 표현 연구에만 사용하고 상품 사실로 쓰지 않는다.
- 검색 결과를 자동으로 스타일 레퍼런스에 넣거나 제3자 상세페이지·카피·고유 디자인을 복제하지 않는다.
- 웹 자료가 사용자 원본과 충돌하면 사용자 원본을 우선하고 필요한 경우 한 질문으로 확인한다.
- 접근 가능한 실제 상세페이지를 최소 3개 비교한다. 가능하면 `동일·유력 제품 1개 + 같은 카테고리 2개 이상 + 정보 구조가 좋은 패션 상세페이지 1개`를 본다.
- 각 페이지에서 `첫 훅`, `설명 문단`, `카드·칩`, `디테일 캡션`, `비교·추천·CTA`, `타이포 계층`, `과장·혼잡 요소`를 표로 기록한다.
- 특정 URL이 차단되면 접근한 것처럼 분석하지 않는다. 차단 사실을 기록하고 검색 색인 또는 다른 접근 가능한 페이지로 패턴 표본을 보완한다.
- 채택하는 것은 정보 순서와 추상적 구성 원리다. 제3자의 실제 문구, 수치, 로고, 고유 그래픽과 제품 기능은 현재 상품으로 옮기지 않는다.
- 공개 순위·최근 구매량·리뷰 수는 사례 선정 근거와 조사일 스냅샷으로만 기록한다. 현재 상품 카피, 예상 판매량이나 성능 근거로 쓰지 않는다.
- 내려받은 `WEB_MATCH`·`REF_*`는 `web-research.md`에서 한 행에 정확히 한 `ASSET_ID`와 canonical 출처 URL을 연결한다. 서로 다른 로컬 SHA256 자산을 같은 direct image URL에 연결하지 않는다. 같은 HTML 상품 페이지에서 여러 컷을 얻었어도 자산별 행과 실제 파생·캡처 관계를 분리해 기록한다.
- 현재 카테고리와 작동 방식이 가까운 사례는 [references/case-studies-001-010.md](references/case-studies-001-010.md)에서 고르되, 매 실행에서 원문 접근 상태와 현재 정보를 다시 확인한다.

### 3. R2P 자산 계보·사실 원장·가변 장수 계획을 잠근다

먼저 `fact-ledger.md`에 허용 사실과 금지 주장을 기록한 뒤, 사실을 구매자가 실제로 궁금해하는 독점 정보 단위로 묶는다.

```text
INFO_ID | 구매 질문 | 독점 Fact ID | 필수 시각 증거 | 다른 장과 겹치지 않는 새 정보 | 상태
```

`asset-map.md`에는 `Asset Registry / Evidence Ledger / Reference Principle Ledger / Page Source Contract` 네 표를 채운다. 사용자 진술 치수에 자 사진이 없으면 `USER_DECLARED_SPEC / USER_CONFIRMED_NO_PHOTO`로 표시한다. 원본에 보이는 수량은 `PACKAGE_VISIBLE`이며 판매 구성 `PACKAGE_SALE`로 승격하지 않는다.

각 페이지 계약은 다음 계보를 가져야 한다.

```text
PAGE_NO / INFO_ID / DECISION_STAGE
RAW_ASSET_IDS / REF_PRINCIPLE_IDS / PROOF_ID / PRIMARY_FACT_IDS
PROOF_MODE / EXCLUSIVE_GAIN / DROP_TEST / CLAIM_BOUNDARY
```

다음 두 게이트를 `plan-gate.md`에 채운다.

```text
핵심 기능 소구: <가장 중요한 기능 또는 없음>
기능 근거 Fact ID: <Fact ID 또는 없음>
기능이 답하는 구매 불편: <실용적 문제>
디자인 보조 소구: <기능 뒤에 설명할 외형·무드>
기능 우선 적용 장: <실제 선정 장 중 번호>
기능 없음 사유: <기능이 없을 때만>
기능 우선 상태: 완료

정보 단위 수: <중복 제거 뒤 개수>
선정 장수: <3~10>
장수 결정 근거: <왜 이 장수면 충분한지>
삭제·병합 역할: <반복 때문에 없앤 비교·추천·요약 등>
장수 결정 상태: 완료
```

- `선정 장수`는 정보 단위 수와 같아야 한다. 독립 CTA가 기존 요약만 반복하면 만들지 않고 마지막 정보 장에 CTA를 붙인다.
- 기본 필수 흐름은 `01 PROBLEM_HOOK → PRODUCT_INTRO → 근거 있는 정보 장들 → 마지막 정보+CTA`다. `PROBLEM_HOOK`은 공포 마케팅이 아니라 카테고리에서 가장 큰 실패 위험을 여는 역할이며, 핏·호환·스펙·사용·맛/선호 질문으로 구체화할 수 있다.
- 허용 역할 예: `FIT_STRUCTURE`, `FEATURE_EVIDENCE`, `MEASURED_SIZE`, `COMPONENTS`, `OPTIONS`, `HOW_TO_USE`, `CARE_GUIDE`, `SAFETY_GUIDE`, `SITUATION_USE`, `NEUTRAL_COMPARE`, `USE_CASES`, `SPEC_CTA`, `GUIDE_CTA`, `OPTIONS_CTA`.
- `NEED_REASON`, `NEUTRAL_COMPARE`, `RECOMMENDATION`, `USE_CASES`, 독립 `CTA`는 새 독점 정보가 있을 때만 사용한다. 역할을 채우기 위해 만들지 않는다.
- 실측은 현재 판매 제품을 편평하게 놓고 잰 사용자 수치·자 사진, 또는 모델이 일치하는 공식 M1+E1/E2 표만 허용한다. 유사 제품·사진 비율·후기에서 치수를 추정하지 않는다.
- 길이에 관한 후기처럼 구매 반론이 발견되면 실측 페이지의 우선순위를 올리되, 후기 문장을 제품의 보편 사실로 바꾸지 않는다.

장별 표에는 아래 열을 빈칸 없이 둔다.

```text
장 | ROLE_ID | 역할 | 필수 모듈 | 고유 구매 질문 | INFO_ID | PRIMARY_FACT | 필수 시각 증거 | H1 핵심어 | SHOT_ID | SCENE_ID | LAYOUT_ID | 다음 장과 연결 | 모션 역할
```

- 페이지는 `01`부터 선정 장수까지 빠짐없이 연속한다. INFO_ID·고유 질문·PRIMARY_FACT·PROOF_ID·SHOT_ID·SCENE_ID·LAYOUT_ID를 재사용하지 않는다. 서로 다른 기능 증거처럼 정보·Fact·Proof가 다르면 같은 ROLE_ID를 반복할 수 있지만 PRODUCT_INTRO는 한 번만 쓴다.
- 각 장은 다른 장에 없는 독점 Fact ID 또는 관찰 가능한 정보 역할 하나를 소유한다. 소개 장에서 다른 장의 결론을 미리 나열하지 않는다.
- 동일한 4어절 이상 카피, 같은 구매 논리, 제품 크롭, 모델·행동·포즈와 지배 레이아웃을 재사용하지 않는다.
- 한 장을 삭제해도 구매자가 잃는 새 정보가 없다면 그 장을 삭제한다. 추천 대상과 활용 장면의 문구만 바꾼 반복은 같은 장으로 병합한다.
- 한 장의 모든 문자열은 `EYEBROW / H1 / BODY / CARD·CHIP·CAPTION / CTA` 매니페스트로 먼저 고정한다. 승인 문자열 밖의 문구를 생성하지 않는다.
- 가격·리뷰·수치·소재·인증·시험·효능은 근거 범위를 넘어 만들지 않는다.

`python3 scripts/validate_plan.py <project-no>`, `python3 scripts/validate_asset_map.py <project-no>`와 [references/hook-uniqueness.md](references/hook-uniqueness.md)의 의미 중복 검사를 모두 통과하지 못하면 생성 승인을 묻지 않는다. 자산 검사는 실제 파일 해시, Fact 출처, 레퍼런스 오용, 페이지별 Proof와 Fact 집합 중복까지 확인한다.

### 4. 공통 카피·타이포·디자인 시스템을 만든다

`font-plan.md`에 정지·GIF·세로 영상의 실제 폰트 계열, 사용 굵기, 크기 토큰, 안전 여백과 조판 환경을 먼저 잠그다. 사용 가능한 굵기가 다른 대체 서체로 바뀌면 줄바꿈·자폭 QA를 다시 한다. 폰트 파일을 납품물에 포함할 때는 배포 라이선스를 확인한다.

`prompt-set.md`에 한 번 확정한 아래 블록을 승인된 모든 장의 프롬프트에 동일하게 적용한다.

```text
COPY_SYSTEM
- voice: 전체 장에서 같은 말투, 짧은 제목과 자연스러운 설명 문장
- hook: 01은 고객 중심 문제 공감 훅, 나머지는 각 장의 독점 구매 질문에 답하는 큰 한국어 메시지
- priority: 확인된 핵심 기능과 그것이 해결하는 불편을 먼저, 구조·사용 증거를 다음, 디자인·무드를 마지막 보조 정보로 배치
- manifest: EYEBROW / H1 / BODY / CARD·CHIP / CAPTION / CTA 중 장의 역할에 맞는 필드
- density: 3~6개 세로 정보 구역, 구역마다 한 메시지, 카드·캡션은 중복 없이 구체적으로
- exact copy only: 매니페스트 문자열의 축약·의역·누락·추가 금지

TYPOGRAPHY_SYSTEM
- family: 전체 장에서 같은 인상의 현대적인 한국어 산세리프 한 계열
- weight: H1 800~900 / H2·카드 제목 700~800 / BODY 500~600 / 라벨·캡션 600 이상
- hierarchy at 800px source: H1 72~104px / H2 44~64px / BODY 32~40px / 모든 라벨·캡션 최소 32px
- mobile minimum: 800px 원본을 400 CSS px로 볼 때 모든 정보 문구가 16px 이상이 되게 하며, 32px보다 작은 소문자·각주를 만들지 않음
- contrast: 밝은 배경에는 짙은 글자, 사진에는 충분한 단색 여백 또는 고대비 오버레이
- alignment: 정한 정렬 규칙과 줄 간격을 전체 장에 일관되게 유지
- forbidden: 서체 인상 변화, 제각각인 자폭·획 모양, 작은 각주, 얇은 글자, 장식체 혼용, 낮은 대비, 글자 겹침·잘림

DESIGN_SYSTEM
- palette / product treatment / lighting / cards / icons / spacing / CTA
- `RAW_PRIMARY`·`RAW_DETAIL`에서 잠근 상품 불변 요소
- `REF_*`에서 추출한 추상 원리와 복제 금지 요소
```

전체 기획의 카피, 후킹, 읽는 순서와 타이포 체계는 6단계의 `plan-review.html`에 포함해 번호 선택으로 승인받는다. 승인 전 생성하지 않는다.

### 5. 제품 고유 특징을 증명하는 GIF·영상 기회를 함께 기획한다

가변 장수 기획과 동시에 `motion-plan.md`를 작성한다. 각 장에 `정지 이미지 유지`, `GIF 추천`, `짧은 영상 추천` 중 하나를 표시하고 움직임이 구매 이해를 실제로 높이는 경우에만 추천한다.

- 후보마다 `구매 반론 / 한정 주장 / 시험 또는 동작 / 화면에서 판정 가능한 결론`을 먼저 고정한다. `문제·반론 1초 → 실제 제품의 한 시험·동작 2~4초 → 확인 가능한 결과 1~2초`의 구조를 우선한다.
- 모든 후보에 `CAPTURE_MODE`를 `REAL_TEST / REAL_DEMO / AI_ILLUSTRATION / NO_PROOF_HOOK` 중 하나로 기록한다. 물성·성능·내구·고정력·효능처럼 물리적 결과를 증명하려면 실제 동일 제품을 촬영한 `REAL_TEST`가 필수다. `REAL_DEMO`는 눈으로 확인되는 구조·착용·조작만 설명할 수 있다.
- 생성형 영상과 ComfyUI 결과는 `AI_ILLUSTRATION`이며 이미 허용된 사실을 이해시키는 연출로만 사용한다. 실제 성능의 증거가 아니므로 `테스트`, `입증`, `버틴다`, `된다` 같은 실증 카피를 붙이지 않는다.
- 모든 후보를 `동작 필요성`, `주장 안전성`, `전환 관련성`, `제작 실행성`, `제품 안정성`, `고유 소구 선명도`, `실증 후킹력` 일곱 축으로 각 0~20점 평가한다. 총점은 140점이다. `실증 후킹력`은 구매 반론을 실제 조건에서 반증 가능하게 시험하고 시청자가 결과를 직접 판정할 수 있는 정도다.
- TOP1은 `고유 소구 선명도`와 `실증 후킹력`이 각각 12점 이상이고 주장·제품 안정성 하드 게이트를 모두 통과해야 한다. `AI_ILLUSTRATION`의 `실증 후킹력`은 최대 5점이며 TOP1이 될 수 없다. 통과 후보가 없으면 장식·사용법 영상을 승격하지 말고 `CAPTURE_MODE: NO_PROOF_HOOK`과 필요한 실사 근거를 명시한다.
- 하드 게이트를 통과한 후보 중 모션으로 구매 반론을 가장 크게 줄이는 하나를 `가장 영상이 필요한 소구점`으로 명시한다.
- 점수 상위 후보를 `video-plan.md`의 TOP1~TOP3 스토리보드로 구체화한다. 각 보드에 `CAPTURE_MODE`, 한정 주장, 시험 조건·통제, 보이는 판정, 실사 원본 경로·편집 정책 또는 AI 연출 표시와 함께 삽입 위치, 캔버스, 길이, FPS, 루프, 타임라인, 제품 불변 요소와 QA를 기록한다.
- 영상의 광고 카피는 `font-plan.md`에 잠근 실제 폰트로 한 번 조판한 `FIXED_TEXT_LAYER`로 후합성한다. 프레임마다 글자를 재생성하지 않는다. 제품에 원래 붙은 물리 라벨은 원본 텍스처로 트래킹한다.

- 좋은 후보: 착용 순서, 접고 펴기, 질감·주름 움직임, 크기·구성품 전환, 사용 전 불편 상황에서 사용 장면으로 이어지는 변화.
- 피할 후보: 근거 없는 기능 효과, 신체 변화 Before/After, 의미 없는 장식 애니메이션.
- 충격·진동·파손 방지 같은 극적인 데모는 실제 동일 제품, 기록된 부하·환경, 안전한 촬영 조건과 핵심 시험 구간의 연속 원본이 있을 때만 `REAL_TEST`로 사용한다. 한 번의 촬영 결과를 일반적 보증으로 확대하거나 근거 없이 `부서지지 않는다`고 말하지 않는다.
- 기본 납품은 승인된 장수의 PNG다. GIF·영상 생성은 사용자가 별도로 선택했을 때만 실행한다.
- ComfyUI가 연결되어 있으면 시작·끝 프레임, 길이, FPS, 루프, 카메라, 제품 불변 요소, 네거티브 프롬프트와 입력 경로를 핸드오프로 제공한다.
- `AI_ILLUSTRATION`을 실제 생성하려면 ComfyUI 상태가 `CONNECTED`이고 helper receipt뿐 아니라 생성 게이트 시점의 `/system_stats` 재확인도 성공해야 한다. `WORKFLOW_PROVIDED`는 구조가 검증된 ComfyUI 워크플로를 함께 넘기는 핸드오프 전용 상태이며 실제 렌더 완료를 뜻하지 않는다. 워크플로 없는 문서·프롬프트 인계는 `HANDOFF_ONLY`다. 실제 동일 제품을 촬영하는 `REAL_TEST`·`REAL_DEMO`는 ComfyUI 없이 `NOT_REQUIRED`로 실제 제작할 수 있다.
- REAL_TEST·REAL_DEMO 실제 GIF·영상 실행에는 FFmpeg의 `ffprobe`가 필수다. RAW_TEST·RAW_DEMO 원본 클립의 decode 가능 여부, dimensions, duration, frames를 모두 검사하며 도구가 없거나 어느 값이든 확인되지 않으면 fail-closed한다.
- 모션 기획을 채운 뒤 `python3 scripts/validate_motion.py <project-no>`를 실행한다. 실패하면 증명형 영상 후보를 승인·납품하지 않는다.

### 6. `plan-review.html`로 사용자 검토를 받고 생성 범위를 잠근다

[references/approval-generation.md](references/approval-generation.md)의 순서와 질문 문구를 그대로 따른다.

1. `python3 scripts/check_project.py <project-no>`, `python3 scripts/validate_plan.py <project-no>`, `python3 scripts/validate_asset_map.py <project-no>`를 통과한다.
2. `python3 scripts/build_plan_review.py <project-no>`를 실행해 `outputs/<project-no>/plan-review.html`을 만든다.
3. HTML 링크를 사용자에게 제공하고 선정된 모든 장의 `주제 / H1·BODY·카드·캡션·CTA / 필수 화면 구성 / RAW·Proof·레퍼런스 원리 / 주장 경계 / 모션 후보`를 검토받는다.
4. 사용자가 `이 기획 확정`의 1번을 선택한 뒤에만 `generation-gate.md`에 `기획 검토 상태: 승인`, `YYYY-MM-DD · APPROVE_PLAN · ANSWER=1`, HTML의 `data-source-digest` 64자와 승인한 `plan-review.html` 파일 자체의 SHA256을 기록한다.
5. 다음 응답부터 한 질문씩 정확한 `motion-NN` ID, 지원 형식에 맞는 `STATIC_PLUS_GIF / STATIC_PLUS_VIDEO / STATIC_PLUS_GIF_VIDEO / STATIC_PLUS_MOTION_HANDOFF / STATIC_ONLY`, CAPTURE_MODE에 맞는 실행 환경을 차례로 선택받는다.
6. `CONNECTED`·`WORKFLOW_PROVIDED`는 `scripts/comfyui_receipt.py`가 실제 `/system_stats` probe 또는 구조가 유효한 프로젝트 내부 ComfyUI 워크플로 검증으로 만든 receipt JSON 없이는 기록하지 않는다. helper schema·tool marker·무결성 ID 계약에 맞지 않는 수기·generic JSON은 무효다. `CONNECTED`는 24시간 이내 receipt와 게이트 시점 live 재확인을 모두 요구한다. REAL_TEST·REAL_DEMO 실사 촬영은 `NOT_REQUIRED` 또는 live `CONNECTED`, AI_ILLUSTRATION 실제 생성은 live `CONNECTED`만 허용한다. `WORKFLOW_PROVIDED`는 `STATIC_PLUS_MOTION_HANDOFF`에만 쓴다. `receipt_id`는 외부 서명이 아니므로 실제 실행 상태는 live probe와 endpoint 정체성으로 판정한다.
7. 환경 선택은 `YYYY-MM-DD · SELECT_ENV · SCOPE=<범위> · MOTION=<정렬된 ID 또는 NONE> · COMFY=<상태>`, 최종 실행 승인은 `YYYY-MM-DD · APPROVE_EXECUTION · SCOPE=<범위> · MOTION=<정렬된 ID 또는 NONE> · COMFY=<상태>` 형식으로 정확히 기록한다. 날짜는 Asia/Seoul 오늘보다 미래일 수 없고 `기획 승인 ≤ 환경 선택 ≤ 최종 승인` 순서여야 한다. 정적 이미지 생성 승인과 GIF·영상 생성 또는 핸드오프 준비 승인을 서로 다른 질문으로 받고, 마지막 질문에서 선택 ID·형식·환경을 요약한다. 자유문·거절문·서로 모순된 기록은 승인으로 인정하지 않으며 세 승인은 서로 대신할 수 없다. `generation-gate.md`의 표준 필드는 각각 정확히 한 번만 존재해야 하고, `기획 리뷰 HTML`은 정확히 `plan-review.html`, `선정 모션 ID`는 `해당 없음` 또는 중복 없는 `motion-NN` 쉼표 목록이어야 한다.
8. 승인 뒤 `product-info.md`, 조사·분석, `plan-gate.md`, `fact-ledger.md`, `asset-map.md`, `prompt-set.md`, `font-plan.md`, `motion-plan.md`, `video-plan.md`는 승인 스냅샷으로 잠근다. 실제 시도 횟수·생성 파일·실패 사유·최종 해시는 `execution-log.md`와 `qa-report.md`에만 기록한다. 승인 소스에 실행 상태를 덮어써 해시를 깨지 않는다.

기획 승인 전에 ComfyUI 질문이나 마지막 생성 질문을 묻지 않는다. 승인 후 상품 정보·카피·장면·근거·자산 계보·프롬프트·폰트·TOP3를 바꾸면 소스 해시가 달라진다. `기획 검토 상태`, 두 승인 해시와 모든 생성 승인을 무효화하고 HTML부터 다시 만든다.

정적 이미지 생성 직전에는 아래 검사를 반드시 통과한다.

```bash
python3 scripts/validate_generation_gate.py <project-no> --target static
```

실제 GIF·영상 생성 직전에는 `--target motion`, ComfyUI 없는 인계 문서 확정 직전에는 `--target handoff`를 사용한다. `HANDOFF_ONLY` 또는 `STATIC_ONLY`는 실제 모션 생성 검사를 통과할 수 없다. 어느 검사든 실패하면 해당 생성 도구를 호출하지 않는다.

### 7. `image_gen`에서 디자인과 카피를 한 번에 생성한다

- 첫 호출 직전에 정적 생성 게이트를 다시 실행하고, 통과한 보고서를 확인한 뒤 장마다 독립된 `ads-marketing` 이미지 호출을 사용한다.
- 모든 호출에 같은 원본 세트와 같은 `COPY_SYSTEM`, `TYPOGRAPHY_SYSTEM`, `DESIGN_SYSTEM`을 다시 넣는다.
- 이전 생성본을 다음 장의 제품 기준으로 사용하지 않는다.
- 승인·생성에 쓰는 모든 원본은 번호 프로젝트에 저장하고 SHA256 계보를 만든 뒤 `referenced_image_paths`로 전달한다. 대화 전용 이미지를 `num_last_images_to_include`로 바로 생성에 쓰지 않는다.
- 결과를 `outputs/<project-no>/raw/page-NN.png`로 복사한다. 교체 전 결과는 `raw/retries/page-NN-attempt-K.png`로 보존한다.
- `prompt-set.md`의 장 번호·최종 프롬프트·참조 경로·허용 사실·출력 경로 계약은 승인 뒤 수정하지 않는다.
- 실제 호출마다 장 번호, 시도 번호, 사용 도구, 참조 경로, 생성 원본 경로, 실패 사유와 판정을 `execution-log.md`에 추가한다. 최종 장별 PASS/FAIL은 `qa-report.md`에 기록한다.

프롬프트의 고정 순서는 다음과 같다.

```text
사용 사례: ads-marketing
PAGE_NO / ROLE_ID / INFO_ID: <N> / <승인 역할> / <독점 정보 ID>, 변경 금지
ROLE_SUCCESS_CRITERIA / REQUIRED_MODULES / REQUIRED_VISUAL_EVIDENCE / ADVANTAGE_IDS: <plan-gate.md의 해당 셀>
자산 유형: 쿠팡 모바일 상세페이지, 내부 순서 <전체 장수 중 N장>, 픽셀 안에 장 번호 금지
설득 목적과 후킹: <이 장만의 고유 구매 질문과 H1 핵심어>
입력 역할: RAW_PRIMARY·RAW_DETAIL / RAW_MEASUREMENT·RAW_DEMO / WEB_MATCH / REF_*
R2P 자산 계보: RAW_ASSET_IDS / REF_PRINCIPLE_IDS / PROOF_ID / PROOF_MODE / CLAIM_BOUNDARY
제품 불변 요소: <형태·비율·색상·부품·라벨·구성품>
COPY_SYSTEM / TYPOGRAPHY_SYSTEM / DESIGN_SYSTEM: <공통 블록>
장면·구도: 800x2400, 1:3 초세로 캔버스, 안전 여백과 읽는 순서
카피 렌더링 작업: 아래 승인된 한국어를 완성 디자인 안에 직접 조판. 빈 영역·자리표시자 금지.
정확한 카피 매니페스트: EYEBROW "..." / H1 "..." / BODY "..." / CARD·CHIP·CAPTION ["...", "..."] / CTA "..."
필수 제약: 위 매니페스트의 모든 문구를 정확히 조판, 같은 한국어 산세리프 계열과 정해진 크기 토큰, 정보 구역 3~6개, 높은 대비, 모바일 16px 이상 가시성
금지 요소: 추가·깨진 한글, 더미 영문, 근거 없는 주장, 워터마크, 페이지 번호, 쿠팡 UI·로고, 레퍼런스 복제
```

### 8. 장별 의미·역할·비중복 QA 후 실패한 장만 재생성한다

매 호출 직후 `view_image`로 확인하고 `execution-log.md`에 시도 이력, `qa-report.md`에 장별 최종 판정을 기록한다.

- `TEXT`: 카피 매니페스트의 모든 문구와 글자 단위 일치, 자모·오탈자·누락·중복·더미 문구 없음, 자연스러운 줄바꿈, 같은 서체 인상·크기 체계, 모든 정보 문구가 800px 원본에서 최소 32px, 충분한 대비와 여백.
- `PRODUCT`: 실루엣·비율·색상·부품 수·라벨 위치·구성품 수 일치, 임의 추가·삭제·복제·합성 없음.
- `LAYOUT`: 큰 후킹 메시지가 먼저 보이고 3~6개 정보 구역의 위계가 명확함, 기능이 확인된 상품은 핵심 기능과 해결 불편이 디자인보다 먼저 읽힘, 글자·제품·카드가 겹치거나 잘리지 않음, 장별 모듈은 다양하지만 앞뒤 장과 무드·타입 토큰은 일관.
- `CLAIMS`: 금지 UI·로고·페이지 번호·허위 정보·시각적 효능 암시 없음.
- `ROLE`: 해당 번호의 승인 `ROLE_ID`, `INFO_ID`, 필수 모듈과 시각 증거가 화면에서 실제로 보임.
- `SOURCE_LINEAGE`: 화면의 제품·수치·실측·실사·레퍼런스 표현이 승인한 RAW·Proof·Reference 원리와 일치하며 생성 장면을 원본·시험으로 오인시키지 않음.
- `UNIQUENESS`: 다른 장과 INFO_ID, PRIMARY_FACT, 구매 질문, H1 논리, 제품 크롭, 모델·행동·포즈와 지배 레이아웃이 반복되지 않음.

전체 묶음에는 `FLOW`와 `INFORMATION_GAIN` QA를 추가한다. 페이지 번호가 연속이고 선정 장수와 일치하며, 모든 장을 하나씩 가렸을 때 사라지는 독점 정보가 있어야 한다. 사라지는 정보가 없는 장은 실패다.

하나라도 실패하면 결과를 재시도 폴더로 보존하고 실패 원인만 고친 프롬프트로 그 장만 다시 호출한다. 정적 텍스트는 승인 카피를 포함한 `image_gen` 직접 렌더링을 총 2회까지 우선 시도한다. 두 번째 직접 시도도 실패하면 사용자에게 `1. 승인 카피 FIXED_TEXT_LAYER 후편집 허용 / 2. image_gen 한 번 더 재생성 / 3. 카피 단순화 후 기획 재승인 / 4. 다른 답변하기` 중 하나만 묻고 응답·날짜를 제작 기록에 남긴다. 1번의 명시적 승인 전에는 정적 고정 텍스트 레이어를 사용하지 않으며, 제품·레이아웃·사실 오류는 후편집으로 승인하지 않는다. GIF·영상 광고 카피는 처음부터 고정 텍스트 레이어가 필수다.

### 9. `800x2400`으로 정규화하고 검증한다

built-in `image_gen`의 출력 픽셀은 고정되지 않으므로 프롬프트 문구만으로 규격 충족을 선언하지 않는다.

- 기본 비율은 `1:3`, 최종 크기는 `800x2400`이다.
- 정적 규격·decode 검사는 Pillow 자동 runtime과 제공된 안전한 fallback을 사용한다. fallback을 썼다는 이유로 통과를 선언하지 않고 최종 파일을 다시 열어 확인한다.
- 비균일 스트레칭은 금지한다.
- 단색 배경 확장이 안전하면 시각 확인 후 `--allow-background-pad`, 모든 핵심 요소가 중앙 안전 영역 안에 있을 때만 `--allow-center-crop`을 사용한다. 둘 다 안전하지 않으면 재생성한다.
- 실행: `python3 scripts/normalize_pages.py outputs/<project-no>/raw outputs/<project-no>/final [--allow-background-pad 또는 --allow-center-crop]`
- 하드 검증: `python3 scripts/validate_pages.py outputs/<project-no>/final`
- 정규화 뒤 raw 판정을 그대로 승격하지 않는다. 최종 전체 장을 다시 열어 `TEXT / PRODUCT / LAYOUT / CLAIMS / ROLE / UNIQUENESS / FLOW / INFORMATION_GAIN`을 재검사한다.

## 완료 조건

- `web-research.md`에 동일·유사 제품 검색어, URL, M/E 등급, 사용 범위가 있다.
- `detail-page-analysis.md`에 접근 가능한 여러 상세페이지의 훅·본문·카드·캡션·비교·CTA 패턴과 채택·회피 항목이 분석되어 있다.
- `prompt-set.md`에 승인된 전체 장의 카피와 공통 카피·타이포·디자인 시스템이 승인 스냅샷으로 유지된다.
- `execution-log.md`에 실제 장별 호출·재시도·실패 사유·선택 원본·최종 SHA256이 있고, 승인 소스 해시는 생성 전후 동일하다.
- `plan-gate.md`가 기능 우선·장수 결정 게이트와 각 장의 INFO_ID·고유 질문·PRIMARY_FACT·SHOT_ID·SCENE_ID·LAYOUT_ID를 포함하고 `validate_plan.py`를 통과한다.
- `asset-map.md`가 실제 SHA256, Fact→Proof, 추상 레퍼런스 원리와 모든 페이지 계보를 포함하고 `validate_asset_map.py`를 통과한다.
- `plan-review.html`이 핵심 기능·근거·해결 불편·디자인 보조 소구와 최신 기획의 장별 주제·카피·화면·RAW·Proof·레퍼런스 원리·모션 후보를 보여준다.
- `generation-gate.md`에 사용자 기획 승인 기록, 승인한 기획 소스 해시와 리뷰 HTML 파일 SHA256, 정확한 제작 범위·선정 모션 ID·환경 선택 기록, ComfyUI 상태와 필요한 증빙 JSON, 서로 분리된 정적·GIF·영상·최종 실행 승인이 기록되고 실행 대상의 `validate_generation_gate.py`를 통과한다.
- `qa-report.md`의 승인 장 전체가 `TEXT`, `PRODUCT`, `LAYOUT`, `CLAIMS`, `ROLE`, `SOURCE_LINEAGE`, `UNIQUENESS`, `INFORMATION_GAIN` 모두 `PASS`이며 전체 `FLOW`가 통과한다.
- 최종 폴더에 `page-01`부터 선정 장수까지 서로 다른 `800x2400` PNG가 빠짐없이 있다.
- 모든 장이 새 구매 정보를 하나씩 추가하며 마지막 정보 장에 중립 CTA가 있다.
- `motion-plan.md`에 정지/GIF/영상 추천과 ComfyUI 상태가 있다.
- `font-plan.md`에 실제 서체·굵기·크기 토큰, 정적 image_gen 직접 조판 우선·2회 실패 뒤 사용자 승인 시에만 허용하는 대체 `FIXED_TEXT_LAYER`, GIF·영상의 필수 고정 텍스트 방식이 있다.
- `motion-plan.md`의 후보가 7요소·140점으로 점수화되고 `CAPTURE_MODE`, `실증 후킹력`, `가장 영상이 필요한 소구점` 또는 `NO_PROOF_HOOK`이 명시되어 있다.
- `python3 scripts/validate_motion.py <project-no>`가 통과하고, `video-plan.md`에 TOP3 스토리보드, 실사 증거 조건 또는 AI 연출 표시, 고정 텍스트 레이어, 제작 제약·QA와 실행 상태가 있다.
- 입력에 없는 가격·리뷰·인증·수치·효능, 쿠팡 로고·앱 UI·페이지 번호가 없다.

마지막 응답에는 프로젝트 번호, 정보 단위 수와 선정 장수, 기획 검토 HTML과 승인 기록, 최종 이미지 경로, 리서치·프롬프트·실행 로그·QA·폰트·모션·영상 문서 경로, 재생성한 장, 파일 검증 결과, `가장 영상이 필요한 소구점`과 `CAPTURE_MODE`, 실사·AI 여부, ComfyUI 연결·실행 여부를 간결하게 보고한다.
