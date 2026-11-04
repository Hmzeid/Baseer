# Baseer · بصير by Veebase — User Guide

Baseer turns a short site walkthrough (photos, a video, or a live camera)
plus the inspector's Arabic or English notes into an evidence-grounded
safety inspection report. Every finding opens a corrective-action case,
and a case closes only when a person approves it.

The console is bilingual (Arabic right-to-left, English left-to-right) and
has light and dark themes. Switch either one from the top bar, the sign-in
screen, or **My account**.

---

## 1. Signing in

Open the console (production: `http://127.0.0.1:8001`) and sign in with
the account your administrator created. Everything you do (assigning,
verifying, approving, notes) is recorded under your name and role.

| Role | Typical use |
|---|---|
| **Safety Supervisor** (مشرف السلامة) | Runs inspections, verifies fixes, writes case notes |
| **Site Manager** (مدير الموقع) | Assigns corrective actions, approves closures |
| **Contractor** (المقاول) | Reads assigned cases, adds progress notes |
| **Admin** (مدير النظام) | Everything above plus user management |

The permission model is deliberately simple: every signed-in role can
work cases, and only Admin can manage users. The role is stamped on every
audit entry, so who did what stays visible.

Sessions last 12 hours. Five wrong passwords lock the username for five
minutes.

## 2. The console at a glance

The sidebar has three groups:

- **Operations**: Overview, New inspection, Live camera
- **Records**: Inspections (history), Cases (corrective actions), Audit log
- **Account**: Users (Admin only), My account

The top bar shows the page, a **search box** (press <kbd>/</kbd> from
anywhere), the mode badge (**DEMO** = synthetic outputs, **LIVE** = Meta
models connected), the language switch and the theme switch. On a phone,
the sidebar opens from the ☰ button.

## 3. Overview: the safety dashboard

- **KPI cards**: inspections, findings (with the average per inspection),
  high-severity findings, open cases (with the closure rate) and
  **overdue** cases. The case cards link to the Cases view.
- **Daily activity**: inspections and findings per day for the last 14 days.
- **Severity mix**: a donut of high, medium and low findings.
- **Most frequent hazards**: the five hazards that recur most.
- **Cases needing follow-up**: overdue and oldest open cases first. Click
  one to jump straight to that finding in its report.
- **Recent inspections**: click to open the report.
- **Site filter** (top right): scopes the whole dashboard to one site.

While the system is young, the dashboard includes three clearly labeled
demo seed inspections so the charts have shape. A banner says so, and the
seed rows carry a **Demo** tag.

## 4. Running an inspection (upload)

1. Open **New inspection**.
2. Drag photos or a short video onto the drop zone, or click it to choose
   files (JPG, PNG, WEBP, MP4, MOV, up to 150 MB per inspection).
   Thumbnails appear, and you can remove any file with ✕.
3. Write your notes, or press **Record voice note** to dictate. The
   transcript is appended to the notes when voice transcription is
   configured; otherwise just type.
4. Enter the **site** (for example `factory`, `construction`, `farm`). The
   field suggests sites already in use, and the site drives the site
   filters everywhere.
5. Press **Generate report**. A progress panel runs while Baseer extracts
   frames, analyzes the scene and writes the report, usually in about 30
   seconds in live mode. The report then opens.

Baseer reports only what is visible in the frames or stated in your notes.
Anything it cannot determine is marked **Unable to determine**, and that
uncertainty never raises a finding's severity.

## 5. Live camera

1. Open **Live camera**, enter the site, and press **Start live session**.
2. Press **Turn camera on** to use the device camera (on a phone it
   prefers the rear camera). Baseer takes a snapshot every 3 seconds. You
   can also press **Send frame from file** at any time.
3. When a violation first appears, an alert drops into **Live alerts**, a
   notification pops up, and the camera frame flashes red. Each violation
   type alerts once per session.
4. Press **Finish & generate report**. The full report is produced from
   every frame received, through the same reasoning as an upload, and
   opens automatically.

If the server restarts mid-session, the session is kept. Back on the Live
page, pick it under **Unfinished sessions** and press **Resume**.

## 6. Reading a report

- **Header**: the report ID, badges for the pipeline (Demo data / Muse
  vision / SAM 3.1) and the source (Upload / Live camera), the date,
  frame count and site.
- **Actions**: **PDF** (a structured Arabic PDF report rendered on the
  server), **Print**, **WhatsApp** (shares a text summary), **Copy link**
  (a direct link to this report for anyone signed in).
- **Severity strip and summary**: totals by severity, then the AI summary.
- **Attached evidence**: the original uploads, served securely from the
  server. Click an image to enlarge it; videos load on demand.
- **Findings**: each card shows the severity, title, detail, corrective
  action, evidence frame and source (visual model, inspector note, or
  both), with the frame thumbnail when one is available.

### Ask Baseer (evidence chat)

The side panel answers questions strictly from this report's findings and
frames, in Arabic or English, matching the language you ask in. Use the
suggestion chips, or ask things like:

- *Why is finding 1 high severity?*
- *Draft a notice to the contractor*
- *Summarize for the site manager*

## 7. Corrective-action cases

Every finding opens a case, shown under its finding card with a stepper:

**Open → Assigned → Verified → Closed**

| Step | How |
|---|---|
| **Assign** | Type or pick an owner (a role, a company, a person) and press **Assign**. |
| **AI verify** | Asks Baseer whether the finding is resolved. Without new evidence this stays conservative. |
| **Re-inspection evidence** | Upload an *after* photo or video of the same spot. Baseer compares it with the original finding and suggests resolved or not resolved. |
| **Approve closure** | Enabled only after a verification suggests the issue is resolved. You confirm in a dialog, and the closure is final. Baseer never closes a case by itself. |
| **Notes** | Add free-text notes (contractor dialogue, scheduling). Notes are append-only and appear in the case **Activity** timeline. |

**Deadlines.** Each case is due a set time after the inspection,
according to severity: **high 1 day, medium 7 days, low 30 days**. Open
cases past their deadline show as **Overdue** in red.

## 8. Inspections (history)

Every completed inspection, newest first. Search by inspection ID, site,
summary text or hazard name, and filter by site or severity. Each row
shows the top finding, the severity counts and a bar for cases closed.
Click a row to open the report. **Export CSV** downloads the filtered
list.

Pasting an inspection ID into the top search box opens that report
directly.

## 9. Cases

Every corrective-action case across all inspections, most urgent first:
overdue, then by severity, then by deadline. Tabs filter **All / Open /
Assigned / Overdue / Closed** with live counts. Filter by site, export
CSV, and click any row to jump to that finding in its report. The
sidebar's red badge counts open plus assigned cases.

## 10. Audit log

An append-only record of every case action (assign, verify, verify with
evidence, approve, note), with time, inspection, site, finding, action,
actor (`username (role)`) and detail. Search it, filter by action, export
CSV, and click an inspection ID to open the report. Entries can never be
edited or deleted from the application.

## 11. Users (Admin)

- **Add user**: username, a password of 8+ characters, and a role.
- **Change role**: use the role dropdown on the row. It takes effect
  immediately. You cannot remove your own Admin role.
- **Reset password** (key icon): set a new password and share it securely.
- **Delete** (bin icon): the user can no longer sign in. Their past audit
  entries remain.

## 12. My account

Your profile and role, language and theme preferences (remembered on this
device), and **Change password** (you need the current one).

## Keyboard shortcuts

| Key | Action |
|---|---|
| <kbd>/</kbd> | Focus the search box |
| <kbd>Enter</kbd> in search | Open an inspection by ID, or search the history |
| <kbd>Esc</kbd> | Close the image viewer or the mobile menu |

---
*Baseer is a Veebase product. © 2026 Veebase.*
