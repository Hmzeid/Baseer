# Baseer — Demo & Test Footage: Sources and Licenses

All clips below are stock footage from **Pexels**, downloaded 2026-10-21.
License for every clip: **Pexels License** — free to use for personal and
commercial purposes, no attribution required, modification allowed
(https://www.pexels.com/license/). These clips may be used for system
testing, the evaluation set, and the public demo video. All files are
MP4/H.264, 1920×1080 (the format SAM 3.1 accepts).

Content verification: clips marked ✔ were visually verified from an
extracted frame on 2026-10-21; the rest are technically verified (codec /
duration) and title-matched — full labeling happens when the evaluation
set is built (Oct 30–31).

## Factory / warehouse (flagship vertical)

| File | Source (Pexels) | Creator | Length | Intended use |
|---|---|---|---|---|
| footage/factory/forklift-workers-warehouse_32243654.mp4 | https://www.pexels.com/video/warehouse-operations-with-forklift-and-workers-32243654/ | Usman AbdulrasheedGambo | 12s | ✔ FLAGSHIP Observe footage + eval scene factory-01. Verified content: forklift (operator in red helmet) operating in a shared aisle; a pedestrian worker walking with NO helmet and NO vest; no marked walkway. The exact flagship narrative in one real clip. |
| footage/factory/forklift-driving_13422070.mp4 | https://www.pexels.com/video/man-driving-forklift-in-warehouse-13422070/ | Rodrigo Garcin | 39s | Forklift movement/path material; live-mode replay source; eval factory-02. |
| footage/factory/worker-helmet_5100046.mp4 | https://www.pexels.com/video/man-at-work-wearing-his-helmet-5100046/ | Gustavo Fring | 12s | ✔ PPE-positive test + Verify-beat visual. Verified: worker putting ON an orange hard hat in front of a forklift. Edge case: early frames show the helmet in hand, not worn — a strict system should flag "not yet worn", later frames must clear it. |
| footage/factory/worker-machinery_9737949.mp4 | https://www.pexels.com/video/man-using-machinery-in-factory-9737949/ | (Pexels user "K") | 18s | Machine-operation scene; machine-guarding eval material. |
| footage/factory/worker-textile-machine_31007049.mp4 | https://www.pexels.com/video/textile-factory-worker-operating-machine-31007049/ | EqualStock IN | 9s | Worker at a production machine; eval factory scene. |

## Construction / building

| File | Source (Pexels) | Creator | Length | Intended use |
|---|---|---|---|---|
| footage/construction/worker-scaffolding_32228166.mp4 | https://www.pexels.com/video/construction-worker-on-scaffolding-building-exterior-32228166/ | Guadalupe Aizaga | 17s | ✔ Eval construction-01. Verified: worker on scaffold planks at height, hi-vis vest, NO hard hat (hood/cap), plank platform with incomplete guard rails. |
| footage/construction/workers-elevated-platform_32244799.mp4 | https://www.pexels.com/video/construction-workers-on-an-elevated-platform-32244799/ | Usman AbdulrasheedGambo | 10s | Work-at-height group scene; eval material. |
| footage/construction/crew-vests-hardhats_19832500.mp4 | https://www.pexels.com/video/a-group-of-men-in-orange-vests-and-hard-hats-working-on-a-construction-site-19832500/ | CP Khanal | 5s | NEGATIVE (clean) eval scene: full PPE crew — a correct system reports no PPE violations here. |
| footage/construction/worker-goggles_8963855.mp4 | https://www.pexels.com/video/a-construction-worker-putting-on-goggles-8963855/ | Mikael Blomkvist | 6s | PPE close-up (eye protection); stills for evidence-frame tests. |

## Farms

| File | Source (Pexels) | Creator | Length | Intended use |
|---|---|---|---|---|
| footage/farm/vineyard-irrigation-spray_8467118.mp4 | https://www.pexels.com/video/irrigating-a-vine-yard-using-water-spray-8467118/ | Marian Croitoru | 14s | Irrigation equipment in operation; farm eval scene. (Note: the page's first-listed file variant was a dead S3 key; a working variant of the same video was fetched — same Pexels license.) |
| footage/farm/tractor-spraying_36768458.mp4 | https://www.pexels.com/video/modern-tractor-spraying-in-vast-crop-field-36768458/ | Wolfgang Weiser | 9s | ✔ Verified: boom sprayer actively spraying a crop field — chemical-application equipment scene; farm flagship test. |
| footage/farm/greenhouse-worker_3191934.mp4 | https://www.pexels.com/video/a-man-choosing-vegetable-plants-inside-a-greenhouse-3191934/ | Pressmaster | 24s | Greenhouse worker close work; worker/PPE eval material. |
| footage/farm/irrigation-aerial_8357855.mp4 | https://www.pexels.com/video/drone-footage-of-irrigation-on-farmland-8357855/ | Andi Farruku | 17s | Aerial irrigation context; site-overview shots for the demo video. |

## Round 2 — Violation & test media (added 2026-10-21, at Hussein's request)
Chosen specifically because each scene contains — or deliberately does NOT
contain — a detectable mistake. Honest labeling from frame inspection:
stock hunts for "violations" return a mix, and that mix is exactly what a
credible benchmark needs (positives, compliant negatives, indeterminates).

### Videos — footage/violations/
| File | Source (Pexels) | Creator | Length | Verified label |
|---|---|---|---|---|
| man-ladder-facade_13372330.mp4 | https://www.pexels.com/video/man-painting-facade-on-ladder-13372330/ | Fábio Reis de Abreu | 43s | ✔ POSITIVE — painter high on an extension ladder, leaning/reaching sideways beyond the rails, no fall protection, no helmet. Textbook unsafe ladder work. |
| man-using-grinder_6046356.mp4 | https://www.pexels.com/video/a-man-using-a-grinder-6046356/ | (Pexels user "K") | 31s | ✔ UNCERTAIN — grinding with gloves; face largely out of frame and a face shield appears raised. Eye/face protection cannot be determined → an "unable to determine" test. |
| angle-grinder-sparks_6046357.mp4 | https://www.pexels.com/video/angle-grinder-sparks-6046357/ | (Pexels user "K") | 18s | Grinding spark close-ups; label at eval build. |
| man-welding-factory_10641848.mp4 | https://www.pexels.com/video/man-working-at-welding-in-factory-10641848/ | tejinder ladi photography | 24s | ✔ NEGATIVE (compliant) — welder with helmet down and gloves on. A correct system reports NO violation here; flagging it is a false alarm. |
| man-welding-workshop_14314931.mp4 | https://www.pexels.com/video/a-man-welding-a-metal-sheet-at-a-workshop-14314931/ | Andrey Kirievskiy | 16s | Welding scene (720p); label at eval build. |
| worker-descends-maintenance_40195931.mp4 | https://www.pexels.com/video/industrial-worker-descends-for-maintenance-40195931/ | abdo alshreef | 9s | Industrial descent/maintenance movement; label at eval build. |

### Photos — demo/photos/
| File | Source (Pexels) | Creator | Verified label |
|---|---|---|---|
| worker-grinding-sparks_36003964.jpg | https://www.pexels.com/photo/industrial-worker-grinding-metal-with-sparks-36003964/ | Michael Orshan | ✔ UNCERTAIN — heavy grinding spark spray, gloves + apron on, but the worker's face is OUT OF FRAME: eye protection is indeterminable. The benchmark's model case for "unable to determine". |
| construction-workers-site_12314551.jpg | https://www.pexels.com/photo/construction-workers-on-a-building-site-12314551/ | Niklas Jeromin | ✔ NEGATIVE (mostly compliant) — four workers at height, all helmets + hi-vis. Open labeling question: uncapped protruding rebar near the top-left worker. |
| person-grinder_12303734.jpg | https://www.pexels.com/photo/a-person-using-a-grinder-12303734/ | Nishant Aneja | Label at eval build. |
| cutoff-saw-sparks_1145434.jpg | https://www.pexels.com/photo/cut-off-saw-cutting-metal-with-sparks-1145434/ | Anamul Rezwan | Label at eval build. |
| workers-rebar_32141074.jpg | https://www.pexels.com/photo/construction-workers-installing-reinforcement-bars-at-site-32141074/ | Ali | Label at eval build. |
| welder-dark-room_27630177.jpg | https://www.pexels.com/photo/a-welder-in-blue-welding-in-a-dark-room-27630177/ | Felipe Silva | Label at eval build. |
| welder-outdoors_36227261.jpg | https://www.pexels.com/photo/welder-at-work-in-industrial-setting-outdoors-36227261/ | Gizem Gökce | Label at eval build. |
| worker-glove-mask_3678228.jpg | https://www.pexels.com/photo/man-wearing-brown-glove-and-a-mask-3678228/ | Kateryna Babaieva | PPE-portrait; label at eval build. |
| worker-climbing-ladder_38510725.jpg | https://www.pexels.com/photo/construction-worker-climbing-ladder-outdoors-38510725/ | Bulat843 | Label at eval build. |
| man-ladder-roof_19769643.jpg | https://www.pexels.com/photo/man-standing-on-the-ladder-in-a-yard-fixing-a-roof-on-a-house-19769643/ | Lisa Fotios | Ladder/roof work; label at eval build. |

## Still to stage ourselves (not stock)
- The matched BEFORE/AFTER pair for the flagship Verify beat: same spot,
  same worker — first without a helmet, then wearing one. Stock cannot
  give us the same scene twice, so this pair is shot on a phone during
  the event window (any workshop/warehouse corner + a helmet).
- The in-room live-camera beat (camera connected, person walks in) —
  recorded during the Oct 28 live-wiring rehearsal.
