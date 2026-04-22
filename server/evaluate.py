import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from services.recommender_engine import MovieLensRecommender, RecommenderConfig


def _load_env() -> None:
    base_dir = Path(__file__).resolve().parent
    load_dotenv(base_dir / ".env", override=False)


def _has_any_llm_credentials() -> bool:
    return bool(
        os.getenv("OPENAI_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("HUGGINGFACE_API_KEY")
        or os.getenv("HF_TOKEN")
    )


def _build_eval_recommender() -> MovieLensRecommender:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "ml-100k"))
    recommender = MovieLensRecommender(
        RecommenderConfig(
            data_dir=base_dir,
            svd_components=int(os.getenv("SVD_COMPONENTS", "50")),
            n_clusters=int(os.getenv("N_CLUSTERS", "12")),
            positive_threshold=int(os.getenv("POSITIVE_THRESHOLD", "4")),
            require_llm=os.getenv("REQUIRE_LLM", "true").lower() == "true",
        )
    )
    # Evaluation uses existing users only, so classifier training is unnecessary overhead.
    recommender.initialize(build_classifier=False)
    return recommender


def main() -> None:
    _load_env()

    parser = argparse.ArgumentParser(description="Evaluate MovieLens recommender with binary HR/NDCG.")
    parser.add_argument("--splits", default="u1,u2,u3,u4,u5", help="Comma-separated split prefixes")
    parser.add_argument("--ks", default="5,10,15", help="Comma-separated K values")
    parser.add_argument("--out", default="evaluation_results.json", help="Output JSON file")
    parser.add_argument(
        "--rank-top-n",
        type=int,
        default=120,
        help="Number of ranked movies generated per user before metric slicing (lower = faster).",
    )
    parser.add_argument(
        "--max-users",
        type=int,
        default=0,
        help="Evaluate only first N eligible users per split for faster demos (0 = all).",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bars/log printing for slightly faster evaluation.",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM scoring for debugging only (not for final project runs).",
    )
    args = parser.parse_args()

    splits = [x.strip() for x in args.splits.split(",") if x.strip()]
    ks = [int(x.strip()) for x in args.ks.split(",") if x.strip()]

    requested_llm = not args.no_llm
    effective_use_llm = requested_llm
    if requested_llm and not _has_any_llm_credentials():
        print(
            "No LLM API key found (OPENAI_API_KEY/GEMINI_API_KEY/HUGGINGFACE_API_KEY/HF_TOKEN). "
            "Falling back to --no-llm for this evaluation run."
        )
        effective_use_llm = False

    recommender = _build_eval_recommender()
    if not effective_use_llm:
        recommender.config.require_llm = False
    rows = []

    for split in splits:
        result = recommender.evaluate_binary_metrics(
            split_name=split,
            ks=ks,
            use_llm=effective_use_llm,
            show_progress=(not args.no_progress),
            rank_top_n=int(args.rank_top_n),
            max_users=(int(args.max_users) if int(args.max_users) > 0 else None),
        )
        for metric in result["metrics"]:
            rows.append(
                {
                    "split": split,
                    "k": metric["k"],
                    "hit_rate": metric["hit_rate"],
                    "ndcg": metric["ndcg"],
                    "evaluated_users": metric["evaluated_users"],
                    "llm_fallback_users": metric.get("llm_fallback_users", 0),
                }
            )

    summary = {
        "positive_threshold": recommender.config.positive_threshold,
        "llm_requested": requested_llm,
        "llm_used": effective_use_llm,
        "progress_enabled": (not args.no_progress),
        "rank_top_n": int(args.rank_top_n),
        "max_users": (int(args.max_users) if int(args.max_users) > 0 else None),
        "rows": rows,
    }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Evaluation completed")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
