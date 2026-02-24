from spotify_client import get_top_5_weekly
import random

def spotify_intake(state):
    print("--- [Node] Spotify Intake ---")
    try:
        top_5 = get_top_5_weekly()
        if not top_5:
            return {"status": "error", "selected_track": None}
        
        # Select a track to focus on
        # Logic: Pick one randomly, or could use memory to see which wasn't picked recently
        selected_track = random.choice(top_5)
        
        return {
            "top_5_tracks": top_5,
            "selected_track": selected_track,
            "status": "researching"
        }
    except Exception as e:
        print(f"Spotify Node Error: {e}")
        return {"status": "error"}
