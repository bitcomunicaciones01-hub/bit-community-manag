import os
from openai import OpenAI
from duckduckgo_search import DDGS
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RADIO_NAME = os.getenv("RADIO_NAME", "Futura Radio")
RADIO_THEME = os.getenv("RADIO_THEME", "Futuristic, Cyberpunk")
RADIO_PERSONA = os.getenv("RADIO_PERSONA", "AI Community Manager from 2099")

def research_artist(artist_name):
    """
    Searches for recent news or interesting facts about the artist.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{artist_name} band news 2026", max_results=3))
            search_data = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
            return search_data
    except Exception as e:
        print(f"Search error: {e}")
        return "No specific recent data found, but they are trending globally."

def generate_content_for_artist(track):
    artist_context = research_artist(track['artist'])
    
    prompt = f"""
    You are {RADIO_NAME}'s community manager. 
    Persona: {RADIO_PERSONA}
    Theme: {RADIO_THEME}

    Your task is to create a viral, futuristic Instagram caption for a post about the song "{track['name']}" by "{track['artist']}" from the album "{track['album']}".
    
    Artist Research Data:
    {artist_context}
    
    Requirements:
    1. Use a high-tech, visionary, and energetic tone.
    2. Incorporate the research data in a way that sounds like it's from the future.
    3. Use relevant emojis (satellites, neon, chips, etc.).
    4. Include hashtags: #{RADIO_NAME.replace(' ', '')} #FuturisticRadio #MusicRanking #Top5Weekly #{track['artist'].replace(' ', '')}.
    5. The output should be only the caption in Spanish.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un Community Manager IA especializado para una radio futurista."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Content gen error: {e}")
        return f"¡Sintoniza la frecuencia del futuro! Hoy escuchamos a {track['artist']} con '{track['name']}'. #FuturaRadio"

def generate_image_prompt(track):
    """
    Generates a prompt for an AI image generator.
    """
    prompt = f"Create a high-resolution, futuristic, cyberpunk-style 1080x1080 visual for the artist '{track['artist']}'. Use neon colors, holograms, and sci-fi radio elements. The vibe is sleek and premium."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a expert prompt engineer for DALL-E 3."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Futuristic cyberpunk visual for {track['artist']}"

if __name__ == "__main__":
    # Test logic
    test_track = {"name": "Test Song", "artist": "Dua Lipa", "album": "Future Nostalgia"}
    print(generate_content_for_artist(test_track))
