# preprocess_dna.py
import os
import json

# Load templates (these define which articles are annotated)
with open("ai_template_dna.json", "r", encoding="utf-8") as f:
    templates = json.load(f)

annotated_ids = set(str(k) for k in templates.keys())

data = {}

for fname in sorted(os.listdir("Files")):
    if fname.endswith(".txt"):
        file_id = fname.split("_")[-1].replace(".txt", "")

        # Only include articles that have annotations
        if file_id not in annotated_ids:
            continue

        with open(os.path.join("Files", fname), "r", encoding="utf-8") as f:
            data[file_id] = {
                "file_id": file_id,
                "dataset": "DNA",
                "text": f.read().strip()
            }

with open("dna.json", "w", encoding="utf-8") as out:
    json.dump(data, out, indent=2, ensure_ascii=False)

print("Klaar.")
