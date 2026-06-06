import os
import json
# preprocess_dna.py

data = {}

for fname in sorted(os.listdir("Files")):
    if fname.endswith(".txt"):
        file_id = fname.split("_")[-1].replace(".txt", "")
        with open(os.path.join("Files", fname), "r", encoding="utf-8") as f:
            data[file_id] = {
                "file_id": file_id,
                "dataset": "DNA",
                "text": f.read().strip()
            }

with open("dna.json", "w", encoding="utf-8") as out:
    json.dump(data, out, indent=2, ensure_ascii=False)

print("Klaar.")
