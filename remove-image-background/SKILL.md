---
name: remove-image-background
description: 사용자를 한 번에 질문 하나씩 안내해 ComfyUI 서버와 입출력 폴더를 최초 설정하고, 입력 이미지를 BiRefNet 워크플로로 배경 제거해 원본명-rmbg.png 투명 PNG로 저장한다. 이미지 배경 제거, 누끼 따기, 투명 배경 생성, 입력 폴더 일괄 처리 또는 Windows/macOS/Linux에서 재사용 가능한 ComfyUI 배경 제거 설정을 요청할 때 사용한다.
---

# ComfyUI 이미지 배경 제거

스킬에 포함된 Python 표준 라이브러리 스크립트와 API 워크플로만 사용한다. 프로젝트나 운영체제에 종속된 절대경로를 가정하지 않는다.

## 최초 설정 인터뷰

`<project-root>/bg-remove/config.json`이 없을 때 아래 순서로 설정한다. **한 메시지에는 질문을 정확히 하나만 포함하고 답을 받은 뒤 다음 질문으로 이동한다.** 이미 답을 알거나 안전하게 자동 감지한 항목은 다시 묻지 않는다.

1. `ComfyUI 서버 주소가 무엇인가요? 로컬 기본값은 http://127.0.0.1:8188입니다.`
2. `배경을 제거할 이미지 입력 폴더를 어디로 할까요? 기본값은 <project-root>/bg-remove/inputs입니다.`
3. `완성된 이미지 출력 폴더를 어디로 할까요? 기본값은 <project-root>/bg-remove/outputs입니다.`

세 답을 모두 받은 후에만 설정을 저장하고 서버를 점검한다.

```bash
<python> <skill-directory>/scripts/remove_background.py \
  --project-root <project-root> \
  --server <server-url> \
  --input-dir <input-directory> \
  --output-dir <output-directory> \
  --configure
```

- macOS/Linux에서는 `<python>`에 `python3`를 사용한다.
- Windows에서는 `<python>`에 `py -3`를 우선 사용하고, 없으면 `python`을 사용한다.
- 공백이 포함된 Windows 경로와 POSIX 경로는 따옴표로 감싼다.

설정 파일이 있으면 저장된 값을 사용하고 인터뷰를 반복하지 않는다. `COMFYUI_SERVER` 환경변수나 `--server`가 있으면 저장된 서버 주소보다 우선한다. 연결이나 설정이 깨졌을 때만 해당 항목을 질문 하나로 다시 확인한다.

## 서버 점검과 모델 설치

설정 시 `/object_info`로 필수 노드와 `birefnet.safetensors`를 점검한다.

- 필수 노드가 없으면 최신 ComfyUI로 업데이트하도록 알리고 `업데이트를 마쳤나요?`만 질문한다.
- 모델이 없고 ComfyUI가 같은 컴퓨터에 있으면 `공식 BiRefNet 모델을 다운로드할까요?`만 질문한다.
- 사용자가 동의한 다음 메시지에서 `ComfyUI 설치 루트 폴더가 어디인가요?`만 질문한다.
- 설치 루트를 받으면 아래 명령을 실행한다. 모델은 약 444 MB이며 다운로드 전 동의를 생략하지 않는다.

```bash
<python> <skill-directory>/scripts/install_birefnet.py <comfyui-root>
```

설치 후 설정 명령을 다시 실행한다. 서버가 원격이고 파일시스템에 접근할 수 없으면 서버 관리자에게 `ComfyUI/models/background_removal/birefnet.safetensors` 설치를 요청해야 함을 알린다. 모델 출처는 `https://huggingface.co/Comfy-Org/BiRefNet`이다.

## 배경 제거 실행

사용자가 새 이미지를 제공하면 설정된 입력 폴더에 원본 파일명 그대로 복사하며, 원본은 삭제하지 않는다. 새 이미지 경로를 인자로 전달하면 복사와 처리를 한 번에 수행한다.

```bash
<python> <skill-directory>/scripts/remove_background.py \
  --project-root <project-root> \
  <input-image> [<input-image> ...]
```

입력 이미지를 지정하지 않으면 설정된 입력 폴더의 지원 이미지 전체를 처리한다.

```bash
<python> <skill-directory>/scripts/remove_background.py \
  --project-root <project-root>
```

입력 폴더가 비어 있고 사용자도 이미지를 제공하지 않았을 때만 `배경을 제거할 이미지를 첨부하거나 경로를 알려주시겠어요?`라고 질문한다.

## 결과 확인

- 종료 코드가 `0`인지 확인한다.
- stdout에 출력된 결과 경로를 전달한다.
- 결과 이름은 `<원본 stem>-rmbg.png`로 고정한다. 예: `photo.jpg` → `photo-rmbg.png`.
- 결과 PNG가 `RGBA`이고 알파 범위에 `0`과 `255`가 포함되는지 가능한 범위에서 확인한다.
- 실패하면 stderr의 `[실패]` 내용을 요약하며 입력 파일과 기존 결과는 삭제하지 않는다.
