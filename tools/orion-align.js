// tools/orion-align.js
import fs from "fs";

const currentMetricsPath = process.argv[2];
const baselineMetricsPath = process.argv[3];

console.log("🌌 Orion Module: Verifying performance alignment constraints...");

try {
  const current = JSON.parse(fs.readFileSync(currentMetricsPath, "utf8"));
  const baseline = JSON.parse(fs.readFileSync(baselineMetricsPath, "utf8"));

  console.log(`   • Baseline Latency: ${baseline.avgLatencyMs}ms`);
  console.log(`   • Current Latency:  ${current.avgLatencyMs}ms`);

  // Fail the gate if current performance drops below baseline threshold tolerances
  if (current.avgLatencyMs > baseline.avgLatencyMs * 1.10) { 
    throw new Error(`❌ Orion Alignment Breach: Latency regression exceeded 10% tolerance limit.`);
  }

  console.log("✅ Orion Aligned: Performance metrics conform to the master baseline.");
} catch (err) {
  console.error(`❌ Orion Failure: Alignment could not be verified.\n   Reason: ${err.message}`);
  process.exit(1);
}
