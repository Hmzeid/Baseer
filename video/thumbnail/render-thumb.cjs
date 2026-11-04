// Render thumbnail.html to a 1280x720 PNG (YouTube thumbnail).
const puppeteer = require(process.env.HF + "/node_modules/puppeteer-core");
const path = require("path");
const CHROME = process.env.HOME + "/.cache/puppeteer/chrome/mac_arm-135.0.7049.95/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing";
(async () => {
  const b = await puppeteer.launch({ executablePath: CHROME, headless: "new", args: ["--allow-file-access-from-files"] });
  const p = await b.newPage();
  await p.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1 });
  await p.goto("file://" + path.resolve(__dirname, "thumbnail.html"), { waitUntil: "networkidle0" });
  await p.evaluate(() => document.fonts.ready);
  await p.screenshot({ path: process.argv[2], type: "png" });
  await b.close();
})();
