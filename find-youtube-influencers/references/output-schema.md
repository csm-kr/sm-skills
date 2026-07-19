# 조사 기록 및 출력 스키마

## UI 진행 상태 JSON

프롬프트에 `UI_RUN_ID`와 UI 출력 경로가 있으면 조사 세션의 실제 상태를 `UI_STATUS_PATH`에 다음 형식으로 기록한다.

```json
{
  "run_id": "youtube-browser-use-YYYY-MM-DDTHH-MM-SS-Z",
  "phase": "verification",
  "message": "후보 30개 중 8개 채널의 최근 일반 영상 검증을 완료했습니다.",
  "updated_at": "YYYY-MM-DDTHH:MM:SS+09:00",
  "candidate_count": 30,
  "verified_count": 8,
  "logs": [
    "[criteria] 일반 영상 3개 · 평균 댓글 50개 · 평균 조회수 1만 조건 확정",
    "[discovery] 공개 검색으로 중복 제거 후보 30개 수집",
    "[verification] 채널 8개 직접 검증 완료"
  ],
  "report_url": null
}
```

`phase`는 다음 값만 사용한다.

- `criteria`: 조건과 필수 게이트 확정
- `discovery`: 공개 검색과 후보 수집 진행
- `verification`: 실제 YouTube 채널·영상 검증 진행
- `scoring`: `score_candidates.py` 계산·판정 진행
- `reporting`: HTML 생성·검수 진행
- `complete`: UI용 JSON과 HTML까지 생성·확인 완료
- `error`: 실제로 더 진행할 수 없는 오류 또는 사용자 조치 필요

다음 규칙을 지킨다.

- `run_id`는 프롬프트의 `UI_RUN_ID`와 정확히 일치시킨다.
- `updated_at`은 상태 파일을 실제 갱신한 시각으로 기록한다.
- `candidate_count`와 `verified_count`는 확인된 실제 개수만 넣는다. 아직 모르면 생략한다.
- `logs`는 최대 50개를 유지하고, 실제 완료 순서대로 짧게 적는다. 추정 진행률이나 가짜 CLI 출력을 만들지 않는다.
- 상태 파일은 유효한 JSON 한 개로 완전히 교체하여 UI가 부분 JSON을 읽지 않게 한다.
- `complete`를 기록하기 전에 `UI_SCORED_PATH`에 최종 계산 JSON, `UI_REPORT_PATH`에 최종 HTML을 복사하고 두 파일을 확인한다.
- `complete`의 `report_url`은 `/research-runs/<UI_RUN_ID>/influencer-report.html`로 기록한다.
- 실패 시 이미 확인한 결과를 삭제하지 말고 `phase: "error"`와 실제 원인을 기록한다.

## 입력 JSON

`scripts/score_candidates.py`에 다음 최상위 구조를 전달한다.

```json
{
  "criteria": {
    "product": "",
    "category": "",
    "market": "한국",
    "language": "한국어",
    "target_audience": "",
    "subscriber_min": null,
    "subscriber_max": 100000,
    "recent_video_count": 3,
    "recent_content_type": "longform",
    "comment_rule": "total",
    "minimum_comment_total": null,
    "minimum_average_comments": null,
    "minimum_average_views": null,
    "upload_recency_days": 90,
    "sponsored_content_required": false,
    "preferred_content": [],
    "excluded_content": [],
    "result_count": 5,
    "strictness": "strict",
    "evaluation_date": "YYYY-MM-DD",
    "near_match_tolerance": 0.2,
    "require_complete_evidence": true
  },
  "candidates": []
}
```

`recent_content_type`은 `longform` 또는 `shorts`만 사용한다. 전체 업로드 요청은 같은 후보를 유형별로 나누어 두 번 계산한다. `near_match_tolerance`는 NEAR MATCH 설명에만 쓰며 PASS 기준을 완화하지 않는다.

## 후보 JSON

영상 배열은 최신순으로 기록한다. 제외 영상도 남길 수 있지만 `eligible: false`와 `exclusion_reason`을 반드시 넣는다.

```json
{
  "channel_name": "",
  "channel_url": "",
  "subscriber_count": null,
  "content_type": "longform",
  "recent_videos": [
    {
      "title": "",
      "url": "",
      "published_at": "YYYY-MM-DD",
      "content_type": "longform",
      "views": null,
      "views_displayed": "",
      "views_approximate": false,
      "comments": null,
      "comments_displayed": "",
      "comments_approximate": false,
      "sponsored": null,
      "sponsorship_evidence": "",
      "eligible": true,
      "exclusion_reason": ""
    }
  ],
  "sponsored_content_verified": null,
  "sponsorship_evidence": "",
  "product_relevance_evidence": "",
  "audience_evidence": "",
  "product_fit": null,
  "audience_fit": null,
  "engagement_score": null,
  "reach_score": null,
  "advertising_experience_score": null,
  "activity_score": null,
  "commercial_fit": null,
  "brand_safety": null,
  "authenticity": null,
  "status": "UNVERIFIED",
  "failure_reasons": [],
  "checked_at": "YYYY-MM-DD"
}
```

0~5 평가값은 공개 근거가 있을 때만 넣는다. `null`은 0점이 아니다. `views_approximate` 또는 `comments_approximate`가 true인 경계값 후보는 엄격한 PASS로 쓰지 말고 수동 검토하거나 UNVERIFIED로 둔다.

## 계산 결과 JSON

스크립트는 각 후보에 다음 파생 필드를 추가한다.

- `selected_videos`: 요청한 유형에서 계산에 사용한 최신 N개
- `comment_total`
- `average_comments`
- `average_views`
- `engagement_by_views`
- `days_since_latest_upload`
- `metric_window_complete`
- `weighted_recommendation_score`: 0~100. 여섯 점수 구성요소가 모두 있을 때만 값 생성
- `score_coverage`: 확인된 가중치 비율
- `score_components_missing`
- `status`: `PASS`, `NEAR MATCH`, `FAIL`, `UNVERIFIED`
- `failure_reasons`: 실제값, 요구값, 차이를 포함한 필수 조건 실패 목록
- `verification_issues`: 판정을 막은 누락·근사·증거 문제

## 최종 Markdown

첫 문장은 실제 적용한 조사 기준을 요약한다.

```markdown
조사 기준: 한국 유튜브 채널 중 [상품] 광고에 적합하고, [필수 수치 조건]을 충족하는 [일반 영상/Shorts] 채널을 YYYY-MM-DD 기준으로 조사했습니다.

## PASS

| 순위 | 채널 | 구독자 | 최근 영상 댓글 | 합계 | 평균 조회수 | 광고 경험 | 상품 적합성 | 판정 |
|---|---|---:|---|---:|---:|---|---|---|
| 1 | [채널명](검증된 채널 URL) | 72,000 | 210 / 180 / 155 | 545 | 31,000 | 식품 협찬 | 다이어트 식단 | PASS |

## 상세 분석

### 1. 채널명

- 추천 이유:
- 예상 시청자: 공개 자료 또는 “콘텐츠 근거 추정” 표시
- 기존 제품 소개 방식:
- 콘텐츠 아이디어:
- 주의할 점:
- 최근 영상: [영상 1](URL) — 댓글 N개 / [영상 2](URL) — 댓글 N개 / [영상 3](URL) — 댓글 N개
- 확인 날짜: YYYY-MM-DD

## NEAR MATCH

| 채널 | 탈락 조건 | 실제 수치 | 활용 가능성 |
|---|---|---:|---|

## FAIL / UNVERIFIED

| 채널 | 판정 | 탈락 또는 검증 불가 사유 | 실제 수치 |
|---|---|---|---:|
```

마지막에는 최종 통과 수, 전체 조사 후보 수, 조건별 주요 탈락 원인, 가장 추천하는 1~3개, 다음 행동을 정리한다. FAIL은 전체가 길면 핵심 또는 대표 사례만 표에 싣고 나머지는 조건별 집계한다. UNVERIFIED를 FAIL로 바꾸지 않는다.

PASS가 0명이면 다음 순서를 지킨다.

1. 모든 조건을 충족한 채널을 찾지 못했다고 명시한다.
2. 조사한 전체 후보 수를 밝힌다.
3. 가장 많이 탈락한 조건을 설명한다.
4. NEAR MATCH를 최대 5명 제시한다.
5. 댓글 기준, 표본 수, 구독자 상한, 콘텐츠 유형, 광고 경험 범위를 완화할 때의 예상 영향을 제안한다.

완화안은 제안일 뿐이며 사용자가 승인하기 전에는 PASS 기준이나 결과에 적용하지 않는다.

## HTML 보고서 입력 메타데이터

`score_candidates.py`는 최상위 `report_metadata` 객체가 있으면 계산 결과에 그대로 보존한다. 이 객체에는 계산값을 넣지 말고 보고서 표현과 조사 집계만 넣는다.

```json
{
  "report_metadata": {
    "title": "그래놀라 광고 유튜버 조사",
    "criteria_summary": "한국어 채널 · 구독자 10만 이하 · 최근 일반 영상 3개 댓글 합계 200개 이상",
    "generated_at": "YYYY-MM-DD",
    "researched_candidate_count": 30,
    "conclusion": "필수 조건을 모두 통과한 채널은 3개입니다.",
    "top_recommendations": ["채널 A — 식단 콘텐츠와 광고 경험이 모두 확인됨"],
    "failure_summary": ["댓글 합계 200개 미달이 가장 많았음"],
    "next_actions": ["상위 후보에게 제품·예산·일정이 포함된 브리프 전달"],
    "methodology_notes": ["2026-01-01 기준 공개 유튜브 페이지 직접 확인"]
  }
}
```

후보 객체에는 필요할 때 다음 정성 보고서 필드를 추가한다. 공개 근거 없이 채우지 않는다.

- `priority_rank`: PASS 또는 근접 후보 안에서의 편집 순서
- `fit_summary`: 상품과 채널의 연결을 한 문장으로 요약
- `recommendation_reason`
- `audience_summary`: 공개 자료가 없으면 반드시 “콘텐츠 근거 추정”이라고 표시
- `existing_product_style`
- `content_idea`
- `advertising_experience_evidence`
- `cautions`

## HTML 출력

`scripts/render_report.py`는 계산된 JSON을 받아 UTF-8 자체 포함형 HTML 한 파일을 만든다.

```text
python scripts/render_report.py --input scored-candidates.json --output influencer-report.html
```

HTML에는 다음 블록이 있어야 한다.

1. 보고서 제목, 조사 기준, 생성·확인일
2. 조사 후보 수와 상태별 KPI
3. PASS/NEAR MATCH/FAIL/UNVERIFIED 요약 표
4. 후보별 구독자, 댓글 합계, 평균 조회수, 최근 영상 3개 링크
5. 추천 이유, 예상 시청자, 기존 소개 방식, 콘텐츠 제안, 광고 경험, 주의점
6. 상위 추천, 주요 탈락 원인, 다음 행동, 방법론·한계

렌더링 뒤 Browser Use로 로컬 파일을 열어 다음을 확인한다.

- HTML 제목과 기준 문장이 JSON과 일치한다.
- 상태별 수와 표의 행 수가 계산 결과와 일치한다.
- 실제로 검증한 YouTube HTTPS 링크만 클릭 가능하다.
- 긴 제목과 모바일 폭에서 표와 카드가 잘리지 않는다.
- `null`은 0이 아니라 “확인 불가” 또는 근거 부족으로 표시된다.

검수가 끝나면 조사 시작 전에 저장한 `targetId` 목록과 비교해 이번 작업이 만든 유튜브·검색·로컬 HTML 탭만 닫고, 다시 `list_tabs()`를 실행해 작업 탭이 남지 않았는지 확인한다. 기존 사용자 탭과 로컬 브라우저 프로세스는 닫지 않는다.
