# 실제 상세페이지 레퍼런스와 가변 정보 청사진

## 목차

- [레퍼런스의 역할](#레퍼런스의-역할)
- [저장 위치](#저장-위치)
- [분석 양식](#분석-양식)
- [웹 리서치 레퍼런스](#웹-리서치-레퍼런스)
- [참고 가능 요소와 복제 금지 요소](#참고-가능-요소와-복제-금지-요소)
- [디자인 시스템 합성](#디자인-시스템-합성)
- [카피와 가시성 기획](#카피와-가시성-기획)
- [가변 정보 청사진](#가변-정보-청사진)
- [공통 카피와 광고 제한](#공통-카피와-광고-제한)
- [한 호출 직접 조판 프롬프트](#한-호출-직접-조판-프롬프트)
- [직접 QA와 부분 재생성](#직접-qa와-부분-재생성)

## 레퍼런스의 역할

실제 상세페이지 레퍼런스를 레이아웃, 색상 관계, 정보 위계, 여백, 사진 조명과 카피 리듬을 파악하는 스타일 자료로만 사용한다. 상품 사실이나 광고 근거로 사용하지 않는다. `asset-map.md`에는 `REF_STRUCTURE / REF_MOOD / REF_TYPO / REF_PHOTO` 역할, 실제 SHA256과 추상 원리를 기록한다.

레퍼런스가 없으면 사용자 입력과 필수 웹 리서치에서 확인한 카테고리의 공통 디자인 문법을 바탕으로 새 디자인 시스템을 만든다. 웹 자료에서도 추상적인 구성 원리만 채택하고 특정 상세페이지의 상품, 카피, 로고, 고유 그래픽과 트레이드 드레스를 복제하지 않는다.

## 저장 위치

실행에 사용하는 실제 상세페이지 스타일 레퍼런스를 다음 폴더에 저장한다.

```text
<skill-root>/inputs/<project-no>/real-references/
```

예시:

```text
inputs/001/real-references/reference-01.jpg
inputs/001/real-references/reference-02.jpg
```

다른 위치의 파일은 원본을 보존한 채 이 폴더로 복사한다. 기존 파일을 덮어쓰지 않는다. 실행용 이미지와 스킬 지침 문서가 섞이지 않도록 스킬의 `references/` 폴더에는 저장하지 않는다.

## 분석 양식

로컬 레퍼런스를 `view_image`로 확인하고 각 파일을 다음 형식으로 기록한다.

```text
ASSET_ID: Axx
ROLE: REF_STRUCTURE | REF_MOOD | REF_TYPO | REF_PHOTO
경로: <skill-root>/inputs/<project-no>/real-references/<filename>
SHA256: <실제 파일 해시>
팔레트: <배경, 주조색, 강조색>
여백: <넓음/보통/조밀함과 구간 리듬>
정보 밀도: <헤드라인, 보조문구, 카드 수>
레이아웃 문법: <히어로, 분할, 카드, 체크리스트, 비교>
사진 문법: <시점, 조명, 그림자, 배경>
타이포 리듬: <짧은 헤드라인, 강조 방식, 정렬>
채택할 원리: <추상적 특징>
적용 페이지: <RPxx와 PAGE_NO>
배제할 요소: <브랜드·제품·문구·수치·고유 그래픽>
```

## 웹 리서치 레퍼런스

사용자 제공 레퍼런스 유무와 관계없이 동일 제품과 유사 제품을 웹에서 찾아 기획에 반영한다. 등급과 기록 형식은 [research-motion.md](research-motion.md)를 따른다.

- 동일 제품 자료: `M1` 또는 `M2`와 적절한 `E` 등급을 충족할 때만 라벨, 옵션, 구성과 보이는 디테일 확인을 보조한다.
- 유사 제품 자료: 카테고리 고객이 익숙하게 보는 문제 제기, 장면 유형, 정보 순서, 여백과 카드 밀도를 파악하는 기획용 자료로만 쓴다.
- 여러 유사 제품에서 반복되는 원리를 추출하되 어느 한 페이지의 문장, 배치, 인물, 소품, 제품 외형과 고유 스타일을 재현하지 않는다.
- 검색어, 직접 URL, 접근일, `M0~M3`, `E1~E4`, 관찰 내용과 `사실 확인용` 또는 `기획 전용` 사용 범위를 기록한다.

## 참고 가능 요소와 복제 금지 요소

참고할 수 있는 요소:

- 밝고 어두운 영역의 비율
- 배경과 제품 사이의 대비
- 여백과 정보 밀도의 리듬
- 카드, 구분선, 아이콘의 추상적 스타일
- 제품 사진의 조명, 시점과 그림자 강도
- 헤드라인과 보조 문구의 크기 관계
- 섹션 전환 방식과 CTA의 시각적 무게

복제하지 않을 요소:

- 레퍼런스 속 상품, 패키지, 인물과 소품
- 브랜드명, 로고, 슬로건과 원문 카피
- 가격, 할인, 리뷰, 별점, 판매량과 랭킹
- 인증, 시험 수치, 배지, 수상과 보증
- 고유 일러스트, 아이콘 세트와 식별 가능한 트레이드 드레스
- 쿠팡 로고, 검색창, 앱 UI, 장바구니·하트 아이콘과 스마트폰 목업

특정 경쟁사 상세페이지를 거의 동일하게 재현하지 않는다. 여러 레퍼런스의 공통 원리를 추출해 상품에 맞는 새로운 디자인 시스템으로 합성한다.

## 디자인 시스템 합성

레퍼런스마다 채택할 특징을 최대 2개만 고른다. 서로 충돌하는 특징은 상품 분위기와 모바일 가독성을 기준으로 하나만 선택한다.

다음 항목을 한 번 확정해 모든 장에 동일하게 반복한다.

```text
DESIGN_SYSTEM
palette: <background / primary / accent>
product treatment: <photo or polished product render>
lighting: <direction / softness / shadow strength>
cards: <shape / radius / border / fill>
icons: <line or filled; simple; no app-commerce icons>
typography: <one Korean sans-serif family / H1·H2·BODY·LABEL tokens / alignment>
spacing: <generous mobile whitespace / section rhythm>
cta: <neutral wording / visual treatment>
```

스타일 레퍼런스가 제품 원본의 색상, 재질, 부품 또는 라벨을 바꾸게 하지 않는다.

기본 캔버스는 `800x2400` 세로형이다. 선정한 모든 페이지에 같은 굵은 한글 산세리프 계열, 동일한 헤드라인 굵기, 모서리·카드 문법, 팔레트와 사진 조명을 유지한다. 페이지별 정보는 달라도 한 브랜드의 연속 상세페이지처럼 보여야 한다.

## 카피와 가시성 기획

이미지를 만들기 전에 고유 정보 단위를 먼저 확정하고, 단위마다 정확한 한글 카피와 배치를 정한다. 흐름은 `문제 인식 → 단 한 번의 상품 소개 → 검증된 기능·구조·실측·사양·구성품·사용법·관리 중 필요한 정보 → 마지막 정보와 CTA`를 따른다. 장수는 `3~10장`, 보통 `5~8장`이며 독점 정보 단위 수와 같아야 한다.

- 각 장의 메인 헤드라인은 하나만 쓰고, 한눈에 읽히는 짧고 강한 후킹 메시지로 만든다.
- 후킹은 검증된 고객 불편, 원하는 사용 장면 또는 제품의 확인된 차별점에서 만든다. 불안 조장, 절대 표현과 근거 없는 효능은 사용하지 않는다.
- 전체 헤드라인을 같은 한글 산세리프 계열과 같은 시각적 무게로 통일한다. 800px 원본 기준 `H1 72~104px`, `H2 44~64px`, `BODY 32~40px`, `라벨·캡션 최소 32px`의 토큰을 고정한다.
- 텍스트와 배경 사이에 강한 명도 대비를 확보한다. 사진의 복잡한 영역 위에는 글자를 놓지 말고 단색 면, 그라데이션 또는 충분한 여백을 설계한다.
- 핵심 단어 한두 개만 브랜드 강조색으로 표시한다. 색만으로 의미를 구분하지 않는다.
- 한 장의 큰 헤드라인은 하나로 두되 `EYEBROW`, `BODY`, 2~4개 카드·칩, 사진 캡션과 CTA를 장의 목적에 맞게 조합한다. 기본은 3~6개 세로 정보 구역이다.
- 긴 문단을 작은 글자로 압축하거나 복잡한 표, 32px 미만 각주와 의미 없는 영문 장식을 사용하지 않는다.
- 각 장 프롬프트에 렌더링할 모든 문자열을 필드별로 정확히 열거하고 `이 매니페스트 밖의 글자는 넣지 않기`를 명시한다. 이 문장은 승인된 정보 모듈을 두 줄로 줄이라는 뜻이 아니다.
- 제품명, 카피와 디자인 배치까지 먼저 승인 가능한 기획표로 만든 뒤 생성한다. 이미지 생성 뒤 별도 카피를 얹는 흐름을 기본값으로 삼지 않는다.

## 가변 정보 청사진

먼저 다음 표로 후보를 만든다.

```text
PAGE_ID | ROLE_ID | INFO_ID | 구매 질문 | 독점 Fact ID | 필수 시각 증거 | 새 정보 | 상태
```

적용 규칙:

1. 첫 페이지는 `PROBLEM_HOOK`으로 고객의 확인된 핵심 불편 하나를 연다.
2. `PRODUCT_INTRO`는 정확히 한 페이지만 두고 상품 정체성과 가장 중요한 기능을 소개한다.
3. 이후에는 현재 상품에 검증된 정보만 선택한다. 우선 후보는 구조, 기능 근거, 실제 치수, 정확한 사양, 구성품, 사용 방법, 옵션, 관리·세탁·보관과 주의사항이다.
4. 실측은 현재 제품과 자를 함께 둔 사진, 사용자가 직접 제공한 값 또는 정확한 동일 옵션의 `M1 + E1/E2` 공식 사양만 쓴다. 사진 비율, 유사 제품, 리뷰와 생성형 추정은 금지한다.
5. 비교·추천 대상·다양한 활용은 다른 페이지에 없는 객관적 선택 정보를 줄 때만 포함한다.
6. 마지막으로 필요한 정보 페이지에 중립 CTA를 함께 넣는다. 요약이나 CTA만을 위한 독립 페이지는 만들지 않는다.
7. 같은 사실을 다른 표현으로 되풀이하는 후보는 삭제하거나 병합한다. 정보가 부족하면 장수를 줄이고 빈 페이지를 만들지 않는다.

각 페이지는 `800x2400` 독립 이미지이며 `page-01.png`부터 선정한 마지막 번호까지 연속 저장한다. 픽셀 안에는 `Page`나 페이지 번호를 렌더링하지 않는다.

## 공통 카피와 광고 제한

- 모든 문구를 자연스러운 한글로 작성한다.
- 한 장에 메인 헤드라인 1개와 목적에 맞는 설명·카드·캡션·CTA를 사용한다.
- 3~6개 정보 구역으로 나누고, 한 구역에 한 메시지만 둔다.
- 32px 미만 작은 글씨, 억지로 압축한 긴 문단, 복잡한 표와 의미 없는 영문 더미를 사용하지 않는다.
- 정확한 카피 매니페스트를 필드별로 지정하고 매니페스트 밖의 텍스트를 금지한다.
- 가격, 할인율, 리뷰, 별점, 판매량, 랭킹, 인증, 테스트, 수상과 보증은 `allowed facts`에 있을 때만 쓴다.
- 의학적 효능, 치료, 완치, 회복과 개선 보장처럼 보이는 표현을 사용하지 않는다.
- 환불, 무료배송, 이벤트와 보증 정보를 입력 없이 CTA에 추가하지 않는다.
- 브랜드명이 없으면 임의 브랜드명이나 로고를 만들지 않는다.
- 제품과 무관한 인물, 배경과 소품을 넣지 않는다.

중립 CTA 예시:

- `지금 일상에 더해보세요`
- `눈에 보이는 디자인으로 골라보세요`
- `오늘의 옷차림에 더해보세요`
- `당신의 스타일에 맞춰보세요`

상품과 타깃에 자연스럽게 맞는 문구 하나만 선택하거나 같은 강도의 새 문구를 작성한다.

## 한 호출 직접 조판 프롬프트

각 장을 별도의 `image_gen` 호출로 생성하되, 한 호출 안에서 제품 장면, 배경, 레이아웃과 승인된 한글 카피를 모두 완성한다. 텍스트 없는 배경을 만든 뒤 별도 오버레이하는 방식을 기본 생성 경로로 사용하지 않는다.

모든 호출에 다음 역할과 공통 디자인 블록을 포함한다.

```text
Input images:
- `RAW_PRIMARY` / `RAW_DETAIL`: the only visual source of truth for product identity, shape, color, visible components, label and package.
- `REF_STRUCTURE` / `REF_MOOD` / `REF_TYPO` / `REF_PHOTO`: inspiration only for layout rhythm, whitespace, color relationships, lighting and information hierarchy.
- `WEB_MATCH`: optional M1 or M2 support; never higher priority than persisted RAW. M2/E3 may support only non-conflicting visible details.

Never copy `REF_*` products, people, props, copy, logos, prices, reviews, certifications, metrics, badges, UI or unique graphics.
If any reference conflicts, persisted `RAW_*` and verified allowed facts take precedence.

Canvas and typography:
- create one 800x2400 vertical Korean commerce detail image
- use one consistent modern Korean sans-serif family shared by all selected images
- H1 72-104px, H2 44-64px, BODY 32-40px, every label and caption at least 32px on the 800px source
- use 3-6 clearly separated vertical information zones; each zone communicates one idea
- make the hook immediately visible on mobile with strong contrast and generous whitespace
- typeset the approved Korean copy directly as part of this image

Exact visible copy manifest:
- EYEBROW: "<필요한 경우>"
- H1: "<승인된 헤드라인>"
- BODY: "<승인된 설명>"
- CARD / CHIP / CAPTION: ["<문구 1>", "<문구 2>", "<필요한 만큼>"]
- CTA: "<필요한 경우>"
- render every listed string exactly and no text outside this manifest; no omissions, pseudo-Korean, English filler, watermark, page number or UI

Page contract:
- PAGE_NO: <선정 장수 중 현재 연속 번호>
- ROLE_ID: <승인 역할>
- INFO_ID: <이 페이지만 소유하는 정보 단위>
- PURCHASE_QUESTION: <이 페이지가 답할 한 가지 질문>

Page composition:
- <이 페이지의 목적, 필수 시각 증거, 제품 크기, 장면, 카드 수, 정렬과 여백>

Verified facts allowed:
- <이 장에서 표현할 수 있는 검증 사실>

Forbidden:
- <금지 표현과 시각적 암시>
```

헤드라인과 제품의 우선순위가 경쟁하지 않게 먼저 큰 후킹 문구, 다음 제품, 마지막 보조 정보 순으로 시선을 설계한다. 한글이 깨지거나 다른 문자열이 생기면 텍스트를 제거해 타협하지 말고 같은 정확한 카피로 해당 장만 한 번 다시 생성한다. 두 번째 시도도 실패하면 실패 사실과 후보를 사용자에게 보여주고 재생성·후편집·카피 단순화 중 다음 처리 방향을 번호로 묻는다.

## 직접 QA와 부분 재생성

선정한 모든 페이지가 생성되면 에이전트가 결과를 직접 열어 확대 검수한다. 파일 존재나 스크립트 통과만으로 시각 QA를 대체하지 않는다.

1. 파일이 열리고 실제 래스터 크기가 `800x2400`인지 확인한다.
2. 승인된 한글 카피를 글자 단위로 대조한다. 깨진 한글, 누락, 중복, 오탈자, 의사문자와 추가 텍스트가 없어야 한다.
3. 전체 헤드라인·본문·카드·캡션이 같은 한글 산세리프 계열, 정해진 굵기·크기 토큰과 정렬 원칙을 유지하는지 확인한다.
4. 모바일 축소 보기에서도 후킹 헤드라인, 제품과 모든 정보 문구가 구분되며, 본문·라벨·캡션이 800px 원본 기준 최소 32px인지 확인한다.
5. 원본 대비 제품의 실루엣, 색상, 재질, 구성품, 라벨과 착용 방향이 보존됐는지 확인한다.
6. 카피와 장면이 검증된 사실만 표현하고, 유사 제품의 사양·효능·카피를 가져오지 않았는지 확인한다.
7. 레퍼런스의 고유 상품·로고·문구·수치·배지·UI·식별 가능한 디자인을 복제하지 않았는지 확인한다.
8. 각 페이지의 승인된 INFO_ID와 구매 질문이 화면에서 성립하고 다른 페이지의 내용을 반복하지 않는지 확인한다.

실패 장 번호, 실패 이유와 재생성 시도 번호를 기록하고 그 장만 같은 디자인 시스템과 원본 세트로 다시 생성한다. 정상 장은 보존한다. 재생성본도 같은 QA를 다시 통과해야 최종본으로 이동한다. GIF·영상 후보와 선택적인 ComfyUI 핸드오프는 [research-motion.md](research-motion.md)의 모션 절차를 따른다.
