import json
import os
from pathlib import Path
from urllib.parse import quote

import httpx
from dotenv import load_dotenv


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    load_dotenv(base_dir / ".env")

    token = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
    if not token:
        print("Missing HUGGINGFACE_API_KEY/HF_TOKEN in server/.env")
        return

    models = [
        os.getenv("HUGGINGFACE_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
        "mistralai/Mistral-7B-Instruct-v0.1",
        "HuggingFaceH4/zephyr-7b-beta",
    ]

    payload = {
        "inputs": "Return strict JSON: {\"results\": [{\"movie_id\": 1, \"llm_score\": 77, \"reason\": \"demo\", \"summary\": \"demo\"}]}",
        "parameters": {
            "max_new_tokens": 120,
            "temperature": 0.2,
            "return_full_text": False,
        },
        "options": {
            "wait_for_model": True,
            "use_cache": False,
        },
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    endpoint_templates = [
        "https://router.huggingface.co/hf-inference/models/{model}",
        "https://api-inference.huggingface.co/models/{model}",
        "https://api-inference.huggingface.co/pipeline/text-generation/{model}",
    ]

    with httpx.Client(timeout=60.0) as client:
        for model in models:
            encoded = quote(model, safe="/")
            print(f"\n=== Model: {model} ===")
            for template in endpoint_templates:
                url = template.format(model=encoded)
                try:
                    resp = client.post(url, headers=headers, json=payload)
                    print(f"{url} -> HTTP {resp.status_code}")
                    body = resp.text.strip().replace("\n", " ")
                    print(body[:400])
                except Exception as exc:
                    print(f"{url} -> ERROR: {exc}")

        print("\n=== OpenAI-Compatible HF Router Check ===")
        for model in models:
            chat_payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Reply with strict JSON: {\"ok\": true}",
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 64,
            }
            try:
                resp = client.post(
                    "https://router.huggingface.co/v1/chat/completions",
                    headers=headers,
                    json=chat_payload,
                )
                print(f"model={model} -> HTTP {resp.status_code}")
                print(resp.text[:400].replace("\n", " "))
            except Exception as exc:
                print(f"model={model} -> ERROR: {exc}")


if __name__ == "__main__":
    main()
