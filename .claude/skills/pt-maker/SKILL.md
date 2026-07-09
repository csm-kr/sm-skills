---
name: pt-maker
description: Use when Claude Code needs to create/design a presentation deck or 발표자료 from topic discussion, notes/sketches, web pages, docs, reference decks, URLs, or web-researched requests, and produce a branded reveal.js HTML deck exported by default to .html and .pdf; image-based .pptx is optional and only on explicit request. Start with one-question-at-a-time Grill Me intake when the user gives only a topic/rough idea, asks to be grilled, or asks to find info online; first check for PPT/PDF/PPTX/docs/screenshots/URLs/data, then determine purpose, audience, context, message, evidence, CTA, mood, and image level before drafting. Use Color Hunt only as a palette source when color direction/redesign is needed. Use for Korean presentation planning, web-researched PT creation, slide narrative, HTML deck construction, PDF export, optional PPTX export, and taste-profile iteration.
---

# pt-maker

## Required update: spacing and image decision rules
These rules override older deck-building habits whenever they conflict.

### Speaker-language and person-image saliency guardrail
Treat visible language consistency and human-subject cropping as hard QA gates.

- Match the visible deck language to the user's language and expected speaker/audience language unless the user explicitly asks otherwise. If the user speaks Korean and asks for a Korean PT, default all audience-facing labels to Korean.
- Apply this to slide titles, section/kicker labels, chart labels, brackets, scoreboards, tier lists, badges, map pins, footers, captions, and short UI-like labels. Do not leave mixed English such as `winner pick`, `market signal`, `France`, `Spain`, `FRA`, `ARG`, etc. unless it is an official source name, proper noun, model/product name, player name, or intentionally taught abbreviation.
- In a Korean deck, visible country/team names must be written in Korean. Three-letter country codes may be used only as small decorative metadata when paired with Korean names or when space makes the code clearly intentional.
- Use the same rule for any other presentation language: country/team names and explanatory labels should match the deck language unless an official English brand/name is intentionally required.
- After localization, rerender and inspect compact UI elements because translated names can be longer than three-letter codes.
- For people photos, do not ship crops that cut off faces, heads, hands holding key objects, or the obvious salient subject. Use a better source image, `object-position`, a focal crop, or `object-fit: contain` when needed.
- For player/person cards, inspect at least one full-size rendered slide for every reused crop pattern. If the cover or final slide uses a wide image crop, verify that the face and primary subject remain readable at thumbnail and full size.
- Generated or self-made visuals must also preserve the salient subject. Do not let labels, badges, dark overlays, or decorative panels cover a face or the main object.

### Narrative arc and layout variation guardrail
Treat deck rhythm as a hard design requirement, especially for promotional decks.

- Plan the slide sequence as `기-승-전-결`: opening hook, identity/build-up, proof/expansion, closing takeaway or action.
- Treat each slide as one topic. Do not make a slide explain two unrelated claims; split it or rewrite the title so the slide has a single role in the explanation flow.
- Before building, write a one-line role for each slide in the arc. The PDF should read in order without requiring presenter improvisation to connect the logic.
- Use deliberate layout variation only when it improves rhythm without breaking the deck's design system. Preserve the same typography, color tokens, footer/header logic, and spacing rules while varying object placement.
- For first/last slide variation, prefer a mirrored relationship rather than a new style. Example: if slide 1 uses `portrait photo | headline text`, the final slide may use `closing text | portrait photo`; this is allowed variation because the design language stays intact.
- Do not force variation into every slide. Use alternating split layouts, centered statement, member/grid, timeline, data cards, and final CTA only when the content supports that structure.
- Promotional decks should end with a clear synthesis, not another generic summary slide. The final slide should answer "why this matters now" or "what the audience should remember."
- During QA, inspect the contact sheet for rhythm: the eye should not see five nearly identical slides in a row, and the first/last slide should feel intentionally related but not duplicated.
- Layout variation must never lower finish quality. If a varied layout causes weaker alignment, awkward wrapping, text overflow, cramped cards, or unclear hierarchy, revert to a stronger layout or redesign it.
- Variation should be structural, not decorative: alternate between split, mirrored split, centered statement, matrix/table, flow/timeline, checklist, dashboard, and image-led layouts only when the content genuinely fits that form.
- Do not use variation as an excuse for inconsistency. Headers, page/kicker logic, type scale, color tokens, safe areas, and footer/source behavior must remain stable.
- If several slides repeat the same card grid but the copy does not fit, do not shrink the grid text. Change the layout pattern, reduce points, or split the slide while preserving polish.

### Spacing guardrail: readable but aesthetically light
Treat readable typography as a hard QA gate, but do not make every slide oversized.

- For the 1280x720 reveal canvas, use Pretendard as the default body typeface and target a lighter aesthetic scale: body and bullets normally `28-30px`, hard floor `26px`, card body `24-26px`, supporting labels `20-22px`, and source/fine-print `15-16px`. If the deck is for a large room/projector or accessibility-first delivery, raise primary body back toward `32px`.
- Body text must use `line-height >= 1.5`, normally `1.54-1.62`; dense captions, source notes, and labels must use `line-height >= 1.38`.
- Adjacent text blocks must have visible breathing room: bullet items `margin-block >= .58em`, card paragraphs `margin-block >= .46em`, and heading-to-body gaps `>= .52em`.
- If a slide feels crowded, reduce words first, split the idea into another slide second, and only then reduce font size. Do not solve crowding by tightening line-height.
- Small text is allowed only when it still looks airy: use wider line-height, shorter lines, and more surrounding whitespace.
- During visual QA, reject any slide where Korean lines visually touch, where two text blocks read as one paragraph, where a label sits too close to an icon/number, or where body text looks heavy and poster-like because everything was forced to 32px+.

### Text fit, wrapping, and layout integrity hard gate
Treat text fit as a zero-tolerance QA gate. A slide that looks pleasant in the source HTML but breaks after PDF/export is a failed deck.

- Any text that overflows its box, escapes the slide, touches a card edge, collides with another object, is clipped, or becomes visually trapped is a P0 hard fail.
- Any awkward Korean line break that splits a word, number/unit, product name, proper noun, section number, or short label in a way that looks accidental is a P0 hard fail.
- Any table, card grid, checklist, timeline, diagram label, or footer/source note whose wrapping makes the layout look misaligned, cheap, or broken is a P0 hard fail even if the text is technically readable.
- Do not “fix” overflow by only shrinking text. First reduce copy, then simplify the structure, then split the slide, and if the slide still does not fit, redesign the layout completely.
- If a row/column card layout cannot hold the text cleanly, change the layout: use fewer cards, a larger matrix, a split layout, a single diagram, or multiple slides.
- Before delivery, inspect the rendered PDF, not only the browser HTML. If the HTML looks good but the PDF/contact sheet is wrong, the deck is not done.

### Text overflow zero-score guardrail
Treat text stability as a hard fail, not a polish preference. A slide can have attractive typography and still score zero if text escapes, clips, collides, or wraps awkwardly in the rendered PDF/contact sheet.

- Reject any slide with text outside its container, clipped text, overlapping text, Korean syllables or English words broken in an unnatural place, labels touching borders/icons/footers, or a line break that makes the sentence visually unbalanced.
- QA must inspect rendered output, not only HTML/CSS. Check the contact sheet first, then full-size PNGs for dense slides, long headings, code blocks, cards, tables, diagrams, and any slide the user flagged.
- When a text defect is found, the agent must take corrective action before reporting: shorten the copy, reduce card/code/supporting text size, widen or move the container, split the slide, or simplify the layout. Do not merely list the issue as a QA note.
- Prefer deleting words and simplifying claims before shrinking below the readable floor. For dense cards/code, use the deck's proven small-content scale rather than keeping all body text at the base size.
- After every corrective action, rerender the PDF/contact sheet and recheck the affected slides. Do not deliver a deck with unresolved text overflow, clipping, or broken wrapping.
- In scoring, any unresolved text overflow/clipping/overlap/broken wrapping is `P0` and sets the deck score to `0` until fixed, regardless of overall visual style.

### Rendered micro-polish QA guardrail
Treat these as mandatory rendered-output checks, not subjective afterthoughts. The reviewer must call them out with page numbers, and the main agent must fix and rerender before delivery when they affect finish quality.

- **Bad short-line wrap**: If a heading or prominent sentence wraps into two lines where the second line is only a short tail, mark it `P2` at minimum. If the short tail makes the slide look broken or cheap, mark it `P0`. Prefer widening the text frame, reducing or moving the image/map, shortening copy, or using a slightly smaller heading within the approved scale. Do not accept an ugly two-line title just because it technically fits.
- **Five-character orphan line**: If a rendered Korean heading or prominent sentence leaves any wrapped line, especially the final line, with 5 Korean characters or fewer excluding punctuation and spaces, mark it `P0` unless the break is clearly intentional typography. Fix it by changing the layout first: widen the text region, reduce/reposition the image/map, change the grid, or shorten the phrase. Do not accept it as a font-size-only fix.
- **One-line opportunity**: If a title can naturally fit on one line by modestly reducing the visual region or widening the text region, do that before shrinking text. This is especially important for route/stage slides and activity slides.
- **Stale template or leftover copy**: Any visible text from a previous version, placeholder, old prompt, duplicated label, or removed component is a `P0` stale-content failure. Delete it and rerender.
- **Bottom spill and lower-third crowding**: Any content that exits the safe area, touches the footer, overlaps another element, or looks compressed into the bottom edge is a `P0`. Fix by expanding the content area horizontally, moving material to the right/left, increasing map/image flexibility, reducing list count, or splitting the structure. Do not solve by only shrinking text.
- **Title-to-subtitle spacing**: On closing, statement, and section slides, the main title and supporting line must have deliberate breathing room. If they look visually stuck together, mark `P2`; if they touch or undermine hierarchy, mark `P0`.
- **Large-heading neighbor spacing**: When using very large display type, the adjacent subtitle/body must not look snapped to the headline. If the headline and supporting paragraph read as one cramped block, mark it `P2`; if the hierarchy becomes unclear or the lines nearly touch, mark it `P0`. Fix with grid spacing, margin, copy position, or layout changes before reducing font size.
- **Text over image/map contrast**: Any text, footer, caption, or label placed over a map, photo, screenshot, or busy illustration must remain clearly readable in the rendered PDF. If the background image makes text hard to read, mark it `P0`. Fix by moving or dimming the visual, adding a solid/translucent complementary text panel, increasing local contrast, or relocating the text; do not rely on hope or thumbnail-only inspection.
- **Flagged-page recheck**: When a user names pages or visual defects, export full-size PNGs for those exact pages after the fix and inspect them again before reporting. The final response must mention that the flagged pages were rechecked.
- **Regression recheck**: After fixing any page, regenerate the full final PDF/contact sheet from the exact current source and inspect the whole deck for new wrapping, overflow, contrast, page-order, or visual-crop regressions. Do not deliver based only on the fixed page PNGs.

### Composition balance guardrail: do not dump content at the bottom
Treat layout balance as a hard QA gate. A slide can have enough whitespace and still fail if the visual weight is pushed to the bottom edge or one side.

- Do not use a row of small bottom cards as the default way to hold extra content. Use it only when each card has enough height, text is short, and the row does not feel like an afterthought.
- The primary message should sit near the visual center or optical center of the slide. If a slide has no large image, chart, or diagram, use the central area for the main structure rather than leaving the middle empty and crowding the bottom.
- Keep bottom content above the footer with clear separation. As a rule of thumb, leave at least `.42in` between content boxes and the footer zone in 16:9 paged decks.
- Avoid overlapping or near-overlapping boxes and Korean text. Reject any slide where a text baseline visually touches a box border, footer, card edge, icon, or neighboring label.
- Balance the visual mass: if an image sits on the right, the left should have comparable text/diagram weight; if a card stack sits on one side, the other side needs a deliberate counterweight.
- Prefer centered diagrams, two-column rhythm, or one strong statement plus one supporting visual over many small boxes.
- If content does not fit comfortably, reduce the number of boxes, merge points into a single diagram, or split the idea into another slide. Do not shrink text or compress lower margins to force it in.

### XYWH specificity guardrail: place objects deliberately
For every major slide object, decide the reference frame and record its actual `x y w h` as normalized ratios. Use this to make layout intent concrete instead of relying on vague visual feel.

- Default reference frame is the full 16:9 slide canvas, origin at top-left: `x = left / slideWidth`, `y = top / slideHeight`, `w = width / slideWidth`, `h = height / slideHeight`.
- For paged decks, use `slideWidth = 13.333in` and `slideHeight = 7.5in`. Example: `left: .86in; top: .72in; width: 5.2in; height: 4.1in` becomes `xywh: 0.065 0.096 0.390 0.547`.
- For percentage CSS, the ratio is direct: `left: 6.2%; top: 8%; width: 42%; height: 64%` becomes `xywh: 0.062 0.080 0.420 0.640`.
- If using an inner safe area, name it, but still record the full-slide ratio. Example: `frame: slide; safe-area: 0.062 0.080 0.876 0.840`.
- Add a short intent note for non-obvious placements: `intent: optical center pull`, `intent: right visual counterweight`, `intent: low-tension footer clearance`. This should capture the psychological reason for the position.
- During QA, reject placements whose recorded ratios contradict the rendered screenshot: crowded lower-third objects, off-center "centerpiece" objects, or counterweights that are too small to balance the dominant image.

Recommended CSS/layout defaults for paged decks:

```css
.slide main { display: grid; align-items: center; }
.split { align-items: center; gap: .58in; }
.cards { gap: .22in; }
.bottom-band { margin-top: .38in; margin-bottom: .52in; }
.card { min-height: .98in; padding: .22in .24in; }
```

Recommended CSS defaults for new decks:

```css
.reveal { font-size: 30px; line-height: 1.56; }
.reveal p { line-height: 1.6; margin: .5em 0; }
.reveal li { line-height: 1.55; margin: .58em 0; }
.reveal small, .source, .caption { line-height: 1.42; }
```

### Alignment and readability evaluation guardrail
Before final delivery, read and apply [reference/alignment-eval-rubric.md](reference/alignment-eval-rubric.md).

- Treat visual alignment, readable font size, and finished polish as hard QA gates.
- Use a dedicated alignment-review agent when the environment provides subagents and the user permits agent review. Give it the contact sheet plus full-size PNGs of the cover, final slide, and any diagram/table/checklist slide. It should review only alignment, visibility, and polish unless explicitly assigned a disjoint write scope.
- If no subagent is available, run the same rubric manually and record that in build notes.
- Use the web-backed readability baseline from the rubric, translated through the active delivery profile: normal HTML decks use body/bullets `28-30px` with `26px` hard floor; large-room/projector decks use the stricter PowerPoint-style `24pt` body minimum, approximately `32px` in CSS.
- Reject and rebuild any slide where numbered pins, checklist dots, arrow endpoints, card grids, or labels are visibly off their intended anchors.
- Score the deck with the 100-point rubric. If the score is below 90/100 or any hard fail appears, fix the source, rerender, regenerate the contact sheet, and repeat review before delivery.

### Mandatory PT QA iteration guardrail
Before final delivery, read and apply [reference/general-pt-making-checklist.md](reference/general-pt-making-checklist.md). This is a required process gate, not an optional review note.

- Run `python scripts/qa_media_guard.py <final-or-candidate.html>` before PDF export and after every meaningful HTML/CSS/assets edit. Any `P0` from this script blocks export/delivery until fixed. `export_pdf.py` and `export_pdf_shots.py` also run this guard automatically and must stop on P0.
- Use `python scripts/qa_media_guard.py <html> --json` when passing results to a QA reviewer agent. The agent must treat every script `P0` as a real P0 and then verify the affected pages in rendered PDF/PNG.
- Render PDF and contact sheet before claiming the deck is done.
- After rendering the exact final PDF/contact sheet, create a final `qa_ledger.json` and run `python scripts/qa_score_gate.py <html> <qa_ledger.json>`. A deck may not report `pt-qa-result: pass`, a rubric score `>= 90`, or a final delivery candidate unless this score gate passes.
- `qa_score_gate.py` is the checklist enforcement layer: it requires media guard pass, score >= 90, P0=0, rendered PDF evidence, contact-sheet review, full-size PNG evidence, regression review, all required checklist keys marked pass, and diagram-specific checks when diagrams exist.
- After `qa_score_gate.py` passes, show the HTML/PDF candidate and QA result to the user for final review. The deck is still only a candidate at this point.
- After the user's review, create `user_review_ledger.json` and run `python scripts/qa_final_review_gate.py <html> <qa_ledger.json> <user_review_ledger.json>`. A deck may not be called final, delivered as final, or used to update pt-maker taste guidance unless this final review gate passes.
- `qa_final_review_gate.py` enforces that the candidate was reported to the user, user feedback was accepted or resolved, the deck was rechecked after user review, `qa_score_gate.py` was rerun after the review state became final, and the taste-profile update decision was reviewed with the user.
- If user review produces reusable taste guidance, propose a diff to `taste-profile.md` and/or `dark-taste-profile.md`; update those files only after explicit user confirmation, increment the profile version, and record the decision in `user_review_ledger.json`. If there is no reusable learning or the user declines, record `not_applicable` or `declined` with a reason.
- Generate the contact sheet from the exact final PDF artifact, not from cached browser screenshots, stale PNGs, or an earlier export. If page order is uncertain, generate a numbered PDF contact sheet and verify page 1..N against the intended outline.
- Inspect full-size PNGs for the cover, section openers, person/photo-led slides, real-map slides, dense diagrams/SVGs/timelines, activity/quiz slides, and final slide.
- Every custom SVG/CSS/HTML diagram, flow, timeline, network, or triad must be included in full-size rendered QA. Add `data-fullsize-qa="true"` and `data-rendered-qa="true"` to the diagram container only after inspecting the full-size rendered PNG/PDF page. Missing attributes are a blocking source-level P0.
- When the user flags a page number or footer collision, export full-size PNGs for both the PDF page ordinal and any audience-facing slide label with the same number, then inspect both before scoring. Example: if the user says page 15 and the deck has a cover labeled 00, recheck PDF page 15 and the slide whose footer says `15 / N`.
- Treat any body/card/chart/source text that touches, overlaps, sits underneath, or visually competes with the footer, source note, or page number as `P0 footer collision`. The deck cannot be exported or delivered until the source layout is changed, the PDF/contact sheet is regenerated from that exact source, and the flagged page PNGs are rechecked.
- If the environment provides agent/subagent tools, always run a dedicated QA reviewer agent before delivery. Give it the contact sheet, selected full-size PNGs, and the checklist. The reviewer must return only P0 hard fails, P2 polish candidates, 100-point score, required fixes, and recheck pages.
- Give the QA reviewer the `qa_media_guard.py` output too. If the script reports unsafe media crop or inline real-map SVG, the reviewer must inspect those pages and keep the deck failed unless the source was changed or a verified `data-crop-ok="true"` crop with `data-rendered-qa="true"` or `data-fullsize-qa="true"` full-size rendered proof exists.
- If agent tooling is unavailable, record `qa-agent: unavailable` and run the same checklist manually.
- QA is an action loop. If rendered text is too large, clipped, outside a box, badly wrapped, or visually broken, immediately edit the source deck and rerender; do not stop at diagnosis.
- Treat wrong final PDF page order, duplicated/missing pages, stale contact sheets, and HTML/PDF mismatches as P0 export failures. Fix the export path and rerender before delivery.
- Treat any P0, export/aspect-ratio failure, or score below 90/100 as a blocking failure. Fix source HTML/CSS/assets, rerender PDF/contact sheet, and run the QA checklist again.
- Use a scored QA loop for every revision: score the rendered deck on the 100-point rubric, record `qa-score`, `p0-count`, `p2-count`, `fixed-pages`, and `recheck-pages` in build notes, then run `qa_score_gate.py`. Iterate until `p0-count = 0`, `qa-score >= 90`, and `qa_score_gate: pass`. If a user flags specific pages, those pages must appear in `recheck-pages` after the fix.
- Every QA loop must include regression inspection: compare the new contact sheet against the prior accepted version or against the intended outline, then record `regression-check: pass/fail` and any newly affected pages. A failed regression check is blocking even if the originally flagged pages look fixed.
- After internal QA passes, report the QA result and provide the HTML/PDF candidate for user review before entering revision work. Treat user-requested changes as a new version and rerun the QA loop before reporting again. Before final delivery, run `qa_final_review_gate.py`; if it fails, continue the review/update/recheck loop rather than reporting final.
- Do not export PPTX by default. Export PPTX only when the user explicitly asks for PPTX or the agreed output format requires it, and only after PDF/contact sheet QA passes with no P0 and score >= 90/100.

### Image fit rubric and generation trigger
For each slide that needs an image, search web/official/public sources first and score candidate images before use.

Score each candidate from 0-10:

- Content match, 0-3: directly shows the subject, place, species, behavior, data context, or response method named on the slide.
- Evidence value, 0-2: comes from an official, primary, educational, or clearly attributable source.
- Visual clarity, 0-2: readable at slide size, not dark, blurred, over-cropped, cluttered, or watermarked. If a face, head, product, landmark, food, or map detail is important to the slide, it must remain visible in the rendered PDF.
- Layout fit, 0-2: works in the slide crop/aspect ratio without hiding the important subject. A candidate that only works by cutting off the face/head or core object scores 0 for layout fit.
- Tone fit, 0-1: supports the deck mood and does not look like generic stock filler.

Use the image when score >= 7. If the best available web image scores 4-6, prefer a simple self-made diagram/chart/SVG when the slide is explanatory. If the best available web image scores <= 5 and the slide needs a concrete visual, trigger image generation with a short note in the working log: `image-generation-trigger: best web score X/10, reason ...`.

Generated images must be clearly illustrative, not presented as documentary evidence. For factual slides, keep sourced data/text separate from generated artwork and add an asset note in `assets/CREDITS.txt`.

### Image crop and real-map overlay hard gate
Treat image subject integrity as a hard QA gate. A visually stylish crop still fails if it removes the information the slide depends on.

- For people, athletes, interviewees, founders, artists, and profile photos, the face must be intact unless the slide is explicitly about an abstract body/detail crop. Do not cut off the top of the head, eyes, mouth, chin, hands holding the key object, jersey/name cues, or the identity-bearing part of the image.
- For products, food, logos, UI screenshots, buildings, landmarks, and artifacts, the named subject must remain whole enough to recognize. If a short fixed-height `object-fit: cover` frame cuts the subject, switch to `object-fit: contain`, change `object-position`, use a wider/taller frame, choose another image, or redesign the slide.
- Hero photos may use `cover` only after rendered QA confirms the important subject is not clipped. Thumbnails, cards, portraits, documentary photos, and evidence-like visuals default to `contain` or a verified focal crop. A focal-crop override must use `data-crop-ok="true"` plus `data-rendered-qa="true"` or `data-fullsize-qa="true"` after inspecting the rendered full-size PDF/PNG.
- Real geography maps are not freehand illustration tasks. For country, city, route, travel, region, language, food, history, or geopolitics slides, first fetch an official/public/licensed map or screenshot map base, cite it in `assets/CREDITS.txt`, then draw pins, route lines, translucent regions, labels, and callouts as an overlay on top.
- Do not hand-draw country outlines, canton/state borders, coastlines, transit routes, or real geographic shapes unless the slide clearly says it is a conceptual schematic and geographic accuracy is not part of the claim.
- If no acceptable map base can be used, replace the map with a non-geographic diagram/table, ask for a source map, or state the limitation. Do not invent a map outline.
- During QA, inspect all person-photo, product-photo, landmark, screenshot, and map slides at full size. Cropped faces/subjects, inaccurate homemade maps, misplaced pins, or unreadable map labels are P0 failures until fixed.

### Visual material requirement guardrail
Treat concrete visual material as mandatory for major slides, not optional decoration.

- Do not ship text-only major slides. Cover, chapter opener, key concept, evidence/example, comparison, process/timeline, product, place, and closing slides must each have a planned visual asset.
- Acceptable visual assets: user/original image, official/public photo, screenshot, chart/data visualization, SVG diagram/timeline/map/card grid, or approved AI-generated illustration.
- Before building, write a `visual plan` for every slide in the outline: asset type, source/generation path, crop/layout role, subject/focal-point safety, map-base source if relevant, and fallback.
- If no suitable external image exists, build a self-made SVG/chart/diagram first for explanatory content. Use AI generation for conceptual or atmospheric scenes only after placeholder + cost + user approval.
- During QA, reject any deck with two consecutive content slides that are text-only, or any slide whose title promises a visual but the body does not show one.

## Overview
사용자와 **같이 만드는** reveal.js HTML 슬라이드 덱. 고정 브랜드 템플릿("메모장 + 밝은" 크림 종이 테마)을 채워서 `.html`로 배포하고 기본 산출물은 `.pdf`로 추출한다. 이미지 기반 `.pptx`는 사용자가 명시 요청한 경우에만 옵션으로 생성한다. 필요할 때만 덱 내부 콘텐츠 이미지를 생성한다.

핵심 흐름은 **.html 덱을 대화로 구성**하는 것이고, 이미지 생성(gpt-image-2)은 보조 기능이다.

## 시작 프로토콜: Grill Me + 자료 인테이크
사용자가 주제, 아이디어, 발표 목적만 던지거나 "grill me", "캐물어줘", "질문부터 해줘"처럼 말하면 **바로 슬라이드 개요나 HTML을 만들지 않는다**. 먼저 `taste-profile.md`를 읽고 [reference/intake.md](reference/intake.md)의 Grill Me 모드로 들어간다.

시작 게이트:

1. **참고자료 여부 확인** — "추가로 참고할 PPT/PDF/문서/스크린샷/URL/데이터가 있나요?"를 먼저 묻는다. 여기서 reference/참고자료는 사용자가 주는 원자료를 뜻한다. 없으면 바로 인터뷰로 들어간다.
2. **목적별 분류** — 받은 자료를 `content`, `evidence`, `style`, `visual-asset`, `constraint` 중 하나 이상으로 분류하고, 어떤 용도로 쓸지 사용자에게 확인한다.
3. **한 번에 하나씩 인터뷰** — 목적, 기획 방향, 타겟 독자/청중, 발표 상황, 한줄메시지, 근거/데이터, CTA를 순서대로 좁힌다.
4. **비주얼 방향 확인** — 의도와 청중이 정리된 뒤 분위기/톤, 색상 팔레트, 사진·스크린샷·AI 이미지 추가 레벨을 묻는다.
5. **인테이크 노트 확정** — 자료 맵과 필수 4항목, 발표 상황, 분위기/이미지 레벨, 미해결 질문을 짧게 정리한 뒤에야 리서치/기획/빌드로 넘어간다.

사용자가 참고자료가 없다고 하면 그 사실을 인테이크 노트에 남기고 진행한다. 참고자료가 있을 것 같지만 아직 안 줬다면 `input/`에 넣거나 URL/파일명을 알려 달라고 요청한다. Color Hunt 같은 컬러 팔레트 사이트는 참고자료가 아니라 **palette source**로 별도 취급한다.

### 웹에서 찾아서 PT 만들기 모드
사용자가 "웹에서 찾아서", "리서치해서", "요즘 자료로", "최신 근거로"처럼 말하면 [reference/research.md](reference/research.md)를 먼저 따른다. 목적·청중·한줄메시지는 짧게 확인하되, 리서치가 필요한 사실/수치/사례를 명시적으로 소스 맵에 기록한다. 슬라이드에는 출처를 과하게 노출하지 말고, 작업 노트 또는 `assets/CREDITS.txt`에 URL·접속일·사용 사실을 남긴다. 최신성이 중요한 주장은 반드시 웹으로 확인하고, 근거가 약하면 슬라이드 문장을 낮은 확신 표현으로 바꾸거나 제외한다.

## 파일 구조
스킬이 동작하는 작업 공간 레이아웃(프로젝트 루트 기준):

```
input/                          ← 사용자 참고자료 드롭 (이미지·PDF·문서)
output/NN_<slug>_<YYYYMMDD>/    ← 덱마다 폴더 (순번_주제_날짜)
  ├── deck.html · deck.pdf · deck_contact.png
  └── assets/                   ← 이 덱이 쓰는 이미지 전부 (생성+임베드)
archive/                        ← 작업 스크래치 격리
```

- 새 덱은 `python .codex/skills/pt-maker/scripts/new_deck.py "<slug>"` 로 폴더를 만든다(순번=기존 최대+1, 날짜=오늘 자동). 출력된 경로의 `deck.html`을 편집.
- 덱 산출물은 **항상 그 덱 폴더 안**에 둔다. 루트에 흩뿌리지 않는다.
- 덱 내부 이미지는 전부 상대경로 `assets/...` (폴더째 옮겨도 안 깨짐).

## 입력 (Codex가 이해하는 무엇이든)
손글씨·스케치·이미지 같은 참고자료가 있을 법하면 **먼저 "인풋을 넣어 달라"고 요청**한다. 받은 뒤에는 **그걸 어떻게 쓸지를 사용자에게 물어본 다음** 진행한다 — 단정하고 바로 쓰지 않는다.

- **자유 텍스트 토론**: 주제만 주면 같이 구조를 잡아간다.
- **이미지/스케치/필기**: 첨부 이미지나 `input/` 파일을 Codex가 직접 읽는다. 받은 이미지를 **어떻게 쓸지 반드시 확인**한다:
  - **(a) 내용으로만 활용** — 손글씨·메모에 적힌 데이터·아이디어를 읽어 **정자체 슬라이드로 재구성**(깔끔하게 타이핑).
  - **(b) 원본 그대로 임베드** — 손그림 다이어그램·스케치 자체를 **폴라로이드 프레임에** 리사이즈·재생성 없이 그대로 넣음(§2).
  손그림 자체에 의미가 있으면 보통 (b), 텍스트·데이터 메모면 (a)지만 **추측하지 말고 물어본다**. 참고자료는 `input/`에 두면 거기서 읽는다.
- **웹 URL**: 사용 가능한 브라우저/웹 도구로 페이지를 가져와 자료로 활용한다.
- **문서/데이터**: 요약·재구성해서 슬라이드로.

## Workflow
덱을 만들기 전에 **`taste-profile.md`를 읽어** 톤·구조·브랜드 프리셋 기본값을 적용한다(없으면 빈 템플릿 생성). 슬라이드 품질 기준은 [reference/presentation-craft.md](reference/presentation-craft.md). 단계 순서는 상황에 맞게 바뀔 수 있다(예: 참고자료를 먼저 받으면 4가 앞당겨짐).

1. **소스 확보 (Grill Me + 자료 인테이크)** → [reference/intake.md](reference/intake.md)를 따른다. 먼저 참고자료 여부를 확인하고, 없으면 바로 인터뷰로 들어간다. 질문은 **한 번에 하나씩** 하며 목적, 타겟 독자/청중, 한줄메시지, 발표 상황, 근거/데이터, CTA, 기획 방향을 좁힌 뒤 분위기/톤, 색상 팔레트, 사진·스크린샷·AI 이미지 추가 레벨을 확인한다. 받은 자료는 목적별로 분류하고, 손글씨·스케치·이미지는 활용 방식((a) 내용 재구성 vs (b) 원본 임베드)을 물어본 뒤 진행한다. → 산출물: 인테이크 노트 + 자료 맵 + 비주얼 방향.
2. **웹 리서치** → [reference/research.md](reference/research.md). 근거가 빈 항목·최신 데이터를 웹으로 보강하고, 사용자가 웹에서 찾아서 만들라고 한 경우에는 이 단계를 생략하지 않는다. 리서치 결과는 `claim / source / date / slide-use` 형태로 소스 맵에 남긴다.
3. **기획** → 스토리 짜기 전에 먼저 [reference/product-judgment.md](reference/product-judgment.md)로 **제품 판단 블록**(타겟 순간·king action·AI 특이점·신뢰 장치·반복 루프·뺄 것)을 한 번 잡는다 — 제품/AI 기능을 파는 덱이면 필수, 단순 정보 전달 덱이면 생략 가능. 그 위에서 **타겟 청중을 확정**하고 그들에게 꽂히는 한줄메시지·스토리라인·Chapter 구조를 잡는다. 슬라이드 개요(슬라이드별 제목+요점+`visual plan`)를 사용자와 합의. `visual plan`에는 사진/스샷/차트/SVG/생성 후보, 출처·경로, 레이아웃 역할, subject/focal-point 안전성, 지도라면 map-base 출처, fallback을 적는다. **One idea per slide** — 제목에 "그리고/및"이 들어가면 두 장으로.
4. **구성/빌드** → `new_deck.py "<slug>"`로 덱 폴더(`output/NN_slug_date/`)를 만들고 출력된 `deck.html`의 `<section>`을 복제·수정. 사용자가 참고자료 덱(PPT/PDF)을 주면 [reference/reference-ingest.md](reference/reference-ingest.md)로 콘텐츠+스타일을 흡수(스타일은 확인 후 취향 반영). 주요 슬라이드는 텍스트만으로 빌드하지 않고, `visual plan`의 시각자료 슬롯을 실제 사진·스샷·차트·SVG·승인된 생성 이미지 중 하나로 채운다. **빌드 내내 craft.md의 [★ 심미성 체크리스트](reference/presentation-craft.md)(가독성·통일성·균형·여백·시각자료·다양성·디테일)를 기준으로 만든다.** → 검증: 슬라이드 수 = 개요.
5. **이미지/시각자료** → 모든 주요 슬라이드는 시각자료 슬롯을 가진다. 웹·공식·공개 자료에서 먼저 찾고(스샷/실물 우선), 데이터·흐름·비교는 인라인 SVG/차트/다이어그램을 우선한다. 생성이 필요하면 **묻지 말고 바로 생성하지 않는다**: 먼저 해당 슬라이드에 `🖼 AI로 그릴 그림입니다` 플레이스홀더로 1차 초안을 만들고, **예상 장수·비용($0.03/장)을 알려 사용자에게 생성 여부를 확인**한다. 승인받은 뒤에만 `gen_image.py`로 생성(presentation-craft.md §3 기준·현재 활성 팔레트 반영)해 플레이스홀더를 교체. 사용자 원본 이미지는 생성 말고 그대로 임베드. 생성·임베드 이미지는 모두 그 덱의 `assets/`에 둔다(사용자 원본은 `input/`→`assets/` 복사).
6. **필수 QA iteration + 사용자 검수 단계** → PDF/contact sheet를 렌더링하고 [reference/general-pt-making-checklist.md](reference/general-pt-making-checklist.md)와 [alignment-eval-rubric.md](reference/alignment-eval-rubric.md)로 채점한다. agent/subagent 도구가 있으면 **반드시 dedicated QA reviewer agent**를 실행해 P0/P2/100점 점수/수정 목록을 받는다(없으면 `qa-agent: unavailable` 기록 후 수동으로 동일 체크). P0가 하나라도 있거나 점수 < 90이면 source HTML/CSS/assets를 수정 → PDF/contact sheet 재렌더 → agent/manual QA를 다시 반복한다. 통과하면 먼저 QA 결과(score, P0=0, 남은 P2)와 HTML/PDF 후보를 사용자에게 보고하고, 그 다음 수정 요청 단계로 들어간다. 사용자가 수정 요청을 주면 새 버전으로 처리해 수정 → 재렌더 → QA 반복 → 재보고한다. **변경마다 덱 버전을 올린다.** 최종 마감 시 이번 덱에서 배운 취향을 **diff로 제안**하고 사용자가 확인한 것만 `taste-profile.md`에 기록(version +1). 조용히 바꾸지 않는다. 생성 이미지 개수·비용($0.03/장)도 요약.

## 취향 학습 루프
`taste-profile.md`가 취향 정본(구조·스토리 / 비주얼·브랜드 프리셋 / 어투·톤 / 안티-취향, 각 항목 `[conf:]`). 3지점에서 동작:
- **읽기**(시작): Phase 1 전에 읽어 기본값 적용. 없으면 빈 템플릿 생성.
- **흡수**(사용자 참고자료): 스타일을 추출해 "프로필에 추가할까요?" 제안 → 확인 시 반영.
- **갱신**(마감): 피드백을 diff로 제안 → **확인된 것만** 기록, version +1. silent drift 금지.

## 1. 덱 빌드
`assets/template.html`이 고정 브랜드 템플릿이다. 슬라이드 종류(클래스): `s-title` · `s-section` · `s-bullets` · `s-image` · `s-statement` · `s-end`. 블록을 복제해 내용만 채운다. `kicker`의 번호(`00 / ...`)를 순서대로 갱신. **kicker는 `.s-head`로 감싸 좌상단에 절대배치** — 콘텐츠 정렬(center/statement)과 무관하게 **번호가 모든 슬라이드 같은 자리**에 오도록 한다(마무리 s-end도 포함해 통일).

브랜드 토큰을 임의로 바꾸지 말 것 — 일관성이 핵심. 단, 사용자가 색상 변경/새 무드/팔레트 재구성을 요청했거나 기존 덱과 다른 톤이 명확히 필요하면 아래 Color Hunt 규칙으로 토큰을 재구성한다.

| 토큰 | 값 | 용도 |
|---|---|---|
| `--paper` | `#FAF3DE` | 종이 배경 |
| `--card` | `#FFFCF1` | 노트 카드 |
| `--ink` | `#20174A` | 본문 잉크 |
| `--accent` | `#C73463` | 제목·강조 (로즈) |
| `--cream-line` | `#E7DCB6` | 테두리 |
| 폰트 | Pretendard / JetBrains Mono / Nanum Pen Script | 본문 / 라벨 / 손글씨 |

### 컬러 팔레트 구성 (Color Hunt)
Color Hunt(`https://colorhunt.co/`)는 **reference 자료가 아니라 palette source**다. PPT/PDF/문서/스크린샷처럼 내용을 읽는 원자료로 취급하지 않는다. 색상 변경이나 새 무드가 필요할 때만 팔레트 영감과 후보 색을 찾는 용도로 쓴다.

- 사용자가 "색 바꿔줘", "다른 톤", "디자인 컬러 팔레트 참고"처럼 요청하면 Color Hunt에서 직접 팔레트를 찾고 덱 토큰을 재구성한다.
- 무드가 있으면 Color Hunt 태그(`Pastel`, `Vintage`, `Retro`, `Neon`, `Gold`, `Light`, `Dark`, `Warm`, `Cold`, `Nature`, `Earth`, `Night`, `Sky`, `Sea` 등)로 좁힌다. 무드가 없으면 발표 주제와 청중에 맞춰 2~3개 후보를 고른다.
- 후보 팔레트는 그대로 베끼지 말고 발표용 토큰으로 매핑한다: `paper/background`, `card/surface`, `ink/text`, `accent`, `line/border`, `muted`.
- 선택 기준은 가독성이 우선이다. `ink`는 배경과 충분히 대비되어야 하고, accent는 강조 1~2개에만 쓴다. 예쁜 팔레트라도 본문 대비가 약하면 버린다.
- 한 덱이 한 계열 색만 반복되는 one-note 팔레트가 되지 않게 한다. 사용자가 원하지 않는 한 과한 보라/남보라 그라데이션, 베이지/크림 일변도, 어두운 남색/슬레이트 일변도, 브라운/오렌지 일변도는 피한다.
- 최종 적용 전 작업 노트에 `palette source: Color Hunt`, 후보 hex, 선택 이유, 토큰 매핑을 짧게 남긴다. `taste-profile.md`에는 사용자가 확인한 경우에만 반영한다.

## 2. 사용자 이미지 임베드 (원본 보존)
**(b) 원본 임베드로 확인된 경우에만**(§입력에서 활용 방식을 물어본 뒤). `s-image`의 `<figure class="polaroid">` 안 `<img src="...">`에 원본 경로 또는 data URI를 넣는다. **리사이즈·재생성 금지**, 원본 그대로. 여러 장이면 `s-image` 슬라이드를 복제.

## 2.5 웹/스샷 쇼케이스 & 검증
- **결과물 스샷**: 배포된 웹은 Codex 브라우저 도구로 열고 로드 완료 후 스크린샷을 찍는다. SPA가 networkidle 타임아웃이면 load 완료 기준으로 확인한다.
- **세로로 긴 스샷**(풀페이지·상세페이지)은 폴라로이드 대신 **썸네일 카드** — `.thumb{height:~96px;overflow:hidden} img{object-fit:cover;object-position:top}`. 여러 프로젝트는 4열 카드 그리드로 쇼케이스.
- **슬라이드별 검증**: 브라우저에서 `Reveal.configure({transition:'none'}); Reveal.slide(N)`를 실행한 뒤 스크린샷을 찍는다. (fade 전환 중 캡처하면 이전 슬라이드가 겹쳐 보이는 잔상이 생김 → 전환을 끄면 깨끗.)
- **버전**: 표지/푸터에 `vX.Y`를 표기하고 변경마다 올린다.

## 3. 내부 이미지 생성 (보조)
```bash
python scripts/gen_image.py "프롬프트" output/NN_slug_date/assets/img1.png --size 1536x1024
```
- 키는 `.env`에서 읽음 — **프로젝트 루트 → 상위, 그다음 이 스킬 폴더 → 상위** 순으로 탐색하므로, 스킬 폴더 안에 `.env`를 두면 폴더만 떼어가도 동작한다(`env.example`을 `.env`로 복사 후 키 입력).
- **`.env`(키)가 없으면 이미지 생성을 건너뛴다**(`SKIP` 메시지 후 종료, 네트워크 호출 없음). 이 경우 덱은 `AI로 그릴 그림입니다` 플레이스홀더로 계속 진행한다.
- 모델 기본 `gpt-image-2-vip`(16:9 치수 제어). 빠른 생성·텍스트 중심이면 `.env`의 `OPENAI_IMAGE_MODEL=gpt-image-2-all`.
- 16:9 슬라이드 배경은 `--size 2048x1152` 또는 `1792x1024`.
- 자세한 API는 `reference/apiyi.md`.

## 4. 내보내기
```bash
# 0) 작업본 deck.html → 주제+버전 이름으로 확정(rename). 같은 폴더라 assets 상대경로 안 깨짐.
#    (PowerShell)  Rename-Item output/NN_slug_date/deck.html "<주제>v<N>.html"
mv output/NN_slug_date/deck.html "output/NN_slug_date/<주제>v<N>.html"
# 1) 그 html에서 PDF 생성 — deck.pdf 말고 같은 주제+버전 이름으로.
python scripts/qa_media_guard.py "output/NN_slug_date/<주제>v<N>.html"                         # media crop/map P0 guard
python scripts/export_pdf.py "output/NN_slug_date/<주제>v<N>.html" "output/NN_slug_date/<주제>v<N>.pdf"        # 기본: print-pdf
python scripts/export_pdf_shots.py "output/NN_slug_date/<주제>v<N>.html" "output/NN_slug_date/<주제>v<N>.pdf"   # 화면과 1:1(스샷 합치기)
python scripts/verify_pdf.py "output/NN_slug_date/<주제>v<N>.pdf"                                              # bleed 검증(콘택트 시트) → Read로 확인
# 2) 렌더 QA 후 점수 게이트 — qa_ledger.json 작성 후 통과해야 pass/90점 이상 보고 가능.
python scripts/qa_score_gate.py "output/NN_slug_date/<주제>v<N>.html" "output/NN_slug_date/qa_ledger.json"
# 3) 사용자 최종 리뷰 후 최종 게이트. user_review_ledger.json 작성 후 통과해야 final delivery 가능.
python scripts/qa_final_review_gate.py "output/NN_slug_date/<주제>v<N>.html" "output/NN_slug_date/qa_ledger.json" "output/NN_slug_date/user_review_ledger.json"

# 선택) 사용자가 PPTX를 명시 요청한 경우에만, PDF/contact sheet QA 통과 후 생성.
python scripts/export_pptx.py "output/NN_slug_date/<주제>v<N>.html" "output/NN_slug_date/<주제>v<N>.pptx"      # 정렬 보존용 이미지 기반 PPTX
```
- **파일명** — 산출물(`.html`·`.pdf`)은 `deck.*`가 아니라 **주제+버전**(`<주제>v<N>.html`/`.pdf`, 공백 없이)으로 저장한다. **`deck.html`을 그대로 남기지 않는다** — 작업 중엔 `deck.html`을 편집하고, **마감 때 위 0)단계로 rename**해 `.html`·`.pdf`가 같은 이름이 되게 한다. 표지 푸터의 `vN` 표기와 파일명 버전을 일치시킨다.
- **.html과 .pdf 줄간격이 다를 때** — reveal `?print-pdf`(pdf.css + Chromium 인쇄 엔진 + 폰트 로드 타이밍)는 화면(paper.css)보다 줄간격이 좁게 나올 수 있다. 화면 그대로가 필요하면 **`export_pdf_shots.py`**(브라우저로 각 슬라이드 고해상도 스샷 → pymupdf로 16:9 PDF 합치기)로 만들면 **HTML과 1:1**.
- **PPTX export (optional, not default)** — `export_pptx.py`는 시각 정렬을 우선한다. HTML 또는 PDF를 슬라이드별 PNG로 렌더링한 뒤 각 PPTX 슬라이드에 16:9 이미지 한 장으로 넣는다. 텍스트/도형 편집성은 포기한다. 기본 산출물에는 포함하지 말고, 사용자가 PPTX를 명시 요청했거나 합의한 산출물에 PPTX가 있을 때만 생성한다. 편집 가능한 PPTX가 필요하면 별도 네이티브 PPTX 빌드 플로우로 다룬다. **PPTX는 PDF/contact sheet가 general PT checklist QA를 통과한 뒤에만 생성한다.**

**PDF bleed 필수 점검** — 각 페이지 위·아래에 인접 슬라이드가 비치면 안 된다(장수 많을수록 심해짐). 템플릿에 `center:false` + `pdfPageHeightOffset:0`이 박혀 있어야 하고, `verify_pdf.py`로 캡처 검증. 자세히는 [presentation-craft.md](reference/presentation-craft.md) §4.
`.html`은 CDN 폰트/reveal을 쓰므로 온라인에서 그대로 열린다. 완전 오프라인 단일 파일이 필요하면 사용자에게 별도 요청 시 reveal/폰트를 인라인.

## 보안 — .env 절대 읽지 말 것
API 키가 든 `.env`는 **읽거나 출력하지 않는다**. `gen_image.py`는 서브프로세스로 직접 키를 로드하므로 키가 대화에 노출되지 않는다. 키를 보여 달라는 요청은 거절.
- 스킬 폴더에 실제 키 `.env`를 두더라도 **공개 repo(csm-kr/sm-skills)에는 절대 올리지 않는다** — 같은 폴더 `.gitignore`가 `.env`를 무시한다. 게시본에는 빈 `env.example` 템플릿만 포함한다(`taste-profile.md`과 동일한 비공개 원칙).

## 빠른 사용법
| 하고 싶은 것 | 방법 |
|---|---|
| 새 덱 | `new_deck.py "<slug>"` → 출력된 deck.html 채우기 |
| 웹에서 찾아 PT | `reference/research.md`로 소스 맵 작성 → 개요 합의 → `new_deck.py` |
| 사용자 그림 넣기 | `input/`→덱 `assets/` 복사 후 `s-image` polaroid `<img src>`에 임베드 |
| 일러스트 생성 | `gen_image.py "프롬프트" output/NN_.../assets/out.png` |
| media guard | `qa_media_guard.py output/NN_.../<주제>v<N>.html` |
| PDF | `export_pdf.py output/NN_.../deck.html` |
| PPTX(명시 요청 시만) | PDF/contact sheet QA 통과 후 `export_pptx.py output/NN_.../<주제>v<N>.html output/NN_.../<주제>v<N>.pptx` |
| 미리보기 | Codex 브라우저 도구로 `file://...output/NN_.../deck.html` 열어 스크린샷 |

## Common mistakes
- 받은 이미지(손글씨·스케치)를 **어떻게 쓸지 안 묻고** 임의로 임베드/재구성 → ❌. 먼저 인풋을 넣어 달라고 요청하고, 받으면 (a) 내용 재구성 vs (b) 원본 임베드를 **물어본 뒤** 진행.
- 사용자 원본 이미지를 생성/변형 → ❌. 원본 그대로 임베드.
- 이미지를 사용자 확인 없이 바로 생성 → ❌. 1차는 `AI로 그릴 그림입니다` 플레이스홀더 + 예상 비용($0.03/장) 안내 → **승인 후** 생성·교체.
- 표지·챕터 오프너·핵심 개념·사례·마감 슬라이드가 텍스트만 있음 → ❌. 각 주요 슬라이드에 사진/스샷/차트/SVG/승인된 AI 일러스트 중 하나를 배치하고, 개요 단계부터 `visual plan`을 적는다.
- 콘텐츠 슬라이드가 두 장 이상 연속 텍스트만 있음 → ❌. 설명형이면 SVG/차트/타임라인으로, 무드형이면 승인받은 생성 이미지나 실사진으로 보강한다.
- 모든 콘텐츠 슬라이드가 같은 레이아웃(불릿 좌·비주얼 우) → ❌ 단조롭다. 한 덱에서 카드 그리드·미러(비주얼 좌)·허브·가로 타임라인·중앙 statement·이미지 주연 등 3~4종 이상 섞는다(craft.md §2-11).
- 줄간격이 좁아 빽빽 / 한글 라벨(SVG·kicker)을 모노폰트로 / 정확한 연도·숫자·고유명사를 손글씨 폰트(Nanum Pen)로 → ❌ 가독성. 본문 `line-height ≥ 1.5`, 한글은 Pretendard, 손글씨는 가벼운 메모·감탄에만(사실 정보는 정자체).
- 본문·불릿을 무조건 32px 이상으로 키워 둔탁하게 만들기 → ❌. 일반 HTML 덱은 Pretendard 기준 본문 28-30px, hard floor 26px가 기본. 라벨은 20-22px, 출처/fine-print는 15-16px까지 허용하되, 작아 보이면 문장을 줄이거나 슬라이드를 나눈다. 큰 발표장/프로젝터용이면 32px로 올린다.
- 카드 썸네일/인물/선수/제품/음식 사진을 짧은 고정높이 `object-fit:cover`로 → ❌ 피사체 잘림. `aspect-ratio:3/2` 박스 + `object-fit:contain`(흰 배경) 또는 검증된 focal crop으로 얼굴·머리·손·로고·핵심 사물을 보존한다. 큰 히어로도 중요한 얼굴/피사체가 잘리면 실패다.
- 실제 국가/도시/여행/언어권/음식권/역사 지도에서 손그림 SVG 개략도를 지도로 제시 → ❌. 웹/공식/공개 라이선스 지도 베이스를 가져오고, 그 위에 핀·루트·영역·라벨을 overlay로 그린다. 직접 그린 지도는 "개념 스케치"라고 명시된 경우에만 허용한다.
- 원형 번호·아이콘 뱃지가 옆 라벨보다 커서 아랫줄 침범 → ❌. 라벨 크기에 맞춰 작게(≈1.2~1.3em)·`margin-bottom` 확보, 빌드 후 스샷으로 수직 겹침 점검.
- PDF를 `deck.pdf`로 저장 → ❌. 주제 이름(`"<주제>.pdf"`)으로.
- 산출 `.html`을 `deck.html`로 그대로 남기기 → ❌. 마감 때 `deck.html`을 `<주제>v<N>.html`로 rename(=PDF와 같은 이름). 작업 중 편집은 `deck.html`로 OK.
- `.pdf` 줄간격이 `.html`보다 좁다 → reveal print-pdf의 한계. `export_pdf_shots.py`로 HTML 스샷을 합쳐 1:1로 만든다.
- PPTX를 기본 산출물로 자동 생성하거나 편집 가능한 도형/텍스트로 바로 만들려고 함 → ❌. 현재 PPTX export는 정렬 보존용 이미지 기반 옵션이다. 사용자가 명시 요청한 경우에만 PDF QA 통과 후 생성한다. 편집 가능성이 필요하면 별도 네이티브 PPTX 빌드로 명시하고 QA 기준을 따로 잡는다.
- 최종 점수나 `pt-qa-result: pass`를 말하면서 `qa_score_gate.py`를 통과하지 않음 → ❌. 렌더 QA ledger와 score gate pass 없이는 90점 이상/통과 보고 금지.
- 최종 납품이라고 말하면서 사용자 최종 리뷰와 `qa_final_review_gate.py`를 통과하지 않음 → ❌. score gate 통과본은 후보일 뿐이고, final은 사용자 리뷰 ledger와 final review gate pass 이후에만 가능.
- SVG/CSS 도식 라벨이 도형 밖으로 넘침/도형과 겹쳐 안 읽힘 → ❌. 라벨은 도형 **중앙**(타원이면 `cx,cy`에 `text-anchor:middle`)에 넣거나, 도형과 **충분히 띄운다**. 선/화살표는 대상 중심 또는 경계에 명확히 닿아야 하고, 끊긴 선·떠 있는 선·텍스트를 가로지르는 선은 P0. 도식 컨테이너에는 full-size 렌더 검수 후에만 `data-fullsize-qa="true"`와 `data-rendered-qa="true"`를 붙인다.
- kicker 번호가 슬라이드마다 다른 위치(가운데/좌측 등)에 떠 통일성이 없음 → ❌. kicker를 `.s-head`(absolute 좌상단 고정)로 감싸 **모든 슬라이드 같은 자리**에. (템플릿에 반영됨)
- 브랜드 색·폰트 변경 → ❌. 토큰 고정.
- `.env`를 cat/Read로 열기 → ❌. 그럴 필요도 없고 키가 대화에 노출될 수 있음.
- vip 모델에 `quality` 전송 → ❌. official 전용.
- deck.html을 작업공간 밖에 두고 브라우저 호출 → 열리지 않을 수 있음.
- 세로로 긴 스샷을 폴라로이드(가로)에 → 빈 공간. `object-fit:cover` 썸네일 카드로.
- fade 전환 중 스샷 → 이전 슬라이드 겹침. `transition:'none'` 후 캡처.
- 한 슬라이드에 여러 주장(제목에 "그리고") → 두 장으로. One idea per slide.
- 제목이 시각물(곡선·그래프·그림)을 약속했는데 본문에 안 그림 → ❌. 약속한 비주얼은 실제로 그린다(추상 막대·플레이스홀더 금지). statement 슬라이드는 미니 비주얼로 여백을 채움. 자세히는 [presentation-craft.md](reference/presentation-craft.md) §2-9·§4.
- PDF 각 페이지에 인접 슬라이드가 비침/잘림 → ❌. `Reveal.initialize`에 `center:false` + `pdfPageHeightOffset:0` 필수, `verify_pdf.py`로 캡처 검증. 장수 늘리면 누적되어 심해지니 매번 재검증.
- 인테이크에서 참고자료 여부를 확인하지 않거나, 질문을 여러 개 한꺼번에 던지거나, 필수 4항목(메시지·청중·근거·CTA)과 발표 상황·분위기·이미지 레벨을 안 채우고 슬라이드부터 만들기 → ❌. intake.md 순서대로 먼저.
- 취향을 사용자 확인 없이 조용히 taste-profile에 기록 → ❌. 항상 diff 제안 후 확인.
- 사용자 최종 리뷰에서 나온 취향 학습을 `taste-profile.md`/`dark-taste-profile.md`에 반영할지 묻지 않거나, 반영/미반영 결정을 `user_review_ledger.json`에 남기지 않음 → ❌.
- 덱 산출물(html·pdf·이미지)을 루트나 공용 `out/`에 흩뿌리기 → ❌. `output/NN_slug_date/`(이미지는 그 안 `assets/`)로.

## Cover Background QA

For cover and section-opening slides, follow `reference/cover-background-quality.md`.
Do not put pale paper texture, low-opacity overlays, or same-tone ivory panels behind the cover headline unless the rendered contact sheet confirms the cover is not washed out. If slide 1 looks faded, replace the background with a solid panel or darker field and rerender before delivery.

## Composition Balance QA

For slide layout balance, follow `reference/composition-balance.md`.
Do not push leftover content into shallow bottom cards. Keep the main message near the optical center, preserve clear distance from the footer, and reject any slide where Korean text visually touches card borders, icons, labels, or neighboring boxes. Record major object positions as normalized full-slide `xywh` ratios with a short intent note when placement carries psychological weight. If the lower third feels crowded, redraw the layout instead of shrinking text.
