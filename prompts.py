def generate_prompt(age, gender, occupation, high_rated_movies, low_rated_movies, target_movie, target_genres):
    """
    Generates a prompt for the LLM to predict a movie rating likelihood.
    """
    prompt = f"""You are an advanced recommendation system and an expert movie critic.
You need to predict the likelihood that a specific user will enjoy the target movie on a scale from 0 to 100.

### User Profile
- Age: {age}
- Gender: {gender}
- Occupation: {occupation}

### User's Movie History
The user has previously ENJOYED these movies (rated 4 or 5 out of 5):
{", ".join(high_rated_movies) if high_rated_movies else "None recorded."}

The user DISLIKED these movies (rated 1 or 2 out of 5):
{", ".join(low_rated_movies) if low_rated_movies else "None recorded."}

### Target Movie
- Title: {target_movie}
- Genres: {target_genres}

Predict the likelihood (0-100) this user will enjoy '{target_movie}'.
Output your prediction as a single integer between 0 and 100. Do not output any explanation or extra text.
"""
    return prompt

def generate_batch_prompt(age, gender, occupation, high_rated_movies, low_rated_movies, target_movies):
    movies_text = ""
    for idx, m in enumerate(target_movies):
        movies_text += f"{idx+1}. Title: {m['title']} | Year: {m.get('year', 'Unknown')} | Genres: {m['genres']}\n"

    prompt = f"""You are an advanced recommendation system and an expert movie critic.
You need to predict the likelihood that a specific user will enjoy a list of target movies on a scale from 0 to 100.

### User Profile
- Age: {age}
- Gender: {gender}
- Occupation: {occupation}

### User's Movie History
The user has previously ENJOYED these movies (rated 4 or 5 out of 5):
{", ".join(high_rated_movies) if high_rated_movies else "None recorded."}

The user DISLIKED these movies (rated 1 or 2 out of 5):
{", ".join(low_rated_movies) if low_rated_movies else "None recorded."}

### Target Movies
{movies_text}

Predict the likelihood (0-100) this user will enjoy EACH of the target movies.
First, optionally think step-by-step natively or inside a <thought> block about similarities in genres or release years.
Then, you MUST output your final predictions inside a <scores> tag as a comma-separated list of EXACTLY {len(target_movies)} integers in the exact same order. Do NOT output any other text after the <scores> block.
Example output format:
<thought>
...brief reasoning...
</thought>
<scores>85, 42, 90, 10</scores>
"""
    return prompt
