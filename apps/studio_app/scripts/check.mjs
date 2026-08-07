import { readdir, readFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const src = join(root, "src");
const files = (await readdir(src)).filter((name) => name.endsWith(".js"));
for (const file of files) {
  const result = spawnSync(process.execPath, ["--check", join(src, file)], { encoding: "utf8" });
  if (result.status !== 0) throw new Error(result.stderr || `Syntax error in ${file}`);
}
const css = await readFile(join(src, "styles.css"), "utf8");
for (const token of ["--pink", "--cyan", "prefers-reduced-motion", ":focus-visible"]) {
  if (!css.includes(token)) throw new Error(`Missing required CSS contract: ${token}`);
}
console.log(`Checked ${files.length} JavaScript modules and accessibility CSS contracts.`);
