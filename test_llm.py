from prompts import generate_batch_prompt
from llm_client import get_batch_ratings_from_llm
import os

target_movies = [{"movie_id": 1, "title": "Test 1", "year": "1994", "genres": "Drama"}, {"movie_id": 2, "title": "Test 2", "year": "1995", "genres": "Comedy"}]
prompt = generate_batch_prompt(25, "M", "Engineer", ["Star Wars", "Matrix"], ["Twilight"], target_movies)

try:
    if "GEMINI_API_KEY" in os.environ:
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        print("RAW RESPONSE:")
        print(response.text)
except Exception as e:
    print(f"API ERROR: {e}")

print("PARSED SCORES:")
print(get_batch_ratings_from_llm(prompt, 2))
