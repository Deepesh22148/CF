import argparse
import json
from pathlib import Path

from services.recommender_engine import get_recommender


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate MovieLens recommender with binary HR/NDCG.")
    parser.add_argument("--splits", default="u1,u2,u3,u4,u5", help="Comma-separated split prefixes")
    parser.add_argument("--ks", default="5,10,15", help="Comma-separated K values")
    parser.add_argument("--out", default="evaluation_results.json", help="Output JSON file")
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM scoring for debugging only (not for final project runs).",
    )
    args = parser.parse_args()

    splits = [x.strip() for x in args.splits.split(",") if x.strip()]
    ks = [int(x.strip()) for x in args.ks.split(",") if x.strip()]

    recommender = get_recommender()
    rows = []

    for split in splits:
        result = recommender.evaluate_binary_metrics(split_name=split, ks=ks, use_llm=not args.no_llm)
        for metric in result["metrics"]:
            rows.append(
                {
                    "split": split,
                    "k": metric["k"],
                    "hit_rate": metric["hit_rate"],
                    "ndcg": metric["ndcg"],
                    "evaluated_users": metric["evaluated_users"],
                }
            )

    summary = {
        "positive_threshold": recommender.config.positive_threshold,
        "llm_used": not args.no_llm,
        "rows": rows,
    }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Evaluation completed")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
