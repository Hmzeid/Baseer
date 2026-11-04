// Capture the LIVE-mode Baseer UI (real Meta outputs) for the 3-minute video.
const puppeteer = require(process.env.HF + "/node_modules/puppeteer-core");
const fs = require("fs");
const OUT = process.argv[2], BASE = "http://127.0.0.1:8013/", REPO = "/Users/husseinabdelwahab/Ai/Baseer", MEDIA = process.env.MEDIA;
const HALL = process.env.HALL;  // machine-hall inspection id (staged)
const CHROME = process.env.HOME + "/.cache/puppeteer/chrome/mac_arm-135.0.7049.95/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const boxes = {}, meta = {};
(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new",
    args: ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", `--use-file-for-fake-video-capture=${process.env.CAM}`] });
  const page = await browser.newPage();
  page.setDefaultTimeout(180000);
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 2 });
  const shot = async (name, sels = {}) => {
    await sleep(500);
    const b = {};
    for (const [k, sel] of Object.entries(sels)) {
      b[k] = await page.$eval(sel, (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }).catch(() => null);
    }
    boxes[name] = b;
    await page.screenshot({ path: `${OUT}/${name}.jpg`, type: "jpeg", quality: 90 });
    console.log("shot", name, JSON.stringify(b));
  };
  const prefs = (l, t) => page.evaluate((l, t) => { localStorage.setItem("baseer_lang", JSON.stringify(l)); localStorage.setItem("baseer_theme", t); }, l, t);
  const login = async (u, p) => {
    await page.evaluate(() => localStorage.removeItem("baseer_session"));
    await page.goto(BASE, { waitUntil: "networkidle0" }); await page.reload({ waitUntil: "networkidle0" }); await sleep(500);
    await page.type("#loginUser", u); await page.type("#loginPass", p);
    await page.click("#loginBtn"); await page.waitForFunction(() => !document.body.classList.contains("gated")); await sleep(1200);
  };
  const toFinding = (i) => page.evaluate((i) => window.scrollTo(0, document.getElementById("finding-" + i).getBoundingClientRect().top + scrollY - 24), i);
  const waitChat = async () => { await sleep(400); await page.waitForFunction(() => !document.getElementById("typing"), { timeout: 120000 }); await sleep(400); };
  await page.goto(BASE, { waitUntil: "networkidle0" });
  await page.evaluate(() => localStorage.clear());
  await prefs("en", "light"); await page.reload({ waitUntil: "networkidle0" }); await sleep(600);
  await shot("L01-login", { btn: "#loginBtn" });
  await page.type("#loginUser", "layla"); await page.type("#loginPass", "demo-layla-2026");
  await page.click("#loginBtn"); await page.waitForFunction(() => !document.body.classList.contains("gated")); await sleep(1500);
  await shot("L02-overview", { kpis: ".kpis", overdue: '.kpi[href="#/cases"]', aging: "#agingList", trend: "#trendChart", donut: "#sevDonut" });
  // hero inspection: real ladder photo
  await page.goto(BASE + "#/inspect"); await sleep(600);
  await shot("L03-inspect-empty", { drop: "#dropZone" });
  await (await page.$("#files")).uploadFile(`${REPO}/demo/photos/worker-climbing-ladder_38510725.jpg`);
  await sleep(500);
  await page.type("#notes", "Facade repair, block C. A worker is climbing the ladder to the upper level; checking ladder setup and PPE.");
  await page.type("#ctx", "construction");
  await shot("L04-inspect", { drop: "#dropZone", thumbs: "#thumbs", notes: "#notes", ctx: "#ctx", run: "#runBtn" });
  const t0 = Date.now();
  await page.click("#runBtn"); await sleep(1600);
  await shot("L05-analyzing", { card: ".analyzing-card" });
  await sleep(4000);
  await shot("L06-analyzing", { card: ".analyzing-card" });
  await page.waitForFunction(() => location.hash.startsWith("#/report/"), { timeout: 180000 });
  meta.hero_seconds = (Date.now() - t0) / 1000;
  await sleep(2500);
  const rid = await page.evaluate(() => location.hash.split("/")[2]); meta.hero = rid;
  meta.hero_findings = await page.$$eval(".finding h3", (h) => h.map((x) => x.textContent));
  await shot("L07-report", { strip: "#sevStrip", summary: ".summary", pdf: "#pdfBtn", evidence: "#rEvidence", chips: "#chatChips", badge: "#pipeBadge" });
  await toFinding(0); await sleep(500);
  await shot("L08-finding", { finding: "#finding-0 .finding-body", action: "#finding-0 .action-box", thumb: "#finding-0 .fthumb", case: "#finding-0 .case" });
  await page.evaluate(() => window.scrollTo(0, 0)); await sleep(300);
  await page.click("#rEvidence img"); await sleep(700);
  await shot("L09-lightbox", {});
  await page.click("#lightbox"); await sleep(400);
  // chat (real Muse answers)
  await page.click("#chatChips button"); await waitChat();
  await shot("L10-chat", { chip1: "#chatChips button:nth-child(1)", chip2: "#chatChips button:nth-child(2)", log: "#chatLog", card: ".chat-card" });
  await page.click("#chatChips button:nth-child(2)"); await waitChat();
  await shot("L11-chat-notice", { log: "#chatLog", card: ".chat-card" });
  meta.chat = await page.$$eval(".msg.bot", (m) => m.map((x) => x.textContent.slice(0, 300)));
  // Arabic question on the same report
  await prefs("ar", "light"); await page.reload({ waitUntil: "networkidle0" }); await sleep(1500);
  await page.click("#chatChips button:nth-child(3)"); await waitChat();
  await shot("L12-chat-ar", { log: "#chatLog", card: ".chat-card", chip3: "#chatChips button:nth-child(3)" });
  await shot("L12b-report-ar", { strip: "#sevStrip", summary: ".summary" });
  await prefs("en", "light"); await page.reload({ waitUntil: "networkidle0" }); await sleep(1200);
  // cases board -> machine-hall case -> real before/after verification -> approval
  await page.goto(BASE + "#/cases"); await sleep(1200);
  await shot("L13-cases", { tabs: "#caseTabs", rows: "#caseRows", first: "#caseRows tr" });
  await page.goto(BASE + "#/report/" + HALL + "?f=0"); await sleep(2500);
  await toFinding(0); await sleep(600);
  await shot("L14-hall-case", { finding: "#finding-0 .finding-body", case: "#finding-0 .case", evidence: '[data-case="evidence"][data-i="0"]', note: "#finding-0 .verify-note" });
  await (await page.$("#ver-0")).uploadFile(`${MEDIA}/machine-hall-after.jpg`);
  await page.waitForFunction(() => { const n = document.querySelector("#finding-0 .verify-note"); return n && !/scaffold/.test(n.textContent); }, { timeout: 180000 });
  await sleep(800); await toFinding(0); await sleep(500);
  meta.verify = await page.$eval("#finding-0 .verify-note", (e) => e.textContent);
  meta.verify_ok = await page.$eval('[data-case="approve"][data-i="0"]', (b) => !b.disabled).catch(() => false);
  await shot("L15-hall-verified", { approve: '[data-case="approve"][data-i="0"]', note: "#finding-0 .verify-note", stepper: "#finding-0 .stepper", case: "#finding-0 .case" });
  if (meta.verify_ok) {
    await page.click('[data-case="approve"][data-i="0"]'); await sleep(600);
    await shot("L16-approve-modal", { ok: "#modalOk", card: ".modal-card" });
    await page.click("#modalOk"); await sleep(1500); await toFinding(0); await sleep(500);
    await shot("L17-hall-closed", { stepper: "#finding-0 .stepper", status: "#finding-0 .status", case: "#finding-0 .case" });
  }
  // live camera on the real forklift footage
  await page.goto(BASE + "#/live"); await sleep(800);
  await page.type("#liveCtx", "factory");
  await shot("L18-live-idle", { start: "#liveStart", cam: "#liveCam" });
  await page.click("#liveCam"); await sleep(7200);
  await page.click("#liveCam");  // camera off: no more snapshots, pending frames finish
  await page.waitForFunction(() => document.querySelectorAll("#liveAlerts .alert").length > 0, { timeout: 180000 }).catch(() => {});
  await sleep(8000);
  meta.live_alerts = await page.$$eval("#liveAlerts .alert b", (b) => b.map((x) => x.textContent));
  await shot("L19-live-alerts", { alerts: "#liveAlerts", finish: "#liveFinish", stage: "#stage", stats: ".live-stats", cam: "#liveCam" });
  await page.click("#liveFinish");
  await page.waitForFunction(() => location.hash.startsWith("#/report/"), { timeout: 240000 }); await sleep(2500);
  meta.live_report = await page.evaluate(() => location.hash.split("/")[2]);
  meta.live_findings = await page.$$eval(".finding h3", (h) => h.map((x) => x.textContent));
  await shot("L20-live-report", { strip: "#sevStrip", summary: ".summary", evidence: "#rEvidence" });
  // records
  await page.goto(BASE + "#/cases?status=overdue"); await sleep(1200);
  await shot("L21-cases-overdue", { tabs: "#caseTabs", rows: "#caseRows" });
  await page.goto(BASE + "#/inspections"); await sleep(1200);
  await shot("L22-history", { rows: "#histRows" });
  await page.goto(BASE + "#/audit"); await sleep(1200);
  await shot("L23-audit", { rows: "#auditRows" });
  await page.goto(BASE + "#/overview"); await sleep(1500);
  await shot("L24-overview-after", { kpis: ".kpis", overdue: '.kpi[href="#/cases"]', aging: "#agingList", recent: "#recentList" });
  // admin: users
  await login("admin", "demo-admin-2026");
  await page.goto(BASE + "#/users"); await sleep(1200);
  await shot("L25-users", { rows: "#userRows", form: "#newUserForm" });
  // Arabic dark + mobile
  await prefs("ar", "dark"); await page.goto(BASE + "#/overview"); await page.reload({ waitUntil: "networkidle0" }); await sleep(1500);
  await shot("L26-overview-ar-dark", { kpis: ".kpis" });
  await page.goto(BASE + "#/report/" + rid); await sleep(2500);
  await shot("L27-report-ar-dark", { strip: "#sevStrip" });
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
  await prefs("en", "light");
  await page.goto(BASE + "#/overview"); await page.reload({ waitUntil: "networkidle0" }); await sleep(1500);
  await page.screenshot({ path: `${OUT}/M01-mobile-overview.jpg`, type: "jpeg", quality: 90 });
  await page.goto(BASE + "#/report/" + rid); await sleep(2500);
  await page.screenshot({ path: `${OUT}/M02-mobile-report.jpg`, type: "jpeg", quality: 90 });
  await prefs("ar", "light"); await page.reload({ waitUntil: "networkidle0" }); await sleep(2000);
  await page.screenshot({ path: `${OUT}/M03-mobile-report-ar.jpg`, type: "jpeg", quality: 90 });
  fs.writeFileSync(`${OUT}/../live-boxes.json`, JSON.stringify(boxes, null, 1));
  fs.writeFileSync(`${OUT}/../live-meta.json`, JSON.stringify(meta, null, 1));
  console.log("META", JSON.stringify(meta).slice(0, 1500));
  await browser.close();
})().catch((e) => { console.error("CRASH", e); process.exit(1); });
