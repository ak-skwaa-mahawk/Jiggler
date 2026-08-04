import fs from "fs";
import crypto from "crypto";

export function verifyFile(path, expectedHash = null){
  const code = fs.readFileSync(path, "utf8");
  const hash = crypto.createHash("sha256").update(code).digest("hex");
  if (expectedHash && hash !== expectedHash) {
    throw new Error(`❌ Sentinel breach: ${path} hash mismatch (expected ${expectedHash}, got ${hash})`);
  }
  console.log(`✅ Sentinel aligned: ${path} (${hash})`);
  return hash;
}

if (import.meta.url === `file://${process.argv[1]}`){
  const file = process.argv[2];
  const expected = process.argv[3];
  verifyFile(file, expected);
}
