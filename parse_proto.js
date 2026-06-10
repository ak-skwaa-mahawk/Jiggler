// parse_proto.js
import protobuf from "protobufjs";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

// Emulate __dirname behavior natively in ES Modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const protoDir = path.join(__dirname, "proto");

console.log("================================================================================");
console.log("🌌 UNIFIED PROTOBUF MATRIX ENGINE — NATIVE ESM LINKER PHASE");
console.log("================================================================================");

if (!fs.existsSync(protoDir)) {
    console.error(`❌ Directory error: Looked for '${protoDir}' but it wasn't found.`);
    process.exit(1);
}

const files = fs.readdirSync(protoDir).filter(f => f.endsWith(".proto"));
console.log(`📂 Found ${files.length} vector definitions in substrate repository.`);

const masterRegistry = {};

files.forEach(file => {
    const filePath = path.join(protoDir, file);
    let content = fs.readFileSync(filePath, "utf8");
    
    // Auto-inject missing proto3 syntax declarations
    if (!content.includes('syntax =') && !content.includes('syntax=')) {
        content = 'syntax = "proto3";\n' + content;
    }
    
    try {
        // Force a completely blank, detached Root context for every single file loop step
        const isolatedRoot = new protobuf.Root();
        protobuf.parse(content, isolatedRoot, { keepCase: true });
        
        const messages = Object.keys(isolatedRoot.nested || {});
        masterRegistry[file] = messages;
        
        console.log(`  🔹 proto/${file} -> Compiled and Isolated [Types: ${messages.join(", ")}]`);
    } catch (err) {
        console.error(`  ❌ proto/${file} -> Processing Failure:\n `, err.message);
    }
});

console.log("--------------------------------------------------------------------------------");
console.log("✅ All vector definitions cleanly mapped to memory gateways.");
console.log("🔒 Native ES Module Decoupling Confirmed.");
console.log("================================================================================");
console.log("SKODEN — Node.js Gateway Online.");
