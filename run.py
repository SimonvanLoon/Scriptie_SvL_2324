import os
import json
import argparse
import random
import asyncio
from datetime import datetime
from openai import AsyncOpenAI


# ------------------------------------------------------------
# JSON validator
# ------------------------------------------------------------
def validate_json(text):
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj, True, None
        return None, False, "Top-level JSON is not an object"
    except Exception as e:
        return None, False, str(e)


# ------------------------------------------------------------
# Prompt builders
# ------------------------------------------------------------
def build_strict_prompt(instruction, toponym_keys, article_text, no_article=False):
    if no_article:
        return (
            instruction
            + "\n\nToponym keys:\n"
            + json.dumps(toponym_keys, ensure_ascii=False)
        )
    else:
        return (
            instruction
            + "\n\nToponym keys:\n"
            + json.dumps(toponym_keys, ensure_ascii=False)
            + "\n\nArticle:\n"
            + article_text
        )


def build_fallback_prompt(instruction, toponym_keys, article_text, no_article=False):
    if no_article:
        return (
            instruction
            + "\n\nToponym keys:\n"
            + json.dumps(toponym_keys, ensure_ascii=False)
            + "\n\nYour output must be ONLY the JSON object."
        )
    else:
        return (
            instruction
            + "\n\nToponym keys:\n"
            + json.dumps(toponym_keys, ensure_ascii=False)
            + "\n\nArticle:\n"
            + article_text
            + "\n\nYour output must be ONLY the JSON object."
        )


# ------------------------------------------------------------
# Main async runner
# ------------------------------------------------------------
async def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--dna", action="store_true")
    parser.add_argument("--lgl", action="store_true")
    parser.add_argument("--mode", type=str, required=True)

    parser.add_argument("--split", required=True, choices=["micro_dev", "meso_dev", "test"])
    parser.add_argument("--subset", type=int, default=None)
    parser.add_argument("--pct", type=float, default=None)

    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--file-id", type=str, default=None)

    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--dry-run", action="store_true")

    parser.add_argument("--no-article", action="store_true")

    args = parser.parse_args()

    # ------------------------------------------------------------
    # Dataset selection
    # ------------------------------------------------------------
    if args.dna:
        data_file = "dna.json"
        template_file = "ai_template_dna.json"
        label = "DNA"
    elif args.lgl:
        data_file = "lgl.json"
        template_file = "ai_template_lgl.json"
        label = "LGL"
    else:
        raise ValueError("Use --dna or --lgl")

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(template_file, "r", encoding="utf-8") as f:
        templates = json.load(f)

    templates = {str(k): v for k, v in templates.items()}

    # ------------------------------------------------------------
    # Load prompt instruction
    # ------------------------------------------------------------
    prompt_path = os.path.join("prompts", f"{args.mode}.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        instruction = f.read()

    # ------------------------------------------------------------
    # Deterministic split
    # ------------------------------------------------------------
    all_ids = list(data.keys())
    random.seed(12345)
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

    # ------------------------------------------------------------
    # Select items
    # ------------------------------------------------------------
    if args.file_id:
        items = [article for article in data.values() if str(article["file_id"]) == args.file_id]
    else:
        items = [article for article in data.values() if article["file_id"] in selected_ids]

        if args.seed is not None:
            random.seed(args.seed)
        else:
            random.seed()

        if args.pct is not None:
            pct = args.pct / 100 if args.pct > 1 else args.pct
            k = max(1, int(len(items) * pct))
            items = random.sample(items, k)
        elif args.subset is not None:
            items = random.sample(items, args.subset)

    # ------------------------------------------------------------
    # Output directory
    # ------------------------------------------------------------
    run_dir = os.path.join("outputs", args.mode)
    os.makedirs(run_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(run_dir, f"run_{timestamp}.json")

    # ------------------------------------------------------------
    # OpenRouter client
    # ------------------------------------------------------------
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    print(f"\nRunning {len(items)} articles with prompt: {args.mode}")
    print(f"Dataset: {label}")
    print(f"Model: {args.model}")
    print(f"Output file: {output_path}\n")

    # ------------------------------------------------------------
    # Run record
    # ------------------------------------------------------------
    run_record = {
        "run_metadata": {
            "timestamp": timestamp,
            "model": args.model,
            "instruction_mode": args.mode,
            "dataset": label,
            "num_articles": len(items),
            "reasoning_enabled": True,
            "no_article_mode": args.no_article
        },
        "articles": {}
    }

    # ------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------
    for article in items:
        file_id = str(article["file_id"])
        text = article["text"]
        toponym_keys = list(templates.get(file_id, {}).keys())

        print("\n====================================")
        print(f"ARTICLE ID: {file_id}")
        print("Toponym keys:", toponym_keys)
        print("====================================\n")

        # ------------------------------------------------------------
        # Build prompts
        # ------------------------------------------------------------
        prompt_strict = build_strict_prompt(instruction, toponym_keys, text, no_article=args.no_article)
        prompt_fallback = build_fallback_prompt(instruction, toponym_keys, text, no_article=args.no_article)

        # ------------------------------------------------------------
        # Build reasoning parameters (fresh dict each time)
        # ------------------------------------------------------------
        def build_reasoning():
            if "gpt-5" in args.model.lower():
                return {"reasoning": {"effort": "minimal"}}
            else:
                return {"reasoning": {"effort": "medium"}}

        # ------------------------------------------------------------
        # STRICT ATTEMPT
        # ------------------------------------------------------------
        strict_api_params = {
            "model": args.model,
            "messages": [{"role": "user", "content": prompt_strict}],
            "response_format": {"type": "json_object"},
            "extra_body": build_reasoning()
        }

        try:
            response = await client.chat.completions.create(**strict_api_params)
            api_error = None
            strict_success = True
        except Exception as e:
            api_error = str(e)
            strict_success = False
            response = None

        # ------------------------------------------------------------
        # FALLBACK ATTEMPT (only if strict failed)
        # ------------------------------------------------------------
        if strict_success is False:
            fallback_api_params = {
                "model": args.model,
                "messages": [{"role": "user", "content": prompt_fallback}],
                "extra_body": build_reasoning()
            }

            try:
                response = await client.chat.completions.create(**fallback_api_params)
                api_error = None
            except Exception as e:
                api_error = str(e)
                response = None

        # ------------------------------------------------------------
        # BOTH ATTEMPTS FAILED → LOG ERROR RECORD
        # ------------------------------------------------------------
        if api_error is not None:
            run_record["articles"][file_id] = {
                "article_id": file_id,
                "model_executed": None,
                "toponym_keys": toponym_keys,
                "raw_article_text": text if not args.no_article else None,

                "error": api_error,
                "llm_response_raw": None,
                "llm_response_parsed": None,

                "valid_json": None,      # IMPORTANT FIX
                "json_error": None,      # IMPORTANT FIX

                "token_metrics": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "reasoning_tokens": 0,
                    "total_tokens": 0
                },

                "reasoning": {
                    "requested_effort": build_reasoning()["reasoning"]["effort"],
                    "actual_reasoning_tokens": 0,
                    "reasoning_text": None
                }
            }

            print(f"❌ {file_id} | API error logged: {api_error}")
            continue

        # ------------------------------------------------------------
        # SUCCESS PATH — Process response
        # ------------------------------------------------------------
        usage = response.usage
        msg = response.choices[0].message
        actual_model_used = response.model

        # Reasoning tokens
        reasoning_tokens = 0
        if usage and hasattr(usage, "completion_tokens_details") and usage.completion_tokens_details:
            reasoning_tokens = getattr(usage.completion_tokens_details, "reasoning_tokens", 0)

        # Reasoning text
        reasoning_text = None
        if hasattr(msg, "reasoning"):
            reasoning_text = msg.reasoning
        elif hasattr(msg, "reasoning_details"):
            reasoning_text = msg.reasoning_details

        # Raw output
        llm_output = msg.content if msg and msg.content else ""

        # JSON validation
        parsed, valid, json_error = validate_json(llm_output)

        run_record["articles"][file_id] = {
            "article_id": file_id,
            "model_executed": actual_model_used,
            "toponym_keys": toponym_keys,
            "raw_article_text": text if not args.no_article else None,

            "error": None,

            "reasoning": {
                "requested_effort": build_reasoning()["reasoning"]["effort"],
                "actual_reasoning_tokens": reasoning_tokens,
                "reasoning_text": reasoning_text
            },

            "token_metrics": {
                "input_tokens": usage.prompt_tokens,
                "output_tokens": usage.completion_tokens,
                "reasoning_tokens": reasoning_tokens,
                "total_tokens": usage.total_tokens
            },

            "llm_response_raw": llm_output,
            "llm_response_parsed": parsed,
            "valid_json": valid,
            "json_error": json_error
        }

        print(
            f"✔ {file_id} | Model: {actual_model_used} | "
            f"Reasoning tokens: {reasoning_tokens}"
        )

    # ------------------------------------------------------------
    # Save run
    # ------------------------------------------------------------
    if not args.dry_run:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(run_record, f, indent=2, ensure_ascii=False)

    print("\nDone.\n")


if __name__ == "__main__":
    asyncio.run(main())
