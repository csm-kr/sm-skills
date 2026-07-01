# sm-skills

Claude Code 용 스킬 모음.

## Skills

- **paper-reading** — 연구 논문을 한국어로 한 단계씩(central claim → ... → what to remember) 설명하고, 매 단계 이해를 확인한 뒤 진행하는 스킬.
- **paper-scout** — detection·feature-extraction·generative-detection 관련 논문/자료를 웹에서 찾아 핵심 contribution 을 구조화(contribution card)해 뽑아오는 스킬.
- **ppt-maker** — 주제·노트·이미지·문서로부터 브랜드 reveal.js HTML 덱을 같이 만들어 `.html`·`.pdf`로 뽑는 스킬. `input/` → `output/NN_주제_날짜/` 구조로 입출력을 정리한다.
- **ai-readiness-cartography** — 임의 레포를 AI-Ready v2 루브릭(100점 · 7 카테고리)으로 감사해 전문 기술 대시보드 HTML + 점수 JSON + ROI 순 액션 리스트를 뽑는 스킬. `scripts/score.py`가 커버리지·hallucinated path·drift·god file 을 자동 채점한다.

각 스킬은 해당 디렉토리의 `SKILL.md` 에 정의돼 있다.

## 설치

특정 스킬 하나만 받으려면 (예: `ppt-maker`):

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/csm-kr/sm-skills /tmp/sm-skills
cd /tmp/sm-skills && git sparse-checkout set ppt-maker
cp -r /tmp/sm-skills/ppt-maker ~/.claude/skills/ppt-maker
```

또는 저장소 전체를 받아 원하는 스킬 폴더만 `~/.claude/skills/` 로 복사한다.
