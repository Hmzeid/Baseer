"""Generate the Baseer walkthrough HyperFrames project (index + 9 scenes)."""
import json
from pathlib import Path

V = Path("/Users/husseinabdelwahab/Ai/Baseer/video")
(V / "compositions").mkdir(exist_ok=True)

CSS = """
    #root { position:absolute; inset:0; overflow:hidden; background:#F3F5F8; font-family:Inter, sans-serif; }
    #root .cam { position:absolute; left:0; top:0; width:1920px; height:1080px; transform-origin:0 0; }
    #root .shot { position:absolute; left:0; top:0; width:1920px; height:1080px; background-size:1920px 1080px; background-repeat:no-repeat; }
    #root .cursor { position:absolute; left:0; top:0; width:30px; height:30px; z-index:40; }
    #root .cursor svg { width:30px; height:30px; transform-origin:4px 3px; filter:drop-shadow(0 3px 5px rgba(0,0,0,.35)); }
    #root .cap { position:absolute; left:0; right:0; bottom:110px; margin:0 auto; width:fit-content; max-width:1400px;
      background:rgba(10,37,64,.96); color:#fff; font-weight:700; font-size:40px; line-height:1.25; letter-spacing:-.01em;
      padding:20px 36px; border-radius:16px; box-shadow:0 18px 50px rgba(10,37,64,.28); z-index:50; text-align:center; }
    #root .cap.left { left:110px; right:auto; margin:0; bottom:140px; max-width:780px; text-align:left; }
    #root .cap .w { display:inline-block; }
    #root .cap .acc { color:#E0C26A; }
"""

CURSOR = ('<div class="cursor" id="{id}-cur"><svg viewBox="0 0 24 24"><path d="M4 3l15 8.5-6.6 1.6L9.6 20z" '
          'fill="#fff" stroke="#0A2540" stroke-width="1.6" stroke-linejoin="round"/></svg></div>')

HELPERS = """
    const W = 1920, H = 1080, S = "#__ID__";
    const tl = gsap.timeline({ paused: true });
    // Split caption text into word spans (accent <b class="acc"> kept as one word).
    document.querySelectorAll(S + " .cap").forEach((cap) => {
      const out = [];
      cap.childNodes.forEach((n) => {
        if (n.nodeType === 3) n.textContent.split(/\\s+/).filter(Boolean).forEach((w) => out.push(`<span class="w">${w}</span>`));
        else { n.classList.add("w"); out.push(n.outerHTML); }
      });
      cap.innerHTML = out.join(" ");
    });
    // Camera: frame box [x,y,w,h] (UI px) at scale s, box centre at (fx*W, fy*H), clamped to the shot.
    function cam(box, s, t, d = 1.2, fx = 0.5, fy = 0.44, ease = "power2.inOut") {
      const cx = box[0] + box[2] / 2, cy = box[1] + box[3] / 2;
      const x = Math.min(0, Math.max(W - W * s, W * fx - s * cx));
      const y = Math.min(0, Math.max(H - H * s, H * fy - s * cy));
      if (d === 0) tl.set(S + " .cam", { x, y, scale: s }, t);
      else tl.to(S + " .cam", { x, y, scale: s, duration: d, ease }, t);
    }
    // Blur swap: the next screen sharpens in over the current one.
    function swap(sel, t) {
      tl.fromTo(sel, { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.22, ease: "power2.out" }, t);
    }
    function cap(sel, tin, tout) {
      tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: 0.15, ease: "power2.out" }, tin);
      tl.fromTo(sel + " .w", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.13, stagger: 0.07, ease: "power2.out" }, tin + 0.05);
      if (tout !== undefined) tl.to(sel, { opacity: 0, filter: "blur(6px)", duration: 0.22, ease: "power3.in" }, tout);
    }
    // Cursor tip to point (UI px); click dips the arrow.
    function move(pt, t, d = 0.8) { tl.to(S + " .cursor", { x: pt[0], y: pt[1], duration: d, ease: "power2.inOut" }, t); }
    function click(t) {
      tl.to(S + " .cursor svg", { scale: 0.82, duration: 0.08, ease: "power2.in" }, t);
      tl.to(S + " .cursor svg", { scale: 1, duration: 0.14, ease: "power2.out" }, t + 0.08);
    }
    const mid = (b) => [b[0] + b[2] / 2 - 4, b[1] + b[3] / 2 - 3];
"""


def shot(sid, name, z=1, hidden=True):
    op = "opacity:0;" if hidden else ""
    return f'<div class="shot" id="{sid}-{name}" style="background-image:url(assets/shots/{name}.jpg);z-index:{z};{op}"></div>'


def scene(sid, dur, body, script, extra_css=""):
    html = f"""<template>
  <style>{CSS.replace("#root", "#root")}{extra_css}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
{body}
  </div>
  <script>{HELPERS.replace("__ID__", sid)}{script}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""
    (V / "compositions" / f"{sid}.html").write_text(html)
    return sid, dur


B = json.loads((V / "assets" / "boxes.json").read_text())
scenes = []

# ---------------------------------------------------------------- 1 hook
scenes.append(scene("hook", 7, f"""
    <div class="cam">{shot("hook", "c02-inspect", 1)}</div>
    <div id="hook-photo" style="position:absolute;left:0;top:0;width:1920px;height:1080px;z-index:5;transform-origin:0 0;
      background:url(assets/photo-scaffold.jpg) center 38%/cover no-repeat;clip-path:inset(0px 0px 0px 0px round 0px)"></div>
    <div id="hook-note" style="position:absolute;left:1180px;top:150px;width:600px;z-index:6;background:#fff;border-radius:18px;
      padding:26px 30px;box-shadow:0 24px 60px rgba(10,37,64,.35);font:600 34px/1.4 Inter,sans-serif;color:#0E1726;opacity:0">
      <div data-layout-ignore style="font:700 22px Inter;letter-spacing:.12em;color:#8A6A1A;margin-bottom:10px">INSPECTOR'S NOTE</div>
      Level 4 scaffold: one worker not tied off.</div>
    <div class="cap left" id="hook-c1">One site photo. One <b class="acc">inspector's</b> note.</div>
    <div class="cap left" id="hook-c2">Here is what <b class="acc">Baseer</b> does with it.</div>
    <div id="hook-demo" style="position:absolute;left:110px;bottom:72px;z-index:50;font:600 28px Inter;color:#fff;
      background:rgba(10,37,64,.7);padding:6px 14px;border-radius:8px;opacity:0">Demo mode shown · findings are synthetic samples</div>
""", """
    tl.fromTo(S + " #hook-photo", { scale: 1.0 }, { scale: 1.05, duration: 4.8, ease: "none" }, 0);
    tl.set(S + " #hook-c1", { opacity: 1 }, 0);
    tl.fromTo(S + " #hook-c1 .w", { opacity: 0.6 }, { opacity: 1, duration: 0.13, stagger: 0.06 }, 0);
    tl.to(S + " #hook-c1", { opacity: 0, filter: "blur(6px)", duration: 0.22, ease: "power3.in" }, 2.9);
    tl.fromTo(S + " #hook-note", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.6, ease: "expo.out" }, 0.9);
    cap(S + " #hook-c2", 3.1, 5.0);
    tl.fromTo(S + " #hook-demo", { opacity: 0 }, { opacity: 1, duration: 0.3 }, 2.1);
    tl.to(S + " #hook-demo", { opacity: 0, duration: 0.2 }, 5.0);
    // Carry across: the photo crops to 4:3 and lands in the upload thumbnail; the note drops into the notes field.
    tl.set(S + " #hook-c02-inspect", { opacity: 1 }, 5.0);
    tl.to(S + " #hook-photo", { clipPath: "inset(0px 240px 0px 240px round 130px)", x: 406 - 240 * 0.0854, y: 363, scale: 0.0854,
      duration: 1.15, ease: "power3.inOut" }, 5.1);
    tl.to(S + " #hook-photo", { opacity: 0, duration: 0.25 }, 6.25);
    tl.to(S + " #hook-note", { x: 405 - 1180, y: 497 - 150, scale: 0.5, opacity: 0, duration: 1.0, ease: "power3.inOut" }, 5.15);
"""))

# ---------------------------------------------------------------- 2 upload
b = B["c02-inspect"]
scenes.append(scene("upload", 10, f"""
    <div class="cam">{shot("upload", "c02-inspect", 1, False)}{shot("upload", "c03-analyzing", 2)}{shot("upload", "c03b-analyzing", 3)}
      {CURSOR.format(id="upload")}</div>
    <div class="cap" id="upload-c1">Add the photos, your note and the <b class="acc">site</b></div>
    <div class="cap" id="upload-c2">Frames extracted, scene analyzed, <b class="acc">report</b> written</div>
""", f"""
    tl.set(S + " .cursor", {{ x: 1300, y: 980, opacity: 0 }}, 0);
    cam([405, 181, 814, 611], 1.28, 0.3, 1.4);
    cap(S + " #upload-c1", 0.6, 4.0);
    tl.to(S + " .cursor", {{ opacity: 1, duration: 0.2 }}, 2.4);
    move(mid({b["run"]}), 2.5, 1.0);
    click(3.7);
    tl.to(S + " .cursor", {{ opacity: 0, duration: 0.2 }}, 4.1);
    swap(S + " #upload-c03-analyzing", 4.0);
    cam([750, 378, 420, 324], 1.55, 4.3, 1.3, 0.5, 0.42);
    cap(S + " #upload-c2", 4.7, 9.7);
    swap(S + " #upload-c03b-analyzing", 6.6);
"""))

# ---------------------------------------------------------------- 3 report
r = B["c04-report"]; f = B["c05-finding"]
scenes.append(scene("report", 13, f"""
    <div class="cam">{shot("report", "c04-report", 1, False)}{shot("report", "c05-finding", 2)}</div>
    <div class="cap" id="report-c1">Severity, evidence and a summary, in <b class="acc">Arabic</b> and English</div>
    <div class="cap" id="report-c2">Each finding shows its frame and the <b class="acc">fix</b></div>
""", f"""
    tl.fromTo(S + " .cam", {{ filter: "blur(10px)" }}, {{ filter: "blur(0px)", duration: 0.3, ease: "power2.out" }}, 0);
    cam([405, 120, 972, 330], 1.0, 0, 0);
    cam([405, 130, 972, 320], 1.62, 0.9, 1.4);
    cap(S + " #report-c1", 1.5, 5.9);
    cam([405, 250, 972, 470], 1.42, 3.7, 1.6, 0.5, 0.44);
    swap(S + " #report-c05-finding", 6.1);
    cam({f["finding"]}, 1.0, 6.1, 0);
    cam({f["finding"]}, 1.72, 6.3, 1.3, 0.5, 0.42);
    cap(S + " #report-c2", 6.9, 12.7);
    cam([{f["action"][0]}, 30, {f["finding"][2]}, 210], 1.95, 9.6, 1.4, 0.5, 0.42);
"""))

# ---------------------------------------------------------------- 4 chat
c = B["c06-chat"]
scenes.append(scene("chat", 9, f"""
    <div class="cam">{shot("chat", "c04-report", 1, False)}{shot("chat", "c06-chat", 2)}{shot("chat", "c06b-chat", 3)}
      {CURSOR.format(id="chat")}</div>
    <div class="cap left" id="chat-c1">Ask Baseer: answers come only from this <b class="acc">evidence</b></div>
    <div class="cap left" id="chat-c2">Draft the contractor <b class="acc">notice</b> in one click</div>
""", f"""
    tl.fromTo(S + " .cam", {{ filter: "blur(10px)" }}, {{ filter: "blur(0px)", duration: 0.3, ease: "power2.out" }}, 0);
    cam([1418, 121, 380, 600], 1.0, 0, 0);
    cam([1418, 121, 380, 600], 1.42, 0.2, 1.2, 0.68, 0.46);
    tl.set(S + " .cursor", {{ x: 1250, y: 700 }}, 0);
    cap(S + " #chat-c1", 0.5, 4.4);
    move(mid({c["chip1"]}), 1.0, 0.9);
    click(2.0);
    swap(S + " #chat-c06-chat", 2.25);
    move(mid({c["chip2"]}), 4.2, 0.8);
    click(5.1);
    swap(S + " #chat-c06b-chat", 5.35);
    cam([1418, 560, 380, 520], 1.42, 5.6, 1.3, 0.68, 0.5);
    cap(S + " #chat-c2", 5.6, 8.8);
"""))

# ---------------------------------------------------------------- 5 case
k = B
scenes.append(scene("case", 16, f"""
    <div class="cam">{shot("case", "c07-case-open", 1, False)}{shot("case", "c07b-case-typed", 2)}{shot("case", "c08-assigned", 3)}
      {shot("case", "c09-verified", 4)}{shot("case", "c10-modal", 5)}{shot("case", "c11-closed", 6)}{CURSOR.format(id="case")}</div>
    <div class="cap" id="case-c1">Every finding opens a corrective-action <b class="acc">case</b></div>
    <div class="cap" id="case-c2">Assign it, then verify with an <b class="acc">after-photo</b></div>
    <div class="cap" id="case-c3">Only a <b class="acc">person</b> can approve the closure</div>
    <div class="cap" id="case-c4">Every step is signed into the <b class="acc">audit trail</b></div>
""", f"""
    tl.fromTo(S + " .cam", {{ filter: "blur(10px)" }}, {{ filter: "blur(0px)", duration: 0.3, ease: "power2.out" }}, 0);
    cam([383, 26, 1016, 440], 1.0, 0, 0);
    cam([383, 26, 1016, 440], 1.45, 0.2, 1.2, 0.5, 0.42);
    tl.set(S + " .cursor", {{ x: 760, y: 560 }}, 0);
    cap(S + " #case-c1", 0.3, 3.4);
    cam([383, 282, 1016, 200], 1.7, 1.5, 1.1, 0.5, 0.42);
    move(mid({k["c07-case-open"]["input"]}), 1.3, 0.8);
    click(2.15);
    swap(S + " #case-c07b-case-typed", 2.4);
    move(mid({k["c07-case-open"]["assign"]}), 2.7, 0.6);
    click(3.35);
    swap(S + " #case-c08-assigned", 3.55);
    cap(S + " #case-c2", 3.8, 8.4);
    move(mid({k["c08-assigned"]["evidence"]}), 4.3, 0.8);
    click(5.2);
    swap(S + " #case-c09-verified", 6.0);
    cam([383, 282, 1016, 380], 1.6, 6.0, 1.0, 0.5, 0.42);
    move(mid({k["c09-verified"]["approve"]}), 6.9, 0.8);
    click(7.8);
    swap(S + " #case-c10-modal", 8.05);
    cam({k["c10-modal"]["card"]}, 1.7, 8.1, 0.9, 0.5, 0.45);
    cap(S + " #case-c3", 8.6, 12.9);
    move(mid({k["c10-modal"]["ok"]}), 8.9, 0.9);
    click(10.0);
    tl.to(S + " .cursor", {{ opacity: 0, duration: 0.2 }}, 10.3);
    swap(S + " #case-c11-closed", 10.25);
    cam([383, 282, 1016, 520], 1.5, 10.3, 1.2, 0.5, 0.44);
    cap(S + " #case-c4", 13.1, 15.8);
"""))

# ---------------------------------------------------------------- 6 live
l = B["c12-live"]; li = B["c12a-live-idle"]
st = l["stage"]
scenes.append(scene("live", 10, f"""
    <div class="cam">{shot("live", "c12a-live-idle", 1, False)}
      <div id="live-on" style="position:absolute;inset:0;z-index:2;opacity:0">
        {shot("live", "c12-live", 1, False)}
        <video id="live-feed" class="clip" data-start="1.9" data-duration="8.1" data-track-index="2" muted playsinline
          src="assets/live-forklift.mp4" style="position:absolute;left:{st[0]+3}px;top:{st[1]+3}px;width:{st[2]-6}px;height:{st[3]-6}px;
          object-fit:cover;border-radius:12px;z-index:2"></video>
        <div style="position:absolute;inset:0;z-index:3;background:url(assets/shots/c12-live.jpg) 0 0/1920px 1080px;clip-path:inset(176px 1392px 875px 416px round 7px)"></div>
        <div style="position:absolute;inset:0;z-index:3;background:url(assets/shots/c12-live.jpg) 0 0/1920px 1080px;clip-path:inset(176px 712px 875px 1135px round 7px)"></div>
        <div id="live-cover1" style="position:absolute;left:1280px;top:198px;width:500px;height:80px;background:#fff;z-index:4"></div>
        <div id="live-cover2" style="position:absolute;left:1280px;top:278px;width:500px;height:80px;background:#fff;z-index:4"></div>
        <div style="position:absolute;left:1380px;top:940px;width:540px;height:140px;background:#F3F5F8;z-index:4"></div>
      </div>
      {CURSOR.format(id="live")}</div>
    <div class="cap" id="live-c1">Or point a <b class="acc">live camera</b> at the site</div>
    <div class="cap" id="live-c2">Each violation raises an alert on <b class="acc">first sight</b></div>
    <div class="cap" id="live-c3">Finish, and the <b class="acc">full report</b> is written</div>
""", f"""
    tl.fromTo(S + " .cam", {{ filter: "blur(10px)" }}, {{ filter: "blur(0px)", duration: 0.3, ease: "power2.out" }}, 0);
    tl.set(S + " .cursor", {{ x: 900, y: 900 }}, 0);
    cap(S + " #live-c1", 0.3, 3.4);
    move(mid({li["cam"]}), 0.4, 0.9);
    click(1.5);
    swap(S + " #live-on", 1.8);
    cam([405, 165, 1370, 560], 1.3, 2.2, 1.3, 0.5, 0.42);
    tl.to(S + " #live-cover1", {{ opacity: 0, duration: 0.25 }}, 3.9);
    tl.to(S + " #live-cover2", {{ opacity: 0, duration: 0.25 }}, 5.0);
    cap(S + " #live-c2", 3.7, 7.2);
    move(mid({l["finish"]}), 6.4, 0.9);
    click(7.5);
    cap(S + " #live-c3", 7.4, 9.8);
"""))

# ---------------------------------------------------------------- 7 records
o = B["c13b-overview"]
scenes.append(scene("records", 11, f"""
    <div class="cam">{shot("records", "c13b-overview", 1, False)}{shot("records", "c14-cases", 2)}{shot("records", "c15-audit", 3)}
      {CURSOR.format(id="records")}</div>
    <div class="cap" id="records-c1">Deadlines follow severity: <b class="acc">one day</b> for high</div>
    <div class="cap" id="records-c2"><b class="acc">Overdue</b> cases rise to the top</div>
    <div class="cap" id="records-c3">Every action is signed, timed and <b class="acc">kept</b></div>
""", f"""
    tl.fromTo(S + " .cam", {{ filter: "blur(10px)" }}, {{ filter: "blur(0px)", duration: 0.3, ease: "power2.out" }}, 0);
    tl.set(S + " .cursor", {{ x: 1000, y: 700 }}, 0);
    cam([382, 150, 1416, 600], 1.22, 0.3, 1.2, 0.5, 0.44);
    cap(S + " #records-c1", 0.5, 3.6);
    move(mid({o["overdue"]}), 1.6, 1.0);
    click(3.2);
    swap(S + " #records-c14-cases", 3.5);
    tl.to(S + " .cursor", {{ opacity: 0, duration: 0.2 }}, 3.6);
    cam([405, 130, 1370, 560], 1.25, 3.5, 1.0, 0.5, 0.44);
    cap(S + " #records-c2", 4.0, 7.2);
    swap(S + " #records-c15-audit", 7.4);
    cap(S + " #records-c3", 7.6, 10.8);
"""))

# ---------------------------------------------------------------- 8 arabic
scenes.append(scene("arabic", 7, f"""
    <div class="cam">{shot("arabic", "c16-report-ar", 1, False)}
      <div class="shot" id="arabic-dark" style="background-image:url(assets/shots/c17-overview-ar-dark.jpg);z-index:2;clip-path:circle(0px at 51px 46px)"></div></div>
    <div class="cap" id="arabic-c1"><b class="acc">Arabic-first</b>, right to left, end to end</div>
    <div class="cap" id="arabic-c2">And a <b class="acc">dark</b> theme for the control room</div>
""", """
    tl.fromTo(S + " .cam", { filter: "blur(10px)" }, { filter: "blur(0px)", duration: 0.3, ease: "power2.out" }, 0);
    tl.fromTo(S + " .cam", { scale: 1.0 }, { scale: 1.04, duration: 3.2, ease: "none" }, 0);
    cap(S + " #arabic-c1", 0.4, 3.2);
    tl.to(S + " .cam", { scale: 1.0, duration: 0.3, ease: "power2.out" }, 3.2);
    tl.to(S + " #arabic-dark", { clipPath: "circle(2300px at 51px 46px)", duration: 0.7, ease: "power2.in" }, 3.4);
    cap(S + " #arabic-c2", 4.2, 6.8);
"""))

# ---------------------------------------------------------------- 9 end
scenes.append(scene("end", 7, """
    <div style="position:absolute;inset:0;background:radial-gradient(900px 500px at 80% 0%, rgba(201,169,78,.26), transparent 60%),
      radial-gradient(700px 600px at 0% 100%, rgba(47,111,228,.22), transparent 60%), linear-gradient(160deg,#0A2540 0%,#061628 100%)"></div>
    <div style="position:absolute;inset:0;opacity:.07;background-image:linear-gradient(rgba(255,255,255,.6) 1px,transparent 1px),
      linear-gradient(90deg,rgba(255,255,255,.6) 1px,transparent 1px);background-size:44px 44px"></div>
    <div id="end-mark" style="position:absolute;left:810px;top:250px;width:300px;height:300px;border-radius:86px;background:#fff;
      box-shadow:0 30px 80px rgba(0,0,0,.35)">
      <svg viewBox="0 0 24 24" style="position:absolute;inset:50px"><path d="M3.2 12S6.5 6.3 12 6.3 20.8 12 20.8 12 17.5 17.7 12 17.7 3.2 12 3.2 12Z"
        fill="none" stroke="#0A2540" stroke-width="1.7"/><circle id="end-iris" cx="12" cy="12" r="3" fill="#C9A94E"/></svg></div>
    <div id="end-name" style="position:absolute;left:0;right:0;top:600px;text-align:center;color:#fff;font:800 92px/1.1 Inter;letter-spacing:-.02em">
      Baseer <span style="color:#C9A94E">·</span> <span style="font-family:'Geeza Pro AR'">بصير</span></div>
    <div class="cap" id="end-c1" style="bottom:250px;background:transparent;box-shadow:none;font-size:46px;font-weight:600">From walkthrough to <b class="acc">verified closure</b></div>
    <div id="end-demo" style="position:absolute;left:0;right:0;bottom:140px;text-align:center;font:500 28px Inter;color:#AFC0D3;opacity:0">
      Demo mode shown · live mode runs Meta's SAM 3.1 and Muse</div>
""", """
    tl.fromTo(S + " #end-mark", { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.8, ease: "expo.out" }, 0.2);
    tl.fromTo(S + " #end-iris", { scale: 0, transformOrigin: "12px 12px" }, { scale: 1, duration: 0.5, ease: "back.out(1.6)" }, 0.6);
    tl.fromTo(S + " #end-name", { opacity: 0, filter: "blur(10px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.5, ease: "power2.out" }, 0.9);
    cap(S + " #end-c1", 1.7);
    tl.fromTo(S + " #end-demo", { opacity: 0 }, { opacity: 1, duration: 0.4 }, 2.6);
""", extra_css="""
    @font-face { font-family:"Geeza Pro AR"; src: local("Geeza Pro"), local("GeezaPro"), local("GeezaPro-Regular"); }"""))

# ---------------------------------------------------------------- index
t = 0
hosts = []
for sid, dur in scenes:
    hosts.append(f'''      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{t}"
        data-duration="{dur}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>''')
    t += dur
# ---------------------------------------------------------------- audio
import subprocess
starts = {sid: st for (sid, _), st in zip(scenes, [sum(d for _, d in scenes[:i]) for i in range(len(scenes))])}
VO = {"hook": 0.3, "upload": 0.5, "report": 2.4, "chat": 0.6, "case": 1.2, "live": 0.3, "records": 1.0, "arabic": 1.2, "end": 0.8}
CLICKS = {"upload": [3.7], "chat": [2.0, 5.1], "case": [2.15, 3.35, 5.2, 7.8, 10.0], "live": [1.5, 7.5], "records": [3.2]}
def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(V / path)]).decode().strip())
audio = []
for sid, off in VO.items():
    src = f"assets/voice/norm/{sid}.wav"
    audio.append(f'      <audio id="vo-{sid}" class="clip" src="{src}" data-start="{round(starts[sid] + off, 3)}" '
                 f'data-duration="{round(dur(src), 3)}" data-track-index="10" data-volume="0.8"></audio>')
audio.append(f'      <audio id="bgm" class="clip" src="assets/bgm/bed-loop.wav" data-timeline-role="music" data-start="0" data-duration="{t}" '
             f'data-track-index="11" data-volume="0.12" data-fade-in="0.4" data-fade-out="1.5"></audio>')
n = 0
for sid, ts in CLICKS.items():
    for c in ts:
        src = "assets/sfx/click-a.mp3" if n % 2 == 0 else "assets/sfx/click-b.wav"
        audio.append(f'      <audio id="click-{n + 1:02d}" class="clip" src="{src}" data-start="{round(starts[sid] + c + 0.04, 3)}" '
                     f'data-duration="0.366" data-track-index="12" data-volume="0.7"></audio>')
        n += 1
hosts += audio
(V / "index.html").write_text(f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ margin:0; width:1920px; height:1080px; overflow:hidden; background:#F3F5F8; }}
      #root {{ position:relative; width:100%; height:100%; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{t}" data-width="1920" data-height="1080">
{chr(10).join(hosts)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
""")
print("scenes:", [s for s, _ in scenes], "total", t)
