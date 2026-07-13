# 기획 HTML 검토와 생성 승인 게이트

## 목적

고유 정보 단위에 따라 선정한 전체 페이지 기획을 사용자가 실제 생성 전에 한 화면에서 검토하도록 한다. 사용자 기획 승인과 승인 당시의 기획 소스·HTML 파일을 해시로 잠그고, 정확한 모션 ID·출력 형식·실행 환경과 정적·모션·최종 실행 승인을 각각 기록하지 않으면 어떤 생성도 시작하지 않는다.

## 필수 산출물

- `outputs/<project-no>/plan-review.html`: 선정 장수, 장수 근거, 각 페이지의 고유 INFO_ID·구매 질문·카피·화면 구성·RAW·Proof·레퍼런스 원리·주장 경계·모션 후보를 보여주는 검토 보드
- `outputs/<project-no>/generation-gate.md`: 사용자 승인과 생성 권한의 단일 기록원

`plan-review.html`은 아래 문서가 바뀔 때마다 다시 만든다.

```bash
python3 scripts/build_plan_review.py <project-no>
```

대화에 첨부된 파일은 먼저 `inputs/<project-no>/`의 알맞은 폴더에 원본 바이트로 저장하고 `asset-map.md`에 실제 SHA256을 기록해야 한다. 저장·해시 전 첨부는 기획 증거, 승인 대상 또는 `image_gen`·모션 입력으로 사용할 수 없다.

## 고정 순서

질문은 아래 순서대로 한 응답에 정확히 하나씩만 한다. 모든 선택 질문의 마지막 보기는 항상 `다른 답변하기`다.

1. `check_project.py`, `validate_plan.py`, `validate_asset_map.py`, `validate_motion.py`를 통과한다.
2. `build_plan_review.py`로 프로젝트별 HTML을 만든다.
3. 사용자에게 HTML 링크를 제공하고 선정 장수와 모든 페이지 구성을 검토받는다.
4. 사용자가 확정하면 그 응답·날짜, HTML의 `data-source-digest`, 승인한 HTML 파일 자체의 SHA256을 즉시 기록한다.
5. 모션 후보가 있으면 다음 응답에서 실행할 정확한 `motion-NN` ID 또는 정적 전용을 선택받는다.
6. 다음 응답에서 선택 ID가 실제 지원하는 GIF·VIDEO 조합 또는 핸드오프 중 정확한 제작 범위를 선택받는다.
7. 다음 응답에서 선택한 CAPTURE_MODE에 맞는 실사·ComfyUI·핸드오프 환경을 선택받고 응답·날짜와 필요한 증빙 JSON을 기록한다.
8. 다음 응답에서 정적 이미지 생성 승인을 별도로 받는다.
9. 실제 모션 또는 모션 핸드오프 범위라면 다음 응답에서 GIF·영상 생성 또는 핸드오프 준비 승인을 별도로 받는다.
10. 마지막 응답에서 확정된 ID·형식·환경·실행 대상을 모두 요약하고 최종 실행 승인을 받는다.
11. 승인한 대상의 생성 게이트를 실행해 통과한 대상만 생성한다.

## 1. 기획 HTML 승인

HTML을 만든 직후에는 이 질문 하나만 한다.

```text
기획 검토 질문. plan-review.html의 선정 장수와 각 페이지 구성을 확정할까요?
1. 이 기획 확정
2. 수정 후 다시 보기
3. 작업 중단
4. 다른 답변하기
번호로 답해주세요.
```

- `1`: `기획 검토 상태: 승인`으로 바꾸고 `사용자 승인 기록`에 실제 응답과 날짜를 남긴다. 같은 시점의 HTML `data-source-digest` 64자를 `승인한 기획 소스 해시`, HTML 파일 자체의 SHA256을 `승인한 리뷰 HTML 해시`에 기록한다.
- `2`: 다음 응답에서 수정 요구 하나만 받고 기획 문서와 HTML을 다시 만든다. 이전 기획·정적·모션 승인은 모두 `미승인`으로 되돌린다.
- `3`: 생성하지 않는다.
- `4`: 다음 응답에서 원하는 처리 하나만 자유 입력으로 묻는다.

승인 기록 예시는 다음과 같다. 예시 값을 복사하지 말고 실제 응답·날짜·해시만 기록한다.

```text
사용자 승인 기록: 2026-07-14 · APPROVE_PLAN · ANSWER=1
승인한 기획 소스 해시: <plan-review.html의 data-source-digest 64자>
승인한 리뷰 HTML 해시: <shasum -a 256 outputs/<project-no>/plan-review.html 결과 64자>
```

두 해시 중 하나라도 비었거나 현재 파일과 다르면 승인되지 않은 것이다.

`generation-gate.md`의 표준 필드는 각각 정확히 한 번만 둔다. 같은 라벨을 아래에 다시 적어 앞 값을 가리게 만들 수 없다. `기획 리뷰 HTML`은 정확히 `plan-review.html`이어야 한다.

## 2. 정확한 모션 ID 선택

기획 승인 뒤 `motion-plan.md`와 `video-plan.md`의 실제 후보만 번호 보기로 만든다. 후보명만 쓰지 말고 정확한 `motion-NN`, CAPTURE_MODE와 지원 형식을 함께 보여준다. 추천 조합은 별도 번호로 제시할 수 있지만 자동 선택하지 않는다.

```text
실행할 모션 후보를 선택해주세요.
1. motion-01 · REAL_DEMO · GIF
2. motion-02 · REAL_DEMO · VIDEO
3. motion-03 · AI_ILLUSTRATION · GIF·VIDEO
4. motion-01 + motion-02 · REAL_DEMO 조합 (추천)
5. 모션 없이 정적 이미지만
6. 다른 답변하기
번호로 답해주세요.
```

위 ID와 형식은 예시다. 현재 프로젝트의 검증된 후보와 정확히 일치하게 다시 작성한다. 여러 ID를 고르면 `선정 모션 ID: motion-01, motion-02`처럼 중복 없는 쉼표 목록으로 모두 기록한다. 후보명·승인 설명 같은 다른 문장을 이 필드에 섞지 않는다. 정적 전용을 고르면 `선정 모션 ID: 해당 없음`으로 기록한다. `다른 답변하기`를 고르면 다음 응답에서 원하는 정확한 `motion-NN` 목록 또는 `정적만` 중 하나만 묻는다.

## 3. 정확한 GIF·VIDEO 범위 선택

선정 ID가 선언한 형식을 교차 확인한 뒤 호환되는 범위만 번호 보기로 제시한다. GIF 전용 ID를 `STATIC_PLUS_VIDEO`로, VIDEO 전용 ID를 `STATIC_PLUS_GIF`로 승인하지 않는다.

```text
선정한 모션 ID의 제작 범위를 선택해주세요.
1. 정적 + GIF · STATIC_PLUS_GIF
2. 정적 + VIDEO · STATIC_PLUS_VIDEO
3. 정적 + GIF + VIDEO · STATIC_PLUS_GIF_VIDEO
4. 정적 + 선정 모션 제작안 인계 · STATIC_PLUS_MOTION_HANDOFF
5. 모션 ID를 다시 선택
6. 다른 답변하기
번호로 답해주세요.
```

- 현재 선택 ID가 지원하지 않는 보기는 제거하고 남은 번호를 다시 매긴다.
- GIF와 VIDEO ID가 함께 선택되면 두 형식을 모두 포함하는 `STATIC_PLUS_GIF_VIDEO`를 사용한다.
- 정적 전용 선택에는 별도 형식 질문을 반복하지 않고 `제작 범위: STATIC_ONLY`를 기록한다.
- 핸드오프도 정확한 모션 ID가 필요하며 `제작 범위: STATIC_PLUS_MOTION_HANDOFF`로 기록한다.

## 4. CAPTURE_MODE별 환경 선택

정확한 ID와 범위를 기록한 다음에만 환경을 묻는다. 실제 응답은 다음 기계 판독 형식으로 `환경 선택 기록`에 남긴다. `MOTION`은 정렬된 ID를 쉼표와 공백 없이 연결하고 정적 전용이면 `NONE`을 쓴다.

```text
환경 선택 기록: YYYY-MM-DD · SELECT_ENV · SCOPE=<제작 범위> · MOTION=<motion-01,motion-02 또는 NONE> · COMFY=<상태>
```

자유문, 거절·보류 문구, 현재 범위·ID·상태와 모순된 값은 승인 기록이 아니다. 모든 날짜는 Asia/Seoul 오늘보다 미래일 수 없으며 `기획 승인 ≤ 환경 선택 ≤ 최종 승인` 순서여야 한다.

### REAL_TEST·REAL_DEMO만 실제 제작하는 경우

```text
선정한 REAL_TEST·REAL_DEMO 모션의 제작 환경을 선택해주세요.
1. 실제 제품을 촬영하고 ComfyUI 없이 편집 · NOT_REQUIRED
2. 실제 촬영 원본을 연결 확인된 ComfyUI에서 후처리 · CONNECTED
3. 검증된 ComfyUI 워크플로와 촬영·편집안을 인계 · WORKFLOW_PROVIDED
4. 제작 범위를 다시 선택
5. 다른 답변하기
번호로 답해주세요.
```

`NOT_REQUIRED`는 동일 제품을 실제로 촬영하는 `REAL_TEST`·`REAL_DEMO`에 허용된다. 이때 ComfyUI가 없다는 이유로 `HANDOFF_ONLY`로 바꾸지 않는다. 단, 필요한 실사 원본·조건·판정이 없으면 촬영 완료나 모션 완료로 보고하지 않는다. 실제 GIF·영상 실행은 FFmpeg `ffprobe`로 RAW_TEST·RAW_DEMO 클립의 decode·dimensions·duration·frames를 모두 검증하며, 도구나 값이 없으면 fail-closed한다.

3번은 실제 후처리 실행이 아니라 `STATIC_PLUS_MOTION_HANDOFF`로 범위를 바꾸는 인계다. `WORKFLOW_PROVIDED` 상태에서 실제 GIF·영상 완료를 보고하지 않는다.

### AI_ILLUSTRATION이 하나라도 포함된 경우

```text
선정한 AI_ILLUSTRATION 모션의 ComfyUI 환경을 선택해주세요.
1. 실제 연결을 확인한 ComfyUI에서 생성 · CONNECTED
2. 검증된 ComfyUI 워크플로와 제작안을 인계 · WORKFLOW_PROVIDED
3. 워크플로 없이 선정 모션 제작안만 인계 · HANDOFF_ONLY
4. 모션 ID 또는 제작 범위를 다시 선택
5. 다른 답변하기
번호로 답해주세요.
```

AI 모션을 실제 생성하려면 게이트 시점 live 재확인까지 성공한 `CONNECTED`만 허용한다. `NOT_REQUIRED`나 `WORKFLOW_PROVIDED`로 AI 모션을 실행할 수 없다. 2번은 범위를 `STATIC_PLUS_MOTION_HANDOFF`, 상태를 `WORKFLOW_PROVIDED`로 바꾸고, 3번은 같은 범위와 `HANDOFF_ONLY`로 바꾼다. 둘 다 실제 렌더를 금지한다.

### 정적 전용 또는 핸드오프인 경우

- `STATIC_ONLY`: `ComfyUI 상태: NOT_REQUIRED`, `ComfyUI 증빙 JSON: 해당 없음`으로 기록한다.
- `STATIC_PLUS_MOTION_HANDOFF`: 검증된 ComfyUI 워크플로를 함께 넘기면 `WORKFLOW_PROVIDED`와 receipt 경로, 그렇지 않으면 `HANDOFF_ONLY`와 `ComfyUI 증빙 JSON: 해당 없음`을 기록한다. 두 상태 모두 스토리보드·프롬프트·촬영안 인계만 허용한다.

### ComfyUI 증빙 JSON

`CONNECTED` 또는 `WORKFLOW_PROVIDED`는 helper schema·tool marker·무결성 ID 계약에 맞지 않는 수기·generic JSON을 인정하지 않는다. [comfyui-receipt-schema.md](comfyui-receipt-schema.md)의 helper를 사용한다. 생성된 receipt는 `inputs/<project-no>/evidence/` 또는 `outputs/<project-no>/` 아래에 저장하고 그 프로젝트 상대 경로를 `ComfyUI 증빙 JSON`에 기록한다. `receipt_id`는 외부 서명이 아니므로 실제 실행 상태는 gate-time live probe와 endpoint 정체성 일치까지 통과해야 한다.

실제 연결 확인:

```bash
python3 scripts/comfyui_receipt.py probe <project-no> \
  --endpoint http://127.0.0.1:8188
```

helper가 명시적인 `http(s)` base URL의 `/system_stats`를 실제 호출해 2xx ComfyUI JSON을 확인해야 receipt가 생긴다. receipt의 schema·tool marker·시간대 ISO 시각·endpoint·응답 원문 SHA256·변동 카운터를 제외한 endpoint 정체성 SHA256·nonce·receipt ID가 모두 맞아야 하며, `CONNECTED` receipt는 실행 시점 기준 24시간이 지나면 무효다. 생성 게이트는 receipt만 믿지 않고 같은 endpoint의 `/system_stats`를 다시 호출한다. live 재확인이 실패하거나 OS·버전·장치 정체성이 receipt와 달라지면 실제 AI 렌더를 차단한다.

제공 워크플로 확인:

```bash
python3 scripts/comfyui_receipt.py workflow <project-no> \
  --workflow inputs/<project-no>/evidence/comfyui-workflow.json
```

워크플로와 receipt가 모두 같은 번호 프로젝트 안에 있어야 한다. 워크플로는 숫자 문자열 node ID마다 `class_type`과 `inputs`가 있는 ComfyUI API prompt graph이거나, `nodes` 목록과 `links` 목록을 가진 ComfyUI UI workflow여야 한다. helper는 `workflow_kind`와 SHA256을 receipt에 잠그며 generic JSON, 수동 수정, 파일 변경은 실패한다. `WORKFLOW_PROVIDED`는 실행 증빙이 아니라 검증된 워크플로 핸드오프 증빙이다.

## 5. 정적 이미지 생성 승인

환경까지 확정한 다음 아래 질문 하나만 한다.

```text
정적 상세페이지 이미지 생성을 승인할까요?
1. 승인된 기획대로 정적 이미지 생성 승인
2. 기획 HTML 다시 보기
3. 제작 범위 다시 선택
4. 작업 중단
5. 다른 답변하기
번호로 답해주세요.
```

`1`을 받은 뒤에만 `정적 이미지 생성 승인: 승인`으로 기록한다. 이 승인은 GIF·영상이나 핸드오프 준비 권한을 포함하지 않는다.

## 6. GIF·영상 또는 핸드오프 승인

모션 제작 또는 모션 핸드오프 범위일 때만 다음 질문 하나를 한다. 정확한 선택 ID, 형식, CAPTURE_MODE를 질문 위 한 줄로 요약한다.

```text
선정한 GIF·영상 범위를 승인할까요?
1. 선정 모션의 실제 생성 승인
2. 정적 이미지만 진행
3. 모션 ID·형식·환경 다시 선택
4. 작업 중단
5. 다른 답변하기
번호로 답해주세요.
```

- 실제 모션 범위에서 `1`: `GIF·영상 생성 승인: 승인`으로 기록한다.
- `STATIC_PLUS_MOTION_HANDOFF`에서는 1번 문구를 `선정 모션의 촬영안·스토리보드·프롬프트 인계 준비 승인`으로 바꾼다. 이때 `GIF·영상 생성 승인: 승인`은 인계 준비 권한일 뿐 실제 렌더 권한이 아니다.
- 정적 전용이면 사용자가 정적 전용을 선택한 기록에 따라 `GIF·영상 생성 승인: 해당 없음`으로 기록한다.
- 정적 승인을 모션 승인으로, 모션 승인을 정적 승인으로 대신하지 않는다.

## 7. 최종 실행 승인

정적·모션 승인을 각각 기록한 뒤 `제작 범위 / 선정 모션 ID / CAPTURE_MODE / GIF·VIDEO 형식 / ComfyUI 상태 / 실제 실행 대상`을 한 줄로 요약하고 마지막 질문 하나만 한다.

```text
마지막 질문. 위에 확정한 정적·모션 범위의 실행을 시작할까요?
1. 확정 범위 실행 시작
2. 기획 HTML 다시 보기
3. 모션 ID·제작 범위·환경 다시 선택
4. 작업 중단
5. 다른 답변하기
번호로 답해주세요.
```

`1`을 받은 경우에만 다음 형식으로 `최종 생성 승인 기록`에 남긴다. `MOTION` 규칙은 환경 기록과 같다.

```text
최종 생성 승인 기록: YYYY-MM-DD · APPROVE_EXECUTION · SCOPE=<제작 범위> · MOTION=<motion-01,motion-02 또는 NONE> · COMFY=<상태>
```

현재 범위·ID·ComfyUI 상태와 정확히 일치하지 않는 자유문이나 거절문은 무효다. 환경을 바꾸면 같은 날이어도 최종 승인을 다시 받아야 한다. 최종 승인 기록은 정적·모션 개별 승인 필드를 자동으로 승인하는 대체값이 아니다.

## 정적·모션 텍스트 제작 경계

- 정적 이미지는 승인 카피를 포함한 완성 디자인을 built-in `image_gen`에서 직접 생성하는 것이 1차 경로다. 텍스트 없는 플레이트나 `FIXED_TEXT_LAYER` 후합성을 처음부터 기본값으로 사용하지 않는다.
- 정적 파일의 decode·dimensions·정규화 검사는 Pillow 자동 runtime과 안전한 fallback을 사용하고, fallback 뒤에도 파일을 다시 열어 시각 검수한다.
- 정적 텍스트가 실패하면 같은 승인 카피로 직접 생성 2회까지 시도한다. 두 번 모두 실패한 뒤 사용자가 번호 질문에서 명시적으로 `승인 카피 FIXED_TEXT_LAYER 후편집`을 선택한 경우에만 정적 고정 텍스트 레이어로 대체한다.
- 고정 텍스트 레이어는 글자 정확성만 고친다. 제품·레이아웃·사실 오류는 후편집으로 통과시키지 않는다.
- GIF·영상 광고 카피는 항상 실제 폰트로 한 번 조판한 `FIXED_TEXT_LAYER`를 후합성한다. 프레임마다 광고 글자를 생성하지 않는다.

## 실행 차단 명령

승인된 정적 페이지 생성 직전:

```bash
python3 scripts/validate_generation_gate.py <project-no> --target static
```

실제 GIF·영상 생성 직전:

```bash
python3 scripts/validate_generation_gate.py <project-no> --target motion
```

모션 인계 문서 확정 직전:

```bash
python3 scripts/validate_generation_gate.py <project-no> --target handoff
```

검증이 실패하면 `image_gen`, GIF·영상 렌더 또는 ComfyUI를 호출하지 않는다. `HANDOFF_ONLY`는 실제 모션 생성 게이트를 통과할 수 없고, AI 모션을 포함한 범위는 실행 가능한 ComfyUI 상태와 증빙 JSON 없이는 통과할 수 없다.

## 승인 무효화

승인 후 아래 항목 중 하나가 달라지면 `기획 검토 상태`, 정적 이미지 승인과 GIF·영상 승인을 모두 `미승인`으로 되돌리고 두 승인 해시를 비운 뒤 HTML부터 다시 검토받는다.

- 장별 H1·BODY·카드·캡션·CTA
- 선정 장수, ROLE_ID·INFO_ID·구매 질문 또는 필수 화면 구성
- 허용 사실·금지 주장
- 제품의 핵심 기능·장점과 그 근거 범위
- 디자인·폰트 시스템의 중요한 방향과 정적 텍스트 제작 경로
- 가장 영상이 필요한 소구점, TOP3와 CAPTURE_MODE·주장 범위
- RAW·Proof·레퍼런스 원리와 주장 경계

기획은 그대로지만 `선정 모션 ID`, GIF·VIDEO 제작 범위 또는 실행 환경만 바꾸면 해당 선택 이후의 정적·모션·최종 승인 기록을 다시 받는다. 새 조합이 기획 카피·장면·TOP3·폰트 계약을 바꾸면 기획 승인부터 다시 받는다.

승인을 무효화한 뒤 `build_plan_review.py`를 다시 실행하고 새 HTML을 검토받는다. 이전 해시를 새 파일에 복사해 승인을 가장하지 않는다.
