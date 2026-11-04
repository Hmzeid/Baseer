# YouTube upload kit — Baseer walkthrough

- **Video:** `docs/media/baseer-walkthrough.mp4` (1920×1080, 30 fps, **2:58**, H.264 + AAC, −15.4 LUFS, 84 MB)
  — the Meta submission cut, recorded live on Muse Spark 1.3. A 90 s demo-mode cut is kept as
  `baseer-walkthrough-90s.mp4` for social clips.
- **Thumbnail:** `docs/media/youtube-thumbnail.png` (1280×720 PNG, 0.8 MB; YouTube max 2 MB), built from the
  real hero finding
- **Category:** Science & Technology · **Language:** English (audio), Arabic + English (product)
- **Made for kids:** No · **Altered or synthetic content:** Yes, because the narration voice is AI-generated (Kokoro)

## Title (pick one, ≤ 70 characters shows in full)

1. `Baseer by Veebase: AI Safety Inspections in Arabic, from Photo to Closed Case`
2. `AI Safety Inspector for Construction & Factories in Arabic | Baseer by Veebase`
3. `بصير Baseer: Arabic AI Field Inspection Copilot (Veebase) | 3-Minute Walkthrough`

## Description

```
Baseer (بصير) by Veebase turns one site photo and an inspector's note into a full safety inspection report, in Arabic and English, then tracks every corrective action until a person approves the closure.

In 3 minutes, recorded live on Meta's Muse: a real site photo becomes three high-severity findings in about forty seconds; the evidence chat explains them and drafts the contractor notice; a case is verified with a genuine after-photo (and a wrong one is refused); a live camera on a warehouse floor raises real alerts; then deadlines, the audit trail, the Arabic PDF and the measured benchmark.

⏱ Chapters
0:00 The problem, and meet Baseer by Veebase
0:19 Safety overview
0:29 Running an inspection
0:39 How Baseer reads a site (SAM 3.1 + Muse)
0:52 A real report from Muse
1:06 Evidence chat, in English and Arabic
1:25 Cases, and a refused after-photo
1:36 Verified closure, approved by a person
1:51 Live camera alerts on a warehouse floor
2:09 Deadlines, history and the audit log
2:22 Arabic PDF, roles and mobile
2:39 Measured results

🔎 What Baseer does
• Photos, a short video or a live camera feed go in; a structured bilingual report comes out
• Every finding carries a severity, the exact evidence frame and a recommended corrective action
• Evidence chat answers only from the inspection's own findings and frames, and drafts contractor notices
• Every finding opens a case: assign → verify with an after-photo → a person approves the closure; the AI never closes a case by itself
• Deadlines by severity (high 1 day, medium 7, low 30), an overdue view, and an append-only audit log
• Server-rendered Arabic PDF reports, CSV exports, roles for safety supervisors, site managers and contractors

🧠 Under the hood
Meta's SAM 3.1 segments the scene and Muse reasons over the segments together with the inspector's notes; when segmentation is unavailable, Muse reads the frames directly. Every report records which path produced it.

ℹ️ About this recording
Recorded live: every finding, chat answer, verification and camera alert is real output from Meta's Muse Spark 1.3 (vision path) on openly licensed Pexels media. The before/after pair is two frames of the same Pexels clip. Earlier history items were back-dated a few days so the deadline views have something to show. Benchmark: fixed 24-scene set, prompt v1.3; misses are published in the project README.

🏆 Built by Veebase for the Meta Global AI Developer Hackathon (Startup track, "Build for Your World"), Oct 26 – Nov 4, 2026.

🎞 Credits
Site photos and footage from Pexels (Pexels License): Bulat843 (ladder), Gizem Gökce (welder), Usman AbdulrasheedGambo (warehouse forklift), Gustavo Fring (machine hall before/after), Guadalupe Aizaga (scaffold).
Narration voice: Kokoro (AI-generated). Music: generated locally with MusicGen.

—
بصير من Veebase: يحوّل صورة من الموقع وملاحظة المفتش إلى تقرير سلامة كامل بالعربية والإنجليزية، ويتابع كل إجراء تصحيحي حتى يعتمد إنسانٌ إغلاقه.

#Veebase #AISafety #ConstructionSafety
```

## Tags (≈ 480 characters)

```
Veebase, Baseer, بصير, AI safety inspection, construction safety, workplace safety, PPE detection, safety inspection app, field inspection, Arabic AI, AI in Arabic, Saudi construction, Middle East construction, factory safety, HSE software, corrective action tracking, safety audit, Meta AI, SAM 3.1, Muse, computer vision safety, AI hackathon, Meta hackathon, safety report generator
```

## Before you publish

- **Music licence:** the MusicGen model weights are licensed CC-BY-NC 4.0 (non-commercial).
  Keep this video unmonetized, or swap the bed for a commercially licensed track before monetizing.
- **Real outputs:** the 3-minute cut shows real Muse output. The 90 s cut is demo mode
  (synthetic findings); if you post that one, say so in its description.
- **Links:** `github.com/Hmzeid/Baseer` is private (404 when signed out). Add it only if you make it public.
