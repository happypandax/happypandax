import fs from "fs";
import Client, { JsonArray, JsonMap, log } from "happypandax-client";
import { hrtime } from "process";

log.enabled = false;

const statsPath = "measure.log";

let stats = {};

if (fs.existsSync(statsPath)) {
  stats = JSON.parse(fs.readFileSync(statsPath, "utf-8"));
}

const SERVER = {
  port: 7007,
  host: "localhost",
};

function color(txt: string, color: "red" | "green" | "blue" | "yellow") {
  switch (color) {
    case "red":
      return `\x1b[31m${txt}\x1b[0m`;
    case "green":
      return `\x1b[32m${txt}\x1b[0m`;
    case "blue":
      return `\x1b[34m${txt}\x1b[0m`;
    case "yellow":
      return `\x1b[33m${txt}\x1b[0m`;
  }
}
class HPX {
  client: Client;

  constructor(session_id?: string) {
    this.client = new Client({ name: "tools", session_id });
  }

  async connect(host: string, port: number) {
    await this.client.connect({ host, port });
    await this.client.handshake({ user: null, password: null });
  }

  async call(msg: JsonArray) {
    return await this.client.send(msg);
  }

  async measure(fname: string, body: JsonMap, note, times, y = 0) {
    const precision = 3; // 3 decimal places
    let total = 0;
    let avg = 0;
    let prev_avg = stats[note] ?? 0;
    let diff = 0;
    for (let i = 1; i <= times; i++) {
      const s = hrtime();
      await this.call([{ fname, ...body }]);
      const elapsed = hrtime(s)[1] / 1000000; // divide by a million to get nano to milli
      total += elapsed;
      avg = total / i;
      diff = avg - prev_avg;
      let d = color(
        (diff > 0 ? "+" : "") + diff.toFixed(precision) + " ms",
        diff > 0 ? "red" : "green"
      );

      process.stdout.cursorTo(0, y);
      process.stdout.clearLine();
      process.stdout.write(
        `${i} - ` +
          color(elapsed.toFixed(precision) + " ms", "yellow") +
          " - avg " +
          color(avg.toFixed(precision) + " ms", "blue") +
          " - " +
          `(${d}) ` +
          " - " +
          note
      ); // print message + time
    }
    stats[note] = avg;
    fs.writeFileSync(statsPath, JSON.stringify(stats));
  }

  async measureVarious(
    functions: [fname: string, body: JsonMap, note?: string][],
    times: number
  ) {
    process.stdout.cursorTo(0, 0);
    process.stdout.clearScreenDown();
    for (let i = 0; i < functions.length; i++) {
      const f = functions[i];
      await this.measure(f[0], f[1], `${f[0]}: ` + f?.[2], times, i);
    }
  }
}

const galleryCardDataFields = [
  "artists.preferred_name.name",
  "preferred_title.name",
  "profile",
  "number",
  "page_count",
  "language.code",
  "progress.end",
  "progress.page.number",
  "progress.percent",
  "metatags.*",
];

const galleryCardDataFields2 = [
  "artists.preferred_name.name",
  "preferred_title.name",
  "profile",
  "number",
  "times_read",
  "page_count",
  "language.code",
  "language.name",
  "grouping.status.name",
  "progress.end",
  "progress.page.number",
  "progress.percent",
  "metatags.*",
];

export async function main() {
  const hpx = new HPX();
  await hpx.connect(SERVER.host, SERVER.port);
  await hpx.measureVarious(
    [
      ["library_view", { search_query: "" }, "default view"],
      [
        "library_view",
        { search_query: "", fields: galleryCardDataFields },
        "gallerycard fields",
      ],
      [
        "library_view",
        { search_query: "", fields: galleryCardDataFields2 },
        "gallerycard fields 2",
      ],
      ["library_view", { search_query: "", fields: ["*"] }, "1 level * fields"],
      [
        "library_view",
        { search_query: "", fields: ["**"] },
        "2 level * fields",
      ],
      [
        "library_view",
        { search_query: "", fields: ["***"] },
        "3 level * fields",
      ],
    ],
    100
  );
}

main()
  .then(() => fs.writeFileSync(statsPath, JSON.stringify(stats)))
  .then(() => process.exit(0))
  .catch((e) => {
    console.log("\n");
    console.error(e);
    process.exit(1);
  });
