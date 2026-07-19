# sm-skills

Claude Code와 Codex에서 사용할 수 있는 스킬 모음.

## Skills

- **paper-reading** — 연구 논문을 한국어로 한 단계씩(central claim → ... → what to remember) 설명하고, 매 단계 이해를 확인한 뒤 진행하는 스킬.
- **paper-scout** — detection·feature-extraction·generative-detection 관련 논문/자료를 웹에서 찾아 핵심 contribution 을 구조화(contribution card)해 뽑아오는 스킬.
- **ppt-maker** — 주제·노트·이미지·문서로부터 브랜드 reveal.js HTML 덱을 같이 만들어 `.html`·`.pdf`로 뽑는 스킬. `input/` → `output/NN_주제_날짜/` 구조로 입출력을 정리한다.
- **ai-readiness-cartography** — 임의 레포를 AI-Ready v2 루브릭(100점 · 7 카테고리)으로 감사해 전문 기술 대시보드 HTML + 점수 JSON + ROI 순 액션 리스트를 뽑는 스킬. `scripts/score.py`가 커버리지·hallucinated path·drift·god file 을 자동 채점한다.
- **remove-image-background** — 사용자에게 한 번에 하나씩 질문해 ComfyUI 서버와 입출력 폴더를 설정하고, 로컬 드래그 앤 드롭 화면 또는 파일 경로로 받은 이미지를 BiRefNet으로 처리해 `<원본명>-rmbg.png` 투명 PNG로 저장하는 Windows·macOS·Linux 호환 스킬.
- **inpaint-image-region** — 로컬 화면에서 원본을 드래그하고 변경 박스를 그린 뒤 프롬프트와 선택적 레퍼런스로 ComfyUI Flux 2 Klein 인페인팅을 실행한다. 레퍼런스를 비우면 자동으로 텍스트 전용 모드가 된다.
- **coupang-detail-page** — RAW·WEB_MATCH·실제 레퍼런스를 분리하고 `RAW→REFERENCE→REASON→PROOF→PAGE` 계보로 쿠팡 상세페이지를 기획·생성하는 한국어 스킬. 공개 인기 사례 001–010과 매 프로젝트의 실제 상품 조사를 이용하되 타사 기능은 전이하지 않는다. 기능·실측·구성·사용법을 디자인보다 먼저 두고, 독점 구매 질문 수만큼 3~10장(보통 5~8장)을 선택해 반복을 제거한다. `plan-review.html` 승인과 해시 게이트 뒤에만 `800×2400` PNG 및 선택한 GIF·영상을 실행한다.
- **coupang-product-sourcing** — Browser Use로 도매 후보와 쿠팡 실제 경쟁상품을 교차 조사하고, 하드 필터·수요·마진·경쟁기회·운영위험을 근거 URL과 함께 계산해 `SHORTLIST`·`WATCH`·`REJECT` 후보표와 상세페이지 제작용 핸드오프를 생성한다.
- **find-youtube-influencers** — 상품과 수치 조건에 맞는 유튜버를 공개 웹 검색과 Browser Use로 직접 검증하고 PASS·근접·탈락·검증 불가로 분류한다. 설치된 Codex CLI를 실행하는 로컬 UI, 실시간 JSONL 단계, 후보 상세 슬라이드, 5명 단위 추가 탐색, HTML 보고서 생성이 스킬 폴더 하나에 포함된다.

각 스킬은 해당 디렉토리의 `SKILL.md` 에 정의돼 있다.

## 설치

### 유튜브 인플루언서 스킬만 설치

`find-youtube-influencers` 디렉토리 하나만 Codex 스킬 폴더에 복사하면 UI까지 함께 설치된다. 별도 UI ZIP은 필요 없다.

```powershell
$checkout = Join-Path $env:TEMP 'sm-skills'
git clone --depth 1 --filter=blob:none --sparse https://github.com/csm-kr/sm-skills $checkout
git -C $checkout sparse-checkout set find-youtube-influencers
$skillsRoot = Join-Path $env:USERPROFILE '.codex\skills'
New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null
Copy-Item -Recurse -Force (Join-Path $checkout 'find-youtube-influencers') $skillsRoot
$target = Join-Path $skillsRoot 'find-youtube-influencers'
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $target 'scripts\start_ui.ps1')
```

Codex에서 `$find-youtube-influencers UI를 열어줘`라고 요청해도 같은 번들 런처를 실행한다. Node.js와 로그인된 Codex CLI는 필요하다.

### 영역 인페인팅 스킬 설치·업데이트

처음에는 스킬 하나만 sparse clone한 뒤 프로젝트의 Codex 또는 Claude Code 폴더에 설치한다.

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/csm-kr/sm-skills /tmp/sm-skills
git -C /tmp/sm-skills sparse-checkout set inpaint-image-region

# Codex: <project>/.codex/skills/inpaint-image-region
python3 /tmp/sm-skills/inpaint-image-region/scripts/install_or_update.py \
  --source /tmp/sm-skills/inpaint-image-region \
  --tool codex --project-root /path/to/project

# Claude Code: <project>/.claude/skills/inpaint-image-region
python3 /tmp/sm-skills/inpaint-image-region/scripts/install_or_update.py \
  --source /tmp/sm-skills/inpaint-image-region \
  --tool claude --project-root /path/to/project
```

설치 후에는 설치된 스크립트를 실행하면 GitHub의 최신 버전으로 업데이트된다.

```bash
python3 /path/to/project/.codex/skills/inpaint-image-region/scripts/install_or_update.py \
  --tool codex --project-root /path/to/project
```

Windows에서는 `python3` 대신 `py -3`을 사용하고 `/tmp/sm-skills`, `/path/to/project`를 Windows 경로로 바꾼다. 스킬을 실행할 때 ComfyUI만 열려 있으면 첫 사용 시 서버 주소와 입출력 폴더를 한 번에 하나씩 설정한다.

### Codex

`coupang-detail-page`만 설치하려면:

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/csm-kr/sm-skills /tmp/sm-skills
cd /tmp/sm-skills && git sparse-checkout set coupang-detail-page
PROJECT_DIR="/path/to/your-project"
mkdir -p "$PROJECT_DIR/.agents/skills"
cp -r /tmp/sm-skills/coupang-detail-page "$PROJECT_DIR/.agents/skills/coupang-detail-page"
cd "$PROJECT_DIR/.agents/skills/coupang-detail-page"
python3 scripts/init_project.py --prepare 1
```

입력과 출력이 스킬 폴더 아래에 생성되므로 쓰기 가능한 프로젝트 로컬 `.agents/skills/` 설치를 사용한다. 설치 후 Codex에서 다음처럼 호출하면 한국어 온보딩이 시작된다. 스킬은 한 번에 한 질문만 하고, 모든 선택 질문의 마지막 번호에는 `다른 답변하기`를 제시한다. 입력 확인부터 웹 조사, 가변 장수 기획, HTML 검토, 승인된 `N/선정 장수` 생성·QA·납품까지 진행 상황도 중간중간 알린다.

```text
$coupang-detail-page를 시작해줘.
```

온보딩 안내에 따라 현재 판매 상품의 원본 사진을 `inputs/001/original-images/`에 1장 이상 넣는다. 실측·실사 시험은 `evidence/`, 웹에서 동일·유력으로 확인한 보조 자산은 `web-confirmed/`, 표현 원리만 참고할 실제 상세페이지는 `real-references/`에 각각 분리한다. 상품 정보는 Git에서 제외되는 `inputs/001/product-info.md`에 저장된다. 스킬은 동일·유사 제품과 접근 가능한 실제 상세페이지를 최소 3개 조사하고, 각 웹 자산의 URL·조사일·ASSET_ID·로컬 SHA256 계보를 기록한다.

기능·호환·실측·사양·구성·사용·관리·안전 중 근거가 있는 독점 정보 단위를 세어 3~10장만 기획한다. 생성 전 `outputs/001/plan-review.html`에서 장별 카피·화면·RAW·Proof·레퍼런스 원리·프롬프트·폰트를 검토하고, 소스 해시와 HTML SHA256을 함께 승인해야 한다. 승인된 최종본은 `outputs/001/final/page-01.png`부터 선정한 마지막 번호까지 모두 `800×2400`으로 검증된다. GIF·영상은 정확한 motion ID·형식·환경을 별도 승인한 경우에만 실행하며, 전체 과정은 스킬 폴더의 `workflow.html`에서 볼 수 있다.

이미지 정규화와 전체 디코딩 검증에는 Pillow를 사용한다. 한글 카피는 기본적으로 `image_gen` 호출 안에서 직접 조판하며, 후편집은 두 번의 직접 생성 실패 뒤 사용자가 선택한 예외 경로다. Pillow가 없고 `python3 -m pip`가 사용 가능하면 첫 필요 시 스킬 내부 `.runtime/`에 자동 설치해 시스템 Python 패키지를 변경하지 않는다. `pip`도 없다면 먼저 pip가 포함된 Python을 준비하거나 `python3 -m pip install -r requirements.txt`를 실행한다.

실사 `REAL_TEST`·`REAL_DEMO` GIF·영상의 원본 검증에는 FFmpeg의 `ffprobe`가 필요하다. AI 모션의 실제 렌더는 `scripts/comfyui_receipt.py` receipt와 생성 시점 `/system_stats` 재확인을 모두 통과한 live `CONNECTED` ComfyUI에서만 허용한다. 구조가 검증된 `WORKFLOW_PROVIDED`는 제작안·워크플로 핸드오프 전용이며 실제 렌더 완료를 뜻하지 않는다.

### Claude Code

특정 스킬 하나만 받으려면 (예: `ppt-maker`):

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/csm-kr/sm-skills /tmp/sm-skills
cd /tmp/sm-skills && git sparse-checkout set ppt-maker
cp -r /tmp/sm-skills/ppt-maker ~/.claude/skills/ppt-maker
```

Codex에서는 같은 방식으로 원하는 스킬을 프로젝트의 `.codex/skills/` 또는 사용자 전역 `~/.codex/skills/`에 복사한다.

또는 저장소 전체를 받아 원하는 스킬 폴더만 각 도구의 스킬 디렉토리로 복사한다. `coupang-detail-page`는 Codex의 built-in `image_gen`을 전제로 하며, 실행 데이터를 스킬 폴더 아래에 쓰므로 위의 프로젝트 로컬 설치 명령을 사용한다.
