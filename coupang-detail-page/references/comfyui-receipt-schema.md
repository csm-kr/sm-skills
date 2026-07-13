# ComfyUI 실행 증빙 계약

`CONNECTED`와 `WORKFLOW_PROVIDED`를 자기 진술만으로 기록하지 않는다. 아래 helper가 만든 프로젝트 내부 JSON 경로를 `generation-gate.md`의 `ComfyUI 증빙 JSON`에 기록하고, 실행 또는 핸드오프 확정 직전에 `validate_generation_gate.py`를 통과한다. `CONNECTED`는 실제 실행 상태, `WORKFLOW_PROVIDED`는 검증된 워크플로 핸드오프 상태다.

## CONNECTED

```bash
python3 scripts/comfyui_receipt.py probe 003 --endpoint http://127.0.0.1:8188
```

helper는 명시한 `http(s)` base URL의 `/system_stats`를 실제 호출한다. ComfyUI 형태의 JSON 응답이 성공해야 `inputs/003/evidence/comfyui-connected-receipt.json`을 만든다. receipt에는 다음 필드가 필요하다.

```text
schema / tool / status=CONNECTED / checked_at / endpoint / endpoint_kind
probe_url / probe_ok=true / http_status / response_bytes
response_fingerprint_sha256 / nonce / receipt_id
response_identity_sha256
```

- `checked_at`은 시간대가 있는 ISO 시각이며 검증 시점 기준 24시간 이내여야 한다.
- endpoint는 `http://` 또는 `https://`의 localhost나 명시적 호스트여야 한다. `0.0.0.0`, `::`, 내장 자격 증명, query와 fragment는 금지한다.
- `response_fingerprint_sha256`는 실제 응답 body의 SHA256이다.
- `response_identity_sha256`는 RAM·VRAM free/used 같은 변동 카운터를 제외한 OS·버전·장치 정체성의 정규화 SHA256이다. gate-time probe의 이 값이 receipt와 달라지면 다른 endpoint 상태로 보고 차단한다. 원문 fingerprint는 receipt 당시 응답 감사용으로 보존한다.
- `receipt_id`는 helper가 핵심 필드를 정규화해 계산하는 결정적 무결성 ID다. 필드를 수정하면 무효지만 외부 서명은 아니므로 helper 실행 주체를 암호학적으로 증명하지는 않는다.
- 실제 생성 게이트는 receipt의 시각과 무결성 ID만 확인하지 않는다. 기록된 endpoint의 `/system_stats`를 다시 호출하며 이 live 재확인이 실패하면 AI 렌더를 차단한다.

## WORKFLOW_PROVIDED

워크플로 JSON을 `inputs/<project-no>/evidence/` 또는 `outputs/<project-no>/`에 먼저 저장한다.

```bash
python3 scripts/comfyui_receipt.py workflow 003 \
  --workflow inputs/003/evidence/comfyui-workflow.json
```

receipt에는 `schema`, `tool`, `status=WORKFLOW_PROVIDED`, `checked_at`, `workflow_path`, `workflow_kind`, `workflow_sha256`, `nonce`, `receipt_id`가 필요하다. helper와 validator는 다음 둘 중 하나만 허용한다.

- `API_PROMPT_GRAPH`: 최상위 key가 숫자 문자열 node ID이고 각 node에 비어 있지 않은 `class_type`과 객체 `inputs`가 있다.
- `UI_WORKFLOW`: 비어 있지 않은 `nodes` 목록과 `links` 목록이 있고 각 node에 `id`와 `type`이 있다. 단일 노드 워크플로의 `links`는 비어 있을 수 있다.

generic JSON은 거부한다. validator는 워크플로가 같은 프로젝트 안에 실제로 존재하는지, 판별한 `workflow_kind`와 현재 SHA256이 receipt에 잠긴 값과 일치하는지 다시 계산한다. 이 receipt는 실행 가능한 환경이나 완료 렌더를 증명하지 않으므로 `STATIC_PLUS_MOTION_HANDOFF`에만 사용한다.

## 실패 폐쇄 규칙

- receipt 파일 자체도 해당 번호 프로젝트의 `inputs/.../evidence/` 또는 `outputs/.../` 안에 둔다.
- 잘못된 schema/tool marker, 오래된 CONNECTED probe, 실패한 gate-time live 재확인, 조작된 receipt ID, generic JSON, 존재하지 않거나 바뀐 workflow는 모두 생성 또는 핸드오프 차단이다.
- `HANDOFF_ONLY`와 실사 `REAL_TEST`·`REAL_DEMO`의 `NOT_REQUIRED`에는 이 receipt를 만들지 않는다.
