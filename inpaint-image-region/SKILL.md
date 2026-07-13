---
name: inpaint-image-region
description: 로컬 브라우저에서 원본 이미지를 드래그하고 변경할 박스를 그린 뒤 프롬프트와 선택적 레퍼런스 이미지로 ComfyUI Flux 2 Klein 인페인팅을 실행한다. 이미지 일부 교체, 의상·소품·배경 영역 수정, 박스 인페인팅, 외부 참조 기반 변경 또는 텍스트 전용 영역 변경을 요청할 때 사용한다.
---

# ComfyUI 영역 인페인팅

로컬 선택 화면에서 원본, 박스, 프롬프트, 선택적 레퍼런스를 한 번에 받는다. 별도 모드 질문은 하지 않는다. 레퍼런스 칸이 비어 있으면 `inpainting/red.json`의 텍스트 전용 구성을 API 그래프로 옮긴 워크플로를, 이미지가 있으면 외부 reference-conditioning을 추가한 구성을 사용한다.

## 최초 설정 인터뷰

`<project-root>/inpainting/config.json`이 없을 때 아래 항목을 **한 메시지에 정확히 하나씩** 질문하고, 답을 받은 뒤 다음 항목으로 이동한다. 이미 답을 알거나 안전하게 감지한 항목은 다시 묻지 않는다.

1. `ComfyUI 서버 주소가 무엇인가요? 로컬 기본값은 http://127.0.0.1:8188입니다.`
2. `원본과 레퍼런스 이미지 입력 폴더를 어디로 할까요? 기본값은 <project-root>/inpainting/inputs입니다.`
3. `완성 이미지 출력 폴더를 어디로 할까요? 기본값은 <project-root>/inpainting/outputs입니다.`

세 답을 모두 받은 후 설정을 저장하고 서버의 필수 노드와 모델을 점검한다.

```bash
<python> <skill-directory>/scripts/run_inpainting.py \
  --project-root <project-root> \
  --server <server-url> \
  --input-dir <input-directory> \
  --output-dir <output-directory> \
  --configure
```

- macOS/Linux에서는 `<python>`에 `python3`를 사용한다.
- Windows에서는 `py -3`를 우선 사용하고, 없으면 `python`을 사용한다.
- 공백이 포함된 Windows와 POSIX 경로는 따옴표로 감싼다.
- 설정 파일이 있으면 저장된 값을 사용하고 인터뷰를 반복하지 않는다.
- `COMFYUI_SERVER` 환경변수나 `--server`는 저장된 서버 주소보다 우선한다.

## 선택 화면 실행

아래 명령을 실행한 상태로 유지한다. 기본 브라우저에 `127.0.0.1` 선택 화면이 열리며, Windows/macOS/Linux에서 같은 방식으로 동작한다.

```bash
<python> <skill-directory>/scripts/interactive_intake.py \
  --project-root <project-root>
```

사용자에게 화면에서 다음 순서로 입력하도록 안내한다.

1. `원본` 칸에 이미지를 드래그 앤 드롭한다.
2. 원본 위에서 마우스 휠로 필요한 만큼 확대·축소하고 변경할 사각형을 한 번 드래그한다. 다시 드래그하면 박스가 교체된다.
3. `변경할 내용`에 원하는 결과를 입력한다.
4. 외부 참조가 필요할 때만 `레퍼런스 이미지 (선택)` 칸에 이미지를 드롭한다.
5. `AI 프롬프트 만들기`를 누르고 `보강된 프롬프트 (AI)`를 확인한다.
6. 다른 표현이 필요하면 `다시 만들기`를 누른다.
7. `바로 인페인팅 실행`을 누른다. 실행 후 `원본 | 결과` 슬라이더로 비교한다.

선택 화면은 로컬 인터페이스에만 바인딩되고 임의 토큰으로 보호된다. `AI 프롬프트 만들기`를 누르면 `<project-root>/inpainting/session.json`을 생성하고 창은 agent의 프롬프트 보강을 기다린다. 입력 이미지는 설정된 입력 폴더에 저장한다.

## Agent 프롬프트 보강

선택 화면 프로세스의 stdout에서 `[AGENT_PROMPT]` 또는 `[AGENT_REGENERATE]` JSON을 기다린다. 이 JSON에는 원문 `prompt`, 현재 `current_enhanced_prompt`, `mode`, `manifest`, `enhance_url`이 들어 있다. **번역이나 보강을 스크립트 또는 외부 번역 API에 위임하지 말고 이 스킬을 실행하는 agent가 직접 수행한다.**

- 원문이 한국어이면 의미를 그대로 유지한 짧은 영어 명령 한 문장으로 번역한다.
- 영어 원문이 이미 짧고 명확하면 그대로 사용한다. 문법 교정이나 표현 보강도 하지 않는다.
- 프롬프트는 선택한 네모 crop 안의 변경만 설명하며 가능하면 3~12개 영어 단어로 쓴다.
- 전체 이미지, 박스 밖 배경, 자세, 조명 등의 장황한 보존 지시는 넣지 않는다. 박스 밖 보존은 stitch 단계가 담당한다.
- `natural`, `matching`, 재질, 조명처럼 사용자가 요청하지 않은 수식어를 추가하지 않는다.
- 예: `모자를 대머리로 변경` → `change the hat to bald head`
- 사용자가 요청하지 않은 디자인이나 의미를 새로 만들지 않는다.
- 외부 레퍼런스가 있으면 레퍼런스 사용을 이해하는 데 꼭 필요한 대상만 짧게 명시한다.
- `[AGENT_REGENERATE]`에서도 더 길게 설명하지 말고 같은 의미의 짧은 대안만 만든다.

보강한 영어 프롬프트를 해당 이벤트의 `enhance_url`에 JSON으로 POST한다.

```json
{"prompt": "<agent-enhanced English editing prompt>"}
```

이 요청은 보강 프롬프트만 화면에 반영하며 ComfyUI를 실행하지 않는다. 사용자가 `바로 인페인팅 실행`을 누르면 현재 표시된 보강 프롬프트를 바꾸지 않고 실행한다. 선택 화면은 `/status`를 자동 확인하며 완료 결과를 같은 창의 `원본 | 결과` 슬라이더에 표시한다. 사용자가 `완료하고 창 닫기`를 누를 때까지 프로세스를 유지한다.

## ComfyUI 실행

agent가 보강 프롬프트를 로컬 선택 서버에 전달하면 아래 실행기가 내부적으로 호출되므로 일반 사용 시 별도 명령은 필요 없다. 저장된 세션을 다시 실행할 때만 아래 명령을 사용한다.

```bash
<python> <skill-directory>/scripts/run_inpainting.py \
  --project-root <project-root>
```

실행기는 다음 조건을 자동 적용한다.

- 레퍼런스 없음: 외부 reference-conditioning을 제거하고 `red.json`과 동일한 그래프에서 Klein 증류 모델 권장값인 `context_expand=1.0`, `SamplerCustomAdvanced`, `euler`, `Flux2Scheduler 4 steps`, `cfg=1.0`, `mean_std` stitch를 사용한다.
- 레퍼런스 있음: 외부 레퍼런스 latent를 프롬프트 조건에 추가한다.
- 원본 이미지는 두 모드 모두 필수이며, 선택 박스 밖 영역을 복원하는 기준으로 사용한다.

## 서버 요구사항

실행 전에 `/object_info`로 다음 항목을 점검한다. 누락된 항목이 있으면 오류에 표시된 노드나 모델을 ComfyUI 서버에 설치한 뒤 다시 실행한다.

- 노드: `SMInpaintSquareCrop`, `SMInpaintSquareStitch`, `SamplerCustomAdvanced`, `Flux2Scheduler`, `ReferenceLatent`, `EmptyFlux2LatentImage`
- 모델: `flux-2-klein-9b.safetensors`, `qwen_3_8b_fp8mixed.safetensors`, `flux2-vae.safetensors`

## 결과 확인

- stdout에 출력된 결과 경로를 사용자에게 전달한다.
- 첫 결과 이름은 `<원본 stem>-inpaint.png`이다.
- 기본 결과 위치는 `<project-root>/inpainting/outputs`이며 설정에서 변경할 수 있다.
- 실패하면 stderr의 `[실패]` 원인을 요약하고 원본, 레퍼런스, 기존 결과는 삭제하지 않는다.

## 다른 프로젝트에 설치 또는 업데이트

이미 설치된 스킬의 `install_or_update.py`를 실행하면 GitHub의 최신 버전을 현재 프로젝트에 덮어쓴다. `--tool`에 따라 프로젝트 루트 아래 `.codex/skills/inpaint-image-region` 또는 `.claude/skills/inpaint-image-region`을 사용한다.

```bash
# Codex 프로젝트
<python> <installed-skill-directory>/scripts/install_or_update.py \
  --tool codex --project-root <new-project-root>

# Claude Code 프로젝트
<python> <installed-skill-directory>/scripts/install_or_update.py \
  --tool claude --project-root <new-project-root>
```

처음 설치할 때는 `sm-skills` 저장소에서 이 스킬 폴더를 sparse clone한 뒤 같은 스크립트를 `--source`와 함께 실행한다. Windows PowerShell에서는 임시 경로와 프로젝트 경로를 Windows 형식으로 바꾸고 `<python>`에 `py -3`을 사용한다.

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/csm-kr/sm-skills /tmp/sm-skills
git -C /tmp/sm-skills sparse-checkout set inpaint-image-region
<python> /tmp/sm-skills/inpaint-image-region/scripts/install_or_update.py \
  --source /tmp/sm-skills/inpaint-image-region \
  --tool codex --project-root <new-project-root>
```
