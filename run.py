import os
import json
import argparse
import random
import asyncio
from openai import AsyncOpenAI

# ----------------------------
# JSON validator
# ----------------------------
def validate_json(text):
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj, True, None
        return None, False, "Top-level JSON is not an object"
    except Exception as e:
        return None, False, str(e)

# ----------------------------
# Prompt builder
# ----------------------------
def build_prompt(instruction, toponym_keys, article_text):
    return (
        instruction
        + "\n\nToponym keys:\n"
        + json.dumps(toponym_keys, ensure_ascii=False)
        + "\n\nArticle:\n"
        + article_text
        + "\n\nYour output must be ONLY the JSON object."
    )

# ----------------------------
# Main async runner
# ----------------------------
async def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--dna", action="store_true")
    parser.add_argument("--lgl", action="store_true")
    parser.add_argument("--mode", type=str, required=True)
    parser.add_argument("--split", required=True, choices=["micro_dev", "meso_dev", "test"])
    parser.add_argument("--subset", type=int, default=None)
    parser.add_argument("--pct", type=float, default=None)
    parser.add_argument("--seed", type=int, default=42)

    # NEW: dry-run mode
    parser.add_argument("--dry-run", action="store_true",
                        help="Print output instead of saving to disk.")

    args = parser.parse_args()

    # ----------------------------
    # Dataset selection
    # ----------------------------
    if args.dna:
        data_file = "dna.json"
        template_file = "ai_template_dna.json"
    elif args.lgl:
        data_file = "lgl.json"
        template_file = "ai_template_lgl.json"
    else:
        raise ValueError("Use --dna or --lgl")

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(template_file, "r", encoding="utf-8") as f:
        templates = json.load(f)

    templates = {str(k): v for k, v in templates.items()}

    # ----------------------------
    # Load prompt instruction
    # ----------------------------
    prompt_path = os.path.join("prompts", f"{args.mode}.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        instruction = f.read()

    # ----------------------------
    # Split logic
    # ----------------------------
    all_ids = list(data.keys())
    random.seed(args.seed)
    random.shuffle(all_ids)

    n = len(all_ids)
    n_micro = int(0.20 * n)
    n_meso = int(0.20 * n)

    micro_ids = set(all_ids[:n_micro])
    meso_ids = set(all_ids[n_micro:n_micro + n_meso])
    test_ids = set(all_ids[n_micro + n_meso:])

    if args.split == "micro_dev":
        selected_ids = micro_ids
    elif args.split == "meso_dev":
        selected_ids = meso_ids
    else:
        selected_ids = test_ids

    items = [article for article in data.values() if article["file_id"] in selected_ids]

    # ----------------------------
    # Subset selection
    # ----------------------------
    if args.pct is not None:
        pct = args.pct / 100 if args.pct > 1 else args.pct
        k = max(1, int(len(items) * pct))
        items = random.sample(items, k)

    elif args.subset is not None:
        items = random.sample(items, args.subset)

    # ----------------------------
    # Output directory (only if saving)
    # ----------------------------
    if not args.dry_run:
        out_dir = os.path.join("outputs", args.mode)
        os.makedirs(out_dir, exist_ok=True)

    # ----------------------------
    # OpenRouter client
    # ----------------------------
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    print(f"\nRunning {len(items)} articles with prompt: {args.mode}")
    if args.dry_run:
        print("Mode: DRY RUN (no files will be saved)\n")
    else:
        print("Mode: SAVE OUTPUTS\n")

    # ----------------------------
    # Main loop
    # ----------------------------
    for article in items:
        file_id = str(article["file_id"])
        text = article["text"]

        toponym_keys = list(templates.get(file_id, {}).keys())
        if not toponym_keys:
            print(f"Skipping {file_id}: no toponym keys.")
            continue

        prompt = build_prompt(instruction, toponym_keys, text)

        print(f"→ Calling LLM for article {file_id}...")

        # ----------------------------
        # LLM call (OpenRouter)
        # ----------------------------
        try:
            response = await client.chat.completions.create(
                model="openai/gpt-5-nano",
                messages=[
                    {"role": "system", "content": "You are a precise JSON generator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
        except Exception as e:
            print(f"⚠️ API error for {file_id}: {e}")
            continue

        llm_output = response.choices[0].message.content.strip()

        # ----------------------------
        # Validate JSON
        # ----------------------------
        parsed, valid, error = validate_json(llm_output)

        if args.dry_run:
            print("\n===== OUTPUT =====")
            print(llm_output)
            print("==================\n")
            continue

        # ----------------------------
        # Save output
        # ----------------------------
        if not valid:
            out = {
                "json_valid": False,
                "json_errors": error,
                "raw_output": llm_output
            }
        else:
            out = {
                "json_valid": True,
                "json_errors": None,
                "json": parsed
            }

        out_path = os.path.join(out_dir, f"{file_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)

        print(f"Saved → {out_path}")

    print("\nDone.\n")


if __name__ == "__main__":
    asyncio.run(main())
