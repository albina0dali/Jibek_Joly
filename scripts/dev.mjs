import { Miniflare } from "miniflare";
import { build } from "esbuild";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  ".."
);
process.chdir(root);

const ignored = fs.existsSync(".gitignore")
  ? fs.readFileSync(".gitignore", "utf8")
  : "";

if (!ignored.includes(".jol-local/")) {
  fs.appendFileSync(".gitignore", "\n.jol-local/\n");
}

await import("./build.mjs");
fs.mkdirSync(".jol-local", { recursive: true });

await build({
  stdin: {
    contents: `
      import site from "./dist/server/index.js";

      export default {
        fetch(request, env, ctx) {
          const url = new URL(request.url);

          if (!["localhost", "127.0.0.1"].includes(url.hostname)) {
            return new Response("Local development only", {
              status: 403
            });
          }

          const headers = new Headers(request.headers);
          headers.set(
            "oai-authenticated-user-id",
            "jol-local-developer"
          );
          headers.set(
            "oai-authenticated-user-email",
            "developer@localhost"
          );

          return site.fetch(
            new Request(request, { headers }),
            env,
            ctx
          );
        }
      };
    `,
    resolveDir: root,
    sourcefile: "local-entry.js",
    loader: "js"
  },
  bundle: true,
  format: "esm",
  platform: "browser",
  target: "es2022",
  outfile: ".jol-local/worker.mjs"
});

const mf = new Miniflare({
  modules: true,
  scriptPath: path.join(root, ".jol-local/worker.mjs"),
  host: "127.0.0.1",
  port: 8787,
  compatibilityDate: "2025-09-01",
  d1Databases: ["DB"],
  d1Persist: path.join(root, ".jol-local/database"),
  bindings: {
    ADMIN_EMAIL: "developer@localhost"
  }
});

try {
  const db = await mf.getD1Database("DB");

  await db.prepare(
    "CREATE TABLE IF NOT EXISTS __jol_local_migrations " +
    "(name TEXT PRIMARY KEY)"
  ).run();

  const files = fs.readdirSync("drizzle")
    .filter(name => name.endsWith(".sql"))
    .sort();

  for (const name of files) {
    const existing = await db.prepare(
      "SELECT name FROM __jol_local_migrations WHERE name = ?"
    ).bind(name).first();

    if (existing) continue;

    const statements = fs.readFileSync(
      path.join("drizzle", name),
      "utf8"
    )
      .split("--> statement-breakpoint")
      .map(sql => sql.trim())
      .filter(Boolean);

    await db.batch([
      ...statements.map(sql => db.prepare(sql)),
      db.prepare(
        "INSERT INTO __jol_local_migrations (name) VALUES (?)"
      ).bind(name)
    ]);
  }

  await mf.ready;
  console.log("\nJOL is ready: http://localhost:8787");
  console.log("Stop: Ctrl+C");

  process.on("SIGINT", async () => {
    await mf.dispose();
    process.exit(0);
  });
} catch (error) {
  console.error(error);
  await mf.dispose();
  process.exitCode = 1;
}
