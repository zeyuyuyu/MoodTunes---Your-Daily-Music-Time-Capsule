import os
from datetime import datetime
from typing import List, Dict
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configure Spotify client
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

SCOPES = [
    'playlist-modify-public',
    'user-read-recently-played',
    'user-top-read'
]

# Mood to audio features mapping
MOOD_FEATURES = {
    'happy': {'valence': 0.7, 'energy': 0.7, 'danceability': 0.7},
    'sad': {'valence': 0.3, 'energy': 0.3, 'danceability': 0.4},
    'energetic': {'valence': 0.6, 'energy': 0.8, 'danceability': 0.8},
    'relaxed': {'valence': 0.5, 'energy': 0.3, 'danceability': 0.4},
    'focused': {'valence': 0.5, 'energy': 0.5, 'danceability': 0.4}
}

def get_spotify_client():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPES
    ))

def get_recommended_tracks(sp: spotipy.Spotify, mood: str, limit: int = 20) -> List[Dict]:
    """Get recommended tracks based on mood."""
    # Get user's top tracks as seed
    top_tracks = sp.current_user_top_tracks(limit=5, time_range='short_term')
    seed_tracks = [track['id'] for track in top_tracks['items']]

    # Get mood-based recommendations
    features = MOOD_FEATURES[mood]
    recommendations = sp.recommendations(
        seed_tracks=seed_tracks[:2],
        limit=limit,
        target_valence=features['valence'],
        target_energy=features['energy'],
        target_danceability=features['danceability']
    )

    return recommendations['tracks']

def create_mood_playlist(sp: spotipy.Spotify, mood: str) -> Dict:
    """Create a new playlist based on user's mood."""
    user_id = sp.current_user()['id']
    date_str = datetime.now().strftime('%Y-%m-%d')
    playlist_name = f'MoodTunes: {mood.capitalize()} - {date_str}'

    # Create playlist
    playlist = sp.user_playlist_create(
        user=user_id,
        name=playlist_name,
        description=f'Auto-generated playlist for {mood} mood'
    )

    # Get and add recommended tracks
    tracks = get_recommended_tracks(sp, mood)
    track_uris = [track['uri'] for track in tracks]
    sp.playlist_add_items(playlist['id'], track_uris)

    return {
        'playlist_id': playlist['id'],
        'playlist_url': playlist['external_urls']['spotify'],
        'track_count': len(track_uris)
    }

@app.route('/generate-playlist', methods=['POST'])
def generate_playlist():
    data = request.get_json()
    mood = data.get('mood')

    if not mood or mood not in MOOD_FEATURES:
        return jsonify({
            'error': 'Invalid mood. Must be one of: ' + 
                    ', '.join(MOOD_FEATURES.keys())
        }), 400

    try:
        sp = get_spotify_client()
        playlist_info = create_mood_playlist(sp, mood)
        return jsonify(playlist_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
