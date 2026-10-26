# Baseer — Prompt Refinement Pre-Pack
**Prepared 2026-10-23 (Fri evening) · For Hussein's one-tap review before kickoff Mon Oct 26, 12:00 PM CT**

The four open questions in `backend/prompts.py` (v1.1-draft header), each with a researched recommended default.
Reply **approve** (all four as written), or **adjust N** with your change — no blank-page session needed.

---

## Q1 — Severity thresholds per site type — RECOMMENDED DEFAULT: adopt the matrix below

The "credible worst outcome" rubric stays. What changes: the same visual evidence calibrates differently by site context.
These mappings are grounded in the standards inspectors actually cite (see Q3).

| Site type | Evidence | Default severity | Why |
|---|---|---|---|
| Industrial / warehouse (flagship) | Pedestrian without hard hat in a shared forklift aisle | **HIGH** | Forklift–pedestrian strikes are a leading fatality category; head protection is 29 CFR 1910.135 / ANSI Z89.1 territory |
| Industrial / warehouse | Missing machine guarding | **HIGH** | Credible worst outcome = amputation/fatality |
| Industrial / warehouse | Unmarked pedestrian walkway where forklifts operate | **MEDIUM** | The condition that *enables* the HIGH outcome above |
| Industrial / warehouse | Blocked egress route | **MEDIUM** → **HIGH** if fully blocked | |
| Construction | Worker at height without hard hat / incomplete guardrails at an open edge | **HIGH** | 1926 Subpart M + 1926.100 |
| Construction | Ladder misuse at height (overreach, wrong angle, unsecured) | **HIGH** | Matches eval scene construction-02 |
| Construction | Dust-generating work without respiratory PPE | **MEDIUM** | |
| Farm | Chemical/pesticide spraying without respirator + gloves | **HIGH** | Exposure is the credible worst outcome, not the sprayer |
| Farm | Unguarded PTO shaft / worker under raised unsecured load | **HIGH** | |
| Farm | Heat exposure, no shade/water station | **MEDIUM** | |

**Downgrade rule (new):** if the evidence shows an *inactive* zone (no workers, no operating equipment, inspector notes confirm lockout/tagout), severity steps down one level. **Uncertainty never raises severity** — already in the prompt, unchanged.

*If approved: this table becomes a `SEVERITY_MATRIX` appendix in prompts.py (v1.2-draft).*

---

## Q2 — Arabic register: MSA vs inspector dialect — RECOMMENDED DEFAULT: keep as drafted, one chat-only line

- **Reports stay MSA** (already in the prompt). Ministry/contractor-facing documents need the professional register — a dialect report reads as informal in exactly the rooms Baseer must impress.
- **Inspector notes input already tolerates any dialect or MSA** (already in the prompt). No change.
- **New (chat only):** in evidence-chat mode, mirror the inspector's register lightly — if they write Egyptian/Saudi dialect, answer in clear MSA but keep their key terms as they wrote them (same rule the report prompt already uses for equipment terms, e.g. رافعة شوكية / forklift).

*If approved: one sentence added to CHAT_SYSTEM_PROMPT. Report schema untouched.*

---

## Q3 — Cite a named standard? — RECOMMENDED DEFAULT: keep "never invent", add opt-in presets

Rule 5 already says: cite a standard **only if the site context names one**. Keep that — inventing a regulation Baseer can't verify is exactly the fabrication the grounding rules exist to prevent.

What to add: **per-site-type standard presets**, chosen once at inspection setup (not invented per finding):

- **industrial:** OSHA 29 CFR 1910.135 (head protection) · ANSI/ISEA Z89.1 (industrial head protection) · OSHA 29 CFR 1910.178 (powered industrial trucks)
- **construction:** OSHA 29 CFR 1926.100 (head protection) · OSHA 29 CFR 1926 Subpart M (fall protection)
- **farm:** chemical product-label PPE requirements · ISO 45001 (OHS management)

When a preset is active, findings cite the specific clause (e.g. "1910.135(a)(1)"). When no preset is set, findings cite no standard — same as today.

**Integrity note:** these are US/international references. For a Saudi or Egyptian site, the authoritative local reference (e.g. Egypt Labour Law 12/2003 OSH provisions; Saudi OSH regulation) should be supplied by you per deployment — the prompt must never default a US standard onto a MENA site unasked.

*If approved: presets ship as an optional `site_standards` field in the inspection setup; rule 5 gains the clause-citation format.*

---

## Q4 — Segment-confidence threshold for auto-"uncertain" — RECOMMENDED DEFAULT: drop the threshold plan, use trigger signals instead

**Finding from tonight's code review:** the "tune the threshold on the eval set" plan rests on a premise the codebase itself contradicts. `meta_client.py → parse_sam_output` sets `confidence=0.0` with the comment *"hosted output carries no per-box score"*: SAM 3.1's hosted special-token format (`<|box;x1=..;y1=..;…|>`) carries **no per-box confidence field** to threshold on. (The 0.97/0.91/0.88/0.95 values in `_mock_segments` are synthetic mock shapes, not evidence.) Residual check for Day 0: confirm on the first live call whether any score token is present; `parse_sam_output` should capture it if it ever appears, never fabricate it.

**Recommended replacement — deterministic uncertainty triggers (no threshold to tune):**
1. **Partial visibility (geometric):** box clipped at the frame edge or abnormally small relative area → the occluded attribute is `uncertain` (e.g. eval scene factory-03: grinding sparks visible, face out of frame → eye protection = *unable to determine*, not a guess).
2. **Contradiction:** inspector note conflicts with segments → `uncertain` (already rule 9).
3. **Missing co-evidence:** the confirming segment for an attribute is absent → `uncertain` (eval scene factory-04: face shield appears raised, face mostly out of frame).
4. **LLM judgment backstop:** rule 9 stays — the model may still mark `determination: "uncertain"` when the evidence can't support a verdict.

**Acceptance test change:** the two uncertain-by-design eval scenes (factory-03-grinding-uncertain, factory-04-grinder-uncertain) become the pass/fail gate for the trigger logic, replacing the 0.50/0.60/0.70 sweep.

*If approved: Q4's open question is closed in the prompts.py header; the `determination` field wiring (Finding model, scheduled Oct 26–27) implements triggers 1–3 + the LLM backstop.*

---

## What happens on your reply

- **"approve"** → I cut prompts.py v1.2-draft with the matrix, the chat-register line, the preset field + clause format, and the closed Q4 (triggers documented, threshold plan removed). Nothing else in the pipeline changes; mock behavior unchanged.
- **"adjust N …"** → I apply your change to that item only and re-confirm the rest.
- Useful through kickoff **Mon Oct 26, 12:00 PM CT** — after that the v1.2 draft freezes for the live build.
