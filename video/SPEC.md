# SPEC — Baseer walkthrough

GOAL:    a viewer can say what Baseer does with a site photo: report, ask, act, and a person closes it.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps
TIME:    90 s x 30 = 2700 frames, 9 scenes, silent (music optional, see README)
LOOK:    ground #F3F5F8 (the app's own), ink #0E1726; caption plate #0A2540 at 96%, radius 16, white Inter 700 40 px,
         one accent word in gold #C9A94E per line; end card on navy #0A2540 with the app's login-art grid at 7%.
         Medium: the product UI itself, real 2x screenshots (3840x2160) shown at 1:1 then pushed in to 2x max.
         Shadow on raised plates 0 18 50 rgba(10,37,64,.28). No grain, no vignette.
OBJECTS: the scaffold photo; the upload form; the analysis panel; the report; a finding card with its frame;
         the chat panel; the case stepper Open→Assigned→Verified→Closed; the approval dialog; the live stage
         playing real warehouse footage; the KPI row; the cases table; the audit log; the Arabic report.
MOTION:  camera power2.inOut 1.0–1.4 s; arrivals expo.out 0.6 s; exits power3.in 0.25 s;
         caption words blur 8→0 px + opacity in 0.13 s, 0.07 s apart, never move after landing;
         cursor power2.inOut 0.6–0.9 s, click = scale 0.82 for 0.08 s then back 0.14 s (no rings);
         screen swaps = blur swap 0.2 s on one stage.
SHOTS:   0–7 hook: photo full-bleed, two lines, photo carries into the upload thumbnail
         7–17 upload: push to form, cursor clicks Generate, analysis panel steps
         17–30 report: push to severity strip + summary, then finding #1 and its fix
         30–39 chat: cursor asks two chips, answers appear
         39–55 case: assign → after-photo → approve dialog → closed with activity
         55–65 live: camera on, real footage plays, two alerts land, finish
         65–76 oversight: KPI overdue → cases overdue tab → audit log
         76–83 Arabic RTL report, iris from the theme toggle into dark Arabic overview
         83–90 end card: mark, name, "From walkthrough to verified closure", demo disclosure
BANNED:  dark void with floating UI; glow/particles; three cards in a row; title over a dimmed screenshot;
         click rings; titles drifting after landing; every scene entering the same way; logo docked in a corner;
         any claim the app does not make (no speed multipliers, no accuracy numbers).
QA:      2.0 (hook readable), 6.4 (carry lands in thumb), 11 (cursor on Generate), 21 (strip readable),
         34 (chat answer), 49 (approve dialog), 59 (footage + alerts), 70 (overdue tab), 80 (iris), 88 (end card).
