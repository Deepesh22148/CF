bash

# CF_Project


---

## Client Setup

1. Open a terminal and navigate to the `client` directory:

	```bash
	cd client
	npm install
	```

2. Start the client (if applicable):

	```bash
	npm run dev
	```

	For production preview:

	```bash
	npm run build
	npm start
	```

---

## Server Setup

1. Open a terminal and navigate to the `server` directory:

	```bash
	cd server
	```

2. Create a virtual environment:

	```bash
	python -m venv env
	```

3. Activate the virtual environment (Windows PowerShell):

	```bash
	.\env\Scripts\Activate.ps1
	```

4. Install the required dependencies:

	```bash
	pip install -r requirements.txt
	```

5. Create your local environment file from the example:

	```bash
	copy .env.example .env
	```

	Then edit `.env` and add your real API key(s).

6. Run the server:

	```bash
	uvicorn main:app --host 127.0.0.1 --port 8000 --reload
	```

LLM config lives in `server/.env`.
Provider selection:
- `LLM_PROVIDER=auto` tries `openai -> gemini -> huggingface`
- or set `LLM_PROVIDER=openai|gemini|huggingface` to force one provider

If no configured provider is available at runtime, dataset/personal recommendation endpoints return an explicit error.

Troubleshooting `POST /recommendation` -> `503`:
- If using only Hugging Face (`LLM_PROVIDER=huggingface`), the selected model may be cold/unavailable.
- Prefer `LLM_PROVIDER=auto` so the backend can fallback to any configured provider.
- For HF-only mode, try a smaller widely available model and keep retries enabled:
	- `HUGGINGFACE_MODEL=Qwen/Qwen2.5-7B-Instruct`
	- `HUGGINGFACE_RETRIES=3`
	- `HUGGINGFACE_MAX_NEW_TOKENS=420` (used as base; backend scales tokens with candidate count)
	- Optional custom endpoint base: `HUGGINGFACE_API_BASE=https://router.huggingface.co/hf-inference/models`
	- To print raw LLM output for parser debugging: `LLM_DEBUG=true`

Hugging Face endpoint note:
- The backend uses `https://router.huggingface.co/v1/chat/completions` as the primary HF route.
- This route is OpenAI-compatible and worked with `Qwen/Qwen2.5-7B-Instruct` in this project.

---

## Client Environment Setup

Create your local client env file from example:

```bash
copy .env.example .env.local
```

The default value in `.env.local` is:

```env
FASTAPI_URL=http://127.0.0.1:8000
```

Then run the client with:

```bash
npm run dev
```

Important: after creating/changing `.env` or `.env.local`, restart both servers so env values are reloaded.

Note: use `npm run build` then `npm start` only for production mode.

---


## Database Function Support

The following database functions are supported:

- **add**: Insert a new record
- **search**: Retrieve records (with optional filtering)
- **update**: Modify an existing record (by ID)
- **delete**: Remove a record (by ID)

---

## Recommendation Modes

The backend now supports:

- **dataset mode** (`mode=dataset`): takes existing `user_id` (MovieLens 1-943)
- **personal mode** (`mode=personal`): takes fresh user profile (`age`, `gender`, `occupation`, `genres`)
- **evaluate mode** (`mode=evaluate`): returns binary Hit Rate and NDCG for a selected split

### Core Pipeline

1. Build SVD user/item embeddings from MovieLens ratings.
2. Cluster users by SVD vectors using KMeans.
3. Train LogisticRegression from demographics + genre preferences to cluster labels.
4. Runtime:
	- Existing users: use their learned SVD vector.
	- Fresh users: predict cluster, then use cluster centroid vector.
5. Retrieve candidate movies and apply genre boost.
6. LLM reranking is mandatory and produces final scores, short reasons, and summaries.

Set at least one provider key (`OPENAI_API_KEY`, `GEMINI_API_KEY`, or `HUGGINGFACE_API_KEY`) to run the system. Requests fail with a clear error if LLM scoring is unavailable across providers.

Security note:
- Real env files are gitignored (`server/.env`, `client/.env.local`)
- Only `server/.env.example` and `client/.env.example` are committed

---

## Evaluation For Report (Hit Rate + NDCG)

Run from the `server` directory after installing requirements:

```bash
python evaluate.py --splits u1,u2,u3,u4,u5 --ks 5,10,15 --out evaluation_results.json
```

This evaluation uses LLM scoring by default to align with the project objective.
Use `--no-llm` only for local debugging, not for final report numbers.

This writes a table-ready JSON file containing:

- `split`
- `k`
- `hit_rate`
- `ndcg`
- `evaluated_users`

You can include these rows in your PDF tables and add your YouTube demo link, as required.

### Fast LLM Evaluation (100-150 Users)

Use these commands when you want LLM-based metrics quickly before a full run.

From the `server` directory:

```bash
# Quick sample (about 100 users per split)
python evaluate.py --splits u1,u2,u3,u4,u5 --ks 5,10,15 --max-users 100 --rank-top-n 80 --out evaluation_results_llm_100.json --no-progress

# Slightly larger sample (about 150 users per split)
python evaluate.py --splits u1,u2,u3,u4,u5 --ks 5,10,15 --max-users 150 --rank-top-n 80 --out evaluation_results_llm_150.json --no-progress
```

Why this is faster:
- `--max-users` limits users per split.
- `--rank-top-n 80` reduces rerank depth while still covering K up to 15.
- `--no-progress` avoids tqdm/log overhead.

Then compare with the non-LLM baseline file:
- `evaluation_results_no_llm_full.json`