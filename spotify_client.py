import os
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from openai import OpenAI

load_dotenv()

def get_top_5_from_web():
    """
    Fallback function to get Top 5 songs by searching the web and parsing with LLM.
    Used when Spotify API credentials are unobtainable.
    """
    print("⚠️ Spotify API keys missing or invalid. Switching to Web Search Mode...")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    query = "site:spotifycharts.com OR site:billboard.com current top 5 global songs this week"
    print(f"🔎 Searching web for: {query}")
    
    search_text = ""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            search_text = "\n".join([f"{r['title']}: {r['body']}" for r in results])
    except Exception as e:
        print(f"Web search failed: {e}")
        return []
        
    print("🧠 Parsing search results with AI...")
    prompt = f"""
    Based on the following search results about the current Global Music Charts (Spotify/Billboard):
    {search_text}
    
    Extract the Top 5 songs. 
    CRITICAL: Return a JSON List of Objects. Do NOT return a list of strings.
    If the search results are messy or incomplete, INFERS the top songs based on recent hits (e.g. Sabrina Carpenter, Billie Eilish, Shaboozey) mentioned in the text.
    
    Each object MUST have: "name", "artist", "album", "image".
    
    Correct JSON Format:
    [
      {{"name": "Song Title", "artist": "Artist Name", "album": "Album", "image": "URL"}},
      {{"name": "Song Title 2", "artist": "Artist Name 2", "album": "Album", "image": "URL"}}
    ]
    """
    
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        # Debug: Print raw content to seeing what LLM is returning
        print(f"DEBUG LLM OUTPUT: {content[:200]}...")
        
        # Clean markdown if present
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        elif "```" in content:
             content = content.replace("```", "")
             
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            print(f"JSON Decode Error. Raw content: {content}")
            raise ValueError("LLM did not return valid JSON.")
        
        # Robust extraction strategy
        raw_list = []
        if isinstance(data, list):
            raw_list = data
        elif isinstance(data, dict):
            raw_list = data.get("top_5", data.get("songs", list(data.values())[0]))
        
        clean_tracks = []
        for item in raw_list:
            if isinstance(item, str):
                # If LLM returned strings, try to parse them or just skip/fix
                clean_tracks.append({
                    "name": item, 
                    "artist": "Unknown Artist", 
                    "album": "Single", 
                    "image": "https://placehold.co/1080?text=Hit"
                })
            elif isinstance(item, dict):
                clean_tracks.append({
                    "name": item.get("name", "Unknown"),
                    "artist": item.get("artist", "Unknown Artist"),
                    "album": item.get("album", "Single"),
                    "image": item.get("image", "https://placehold.co/1080?text=Music"),
                    "url": item.get("url", "") # enhance compatibility
                })
                
        if not clean_tracks:
            raise ValueError("No valid tracks parsed.")
            
        return clean_tracks

    except Exception as e:
        print(f"AI Parsing failed: {e}")
        # Emergency hardcoded fallback
        return [
            {"name": "Espresso", "artist": "Sabrina Carpenter", "album": "Single", "image": "https://placehold.co/1080?text=Espresso", "url": ""},
            {"name": "Lunch", "artist": "Billie Eilish", "album": "Hit Me Hard and Soft", "image": "https://placehold.co/1080?text=Lunch", "url": ""}
        ]

def get_top_5_weekly():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    # Try API first
    if client_id and client_secret and client_id != "your_spotify_client_id":
        try:
            auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
            sp = spotipy.Spotify(auth_manager=auth_manager)
            
            # Using "Top 50 - Global" playlist ID
            playlist_id = '37i9dQZEVXbMDoHDw32BYs'
            results = sp.playlist_items(playlist_id, limit=5)
            
            tracks = []
            for item in results['items']:
                track = item['track']
                tracks.append({
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "album": track['album']['name'],
                    "url": track['external_urls']['spotify'],
                    "image": track['album']['images'][0]['url']
                })
            return tracks
        except Exception as e:
            print(f"Spotify API Error: {e}")
            return get_top_5_from_web()
    else:
        # Fallback if no keys
        return get_top_5_from_web()

if __name__ == "__main__":
    # Test
    print(json.dumps(get_top_5_weekly(), indent=2))
