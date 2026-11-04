// Capture the real Baseer UI for the walkthrough video (1920x1080 @2x) + element boxes.
const puppeteer = require(process.env.HF + "/node_modules/puppeteer-core");
const fs = require("fs");
const OUT = process.argv[2], BASE = "http://127.0.0.1:8011/", REPO = "/Users/husseinabdelwahab/Ai/Baseer";
const CHROME = process.env.HOME + "/.cache/puppeteer/chrome/mac_arm-135.0.7049.95/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const boxes = {};
(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new",
    args: ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", `--use-file-for-fake-video-capture=${process.env.CAM}`] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 2 });
  let holdUpload = false;
  await page.setRequestInterception(true);
  page.on("request", async (req) => {
    if (holdUpload && req.method() === "POST" && req.url().endsWith("/inspections")) { await sleep(4200); }
    req.continue();
  });
  const shot = async (name, sels = {}) => {
    await sleep(450);
    const b = {};
    for (const [k, sel] of Object.entries(sels)) {
      b[k] = await page.$eval(sel, (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }).catch(() => null);
    }
    boxes[name] = b;
    await page.screenshot({ path: `${OUT}/${name}.jpg`, type: "jpeg", quality: 90 });
    console.log("shot", name, JSON.stringify(b));
  };
  const setPrefs = (lang, theme) => page.evaluate((l, t) => { localStorage.setItem("baseer_lang", JSON.stringify(l)); localStorage.setItem("baseer_theme", t); }, lang, theme);
  await page.goto(BASE, { waitUntil: "networkidle0" });
  await page.evaluate(() => localStorage.clear());
  await setPrefs("en", "light"); await page.reload({ waitUntil: "networkidle0" });
  await sleep(600);
  await shot("c01-login", { btn: "#loginBtn", user: "#loginUser" });
  await page.type("#loginUser", "layla"); await page.type("#loginPass", "demo-layla-2026");
  await page.click("#loginBtn"); await page.waitForFunction(() => !document.body.classList.contains("gated")); await sleep(1200);
  await shot("c13-overview", { overdue: '.kpi[href="#/cases"]', kpis: ".kpis", aging: "#agingList", trend: "#trendChart" });
  // inspection
  await page.goto(BASE + "#/inspect"); await sleep(500);
  await shot("c02a-inspect-empty", { drop: "#dropZone" });
  const inp = await page.$("#files");
  await inp.uploadFile(`${REPO}/demo/photos/construction-workers-site_12314551.jpg`, `${REPO}/demo/photos/workers-rebar_32141074.jpg`);
  await sleep(500);
  await page.type("#notes", "Level 4 scaffold: two workers on the top lift, one not tied off. Rebar stacked near the slab edge.");
  await page.type("#ctx", "construction");
  await shot("c02-inspect", { drop: "#dropZone", thumbs: "#thumbs", notes: "#notes", ctx: "#ctx", run: "#runBtn" });
  holdUpload = true;
  await page.click("#runBtn"); await sleep(1700);
  await shot("c03-analyzing", { card: ".analyzing-card" });
  await sleep(1300);
  await shot("c03b-analyzing", { card: ".analyzing-card" });
  await page.waitForFunction(() => location.hash.startsWith("#/report/"), { timeout: 30000 });
  holdUpload = false;
  await page.waitForSelector(".finding .fthumb"); await sleep(800);
  const rid = await page.evaluate(() => location.hash.split("/")[2]);
  await shot("c04-report", { strip: "#sevStrip", summary: ".summary", pdf: "#pdfBtn", evidence: "#rEvidence", chips: "#chatChips" });
  await page.evaluate(() => window.scrollTo(0, document.getElementById("finding-0").getBoundingClientRect().top + scrollY - 24)); await sleep(500);
  await shot("c05-finding", { finding: "#finding-0 .finding-body", action: "#finding-0 .action-box", thumb: "#finding-0 .fthumb", case: "#finding-0 .case" });
  // chat
  await page.evaluate(() => window.scrollTo(0, 0)); await sleep(300);
  await page.click("#chatChips button"); await page.waitForFunction(() => !document.getElementById("typing")); await sleep(300);
  await shot("c06-chat", { chip1: "#chatChips button:nth-child(1)", chip2: "#chatChips button:nth-child(2)", log: "#chatLog", card: ".chat-card" });
  await page.click("#chatChips button:nth-child(2)"); await page.waitForFunction(() => !document.getElementById("typing")); await sleep(300);
  await shot("c06b-chat", { log: "#chatLog", card: ".chat-card" });
  // case lifecycle on finding 0
  const scrollCase = () => page.evaluate(() => window.scrollTo(0, document.getElementById("finding-0").getBoundingClientRect().top + scrollY - 24));
  await scrollCase(); await sleep(400);
  await page.$eval("#asg-0", (e) => (e.value = "")); 
  await shot("c07-case-open", { input: "#asg-0", assign: '[data-case="assign"][data-i="0"]', stepper: "#finding-0 .stepper", case: "#finding-0 .case" });
  await page.type("#asg-0", "Gulf Scaffolding Co."); await sleep(200);
  await shot("c07b-case-typed", { input: "#asg-0", assign: '[data-case="assign"][data-i="0"]' });
  await page.click('[data-case="assign"][data-i="0"]'); await sleep(900); await scrollCase();
  await shot("c08-assigned", { evidence: '[data-case="evidence"][data-i="0"]', stepper: "#finding-0 .stepper", case: "#finding-0 .case" });
  const vf = await page.$("#ver-0"); await vf.uploadFile(`${REPO}/demo/photos/workers-rebar_32141074.jpg`); await sleep(1200); await scrollCase();
  await shot("c09-verified", { approve: '[data-case="approve"][data-i="0"]', note: "#finding-0 .verify-note", stepper: "#finding-0 .stepper", case: "#finding-0 .case" });
  await page.click('[data-case="approve"][data-i="0"]'); await sleep(500);
  await shot("c10-modal", { ok: "#modalOk", card: ".modal-card" });
  await page.click("#modalOk"); await sleep(1000); await scrollCase();
  await shot("c11-closed", { stepper: "#finding-0 .stepper", status: "#finding-0 .status", case: "#finding-0 .case" });
  // live camera with real footage
  await page.goto(BASE + "#/live"); await sleep(600);
  await page.type("#liveCtx", "factory");
  await shot("c12a-live-idle", { start: "#liveStart", cam: "#liveCam" });
  await page.click("#liveCam"); await sleep(7600);
  await shot("c12-live", { cam: "#liveCam", alerts: "#liveAlerts", finish: "#liveFinish", stage: "#stage", stats: ".live-stats" });
  await page.click("#liveFinish"); await page.waitForFunction(() => location.hash.startsWith("#/report/")); await sleep(1500);
  await shot("c12b-live-report", { evidence: "#rEvidence" });
  // records
  await page.goto(BASE + "#/cases?status=overdue"); await sleep(900);
  await shot("c14-cases", { tabs: "#caseTabs", rows: "#caseRows" });
  await page.goto(BASE + "#/inspections"); await sleep(900);
  await shot("c18-history", { rows: "#histRows" });
  await page.goto(BASE + "#/audit"); await sleep(900);
  await shot("c15-audit", { rows: "#auditRows" });
  await page.goto(BASE + "#/overview"); await sleep(1200);
  await shot("c13b-overview", { overdue: '.kpi[href="#/cases"]', kpis: ".kpis" });
  // Arabic + dark
  await setPrefs("ar", "light"); await page.goto(BASE + "#/report/" + rid); await page.reload({ waitUntil: "networkidle0" }); await sleep(1500);
  await shot("c16-report-ar", { strip: "#sevStrip", summary: ".summary" });
  await setPrefs("ar", "dark"); await page.goto(BASE + "#/overview"); await page.reload({ waitUntil: "networkidle0" }); await sleep(1500);
  await shot("c17-overview-ar-dark", { kpis: ".kpis" });
  await setPrefs("en", "dark"); await page.goto(BASE + "#/report/" + rid); await page.reload({ waitUntil: "networkidle0" }); await sleep(1500);
  await shot("c19-report-dark", { strip: "#sevStrip" });
  fs.writeFileSync(`${OUT}/../boxes.json`, JSON.stringify(boxes, null, 1));
  await browser.close();
})().catch((e) => { console.error("CRASH", e); process.exit(1); });
