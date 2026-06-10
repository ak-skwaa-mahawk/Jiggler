// tools/relay-run.js
import { execSync } from "child_process";

const command = process.argv[2];

console.log(`🚀 Relay Module: Initiating deterministic execution for [${command}]...`);

if (!command) {
  console.error("❌ Relay Error: Missing execution payload command.");
  process.exit(1);
}

try {
  // Execute the target tests and pass-through stdout/stderr natively
  execSync(command, { stdio: "inherit" });
  console.log("✅ Relay Module: Execution finalized within nominal bounds.");
} catch (error) {
  console.error("❌ Relay Failure: Execution loop broken or timed out.");
  process.exit(1);
}
