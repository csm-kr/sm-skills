# 원본 상품 이미지

## 목차

- [역할과 우선순위](#역할과-우선순위)
- [저장 위치](#저장-위치)
- [입력 목록 작성](#입력-목록-작성)
- [시각 검사](#시각-검사)
- [웹 동일 제품 대조](#웹-동일-제품-대조)
- [제품 불변 요소](#제품-불변-요소)
- [장별 원본 선택](#장별-원본-선택)
- [image_gen 전달](#image_gen-전달)
- [생성 결과 직접 검수](#생성-결과-직접-검수)
- [충돌과 한계](#충돌과-한계)

## 역할과 우선순위

원본 상품 이미지를 제품의 시각적 정체성과 확인 가능한 외관 사실의 기준으로 사용한다. 스타일 레퍼런스나 이전 생성본보다 항상 우선한다.

원본에서 직접 보이지 않는 뒷면, 내부 구조, 부품, 라벨 문구와 구성품을 추정하지 않는다. 사용자가 별도 사실로 제공했더라도 이미지로 확인되지 않는 외형은 보수적으로 표현한다.

## 저장 위치

실행에 사용하는 원본 상품 이미지를 다음 폴더에 저장한다.

```text
<skill-root>/inputs/<project-no>/original-images/
```

실측·실사 시험은 `evidence/`, 웹에서 동일·유력 판정한 이미지는 `web-confirmed/`, 스타일 자료는 `real-references/`에 둔다. 웹 파일을 `original-images/`에 둔 상태는 허용하지 않는다. 과거 실행 자료도 생성 전에 `web-confirmed/`로 이동하고 `product-info.md`·`asset-map.md`의 경로와 실제 SHA256을 갱신한다.

예시:

```text
inputs/001/original-images/front.jpg
inputs/001/original-images/side.jpg
inputs/001/original-images/detail.jpg
```

다른 위치의 파일은 원본을 보존한 채 이 폴더로 복사한다. 기존 파일을 덮어쓰지 않는다. 상품 이미지를 스킬의 `references/` 폴더에 저장하지 않는다.

## 입력 목록 작성

각 파일을 다음 형식으로 기록한다.

```text
ASSET_ID: A01
ROLE: RAW_PRIMARY | RAW_DETAIL | RAW_MEASUREMENT | RAW_DEMO | WEB_MATCH
경로: <skill-root>/inputs/<project-no>/original-images/<filename>
시점: 정면 | 측면 | 후면 | 상단 | 디테일 | 구성품 | 패키지
확인 가능: <형태, 색상, 부품, 라벨, 구성품>
가림/불확실: <보이지 않거나 판독할 수 없는 부분>
우선순위: primary | supporting
SHA256: <실제 파일 해시>
허용 용도:
금지 전이:
```

대표 정면 또는 3/4 이미지를 `primary`로 지정한다. 측면, 디테일과 구성품 이미지는 필요한 장에서만 보조한다.

## 시각 검사

로컬 파일은 먼저 `view_image`로 확인한다. 다음 항목을 텍스트 입력과 대조한다.

- 전체 실루엣과 가로·세로·두께 비율
- 손잡이, 버튼, 뚜껑, 포켓, 끈 등 부품의 수와 위치
- 본체와 포인트 색상
- 금속, 직물, 플라스틱, 유리 등 재질감
- 라벨, 로고, 인쇄와 패턴의 위치
- 패키지 형태와 동봉품 수량
- 사진마다 동일 제품인지 여부

사진끼리 또는 사진과 상품 정보가 충돌하면 임의로 하나를 택하지 않는다. 생성 전에 사용자에게 어느 버전을 기준으로 삼을지 확인한다.

## 웹 동일 제품 대조

상품명, 모델명, 라벨·패키지 문구, 독특한 봉제·부품·실루엣을 조합해 동일 제품과 유사 제품을 모두 검색한다. [research-motion.md](research-motion.md)의 `M0~M3` 동일성 등급과 `E1~E4` 출처 등급으로 각 결과를 평가하고 직접 URL, 확인일과 관찰 근거를 기록한다.

- `M1` 동일 또는 `M2` 유력 제품이며 충분한 출처 근거가 있는 자료만 사용자 원본의 보이지 않는 각도나 표기 확인을 보조할 수 있다.
- `M2`는 동일 제품 유력 후보로만 두고 사용자 원본과 충돌 없는 보이는 외형만 보조한다. `M3` 유사 제품은 기획 힌트로만 사용하고 제품 불변 요소에 추가하지 않는다.
- 유사 제품은 문제 상황, 장면, 정보 위계와 카테고리 관습을 찾는 데만 사용한다. 그 제품의 외형, 사양, 효능, 수치와 카피를 현재 상품에 적용하지 않는다.
- 웹 사진이 사용자 원본과 충돌하면 사용자 원본을 우선한다. 다만 모델·옵션 자체가 다른 것으로 보이면 생성 전에 사용자에게 기준을 한 질문으로 확인한다.
- 직접 URL만 기록하고 검색 결과 페이지를 근거 링크로 쓰지 않는다. 내려받은 자료는 출처와 이용 범위를 함께 기록하며 사용자 원본이라고 표시하지 않는다.
- 검색 결과가 없으면 검색어와 `M0` 판정을 기록하고 사용자 원본 범위로 진행한다. 인터넷 도구 자체를 사용할 수 없으면 검색을 했다고 가장하지 않고 생성 준비를 중단한다.

## 제품 불변 요소

선정한 모든 페이지 프롬프트에 같은 불변 요소 블록을 반복한다.

```text
RAW_PRODUCT invariants (`RAW_PRIMARY` / `RAW_DETAIL`):
- preserve the exact product silhouette and proportions
- preserve the visible component count and placement
- preserve the verified colors, materials, label and logo placement
- preserve the verified package and included-item count
- do not invent hidden sides, accessories, controls, patterns or printed copy
- do not redesign, simplify, merge or multiply the product
- use web-matched facts only when graded M1 and supported by E1 or E2; use M2/E3 only for visible supporting details
- never transfer a similar product's features, claims, copy or appearance
```

제품이 작게 등장하는 생활 장면에도 이 블록을 유지한다. 장식적 이유로 색상을 바꾸거나 구성품을 늘리지 않는다.

## 정보 역할별 원본 선택

- `PROBLEM_HOOK`: 제품이 필요하지 않으면 확인된 불편 상황을 중심으로 구성하고, 등장하면 대표 원본을 쓴다.
- `PRODUCT_INTRO`: 대표 정면 또는 3/4 원본과 현재 판매 구성 원본을 쓴다. 상품 소개 역할은 정확히 한 페이지만 둔다.
- `FIT_STRUCTURE`·`FEATURE_EVIDENCE`: 해당 구조나 허용 기능을 실제로 확인할 수 있는 디테일 원본을 쓴다.
- `MEASURED_SIZE`: 현재 제품과 자의 시작·끝점이 함께 보이는 사진, 사용자 실측값 또는 정확한 동일 옵션의 `M1 + E1/E2` 공식 치수만 쓴다. 자 사진 없는 사용자 값은 `USER_DECLARED_SPEC / USER_CONFIRMED_NO_PHOTO`로 표시하고 자 사진·공식 도면처럼 연출하지 않는다. 사진 비율, 유사 제품, 리뷰나 생성형 추정으로 치수를 만들지 않는다.
- `COMPONENTS`·`OPTIONS`: 현재 판매 구성품 수량 또는 현재 옵션이 한 화면에서 확인되는 원본을 쓴다.
- `HOW_TO_USE`·`CARE_GUIDE`·`SAFETY_GUIDE`: 실제 사용 각도, 라벨, 설명서 또는 사용자가 확인한 순서를 보여주는 원본을 쓴다.
- `SITUATION_USE`: 해당 행동에 맞는 실제 사용 원본을 쓴다. 다른 페이지와 같은 장면을 말투만 바꿔 반복하지 않는다.
- 마지막 정보+CTA: 그 페이지의 새 정보를 증명하는 원본을 우선하고 상품 소개 페이지의 히어로 컷을 그대로 복사하지 않는다.

역할 목록은 고정 장수 청사진이 아니다. 고유 INFO_ID와 근거가 있는 역할만 선택한다. 장별 선택을 달리하더라도 대표 원본과 제품 불변 요소는 모든 호출에 유지한다.

## image_gen 전달

모든 입력이 로컬 파일이면 필요한 경로를 `referenced_image_paths`에 전달하고 프롬프트에서 역할을 명시한다.

```text
Input images:
- Image 1 / RAW_PRIMARY: product identity source; preserve exactly
- Image 2 / RAW_DETAIL: verify visible component details only
- Image 3 / REF_STRUCTURE or REF_MOOD: abstract layout and visual rhythm only; never copy its product or text
```

웹에서 찾은 동일 제품 자료를 호출에 포함해야 한다면 `WEB_MATCH`로 분명히 표시하고 `M1` 또는 `M2` 근거와 직접 URL을 프롬프트 기록에 남긴다. 이는 보조 자료이며 사용자 원본보다 우선하지 않는다. 유사 제품 이미지는 제품 정체성 참조로 전달하지 않는다.

대화에만 있는 이미지는 기획 탐색까지만 사용한다. HTML 승인 전 번호 프로젝트의 `original-images/`에 원본 바이트를 보존하고 SHA256을 등록한 뒤 `referenced_image_paths`로만 생성에 전달한다.

각 장에 동일한 원본 세트를 다시 제공한다. 이전에 생성된 상세페이지 이미지를 다음 장의 제품 기준으로 삼지 않는다. 생성본을 연속 기준으로 사용하면 색상, 부품과 비율이 조금씩 변하는 누적 드리프트가 생길 수 있다.

한 호출 안에서 승인된 한글 카피와 제품 장면을 함께 완성한다. 제품 원본을 충실히 유지하면서 텍스트가 들어갈 공간까지 장면 구성 단계에서 설계하고, 별도 텍스트 합성을 기본 경로로 삼지 않는다.

## 생성 결과 직접 검수

각 생성 직후 원본과 결과를 나란히 확대 확인한다.

- 실루엣, 길이·두께 비율, 색상과 재질감이 같은가
- 부품, 구성품, 라벨과 패턴의 수·위치가 바뀌지 않았는가
- 손가락, 착용 방향, 접힘과 가림이 물리적으로 자연스러운가
- 승인한 한글 카피가 빠짐없이 정확하고, 가짜 라벨·워터마크·추가 문구가 없는가
- `800x2400` 모바일 화면에서 제품과 큰 헤드라인이 함께 읽히는가

실패가 한 장에만 있으면 그 장만 같은 원본 세트, 같은 디자인 시스템과 정확한 카피로 다시 생성한다. 정상 장을 함께 다시 만들지 않는다. 재생성 뒤에도 동일 검수를 반복하고 시도 번호와 실패 이유를 기록한다.

## 충돌과 한계

- 사용자 텍스트와 원본 외형이 충돌하면 생성을 멈추고 확인한다.
- 스타일 레퍼런스와 원본이 충돌하면 원본을 따른다.
- 라벨의 픽셀 단위 동일 재현이 중요하면 생성 결과를 확대 검사한다. 모델이 정확히 재현하지 못하면 원본 합성 또는 결정론적 후편집을 사용한다.
- 제품 원본이 저해상도이거나 주요 면이 가려졌다면 보이지 않는 부분을 꾸며내지 말고 해당 각도를 피한다.
- 특정 기능을 시각적으로 암시할 근거가 없으면 장면에서 그 기능을 표현하지 않는다.
