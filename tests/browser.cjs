const { chromium } = require("playwright-core");
const { spawn } = require("child_process");
const fs = require("fs");
const assert = require("assert");
const childEnv = { ...process.env };
delete childEnv.TESLAFI_API_TOKEN;
const server = spawn(
  "python",
  ["-m", "teslafi_connect", "--serve", "--port", "8768"],
  { env: childEnv, stdio: "ignore" },
);
process.on("exit", () => server.kill());
(async () => {
  await new Promise((resolve, reject) => {
    let attempts = 0;
    const timer = setInterval(async () => {
      try {
        await fetch("http://127.0.0.1:8768");
        clearInterval(timer);
        resolve();
      } catch {
        if (++attempts > 50) {
          clearInterval(timer);
          reject(Error("Server failed to start"));
        }
      }
    }, 100);
  });
  const b = await chromium.launch({
    ...(process.env.CHROMIUM_PATH
      ? { executablePath: process.env.CHROMIUM_PATH }
      : {}),
    args: ["--no-sandbox"],
  });
  const evidence = [];
  for (const width of [390, 768, 1440]) {
    for (const [name, port] of [["teslafi-connect", 8768]]) {
      const p = await b.newPage({
        viewport: { width, height: 1000 },
        acceptDownloads: true,
      });
      await p.route("**/api/status*", (route) =>
        route.fulfill({
          status: 400,
          contentType: "application/json",
          body: JSON.stringify({
            error:
              "Set TESLAFI_API_TOKEN locally before requesting the feed; mocked offline test.",
          }),
        }),
      );
      const errors = [];
      p.on("pageerror", (e) => errors.push(e.message));
      await p.goto(`http://127.0.0.1:${port}`);
      await p.click("#demo");
      if (name === "teslafi-connect") await p.click("#analyze");
      await p.waitForSelector("#workspace:not([hidden])");
      assert.equal(
        await p.evaluate(() => document.documentElement.scrollWidth),
        width,
      );
      if (name === "smsalyzer") {
        assert.equal(await p.locator(".message").count(), 4);
        await p.fill("#search", "receipt");
        assert.equal(await p.locator(".message").count(), 1);
        await p.click("#select-visible");
        const [download] = await Promise.all([
          p.waitForEvent("download"),
          p.click("#export"),
        ]);
        const payload = JSON.parse(
          fs.readFileSync(await download.path(), "utf8"),
        );
        assert.equal(payload.messages.length, 1);
        assert.equal(payload.messages[0].record, 4);
        assert.equal(payload.source.demo, true);
        assert.equal(payload.source.sha256.length, 64);
        await p.fill("#search", "");
        await p.locator(".thread").nth(1).click();
        assert.equal(await p.locator(".attachment").count(), 1);
        await p.click("#clear");
        assert.equal(await p.locator("#workspace").isVisible(), false);
        await p.setInputFiles("#file", {
          name: "owned-test.xml",
          mimeType: "text/xml",
          buffer: Buffer.from(
            '<smses><sms address="tester" type="1" date="1735689600000" body="&lt;script&gt;alert(1)&lt;/script&gt;"/></smses>',
          ),
        });
        await p.waitForSelector("#workspace:not([hidden])");
        assert.equal(
          await p.locator(".message p").innerText(),
          "<script>alert(1)</script>",
        );
        assert.equal(await p.locator("#source").innerText(), "owned-test.xml");
      } else {
        assert.equal(await p.locator("#rows tr").count(), 12);
        await p.selectOption("#unit", "mi");
        await p.fill("#offset", "bad");
        await p.click("#analyze");
        assert.match(await p.locator("#notice").innerText(), /offset/);
        const [invalidExport] = await Promise.all([
          p.waitForEvent("download"),
          p.click("#export"),
        ]);
        const unchanged = JSON.parse(
          fs.readFileSync(await invalidExport.path(), "utf8"),
        );
        assert.equal(unchanged.assumptions.unit, "km");
        assert.equal(unchanged.assumptions.offset, "+00:00");
        await p.fill("#offset", "+00:00");
        await p.fill("#from", "2025-01-03");
        await p.fill("#to", "2025-01-05");
        assert.equal(await p.locator("#rows tr").count(), 6);
        await p.selectOption("#kind", "charge");
        assert.equal(await p.locator("#rows tr").count(), 3);
        const [download] = await Promise.all([
          p.waitForEvent("download"),
          p.click("#export"),
        ]);
        const payload = JSON.parse(
          fs.readFileSync(await download.path(), "utf8"),
        );
        assert.equal(payload.records.length, 3);
        assert.equal(payload.totals.cost.known, 2);
        assert.equal(payload.totals.cost.total, 3);
        assert.equal(payload.source.demo, true);
        await p.click("#clear");
        assert.equal(await p.locator("#workspace").isVisible(), false);
        await p.setInputFiles("#file", {
          name: "owner-export.json",
          mimeType: "application/json",
          buffer: Buffer.from(
            JSON.stringify([
              { type: "charge", start: "2025-01-01", energy: 20, cost: "" },
            ]),
          ),
        });
        await p.waitForSelector("#mapping:not([hidden])");
        await p.fill("#tariff", "0.25");
        await p.click("#analyze");
        assert.equal(await p.locator("#rows tr").count(), 1);
        assert.match(await p.locator("#rows").innerText(), /tariff estimate/);
        await p.click("#status");
        await p.waitForFunction(
          () =>
            !document
              .querySelector("#status-message")
              .textContent.includes("Reading"),
        );
        assert.match(
          await p.locator("#status-message").innerText(),
          /mocked offline test/,
        );
      }
      assert.deepEqual(errors, []);
      evidence.push({
        name,
        width,
        journey: "pass",
        overflow: false,
        pageErrors: errors,
        statusEndpoint: "mocked; no live request",
      });
      await p.close();
    }
  }
  console.log(JSON.stringify(evidence));
  await b.close();
  server.kill();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
