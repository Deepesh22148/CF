import os
import re
import time
import asyncio
from dotenv import load_dotenv

load_dotenv()

def parse_scores(prediction, expected_count):
    # Try to extract the block between <scores> and </scores>
    scores_match = re.search(r'<scores>(.*?)</scores>', str(prediction), re.DOTALL | re.IGNORECASE)
    if scores_match:
        text_to_parse = scores_match.group(1)
    else:
        # Fallback to the whole text if tag is missing
        text_to_parse = str(prediction)

    matches = re.findall(r'\d+', text_to_parse)
    if matches:
        scores = [max(0, min(100, int(x))) for x in matches]
        # Ensure return matches expected count by padding or truncating
        if len(scores) > expected_count:
            scores = scores[:expected_count]
        elif len(scores) < expected_count:
            scores.extend([50] * (expected_count - len(scores)))
        return scores
    else:
        return [50] * expected_count

def get_rating_from_llm(prompt):
    """
    Sends the prompt to an LLM based on available API keys.
    Returns an integer score between 0 and 100.
    """
    prediction = None
    
    if os.environ.get("OPENAI_API_KEY"):
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Output ONLY a single integer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=5
            )
            prediction = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API Error: {e}")

    elif os.environ.get("GROQ_API_KEY"):
        from groq import Groq
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Output ONLY a single integer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            prediction = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq API Error: {e}")
            
    elif os.environ.get("GEMINI_API_KEY"):
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=5,
                )
            )
            prediction = response.text.strip()
        except Exception as e:
            print(f"Gemini API Error: {e}")
    else:
        # Fallback or mock mode if no API keys are found
        return 50

    try:
        match = re.search(r'\d+', str(prediction))
        if match:
            rating = int(match.group())
            return max(0, min(100, rating))
        else:
            return 50
    except:
        return 50

def get_batch_ratings_from_llm(prompt, expected_count):
    """
    Sends the batch prompt to an LLM based on available API keys.
    Returns a list of integer scores.
    """
    prediction = None
    
    if os.environ.get("OPENAI_API_KEY"):
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            prediction = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API Error: {e}")

    elif os.environ.get("GROQ_API_KEY"):
        from groq import Groq
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            prediction = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq API Error: {e}")
            
    elif os.environ.get("GEMINI_API_KEY"):
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0
                )
            )
            prediction = response.text.strip()
        except Exception as e:
            print(f"Gemini API Error: {e}")

    return parse_scores(prediction, expected_count)

async def get_batch_ratings_from_llm_async(prompt, expected_count):
    """
    Sends the batch prompt to an LLM asynchronously based on available API keys.
    Returns a list of integer scores.
    """
    prediction = None
    
    if "OPENAI_API_KEY" in os.environ:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
        try:
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            prediction = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI Async API Error: {e}")

    elif os.environ.get("GROQ_API_KEY"):
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1"
        )
        try:
            response = await client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            prediction = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq API Error: {e}")
            
    elif "GEMINI_API_KEY" in os.environ:
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0
                )
            )
            prediction = response.text.strip()
        except Exception as e:
            print(f"Gemini Async API Error: {e}")

    return parse_scores(prediction, expected_count)
