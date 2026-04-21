import re
from utils.settings import settings
from groq import Groq
from openai import OpenAI, AsyncOpenAI
import google.generativeai as genai


def parse_scores(prediction, expected_count):
    scores_match = re.search(r"<scores>(.*?)</scores>", str(prediction), re.DOTALL | re.IGNORECASE)
    text_to_parse = scores_match.group(1) if scores_match else str(prediction)

    matches = re.findall(r"\d+", text_to_parse)

    if matches:
        scores = [max(0, min(100, int(x))) for x in matches]
        if len(scores) > expected_count:
            return scores[:expected_count]
        if len(scores) < expected_count:
            scores.extend([50] * (expected_count - len(scores)))
        return scores

    return [50] * expected_count


# =========================
# SINGLE RATING
# =========================
def get_rating_from_llm(prompt):
    prediction = None

    # 🔹 OpenAI
    if settings.OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            res = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Output ONLY a single integer."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=5,
            )
            prediction = res.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI Error: {e}")

    # 🔹 Fallback → Groq
    if not prediction and settings.GROQ_API_KEY:
        try:
            client = Groq(api_key=settings.GROQ_API_KEY)
            res = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "Output ONLY a single integer."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            prediction = res.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq Error: {e}")

    # 🔹 Fallback → Gemini
    if not prediction and settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.5-flash")
            res = model.generate_content(
                prompt,
                generation_config={"temperature": 0.0, "max_output_tokens": 5},
            )
            prediction = res.text.strip()
        except Exception as e:
            print(f"Gemini Error: {e}")

    if not prediction:
        return 50

    match = re.search(r"\d+", prediction)
    return max(0, min(100, int(match.group()))) if match else 50


# =========================
# BATCH (SYNC)
# =========================
def get_batch_ratings_from_llm(prompt, expected_count):
    prediction = None

    if settings.OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            res = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Return scores inside <scores> tag"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            prediction = res.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI Error: {e}")

    if not prediction and settings.GROQ_API_KEY:
        try:
            client = Groq(api_key=settings.GROQ_API_KEY)
            res = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Return scores inside <scores> tag"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            prediction = res.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq Error: {e}")

    if not prediction and settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.5-flash")
            res = model.generate_content(prompt)
            prediction = res.text.strip()
        except Exception as e:
            print(f"Gemini Error: {e}")

    return parse_scores(prediction, expected_count)


# =========================
# BATCH (ASYNC)
# =========================
async def get_batch_ratings_from_llm_async(prompt, expected_count):
    prediction = None

    if settings.OPENAI_API_KEY:
        try:
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            res = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Return scores inside <scores> tag"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            prediction = res.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI Async Error: {e}")

    if not prediction and settings.GROQ_API_KEY:
        try:
            client = AsyncOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1",
            )
            res = await client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "Return scores inside <scores> tag"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            prediction = res.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq Async Error: {e}")

    if not prediction and settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.5-flash")
            res = await model.generate_content_async(prompt)
            prediction = res.text.strip()
        except Exception as e:
            print(f"Gemini Async Error: {e}")

    return parse_scores(prediction, expected_count)