// Build a canonical REA Evidence bundle from CLI capture records, using REA's
// own bundle constructor so the manifests are exactly what REA expects.
import { readFileSync, writeFileSync } from "node:fs";
import { createEvidenceBundle } from "rea-agents/dist/domain/evidenceBundle.js";
import { parseEvidence } from "rea-agents/dist/domain/evidence.js";
const [, , out, ...inputs] = process.argv;
const records = inputs.map((p) => parseEvidence(JSON.parse(readFileSync(p, "utf8"))));
const bundle = createEvidenceBundle(records, []);
writeFileSync(out, JSON.stringify(bundle));
console.log(`bundle: ${records.length} records -> ${out}`);
