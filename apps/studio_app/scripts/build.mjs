import { cp, mkdir, readdir, readFile, rm, stat } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const dist = join(root, "dist");
const publicDir = join(root, "public");
const srcDir = join(root, "src");

await rm(dist, { recursive: true, force: true });
await mkdir(join(dist, "assets"), { recursive: true });
await cp(publicDir, dist, { recursive: true });
await cp(srcDir, join(dist, "assets"), { recursive: true });

const required = [
  "index.html",
  "runtime-config.js",
  "assets/app.js",
  "assets/styles.css",
  "assets/media/feed-unit.js",
];
for (const path of required) {
  const info = await stat(join(dist, path));
  if (!info.isFile() || info.size === 0) throw new Error(`Build output missing: ${path}`);
}

const html = await readFile(join(dist, "index.html"), "utf8");
if (!html.includes('/assets/app.js') || !html.includes('/assets/styles.css')) {
  throw new Error("index.html does not reference built assets");
}

async function size(path) {
  const entries = await readdir(path, { withFileTypes: true });
  let total = 0;
  for (const entry of entries) {
    const full = join(path, entry.name);
    total += entry.isDirectory() ? await size(full) : (await stat(full)).size;
  }
  return total;
}

console.log(`AdultGen Studio built: ${(await size(dist) / 1024).toFixed(1)} KiB`);
