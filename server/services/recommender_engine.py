import json
import os
import time
import ast
import re
from urllib.parse import quote
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None


GENRE_NAMES = [
    "unknown",
    "action",
    "adventure",
    "animation",
    "children",
    "comedy",
    "crime",
    "documentary",
    "drama",
    "fantasy",
    "film_noir",
    "horror",
    "musical",
    "mystery",
    "romance",
    "sci_fi",
    "thriller",
    "war",
    "western",
]


@dataclass
class RecommenderConfig:
    data_dir: str
    svd_components: int = 24
    n_clusters: int = 12
    positive_threshold: int = 4
    require_llm: bool = True


class MovieLensRecommender:
    def __init__(self, config: RecommenderConfig):
        self.config = config
        self.initialized = False

        self.users_df: pd.DataFrame = pd.DataFrame()
        self.items_df: pd.DataFrame = pd.DataFrame()
        self.ratings_df: pd.DataFrame = pd.DataFrame()

        self.user_id_to_idx: Dict[int, int] = {}
        self.movie_id_to_idx: Dict[int, int] = {}
        self.idx_to_movie_id: Dict[int, int] = {}

        self.user_vectors: np.ndarray = np.array([])
        self.item_vectors: np.ndarray = np.array([])

        self.kmeans: Optional[KMeans] = None
        self.cluster_labels_by_user: Dict[int, int] = {}
        self.cluster_profiles: Dict[int, Dict[str, Any]] = {}

        self.vectorizer: Optional[DictVectorizer] = None
        self.classifier: Optional[LogisticRegression] = None

        self.seen_movies_by_user: Dict[int, set] = {}
        self.user_liked_samples: Dict[int, List[str]] = {}
        self.user_genre_weights: Dict[int, Dict[str, float]] = {}

    def initialize(self) -> None:
        if self.initialized:
            return

        self.users_df = self._load_users()
        self.items_df = self._load_items()
        self.ratings_df = self._load_ratings("u.data")

        self._fit_from_ratings(self.ratings_df)
        self.initialized = True

    def _data_path(self, filename: str) -> str:
        return os.path.join(self.config.data_dir, filename)

    def _load_users(self) -> pd.DataFrame:
        columns = ["user_id", "age", "gender", "occupation", "zip_code"]
        users = pd.read_csv(
            self._data_path("u.user"),
            sep="|",
            names=columns,
            encoding="latin-1",
        )
        users["user_id"] = users["user_id"].astype(int)
        return users

    def _load_items(self) -> pd.DataFrame:
        columns = [
            "movie_id",
            "title",
            "release_date",
            "video_release_date",
            "imdb_url",
            *GENRE_NAMES,
        ]
        items = pd.read_csv(
            self._data_path("u.item"),
            sep="|",
            names=columns,
            encoding="latin-1",
        )
        items["movie_id"] = items["movie_id"].astype(int)
        return items

    def _load_ratings(self, filename: str) -> pd.DataFrame:
        columns = ["user_id", "movie_id", "rating", "timestamp"]
        ratings = pd.read_csv(
            self._data_path(filename),
            sep="\t",
            names=columns,
            encoding="latin-1",
        )
        ratings["user_id"] = ratings["user_id"].astype(int)
        ratings["movie_id"] = ratings["movie_id"].astype(int)
        ratings["rating"] = ratings["rating"].astype(float)
        return ratings

    def _fit_from_ratings(self, ratings: pd.DataFrame) -> None:
        user_ids = sorted(ratings["user_id"].unique().tolist())
        movie_ids = sorted(self.items_df["movie_id"].unique().tolist())

        self.user_id_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
        self.movie_id_to_idx = {mid: idx for idx, mid in enumerate(movie_ids)}
        self.idx_to_movie_id = {idx: mid for mid, idx in self.movie_id_to_idx.items()}

        row_idx = ratings["user_id"].map(self.user_id_to_idx)
        col_idx = ratings["movie_id"].map(self.movie_id_to_idx)

        matrix = csr_matrix(
            (ratings["rating"].values, (row_idx.values, col_idx.values)),
            shape=(len(user_ids), len(movie_ids)),
        )

        n_components = min(
            self.config.svd_components,
            max(2, matrix.shape[0] - 1),
            max(2, matrix.shape[1] - 1),
        )
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        self.user_vectors = svd.fit_transform(matrix)
        self.item_vectors = svd.components_.T

        self.kmeans = KMeans(n_clusters=self.config.n_clusters, random_state=42, n_init=10)
        labels = self.kmeans.fit_predict(self.user_vectors)
        self.cluster_labels_by_user = {uid: int(labels[self.user_id_to_idx[uid]]) for uid in user_ids}

        self.seen_movies_by_user = {
            int(uid): set(group["movie_id"].tolist())
            for uid, group in ratings.groupby("user_id")
        }

        self._build_user_genre_profiles(ratings)
        self._build_cluster_profiles(ratings)
        self._fit_cluster_classifier()

    def _build_user_genre_profiles(self, ratings: pd.DataFrame) -> None:
        positive = ratings[ratings["rating"] >= self.config.positive_threshold]
        if positive.empty:
            self.user_genre_weights = {}
            self.user_liked_samples = {}
            return

        merged = positive.merge(self.items_df[["movie_id", "title", *GENRE_NAMES]], on="movie_id", how="left")

        self.user_genre_weights = {}
        self.user_liked_samples = {}

        for uid, group in merged.groupby("user_id"):
            uid = int(uid)
            scores: Dict[str, float] = {}
            for genre in GENRE_NAMES:
                genre_weight = float((group[genre] * group["rating"]).sum())
                if genre_weight > 0:
                    scores[genre] = genre_weight

            total = sum(scores.values())
            if total > 0:
                scores = {k: v / total for k, v in scores.items()}

            self.user_genre_weights[uid] = scores
            self.user_liked_samples[uid] = group.sort_values("rating", ascending=False)["title"].head(3).tolist()

    def _build_cluster_profiles(self, ratings: pd.DataFrame) -> None:
        ratings_with_cluster = ratings.copy()
        ratings_with_cluster["cluster_id"] = ratings_with_cluster["user_id"].map(self.cluster_labels_by_user)
        merged = ratings_with_cluster.merge(
            self.items_df[["movie_id", "title", *GENRE_NAMES]], on="movie_id", how="left"
        ).merge(
            self.users_df[["user_id", "age", "gender", "occupation"]], on="user_id", how="left"
        )

        self.cluster_profiles = {}
        for cluster_id, group in merged.groupby("cluster_id"):
            cluster_id = int(cluster_id)
            movie_stats = (
                group.groupby(["movie_id", "title"], as_index=False)["rating"]
                .mean()
                .sort_values("rating", ascending=False)
                .head(10)
            )
            top_movies = [
                {
                    "movie_id": int(row.movie_id),
                    "title": row.title,
                    "avg_rating": round(float(row.rating), 3),
                }
                for row in movie_stats.itertuples(index=False)
            ]

            genre_scores = {}
            for genre in GENRE_NAMES:
                genre_scores[genre] = float((group[genre] * group["rating"]).sum())
            dominant_genres = [
                genre for genre, _ in sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)[:5] if _ > 0
            ]

            avg_age = float(group["age"].mean()) if not group["age"].isna().all() else 0.0
            top_occupations = (
                group["occupation"].value_counts().head(3).index.tolist() if "occupation" in group else []
            )

            self.cluster_profiles[cluster_id] = {
                "cluster_id": cluster_id,
                "top_movies": top_movies,
                "dominant_genres": dominant_genres,
                "avg_age": round(avg_age, 2),
                "common_occupations": top_occupations,
            }

    def _profile_feature_dict(
        self,
        age: Optional[float],
        gender: Optional[str],
        occupation: Optional[str],
        genres: Sequence[str],
    ) -> Dict[str, float]:
        features: Dict[str, float] = {
            "age": float(age or 0),
            f"gender={str(gender or 'unknown').lower()}": 1.0,
            f"occupation={str(occupation or 'unknown').lower()}": 1.0,
        }

        genre_set = {g.strip().lower().replace("-", "_") for g in genres if g}
        for genre in GENRE_NAMES:
            features[f"pref_genre={genre}"] = 1.0 if genre in genre_set else 0.0

        return features

    def _fit_cluster_classifier(self) -> None:
        rows: List[Dict[str, float]] = []
        labels: List[int] = []

        users = self.users_df[["user_id", "age", "gender", "occupation"]].copy()
        for row in users.itertuples(index=False):
            uid = int(row.user_id)
            if uid not in self.cluster_labels_by_user:
                continue

            top_genres = sorted(
                self.user_genre_weights.get(uid, {}).items(),
                key=lambda x: x[1],
                reverse=True,
            )[:3]
            rows.append(
                self._profile_feature_dict(
                    age=float(row.age),
                    gender=str(row.gender),
                    occupation=str(row.occupation),
                    genres=[g for g, _ in top_genres],
                )
            )
            labels.append(self.cluster_labels_by_user[uid])

        if len(set(labels)) < 2:
            self.vectorizer = None
            self.classifier = None
            return

        self.vectorizer = DictVectorizer(sparse=False)
        x = self.vectorizer.fit_transform(rows)
        self.classifier = LogisticRegression(max_iter=1000, multi_class="auto")
        self.classifier.fit(x, labels)

    def _predict_cluster_for_profile(
        self,
        age: Optional[float],
        gender: Optional[str],
        occupation: Optional[str],
        genres: Sequence[str],
    ) -> int:
        if self.classifier is not None and self.vectorizer is not None:
            features = self._profile_feature_dict(age, gender, occupation, genres)
            x = self.vectorizer.transform([features])
            return int(self.classifier.predict(x)[0])

        if self.kmeans is None:
            return 0
        return 0

    def _genre_overlap_score(self, movie_row: pd.Series, preferred_genres: Sequence[str]) -> float:
        preferred = {g.strip().lower().replace("-", "_") for g in preferred_genres if g}
        if not preferred:
            return 0.0

        movie_genres = {g for g in GENRE_NAMES if int(movie_row.get(g, 0)) == 1}
        overlap = len(movie_genres.intersection(preferred))
        return float(overlap) / max(1.0, float(len(preferred)))

    def _movie_genre_string(self, movie_row: pd.Series) -> str:
        genres = [g.replace("_", " ").title() for g in GENRE_NAMES if int(movie_row.get(g, 0)) == 1]
        return ", ".join(genres) if genres else "Unknown"

    def _extract_json_object(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list):
                return {"results": parsed}
        except json.JSONDecodeError:
            pass

        # Common model pattern: JSON inside markdown fences.
        fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text, flags=re.IGNORECASE)
        if fence_match:
            candidate = fence_match.group(1)
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
                if isinstance(parsed, list):
                    return {"results": parsed}
            except json.JSONDecodeError:
                pass

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
                if isinstance(parsed, list):
                    return {"results": parsed}
            except json.JSONDecodeError:
                pass

            # Try a permissive parse path for near-JSON model outputs.
            cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
            cleaned = re.sub(r"\btrue\b", "True", cleaned)
            cleaned = re.sub(r"\bfalse\b", "False", cleaned)
            cleaned = re.sub(r"\bnull\b", "None", cleaned)
            try:
                parsed = ast.literal_eval(cleaned)
                if isinstance(parsed, dict):
                    return parsed
                if isinstance(parsed, list):
                    return {"results": parsed}
            except Exception:
                pass

            # Last-resort single-quote normalization attempt.
            squote_fixed = cleaned.replace("'", '"')
            try:
                parsed = json.loads(squote_fixed)
                if isinstance(parsed, dict):
                    return parsed
                if isinstance(parsed, list):
                    return {"results": parsed}
            except json.JSONDecodeError:
                pass

        # If model returns a top-level list in text, accept it as results.
        list_start = text.find("[")
        list_end = text.rfind("]")
        if list_start != -1 and list_end != -1 and list_end > list_start:
            candidate_list = text[list_start : list_end + 1]
            try:
                parsed_list = json.loads(candidate_list)
                if isinstance(parsed_list, list):
                    return {"results": parsed_list}
            except json.JSONDecodeError:
                pass

        raise ValueError("Model response did not contain a valid JSON object")

    def _debug_llm_output(self, provider: str, content: str) -> None:
        debug_enabled = os.getenv("LLM_DEBUG", "false").lower() == "true"
        if not debug_enabled:
            return
        print(f"[LLM DEBUG][{provider}] Raw output start")
        print(content[:4000])
        print(f"[LLM DEBUG][{provider}] Raw output end")

    def _build_llm_prompt(
        self,
        user_profile: Dict[str, Any],
        cluster_profile: Dict[str, Any],
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        payload_candidates = [
            {
                "movie_id": c["movie_id"],
                "title": c["title"],
                "genres": c["genres"],
                "base_score": round(float(c["base_score"]), 4),
            }
            for c in candidates
        ]

        return {
            "task": "Score each movie from 0 to 100 for expected user like probability and provide a short reason in one sentence.",
            "user_profile": user_profile,
            "cluster_context": {
                "dominant_genres": cluster_profile.get("dominant_genres", []),
                "top_movies": [m["title"] for m in cluster_profile.get("top_movies", [])[:5]],
            },
            "movies": payload_candidates,
            "response_schema": {
                "results": [
                    {
                        "movie_id": "int",
                        "llm_score": "number",
                        "reason": "string",
                        "summary": "string",
                    }
                ]
            },
            "rules": [
                "Be concise and consistent.",
                "Penalize poor genre match.",
                "Reward overlap with user genres and cluster tastes.",
                "Keep reason under 14 words.",
                "Keep summary under 14 words.",
                "Return JSON only without markdown.",
            ],
        }

    def _parse_llm_results(
        self,
        candidates: List[Dict[str, Any]],
        content: str,
        provider: str,
    ) -> List[Dict[str, Any]]:
        self._debug_llm_output(provider, content)
        parsed = self._extract_json_object(content)
        results = parsed.get("results", [])
        result_map = {int(x["movie_id"]): x for x in results if "movie_id" in x}

        reranked = []
        for c in candidates:
            llm_info = result_map.get(c["movie_id"], {})
            llm_score = float(llm_info.get("llm_score", c["base_score"] * 100))
            final_score = 0.7 * float(c["base_score"] * 100) + 0.3 * llm_score
            reranked.append(
                {
                    **c,
                    "score": round(final_score, 2),
                    "reason": str(llm_info.get("reason", c.get("reason", "Strong collaborative and genre fit."))),
                    "summary": str(llm_info.get("summary", c.get("summary", c["title"]))),
                    "used_llm": True,
                }
            )

        reranked.sort(key=lambda x: x["score"], reverse=True)
        return reranked

    def _call_openai_llm(self, prompt: Dict[str, Any]) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a recommendation scorer. Return strict JSON with key 'results'.",
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _call_gemini_llm(self, prompt: Dict[str, Any]) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        response = httpx.post(
            endpoint,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": (
                                    "You are a recommendation scorer. Return strict JSON with top-level key 'results'.\n"
                                    + json.dumps(prompt)
                                )
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json",
                },
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _call_huggingface_llm(self, prompt: Dict[str, Any]) -> str:
        api_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
        model = os.getenv("HUGGINGFACE_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        if not api_key:
            raise RuntimeError("HUGGINGFACE_API_KEY (or HF_TOKEN) not set")

        prompt_text = (
            "You are a recommendation scorer. Return ONLY valid JSON with top-level key 'results'. "
            "No markdown, no code fences, no explanation text.\n"
            + json.dumps(prompt)
        )

        max_retries = int(os.getenv("HUGGINGFACE_RETRIES", "3"))
        base_max_new_tokens = int(os.getenv("HUGGINGFACE_MAX_NEW_TOKENS", "420"))
        movie_count = len(prompt.get("movies", [])) if isinstance(prompt.get("movies", []), list) else 0
        max_new_tokens = min(1800, max(base_max_new_tokens, 200 + movie_count * 80))
        encoded_model = quote(model, safe="/")

        # Primary path: OpenAI-compatible HF router (validated in this workspace).
        for attempt in range(1, max_retries + 1):
            chat_response = httpx.post(
                "https://router.huggingface.co/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Return strict JSON with top-level key 'results'.",
                        },
                        {
                            "role": "user",
                            "content": prompt_text,
                        },
                    ],
                    "temperature": 0.2,
                    "max_tokens": max_new_tokens,
                },
                timeout=60.0,
            )

            chat_raw = chat_response.text
            if chat_response.status_code >= 500:
                if attempt < max_retries:
                    time.sleep(min(2 * attempt, 6))
                    continue
                raise RuntimeError(
                    f"HF chat-completions server error HTTP {chat_response.status_code}: {chat_raw[:500]}"
                )

            if chat_response.status_code >= 400:
                # Fall through to legacy endpoint candidates below.
                break

            chat_data = chat_response.json()
            choices = chat_data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content
            raise RuntimeError(f"Unexpected HF chat-completions format: {str(chat_data)[:500]}")

        endpoint_candidates = [
            f"https://router.huggingface.co/hf-inference/models/{encoded_model}",
            f"https://api-inference.huggingface.co/models/{encoded_model}",
            f"https://api-inference.huggingface.co/pipeline/text-generation/{encoded_model}",
        ]

        custom_base = os.getenv("HUGGINGFACE_API_BASE", "").strip()
        if custom_base:
            endpoint_candidates.insert(0, f"{custom_base.rstrip('/')}/{encoded_model}")

        last_error = ""
        for endpoint in endpoint_candidates:
            for attempt in range(1, max_retries + 1):
                response = httpx.post(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "inputs": prompt_text,
                        "parameters": {
                            "max_new_tokens": max_new_tokens,
                            "temperature": 0.2,
                            "return_full_text": False,
                        },
                        "options": {
                            "wait_for_model": True,
                            "use_cache": False,
                        },
                    },
                    timeout=60.0,
                )

                raw_text = response.text
                if response.status_code in {404, 405}:
                    last_error = f"{endpoint} -> HTTP {response.status_code}: {raw_text[:250]}"
                    break

                if response.status_code >= 500:
                    last_error = f"{endpoint} -> HTTP {response.status_code}: {raw_text[:500]}"
                    if attempt < max_retries:
                        time.sleep(min(2 * attempt, 6))
                        continue
                    break

                if response.status_code >= 400:
                    raise RuntimeError(f"Hugging Face request failed at {endpoint} HTTP {response.status_code}: {raw_text[:500]}")

                data = response.json()

                if isinstance(data, dict) and "error" in data:
                    err = str(data.get("error", "Unknown Hugging Face error"))
                    estimate = float(data.get("estimated_time", 0) or 0)
                    last_error = f"{endpoint} -> {err}"
                    if attempt < max_retries and ("loading" in err.lower() or estimate > 0):
                        time.sleep(min(max(estimate, 2.0), 12.0))
                        continue
                    break

                if isinstance(data, list) and data:
                    if isinstance(data[0], dict) and "generated_text" in data[0]:
                        return str(data[0]["generated_text"])
                if isinstance(data, dict) and "generated_text" in data:
                    return str(data["generated_text"])

                raise RuntimeError(f"Unexpected Hugging Face response format from {endpoint}: {str(data)[:500]}")

        raise RuntimeError(f"Hugging Face failed after retries: {last_error or 'Unknown error'}")

    def _llm_rerank_candidates(
        self,
        user_profile: Dict[str, Any],
        cluster_profile: Dict[str, Any],
        candidates: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], bool, str]:
        if httpx is None:
            raise RuntimeError("httpx dependency is required for LLM scoring.")

        prompt = self._build_llm_prompt(user_profile, cluster_profile, candidates)
        configured_provider = os.getenv("LLM_PROVIDER", "auto").strip().lower()

        providers_in_order: List[str]
        if configured_provider == "auto":
            providers_in_order = ["openai", "gemini", "huggingface"]
        else:
            providers_in_order = [configured_provider]

        errors: List[str] = []
        for provider in providers_in_order:
            try:
                if provider == "openai":
                    content = self._call_openai_llm(prompt)
                elif provider == "gemini":
                    content = self._call_gemini_llm(prompt)
                elif provider in {"huggingface", "hf"}:
                    content = self._call_huggingface_llm(prompt)
                    provider = "huggingface"
                else:
                    errors.append(f"Unsupported provider: {provider}")
                    continue

                reranked = self._parse_llm_results(candidates, content, provider)
                return reranked, True, provider
            except Exception as exc:
                errors.append(f"{provider}: {str(exc)}")

        raise RuntimeError("LLM scoring failed across providers: " + " | ".join(errors))

    def _fallback_reasoning(
        self, candidates: List[Dict[str, Any]], user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        preferred = {g.strip().lower().replace("-", "_") for g in user_profile.get("genres", [])}
        enriched = []
        for c in candidates:
            movie_genres = {g.strip().lower().replace("-", "_") for g in c["genres"].lower().replace(" ", "_").split(",")}
            overlap = preferred.intersection(movie_genres)
            if overlap:
                reason = f"Strong match to your preferred genres: {', '.join(sorted(overlap))}."
            else:
                reason = "High collaborative score from users with similar rating behavior."
            c = {
                **c,
                "score": round(float(c["base_score"]) * 100, 2),
                "reason": reason,
                "summary": f"{c['title']} is likely to fit your taste profile.",
                "used_llm": False,
            }
            enriched.append(c)

        enriched.sort(key=lambda x: x["score"], reverse=True)
        return enriched

    def _recommend_from_vector(
        self,
        user_vector: np.ndarray,
        preferred_genres: Sequence[str],
        exclude_movie_ids: Optional[set],
        top_k: int,
        user_profile: Dict[str, Any],
        cluster_id: int,
        use_llm: bool,
    ) -> Dict[str, Any]:
        raw_scores = self.item_vectors.dot(user_vector)
        candidates = []

        for idx in np.argsort(raw_scores)[::-1]:
            movie_id = self.idx_to_movie_id[idx]
            if exclude_movie_ids and movie_id in exclude_movie_ids:
                continue

            movie_row = self.items_df[self.items_df["movie_id"] == movie_id].iloc[0]
            genre_bonus = self._genre_overlap_score(movie_row, preferred_genres)
            base_score = float(raw_scores[idx]) + 0.15 * genre_bonus

            candidates.append(
                {
                    "movie_id": int(movie_id),
                    "title": str(movie_row["title"]),
                    "genres": self._movie_genre_string(movie_row),
                    "base_score": base_score,
                    "estimated_rating": round(min(5.0, max(1.0, 2.5 + base_score)), 2),
                    "genre_match": round(genre_bonus, 3),
                }
            )

            if len(candidates) >= max(50, top_k * 3):
                break

        cluster_profile = self.cluster_profiles.get(cluster_id, {})
        if use_llm:
            llm_candidate_cap = max(top_k + 5, 20)
            llm_candidates = candidates[:llm_candidate_cap]
            reranked, used_llm, llm_provider = self._llm_rerank_candidates(user_profile, cluster_profile, llm_candidates)
        else:
            if self.config.require_llm:
                raise RuntimeError("LLM is mandatory in this configuration. Set use_llm=True.")
            reranked = self._fallback_reasoning(candidates, user_profile)
            used_llm = False
            llm_provider = "none"

        recommendations = [
            {
                "movie_id": c["movie_id"],
                "title": c["title"],
                "genres": c["genres"],
                "score": round(float(c["score"]), 2),
                "estimated_rating": c["estimated_rating"],
                "reason": c["reason"],
                "summary": c["summary"],
                "genre_match": c["genre_match"],
            }
            for c in reranked[:top_k]
        ]

        return {
            "recommendations": recommendations,
            "cluster": {
                "cluster_id": cluster_id,
                "profile": cluster_profile,
            },
            "llm_used": used_llm,
            "llm_provider": llm_provider,
        }

    def recommend_existing_user(self, user_id: int, top_k: int = 15, use_llm: bool = True) -> Dict[str, Any]:
        self.initialize()
        if user_id not in self.user_id_to_idx:
            raise ValueError(f"User {user_id} not found in dataset")

        user_row = self.users_df[self.users_df["user_id"] == user_id].iloc[0]
        cluster_id = self.cluster_labels_by_user.get(user_id, 0)
        preferred_genres = sorted(
            self.user_genre_weights.get(user_id, {}).items(), key=lambda x: x[1], reverse=True
        )[:3]
        preferred_genre_names = [g for g, _ in preferred_genres]

        user_profile = {
            "user_id": int(user_id),
            "age": int(user_row["age"]),
            "gender": str(user_row["gender"]),
            "occupation": str(user_row["occupation"]),
            "genres": preferred_genre_names,
            "liked_samples": self.user_liked_samples.get(user_id, []),
        }

        rec_payload = self._recommend_from_vector(
            user_vector=self.user_vectors[self.user_id_to_idx[user_id]],
            preferred_genres=preferred_genre_names,
            exclude_movie_ids=self.seen_movies_by_user.get(user_id, set()),
            top_k=top_k,
            user_profile=user_profile,
            cluster_id=cluster_id,
            use_llm=use_llm,
        )

        return {
            "user_info": user_profile,
            **rec_payload,
        }

    def recommend_fresh_user(
        self,
        age: float,
        gender: str,
        occupation: str,
        genres: Sequence[str],
        top_k: int = 15,
        use_llm: bool = True,
    ) -> Dict[str, Any]:
        self.initialize()
        cluster_id = self._predict_cluster_for_profile(age, gender, occupation, genres)
        centroid = self.kmeans.cluster_centers_[cluster_id] if self.kmeans is not None else np.zeros(self.item_vectors.shape[1])

        user_profile = {
            "age": int(age),
            "gender": str(gender),
            "occupation": str(occupation),
            "genres": list(genres),
            "liked_samples": [],
        }

        rec_payload = self._recommend_from_vector(
            user_vector=centroid,
            preferred_genres=genres,
            exclude_movie_ids=None,
            top_k=top_k,
            user_profile=user_profile,
            cluster_id=cluster_id,
            use_llm=use_llm,
        )

        return {
            "user_info": user_profile,
            **rec_payload,
        }

    def evaluate_binary_metrics(
        self,
        split_name: str = "u1",
        ks: Sequence[int] = (5, 10, 15),
        use_llm: bool = True,
    ) -> Dict[str, Any]:
        self.initialize()

        base_file = f"{split_name}.base"
        test_file = f"{split_name}.test"
        base_ratings = self._load_ratings(base_file)
        test_ratings = self._load_ratings(test_file)

        temp = MovieLensRecommender(self.config)
        temp.users_df = self.users_df.copy()
        temp.items_df = self.items_df.copy()
        temp._fit_from_ratings(base_ratings)
        temp.initialized = True

        positives = test_ratings[test_ratings["rating"] >= self.config.positive_threshold]
        positives_by_user = {
            int(uid): set(group["movie_id"].tolist())
            for uid, group in positives.groupby("user_id")
        }

        results = []
        for k in ks:
            hr_scores = []
            ndcg_scores = []

            for user_id, positive_movies in positives_by_user.items():
                if user_id not in temp.user_id_to_idx or not positive_movies:
                    continue

                payload = temp.recommend_existing_user(user_id, top_k=int(k), use_llm=use_llm)
                rec_ids = [r["movie_id"] for r in payload["recommendations"]]

                hit = 1.0 if any(mid in positive_movies for mid in rec_ids) else 0.0
                hr_scores.append(hit)

                dcg = 0.0
                for rank, movie_id in enumerate(rec_ids, start=1):
                    rel = 1.0 if movie_id in positive_movies else 0.0
                    dcg += rel / np.log2(rank + 1)

                ideal_hits = min(len(positive_movies), int(k))
                idcg = sum(1.0 / np.log2(r + 1) for r in range(1, ideal_hits + 1))
                ndcg_scores.append((dcg / idcg) if idcg > 0 else 0.0)

            results.append(
                {
                    "k": int(k),
                    "hit_rate": round(float(np.mean(hr_scores)) if hr_scores else 0.0, 4),
                    "ndcg": round(float(np.mean(ndcg_scores)) if ndcg_scores else 0.0, 4),
                    "evaluated_users": len(hr_scores),
                }
            )

        return {
            "split": split_name,
            "positive_threshold": self.config.positive_threshold,
            "llm_used": use_llm,
            "metrics": results,
        }


_engine: Optional[MovieLensRecommender] = None


def get_recommender() -> MovieLensRecommender:
    global _engine
    if _engine is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml-100k"))
        _engine = MovieLensRecommender(
            RecommenderConfig(
                data_dir=base_dir,
                svd_components=int(os.getenv("SVD_COMPONENTS", "24")),
                n_clusters=int(os.getenv("N_CLUSTERS", "12")),
                positive_threshold=int(os.getenv("POSITIVE_THRESHOLD", "4")),
                require_llm=os.getenv("REQUIRE_LLM", "true").lower() == "true",
            )
        )
    _engine.initialize()
    return _engine
