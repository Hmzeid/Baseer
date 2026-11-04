"""Generate the 3-minute Baseer by Veebase walkthrough (Meta submission cut).

Real live-mode captures (assets/live/, boxes in assets/live-boxes.json), Kokoro
narration (assets/voice/norm/<scene>.wav), MusicGen bed, bundled clicks.
Run: python3 video/tools/gen_video3.py  -> rewrites index.html + compositions/.
"""
import json
import shutil
import subprocess
from pathlib import Path

V = Path(__file__).resolve().parent.parent
COMP = V / "compositions"
shutil.rmtree(COMP, ignore_errors=True)
COMP.mkdir()
B = json.loads((V / "assets" / "live-boxes.json").read_text())

CSS = """
    @font-face { font-family:"Geeza AR"; src: local("Geeza Pro"), local("GeezaPro"), local("GeezaPro-Bold"); }
    #root { position:absolute; inset:0; overflow:hidden; background:#F3F5F8; font-family:Inter, sans-serif; color:#0E1726; }
    #root .cam { position:absolute; left:0; top:0; width:1920px; height:1080px; transform-origin:0 0; }
    #root .shot { position:absolute; left:0; top:0; width:1920px; height:1080px; background-size:1920px 1080px; background-repeat:no-repeat; }
    #root .cursor { position:absolute; left:0; top:0; width:30px; height:30px; z-index:40; }
    #root .cursor svg { width:30px; height:30px; transform-origin:4px 3px; filter:drop-shadow(0 3px 5px rgba(0,0,0,.35)); }
    #root .cap { position:absolute; left:0; right:0; bottom:104px; margin:0 auto; width:fit-content; max-width:1400px;
      background:rgba(10,37,64,.96); color:#fff; font-weight:700; font-size:40px; line-height:1.25; letter-spacing:-.01em;
      padding:20px 36px; border-radius:16px; box-shadow:0 18px 50px rgba(10,37,64,.28); z-index:50; text-align:center; opacity:0; }
    #root .cap.left { left:110px; right:auto; margin:0; bottom:130px; max-width:760px; text-align:left; }
    #root .cap.right { right:110px; left:auto; margin:0; bottom:130px; max-width:760px; text-align:left; }
    #root .cap .w { display:inline-block; }
    #root .cap .acc { color:#E0C26A; }
    #root .ar { font-family:"Geeza AR", Inter, sans-serif; }
    #root .navy { position:absolute; inset:0; background:radial-gradient(900px 500px at 80% 0%, rgba(201,169,78,.24), transparent 60%),
      radial-gradient(700px 600px at 0% 100%, rgba(47,111,228,.2), transparent 60%), linear-gradient(160deg,#0A2540 0%,#061628 100%); }
    #root .grid { position:absolute; inset:0; opacity:.07; background-image:linear-gradient(rgba(255,255,255,.6) 1px,transparent 1px),
      linear-gradient(90deg,rgba(255,255,255,.6) 1px,transparent 1px); background-size:44px 44px; }
    #root .mark { position:absolute; width:300px; height:300px; border-radius:86px; background:#fff; box-shadow:0 30px 80px rgba(0,0,0,.35); }
    #root .mark svg { position:absolute; inset:50px; }
"""
MARK_SVG = ('<svg viewBox="0 0 24 24"><path d="M3.2 12S6.5 6.3 12 6.3 20.8 12 20.8 12 17.5 17.7 12 17.7 3.2 12 3.2 12Z" '
            'fill="none" stroke="#0A2540" stroke-width="1.7"/><circle class="iris" cx="12" cy="12" r="3" fill="#C9A94E"/></svg>')
CURSOR = ('<div class="cursor" id="{id}-cur"><svg viewBox="0 0 24 24"><path d="M4 3l15 8.5-6.6 1.6L9.6 20z" '
          'fill="#fff" stroke="#0A2540" stroke-width="1.6" stroke-linejoin="round"/></svg></div>')

HELPERS = """
    const W = 1920, H = 1080, S = "#__ID__";
    const tl = gsap.timeline({ paused: true });
    document.querySelectorAll(S + " .cap").forEach((cap) => {
      const out = [];
      cap.childNodes.forEach((n) => {
        if (n.nodeType === 3) n.textContent.split(/\\s+/).filter(Boolean).forEach((w) => out.push(`<span class="w">${w}</span>`));
        else { n.classList.add("w"); out.push(n.outerHTML); }
      });
      cap.innerHTML = out.join(" ");
    });
    function cam(box, s, t, d = 1.2, fx = 0.5, fy = 0.44, ease = "power2.inOut") {
      const cx = box[0] + box[2] / 2, cy = box[1] + box[3] / 2;
      const x = Math.min(0, Math.max(W - W * s, W * fx - s * cx));
      const y = Math.min(0, Math.max(H - H * s, H * fy - s * cy));
      if (d === 0) tl.set(S + " .cam", { x, y, scale: s }, t);
      else tl.to(S + " .cam", { x, y, scale: s, duration: d, ease }, t);
    }
    function swap(sel, t) {
      tl.fromTo(sel, { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.22, ease: "power2.out" }, t);
    }
    function cap(sel, tin, tout) {
      tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: 0.15, ease: "power2.out" }, tin);
      tl.fromTo(sel + " .w", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.13, stagger: 0.07, ease: "power2.out" }, tin + 0.05);
      if (tout !== undefined) tl.to(sel, { opacity: 0, filter: "blur(6px)", duration: 0.22, ease: "power3.in" }, tout);
    }
    function move(pt, t, d = 0.8) { tl.to(S + " .cursor", { x: pt[0], y: pt[1], duration: d, ease: "power2.inOut" }, t); }
    function click(t) {
      tl.to(S + " .cursor svg", { scale: 0.82, duration: 0.08, ease: "power2.in" }, t);
      tl.to(S + " .cursor svg", { scale: 1, duration: 0.14, ease: "power2.out" }, t + 0.08);
    }
    function enter(sel, t, from = { opacity: 0, y: 40 }, d = 0.7) {
      const to = { opacity: 1, x: 0, y: 0, scale: 1, duration: d, ease: "expo.out" };
      if (from.rotation !== undefined) to.rotation = 0;
      tl.fromTo(sel, from, to, t);
    }
    const mid = (b) => [b[0] + b[2] / 2 - 4, b[1] + b[3] / 2 - 3];
    const blurIn = () => tl.fromTo(S + " .cam", { filter: "blur(10px)" }, { filter: "blur(0px)", duration: 0.3, ease: "power2.out" }, 0);
"""


def shot(sid, name, z=1, hidden=True):
    op = "opacity:0;" if hidden else ""
    return (f'<div class="shot" id="{sid}-{name.split("-")[0]}" '
            f'style="background-image:url(assets/live/{name}.jpg);z-index:{z};{op}"></div>')


scenes = []


def scene(sid, dur, body, script):
    html = f"""<template>
  <style>{CSS}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
{body}
  </div>
  <script>{HELPERS.replace("__ID__", sid)}{script}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""
    (COMP / f"{sid}.html").write_text(html)
    scenes.append((sid, dur))


# 1 ------------------------------------------------------------ problem (10)
panels = "".join(
    f'<div class="panel" id="problem-p{i}" style="position:absolute;left:{i * 640}px;top:0;width:640px;height:1080px;overflow:hidden;'
    f'clip-path:inset(0 0 0 0);border-right:6px solid #F3F5F8"><div class="ph" style="position:absolute;inset:-30px;'
    f'background:url(assets/live/media/{img}) {pos}/cover no-repeat"></div></div>'
    for i, (img, pos) in enumerate([("ladder.jpg", "center 35%"), ("welder.jpg", "center 40%"), ("forklift.jpg", "center")]))
scene("problem", 10, f"""
    {panels}
    <div id="problem-flood" style="position:absolute;inset:0;background:#0A2540;opacity:0;z-index:60"></div>
    <div class="cap" id="problem-c1">Phone photos. <b class="acc">Handwritten</b> notes.</div>
    <div class="cap" id="problem-c2">Typed up <b class="acc">hours</b> later.</div>
    <div class="cap" id="problem-c3">And hazards slip <b class="acc">through</b>.</div>
""", """
    [0, 1, 2].forEach((i) => tl.fromTo(S + ` #problem-p${i} .ph`, { scale: 1.0 }, { scale: 1.06, duration: 9.5, ease: "none" }, 0));
    tl.set(S + " #problem-c1", { opacity: 1 }, 0);
    tl.fromTo(S + " #problem-c1 .w", { opacity: 0.6 }, { opacity: 1, duration: 0.13, stagger: 0.06 }, 0);
    tl.to(S + " #problem-c1", { opacity: 0, filter: "blur(6px)", duration: 0.22, ease: "power3.in" }, 3.4);
    cap(S + " #problem-c2", 3.7, 6.3);
    cap(S + " #problem-c3", 6.6, 9.5);
    tl.to(S + " #problem-flood", { opacity: 1, duration: 0.4, ease: "power2.inOut" }, 9.6);
""")

# 2 ------------------------------------------------------------ intro (9.5)
lb = B["L01-login"]["btn"]
scene("intro", 9.5, f"""
    <div class="navy"></div><div class="grid"></div>
    <div class="mark" id="intro-mark" style="left:810px;top:150px">{MARK_SVG}</div>
    <div id="intro-name" style="position:absolute;left:0;right:0;top:490px;text-align:center;color:#fff;font:800 96px/1.1 Inter;letter-spacing:-.02em">
      Baseer <span style="color:#C9A94E">·</span> <span class="ar">بصير</span></div>
    <div id="intro-by" style="position:absolute;left:0;right:0;top:612px;text-align:center;color:#E0C26A;font:700 44px Inter;letter-spacing:.02em">by Veebase</div>
    <div id="intro-tag" style="position:absolute;left:0;right:0;top:690px;text-align:center;color:#D7E1EC;font:600 40px Inter">Arabic-first field inspection copilot</div>
    <div id="intro-meta" style="position:absolute;left:0;right:0;top:780px;margin:0 auto;width:fit-content;color:#fff;font:700 32px Inter;
      padding:12px 26px;border-radius:14px;background:rgba(255,255,255,.1);border:2px solid rgba(255,255,255,.22)">Built on Meta <span style="color:#E0C26A">SAM 3.1</span> + <span style="color:#E0C26A">Muse</span></div>
    <div id="intro-win" style="position:absolute;left:0;top:0;width:1920px;height:1080px;z-index:20;opacity:0;transform-origin:960px 540px;
      border-radius:40px;overflow:hidden;box-shadow:0 40px 120px rgba(0,0,0,.5)">
      <div class="cam">{shot("intro", "L01-login", 1, False)}</div></div>
""", f"""
    tl.fromTo(S + " #intro-mark", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.8, ease: "expo.out" }}, 0.15);
    tl.fromTo(S + " #intro-mark .iris", {{ scale: 0, transformOrigin: "12px 12px" }}, {{ scale: 1, duration: 0.5, ease: "back.out(1.6)" }}, 0.5);
    tl.fromTo(S + " #intro-name", {{ opacity: 0, filter: "blur(10px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.5 }}, 0.8);
    tl.fromTo(S + " #intro-by", {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.4 }}, 1.6);
    tl.fromTo(S + " #intro-tag", {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.4 }}, 2.4);
    tl.fromTo(S + " #intro-meta", {{ opacity: 0, scale: 0.9 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "expo.out" }}, 4.4);
    tl.fromTo(S + " #intro-win", {{ opacity: 0, scale: 0.18, borderRadius: "40px" }}, {{ opacity: 1, scale: 1, borderRadius: "0px", duration: 0.9, ease: "power2.inOut" }}, 6.6);
    cam([{lb[0] - 40}, 250, {lb[2] + 80}, 460], 1.0, 0, 0);
    cam([{lb[0] - 40}, 250, {lb[2] + 80}, 460], 1.45, 7.6, 1.4, 0.5, 0.46);
""")

# 3 ------------------------------------------------------------ overview (10)
o = B["L02-overview"]
scene("overview", 10, f"""
    <div class="cam">{shot("overview", "L02-overview", 1, False)}</div>
    <div class="cap" id="overview-c1">Every site at <b class="acc">a glance</b></div>
    <div class="cap" id="overview-c2">Open and <b class="acc">overdue</b> cases first</div>
""", f"""
    blurIn();
    cam([382, 150, 1416, 600], 1.0, 0, 0);
    cam({o["kpis"]}, 1.32, 0.6, 1.4, 0.5, 0.3);
    cap(S + " #overview-c1", 1.2, 4.8);
    cam([1122, 760, 653, 260], 1.55, 5.0, 1.5, 0.5, 0.46);
    cap(S + " #overview-c2", 5.6, 9.7);
    cam([1122, 800, 653, 200], 1.75, 7.4, 1.8, 0.5, 0.46);
""")

# 4 ------------------------------------------------------------ upload (10)
u = B["L04-inspect"]
scene("upload", 10, f"""
    <div class="cam">{shot("upload", "L03-inspect-empty", 1, False)}{shot("upload", "L04-inspect", 2)}{shot("upload", "L05-analyzing", 3)}
      {CURSOR.format(id="upload")}</div>
    <div class="cap" id="upload-c1">A photo, a note, the <b class="acc">site</b></div>
""", f"""
    blurIn();
    tl.set(S + " .cursor", {{ x: 1300, y: 980, opacity: 0 }}, 0);
    cam([405, 181, 814, 611], 1.28, 0.3, 1.3);
    tl.to(S + " .cursor", {{ opacity: 1, duration: 0.2 }}, 0.8);
    move(mid({u["drop"]}), 0.9, 0.9);
    click(1.9);
    swap(S + " #upload-L04", 2.2);
    cap(S + " #upload-c1", 2.6, 7.4);
    move(mid({u["run"]}), 5.6, 1.0);
    click(7.2);
    tl.to(S + " .cursor", {{ opacity: 0, duration: 0.2 }}, 7.6);
    swap(S + " #upload-L05", 7.6);
    cam([750, 378, 420, 324], 1.5, 7.9, 1.4, 0.5, 0.45);
""")

# 5 ------------------------------------------------------------ how it works (13)
def node(i, x, title, sub, inner):
    return (f'<div class="node" id="how-n{i}" style="position:absolute;left:{x}px;top:330px;width:380px;min-height:330px;background:#fff;'
            f'border:2px solid #E2E7EE;border-radius:22px;padding:26px;box-shadow:0 18px 50px rgba(10,37,64,.12);opacity:0">'
            f'<div style="font:800 40px Inter;color:#0A2540;letter-spacing:-.02em">{title}</div>'
            f'<div style="font:600 28px/1.35 Inter;color:#6A768A;margin:8px 0 16px">{sub}</div>{inner}</div>')


chips = "".join(f'<span style="display:inline-block;font:700 28px Inter;color:#2156B8;background:#EAF1FE;border-radius:9px;padding:5px 12px;margin:0 6px 8px 0">{c}</span>'
                for c in ["person", "hard hat", "vest", "ladder", "forklift"])
arrows = "".join(f'<div class="arr" id="how-a{i}" style="position:absolute;left:{x}px;top:478px;width:60px;height:8px;border-radius:4px;background:#C9A94E;transform-origin:0 50%"></div>'
                 for i, x in enumerate([510, 960, 1410]))
scene("how", 13, f"""
    <div id="how-title" style="position:absolute;left:120px;top:120px;font:800 72px Inter;letter-spacing:-.03em;color:#0A2540;opacity:0">How Baseer reads a site</div>
    {node(0, 120, "Frames", "photo · video · live camera", '<div style="height:150px;border-radius:14px;background:url(assets/live/media/ladder.jpg) center 30%/cover"></div>')}
    {node(1, 570, "SAM 3.1", "segments what is in the scene", chips)}
    {node(2, 1020, "Muse", "reasons over it with the inspector's note", '<div style="font:600 28px/1.4 Inter;color:#344055;background:#F8F1DE;border-radius:12px;padding:12px 14px">“Checking ladder setup and PPE.”</div>')}
    {node(3, 1470, "Report", "Arabic + English, severity, frame, fix", '<div style="font:700 28px/1.5 Inter;color:#1F6B43">→ a case for every finding</div>')}
    {arrows}
    <div id="how-vision" style="position:absolute;left:120px;top:770px;width:1730px;opacity:0;font:700 32px Inter;color:#0A2540;
      background:#fff;border:3px dashed #C9A94E;border-radius:18px;padding:20px 28px">This recording: Muse's <span style="color:#8A6A1A">vision path</span>, frames straight to Muse</div>
""", """
    tl.fromTo(S + " #how-title", { opacity: 0, filter: "blur(10px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.4 }, 0.2);
    enter(S + " #how-n0", 1.0);
    tl.fromTo(S + " #how-a0", { scaleX: 0 }, { scaleX: 1, duration: 0.4, ease: "power2.out" }, 2.6);
    enter(S + " #how-n1", 2.9);
    tl.fromTo(S + " #how-n1 span", { opacity: 0, scale: 0.8 }, { opacity: 1, scale: 1, duration: 0.25, stagger: 0.12, ease: "back.out(1.6)" }, 3.4);
    tl.fromTo(S + " #how-a1", { scaleX: 0 }, { scaleX: 1, duration: 0.4, ease: "power2.out" }, 5.4);
    enter(S + " #how-n2", 5.7);
    tl.fromTo(S + " #how-a2", { scaleX: 0 }, { scaleX: 1, duration: 0.4, ease: "power2.out" }, 8.0);
    enter(S + " #how-n3", 8.3);
    enter(S + " #how-vision", 9.4, { opacity: 0, y: 30 });
""")

# 6 ------------------------------------------------------------ report (14)
r, f = B["L07-report"], B["L08-finding"]
scene("report", 14, f"""
    <div class="cam">{shot("report", "L07-report", 1, False)}{shot("report", "L08-finding", 2)}</div>
    <div class="cap" id="report-c1">Real Muse output: <b class="acc">3 high-severity</b> findings</div>
    <div class="cap" id="report-c2">Evidence frame, what it sees, the <b class="acc">fix</b></div>
""", f"""
    blurIn();
    cam([405, 120, 972, 360], 1.0, 0, 0);
    cam([405, 125, 972, 350], 1.6, 0.6, 1.4);
    cap(S + " #report-c1", 1.4, 6.8);
    cam([405, 360, 972, 110], 1.75, 3.6, 1.8, 0.5, 0.44);
    swap(S + " #report-L08", 7.0);
    cam({f["finding"]}, 1.0, 7.0, 0);
    cam({f["finding"]}, 1.7, 7.2, 1.3, 0.5, 0.42);
    cap(S + " #report-c2", 7.8, 13.7);
    cam([{f["action"][0]}, 110, {f["finding"][2]}, 180], 2.0, 10.4, 1.4, 0.5, 0.44);
""")

# 7 ------------------------------------------------------------ chat (12)
c = B["L10-chat"]
scene("chat", 12, f"""
    <div class="cam">{shot("chat", "L07-report", 1, False)}{shot("chat", "L10-chat", 2)}{shot("chat", "L11-chat-notice", 3)}
      {CURSOR.format(id="chat")}</div>
    <div class="cap left" id="chat-c1">Answers grounded only in this <b class="acc">evidence</b></div>
    <div class="cap left" id="chat-c2">It drafts the contractor <b class="acc">notice</b></div>
""", f"""
    blurIn();
    cam([1418, 121, 380, 640], 1.0, 0, 0);
    cam([1418, 121, 380, 640], 1.35, 0.2, 1.2, 0.68, 0.48);
    tl.set(S + " .cursor", {{ x: 1250, y: 700 }}, 0);
    cap(S + " #chat-c1", 0.6, 5.4);
    move(mid({c["chip1"]}), 1.0, 0.9);
    click(2.0);
    swap(S + " #chat-L10", 2.3);
    cam([1418, 300, 380, 600], 1.35, 3.0, 1.2, 0.68, 0.5);
    move(mid({c["chip2"]}), 5.0, 0.8);
    cam([1418, 121, 380, 640], 1.35, 5.0, 0.8, 0.68, 0.48);
    click(6.0);
    swap(S + " #chat-L11", 6.3);
    cam([1418, 560, 380, 520], 1.35, 6.7, 1.4, 0.68, 0.5);
    cap(S + " #chat-c2", 6.6, 11.7);
    cam([1418, 700, 380, 300], 1.65, 8.8, 2.2, 0.68, 0.5);
""")

# 8 ------------------------------------------------------------ chat_ar (7)
ca = B["L12-chat-ar"]
scene("chat_ar", 7, f"""
    <div class="cam">{shot("chat_ar", "L12-chat-ar", 1, False)}</div>
    <div class="cap right" id="chat_ar-c1"><b class="acc ar">بالعربية</b> too, right to left</div>
""", f"""
    blurIn();
    cam({ca["card"]}, 1.0, 0, 0);
    cam({ca["card"]}, 1.3, 0.2, 1.4, 0.3, 0.48);
    cap(S + " #chat_ar-c1", 0.9, 6.7);
    cam([122, 420, 380, 400], 1.45, 3.2, 1.8, 0.3, 0.48);
""")

# 9 ------------------------------------------------------------ board (11)
h = B["L14-hall-case"]
scene("board", 11, f"""
    <div class="cam">{shot("board", "L13-cases", 1, False)}{shot("board", "L14-hall-case", 2)}{CURSOR.format(id="board")}</div>
    <div class="cap" id="board-c1">Every finding opens a <b class="acc">case</b></div>
    <div class="cap" id="board-c2">Wrong after-photo? Baseer <b class="acc">refuses</b> to verify</div>
""", f"""
    blurIn();
    cam([405, 140, 1370, 440], 1.2, 0.3, 1.2, 0.5, 0.42);
    tl.set(S + " .cursor", {{ x: 900, y: 700 }}, 0);
    cap(S + " #board-c1", 0.4, 3.7);
    move([560, 330], 1.4, 0.9);
    click(2.6);
    swap(S + " #board-L14", 2.9);
    tl.to(S + " .cursor", {{ opacity: 0, duration: 0.2 }}, 3.0);
    cam([383, 236, 1016, 300], 1.0, 2.9, 0);
    cam([383, 560, 1016, 200], 1.55, 3.3, 1.4, 0.5, 0.42);
    cap(S + " #board-c2", 4.4, 10.7);
    cam({h["note"]}, 1.9, 6.4, 1.6, 0.5, 0.44);
""")

# 10 ----------------------------------------------------------- closure (15)
v = B["L15-hall-verified"]; m = B["L16-approve-modal"]
scene("closure", 15, f"""
    <div class="cam">{shot("closure", "L14-hall-case", 1, False)}{shot("closure", "L15-hall-verified", 2)}{shot("closure", "L16-approve-modal", 3)}
      {shot("closure", "L17-hall-closed", 4)}{CURSOR.format(id="closure")}</div>
    <div id="closure-ba" style="position:absolute;inset:0;z-index:30;background:rgba(243,245,248,.97);opacity:0">
      <div id="closure-b" style="position:absolute;left:170px;top:190px;width:760px">
        <div style="height:428px;border-radius:20px;background:url(assets/live/media/before.jpg) center/cover;box-shadow:0 24px 60px rgba(10,37,64,.25)"></div>
        <div style="font:800 40px Inter;color:#B02A1D;margin-top:18px">Before: no hard hat</div></div>
      <div id="closure-a" style="position:absolute;left:990px;top:190px;width:760px">
        <div style="height:428px;border-radius:20px;background:url(assets/live/media/after.jpg) center/cover;box-shadow:0 24px 60px rgba(10,37,64,.25)"></div>
        <div style="font:800 40px Inter;color:#1F6B43;margin-top:18px">After: same spot, hard hat on</div></div>
    </div>
    <div class="cap" id="closure-c1">Same spot, hard hat on: <b class="acc">resolution suggested</b></div>
    <div class="cap" id="closure-c2">Only a <b class="acc">person</b> approves the closure</div>
    <div class="cap" id="closure-c3">Signed into the <b class="acc">audit trail</b></div>
""", f"""
    cam([383, 560, 1016, 200], 1.55, 0, 0, 0.5, 0.42);
    tl.fromTo(S + " #closure-ba", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, 0.3);
    enter(S + " #closure-b", 0.5, {{ opacity: 0, x: -60 }});
    enter(S + " #closure-a", 1.4, {{ opacity: 0, x: 60 }});
    tl.to(S + " #closure-ba", {{ opacity: 0, filter: "blur(8px)", duration: 0.35, ease: "power3.in" }}, 3.5);
    swap(S + " #closure-L15", 3.7);
    cam([383, 520, 1016, 200], 1.55, 3.7, 0.8, 0.5, 0.42);
    cap(S + " #closure-c1", 4.0, 7.3);
    tl.set(S + " .cursor", {{ x: 900, y: 760 }}, 0);
    move(mid({v["approve"]}), 5.4, 0.9);
    click(6.7);
    swap(S + " #closure-L16", 7.0);
    cam({m["card"]}, 1.6, 7.0, 0.9, 0.5, 0.45);
    cap(S + " #closure-c2", 7.5, 11.2);
    move(mid({m["ok"]}), 7.9, 0.9);
    click(9.3);
    tl.to(S + " .cursor", {{ opacity: 0, duration: 0.2 }}, 9.6);
    swap(S + " #closure-L17", 9.6);
    cam([383, 505, 1016, 510], 1.45, 9.7, 1.2, 0.5, 0.46);
    cap(S + " #closure-c3", 11.5, 14.8);
""")

# 11 ----------------------------------------------------------- live (18)
lv = B["L19-live-alerts"]; st = lv["stage"]
scene("live", 18, f"""
    <div class="cam">{shot("live", "L18-live-idle", 1, False)}
      <div id="live-on" style="position:absolute;inset:0;z-index:2;opacity:0">
        {shot("live", "L19-live-alerts", 1, False)}
        <video id="live-feed" class="clip" data-start="1.9" data-duration="10.6" data-track-index="2" muted playsinline
          src="assets/live-forklift.mp4" style="position:absolute;left:{st[0] + 3}px;top:{st[1] + 3}px;width:{st[2] - 6}px;height:{st[3] - 6}px;
          object-fit:cover;border-radius:12px;z-index:2"></video>
        <div style="position:absolute;inset:0;z-index:3;background:url(assets/live/L19-live-alerts.jpg) 0 0/1920px 1080px;clip-path:inset(176px 1392px 875px 416px round 7px)"></div>
        <div style="position:absolute;inset:0;z-index:3;background:url(assets/shots/c12-live.jpg) 0 0/1920px 1080px;clip-path:inset(723px 1345px 315px 403px round 9px)"></div>
        <div id="live-cover1" style="position:absolute;left:1280px;top:198px;width:500px;height:80px;background:#fff;z-index:4"></div>
        <div id="live-cover2" style="position:absolute;left:1280px;top:278px;width:500px;height:80px;background:#fff;z-index:4"></div>
      </div>
      {shot("live", "L20-live-report", 5)}
      {CURSOR.format(id="live")}</div>
    <div class="cap" id="live-c1">Live camera: analyzed <b class="acc">as it streams</b></div>
    <div class="cap" id="live-c2">An alert the <b class="acc">first time</b> each violation appears</div>
    <div class="cap" id="live-c3">Finish: the <b class="acc">full report</b>, same pipeline</div>
""", f"""
    blurIn();
    tl.set(S + " .cursor", {{ x: 900, y: 900 }}, 0);
    cap(S + " #live-c1", 0.3, 3.8);
    move(mid({B["L18-live-idle"]["cam"]}), 0.4, 0.9);
    click(1.5);
    swap(S + " #live-on", 1.8);
    cam([405, 165, 1370, 560], 1.3, 2.3, 1.3, 0.5, 0.42);
    tl.to(S + " #live-cover1", {{ opacity: 0, duration: 0.25 }}, 4.4);
    tl.to(S + " #live-cover2", {{ opacity: 0, duration: 0.25 }}, 6.6);
    cap(S + " #live-c2", 4.2, 11.6);
    move(mid({lv["finish"]}), 10.6, 1.0);
    click(12.1);
    tl.to(S + " .cursor", {{ opacity: 0, duration: 0.2 }}, 12.4);
    swap(S + " #live-L20", 12.4);
    cam([405, 120, 972, 360], 1.0, 12.4, 0);
    cam([405, 125, 972, 350], 1.55, 12.6, 1.4);
    cap(S + " #live-c3", 12.9, 17.8);
""")

# 12 ----------------------------------------------------------- oversight (13)
scene("oversight", 13, f"""
    <div class="cam">{shot("oversight", "L21-cases-overdue", 1, False)}{shot("oversight", "L22-history", 2)}{shot("oversight", "L23-audit", 3)}</div>
    <div class="cap" id="oversight-c1">High severity: due in <b class="acc">one day</b></div>
    <div class="cap" id="oversight-c2">Every inspection, <b class="acc">searchable</b></div>
    <div class="cap" id="oversight-c3">An <b class="acc">append-only</b> audit log</div>
""", """
    blurIn();
    cam([405, 120, 1370, 300], 1.3, 0.3, 1.2, 0.5, 0.4);
    cap(S + " #oversight-c1", 0.6, 4.1);
    swap(S + " #oversight-L22", 4.3);
    cam([405, 120, 1370, 560], 1.18, 4.3, 0.9, 0.5, 0.44);
    cap(S + " #oversight-c2", 4.6, 8.1);
    swap(S + " #oversight-L23", 8.3);
    cam([405, 120, 1370, 560], 1.25, 8.3, 0.9, 0.5, 0.44);
    cap(S + " #oversight-c3", 8.6, 12.8);
    cam([405, 480, 1370, 520], 1.25, 10.0, 1.8, 0.5, 0.44);
""")

# 13 ----------------------------------------------------------- pdf + users (9)
scene("pdf", 9, f"""
    <div class="cam">
      <div id="pdf-sheet" style="position:absolute;left:300px;top:60px;width:700px;height:990px;background:#fff url(assets/live/pdf/hall-1.png) center/contain no-repeat;
        box-shadow:0 30px 80px rgba(10,37,64,.3);border-radius:6px;opacity:0"></div>
      <div id="pdf-note" style="position:absolute;left:1100px;top:330px;width:640px;opacity:0">
        <div style="font:800 64px/1.1 Inter;color:#0A2540;letter-spacing:-.02em">Arabic PDF report</div>
        <div style="font:600 32px/1.4 Inter;color:#6A768A;margin-top:16px">Findings, verification and the full audit trail, server-rendered right to left.</div></div>
      {shot("pdf", "L25-users", 5)}
    </div>
    <div class="cap" id="pdf-c1">Roles for every <b class="acc">team</b></div>
""", f"""
    enter(S + " #pdf-sheet", 0.2, {{ opacity: 0, y: 120, rotation: -3 }}, 0.9);
    enter(S + " #pdf-note", 0.8, {{ opacity: 0, x: 40 }});
    cam([300, 760, 700, 300], 1.0, 0, 0);
    cam([300, 700, 700, 330], 1.6, 2.4, 1.4, 0.36, 0.5);
    swap(S + " #pdf-L25", 5.0);
    cam([0, 0, 1920, 1080], 1.0, 5.0, 0);
    cam({B["L25-users"]["rows"]}, 1.45, 5.2, 1.2, 0.5, 0.44);
    cap(S + " #pdf-c1", 5.6, 8.8);
""")

# 14 ----------------------------------------------------------- mobile (8)
phones = "".join(
    f'<div class="phone" id="mobile-ph{i}" style="position:absolute;left:{x}px;top:{y}px;width:300px;height:640px;border-radius:48px;background:#0E1726;'
    f'padding:12px;box-shadow:0 40px 90px rgba(0,0,0,.45);opacity:0"><div style="width:100%;height:100%;border-radius:38px;'
    f'background:url(assets/live/{img}.jpg) top center/cover"></div></div>'
    for i, (x, y, img) in enumerate([(530, 260, "M01-mobile-overview"), (810, 210, "M02-mobile-report"), (1090, 260, "M03-mobile-report-ar")]))
scene("mobile", 8, f"""
    <div class="cam">{shot("mobile", "L26-overview-ar-dark", 1, False)}</div>
    <div id="mobile-world" style="position:absolute;inset:0;z-index:10;clip-path:circle(0px at 51px 46px)"><div class="navy"></div><div class="grid"></div>{phones}</div>
    <div class="cap" id="mobile-c1">Light or dark, on <b class="acc">any phone</b></div>
""", """
    blurIn();
    tl.fromTo(S + " .cam", { scale: 1.0 }, { scale: 1.04, duration: 2.4, ease: "none" }, 0);
    tl.to(S + " #mobile-world", { clipPath: "circle(2300px at 51px 46px)", duration: 0.7, ease: "power2.in" }, 2.0);
    enter(S + " #mobile-ph0", 2.6, { opacity: 0, y: 200 });
    enter(S + " #mobile-ph1", 2.9, { opacity: 0, y: 200 });
    enter(S + " #mobile-ph2", 3.2, { opacity: 0, y: 200 });
    cap(S + " #mobile-c1", 3.9, 7.8);
""")

# 15 ----------------------------------------------------------- eval (11)
def stat(i, big, label):
    return (f'<div class="stat" id="eval-s{i}" style="position:absolute;left:160px;top:330px;opacity:0">'
            f'<div style="font:900 230px/1 Inter;letter-spacing:-.05em;color:#0A2540">{big}</div>'
            f'<div style="font:700 48px Inter;color:#8A6A1A;margin-top:18px">{label}</div></div>')


scene("eval", 11, f"""
    <div id="eval-head" style="position:absolute;left:160px;top:130px;opacity:0">
      <div style="font:800 64px Inter;letter-spacing:-.02em;color:#0A2540">Measured, not claimed</div>
      <div style="font:600 32px Inter;color:#6A768A;margin-top:10px">Fixed 24-scene benchmark · Muse Spark 1.3 · prompt v1.3</div></div>
    {stat(0, "6 of 8", "real hazards caught")}
    {stat(1, "16 of 24", "scenes matched exactly")}
    {stat(2, "0.60", "precision on the SAM 3.1 path")}
    <div id="eval-foot" style="position:absolute;left:160px;top:860px;opacity:0;font:700 36px Inter;color:#0A2540">
      Every miss is published in the project README.</div>
""", """
    tl.fromTo(S + " #eval-head", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.4 }, 0.3);
    const show = (i, t, out) => {
      tl.fromTo(S + ` #eval-s${i}`, { opacity: 0, filter: "blur(12px)", scale: 0.96 }, { opacity: 1, filter: "blur(0px)", scale: 1, duration: 0.35, ease: "expo.out" }, t);
      if (out) tl.to(S + ` #eval-s${i}`, { opacity: 0, filter: "blur(10px)", duration: 0.2, ease: "power3.in" }, out);
    };
    show(0, 1.3, 4.1); show(1, 4.3, 7.1); show(2, 7.3);
    tl.fromTo(S + " #eval-foot", { opacity: 0 }, { opacity: 1, duration: 0.4 }, 8.4);
""")

# 16 ----------------------------------------------------------- end (8)
scene("end", 8, f"""
    <div class="navy"></div><div class="grid"></div>
    <div class="mark" id="end-mark" style="left:810px;top:180px">{MARK_SVG}</div>
    <div id="end-name" style="position:absolute;left:0;right:0;top:520px;text-align:center;color:#fff;font:800 92px/1.1 Inter;letter-spacing:-.02em">
      Baseer <span style="color:#C9A94E">·</span> <span class="ar">بصير</span></div>
    <div id="end-by" style="position:absolute;left:0;right:0;top:636px;text-align:center;color:#E0C26A;font:700 42px Inter">by Veebase</div>
    <div class="cap" id="end-c1" style="bottom:250px;background:transparent;box-shadow:none;font-size:46px;font-weight:600">From walkthrough to <b class="acc">verified closure</b></div>
    <div id="end-foot" style="position:absolute;left:0;right:0;bottom:130px;text-align:center;font:500 28px Inter;color:#AFC0D3;opacity:0">
      Built for the Meta Global AI Developer Hackathon · Recorded live on Muse Spark 1.3</div>
""", """
    tl.fromTo(S + " #end-mark", { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.8, ease: "expo.out" }, 0.2);
    tl.fromTo(S + " #end-mark .iris", { scale: 0, transformOrigin: "12px 12px" }, { scale: 1, duration: 0.5, ease: "back.out(1.6)" }, 0.6);
    tl.fromTo(S + " #end-name", { opacity: 0, filter: "blur(10px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.5 }, 0.9);
    tl.fromTo(S + " #end-by", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.4 }, 1.4);
    cap(S + " #end-c1", 2.0);
    tl.fromTo(S + " #end-foot", { opacity: 0 }, { opacity: 1, duration: 0.4 }, 3.0);
""")

# ------------------------------------------------------------- index + audio
starts, t = {}, 0.0
for sid, dur in scenes:
    starts[sid] = round(t, 3)
    t += dur
TOTAL = round(t, 3)
VO = {"problem": 0.4, "intro": 0.6, "overview": 0.5, "upload": 0.6, "how": 0.8, "report": 0.5, "chat": 0.5, "chat_ar": 1.0,
      "board": 0.5, "closure": 0.8, "live": 0.4, "oversight": 0.6, "pdf": 0.6, "mobile": 0.8, "eval": 0.8, "end": 0.8}
CLICKS = {"upload": [1.9, 7.2], "chat": [2.0, 6.0], "board": [2.6], "closure": [6.7, 9.3], "live": [1.5, 12.1]}


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                          str(V / path)]).decode().strip())


hosts = [f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{starts[sid]}" '
         f'data-duration="{d}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>'
         for sid, d in scenes]
for sid, off in VO.items():
    src = f"assets/voice/norm/{sid}.wav"
    vd = dur(src)
    sd = dict(scenes)[sid]
    assert off + vd < sd, f"voice for {sid} ({vd:.2f}s) does not fit its {sd}s scene"
    hosts.append(f'      <audio id="vo-{sid.replace("_", "-")}" class="clip" src="{src}" data-start="{round(starts[sid] + off, 3)}" '
                 f'data-duration="{round(vd, 3)}" data-track-index="10" data-volume="0.8"></audio>')
hosts.append(f'      <audio id="bgm" class="clip" src="assets/bgm/bed-3min.wav" data-timeline-role="music" data-start="0" '
             f'data-duration="{TOTAL}" data-track-index="11" data-volume="0.12" data-fade-in="0.4" data-fade-out="1.5"></audio>')
n = 0
for sid, ts in CLICKS.items():
    for c_ in ts:
        src = "assets/sfx/click-a.mp3" if n % 2 == 0 else "assets/sfx/click-b.wav"
        hosts.append(f'      <audio id="click-{n + 1:02d}" class="clip" src="{src}" data-start="{round(starts[sid] + c_ + 0.04, 3)}" '
                     f'data-duration="0.366" data-track-index="12" data-volume="0.7"></audio>')
        n += 1
nl = "\n"
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
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
{nl.join(hosts)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
""")
print("scenes", len(scenes), "total", TOTAL, "s")
