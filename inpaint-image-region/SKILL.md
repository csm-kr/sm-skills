---
name: inpaint-image-region
description: 로컬 브라우저에서 원본 이미지를 드래그하고 변경할 박스를 그린 뒤 프롬프트와 선택적 레퍼런스 이미지로 ComfyUI Flux 2 Klein 인페인팅을 실행한다. 이미지 일부 교체, 의상·소품·배경 영역 수정, 박스 인페인팅, 외부 참조 기반 변경 또는 텍스트 전용 영역 변경을 요청할 때 사용한다.
---

# ComfyUI 영역 인페인팅

로컬 선택 화면에서 원본, 박스, 프롬프트, 선택적 레퍼런스를 한 번에 받는다. 별도 모드 질문은 하지 않는다. 레퍼런스 칸이 비어 있으면 텍스트 전용으로, 이미지가 있으면 레퍼런스 조건을 추가해 실행한다.

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

1. 원본 이미지를 드래그 앤 드롭한다.
2. 원본 위에서 변경할 사각형을 한 번 드래그한다. 다시 드래그하면 박스가 교체된다.
3. 변경할 내용을 프롬프트에 입력한다.
4. 외부 참조가 필요할 때만 레퍼런스 칸에 이미지를 드롭한다.
5. `선택 내용으로 인페인팅 준비`를 누른다.

선택 화면은 로컬 인터페이스에만 바인딩되고 임의 토큰으로 보호된다. 제출 후 `<project-root>/inpainting/session.json`을 생성하고 서버가 종료된다. 입력 이미지는 설정된 입력 폴더에 저장한다.

## ComfyUI 실행

선택 화면이 종료된 뒤 아래 명령을 실행한다.

```bash
<python> <skill-directory>/scripts/run_inpainting.py \
  --project-root <project-root>
```

실행기는 다음 조건을 자동 적용한다.

- 레퍼런스 없음: 외부 `LoadImage`, `VAEEncode`, `ReferenceLatent` 체인을 제거하고 텍스트와 원본 박스만 연결한다.
- 레퍼런스 있음: 외부 레퍼런스 latent를 프롬프트 조건에 추가한다.
- 원본 이미지는 두 모드 모두 필수이며, 선택 박스 밖 영역을 복원하는 기준으로 사용한다.

## 서버 요구사항

실행 전에 `/object_info`로 다음 항목을 점검한다. 누락된 항목이 있으면 오류에 표시된 노드나 모델을 ComfyUI 서버에 설치한 뒤 다시 실행한다.

- 노드: `SMInpaintSquareCrop`, `SMInpaintSquareStitch`, `FluxKVCache`, `ReferenceLatent`, `EmptyFlux2LatentImage`
- 모델: `flux-2-klein-9b.safetensors`, `qwen_3_8b_fp8mixed.safetensors`, `flux2-vae.safetensors`

## 결과 확인

- stdout에 출력된 결과 경로를 사용자에게 전달한다.
- 첫 결과 이름은 `<원본 stem>-inpaint.png`이다.
- 기본 결과 위치는 `<project-root>/inpainting/outputs`이며 설정에서 변경할 수 있다.
- 실패하면 stderr의 `[실패]` 원인을 요약하고 원본, 레퍼런스, 기존 결과는 삭제하지 않는다.
