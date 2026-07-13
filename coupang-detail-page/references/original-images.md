# 원본 상품 이미지

## 목차

- [역할과 우선순위](#역할과-우선순위)
- [저장 위치](#저장-위치)
- [입력 목록 작성](#입력-목록-작성)
- [시각 검사](#시각-검사)
- [제품 불변 요소](#제품-불변-요소)
- [장별 원본 선택](#장별-원본-선택)
- [image_gen 전달](#image_gen-전달)
- [충돌과 한계](#충돌과-한계)

## 역할과 우선순위

원본 상품 이미지를 제품의 시각적 정체성과 확인 가능한 외관 사실의 기준으로 사용한다. 스타일 레퍼런스나 이전 생성본보다 항상 우선한다.

원본에서 직접 보이지 않는 뒷면, 내부 구조, 부품, 라벨 문구와 구성품을 추정하지 않는다. 사용자가 별도 사실로 제공했더라도 이미지로 확인되지 않는 외형은 보수적으로 표현한다.

## 저장 위치

실행에 사용하는 원본 상품 이미지를 다음 폴더에 저장한다.

```text
<skill-root>/inputs/<project-no>/original-images/
```

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
ID: ORIGINAL_PRODUCT_01
경로: <skill-root>/inputs/<project-no>/original-images/<filename>
시점: 정면 | 측면 | 후면 | 상단 | 디테일 | 구성품 | 패키지
확인 가능: <형태, 색상, 부품, 라벨, 구성품>
가림/불확실: <보이지 않거나 판독할 수 없는 부분>
우선순위: primary | supporting
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

## 제품 불변 요소

10개 프롬프트에 같은 불변 요소 블록을 반복한다.

```text
ORIGINAL_PRODUCT invariants:
- preserve the exact product silhouette and proportions
- preserve the visible component count and placement
- preserve the verified colors, materials, label and logo placement
- preserve the verified package and included-item count
- do not invent hidden sides, accessories, controls, patterns or printed copy
- do not redesign, simplify, merge or multiply the product
```

제품이 작게 등장하는 생활 장면에도 이 블록을 유지한다. 장식적 이유로 색상을 바꾸거나 구성품을 늘리지 않는다.

## 장별 원본 선택

| 장 | 우선 사용할 원본 |
|---|---|
| 1 문제 후킹 | 제품이 필요하지 않으면 상황 이미지만 사용하고, 등장하면 대표 원본 사용 |
| 2 필요성 | 상황 중심으로 구성하고 제품 등장 시 대표 원본 사용 |
| 3 상품 소개 | 대표 정면/3·4 원본과 패키지 원본 |
| 4 상황 비교 | 대표 원본과 실제 사용 시점 원본 |
| 5 장점 1·2 | 해당 기능을 실제로 확인할 수 있는 디테일 원본 |
| 6 장점 3 | 사용 방법이나 구성품을 확인할 수 있는 원본 |
| 7 차별점 비교 | 우리 제품 쪽에만 대표 원본 사용; 경쟁 상품은 특정 제품으로 재현하지 않음 |
| 8 추천 대상 | 대표 원본 또는 실제 사용 원본 |
| 9 활용 장면 | 실제 사용 각도를 확인할 수 있는 원본 |
| 10 CTA | 3장과 동일한 대표 원본 |

장별 선택을 달리하더라도 대표 원본과 제품 불변 요소는 모든 호출에 유지한다.

## image_gen 전달

모든 입력이 로컬 파일이면 필요한 경로를 `referenced_image_paths`에 전달하고 프롬프트에서 역할을 명시한다.

```text
Input images:
- Image 1 / ORIGINAL_PRODUCT_PRIMARY: product identity source; preserve exactly
- Image 2 / ORIGINAL_PRODUCT_DETAIL: verify component and material details only
- Image 3 / STYLE_REFERENCE: abstract layout and visual rhythm only; never copy its product or text
```

대화에만 있는 이미지는 필요한 모든 입력을 포함하는 최소 `num_last_images_to_include`를 사용한다. 두 입력 방식을 함께 사용하지 않는다.

각 장에 동일한 원본 세트를 다시 제공한다. 이전에 생성된 상세페이지 이미지를 다음 장의 제품 기준으로 삼지 않는다. 생성본을 연속 기준으로 사용하면 색상, 부품과 비율이 조금씩 변하는 누적 드리프트가 생길 수 있다.

## 충돌과 한계

- 사용자 텍스트와 원본 외형이 충돌하면 생성을 멈추고 확인한다.
- 스타일 레퍼런스와 원본이 충돌하면 원본을 따른다.
- 라벨의 픽셀 단위 동일 재현이 중요하면 생성 결과를 확대 검사한다. 모델이 정확히 재현하지 못하면 원본 합성 또는 결정론적 후편집을 사용한다.
- 제품 원본이 저해상도이거나 주요 면이 가려졌다면 보이지 않는 부분을 꾸며내지 말고 해당 각도를 피한다.
- 특정 기능을 시각적으로 암시할 근거가 없으면 장면에서 그 기능을 표현하지 않는다.
