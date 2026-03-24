import os
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

class MoodTunesApp:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
        ))
        self.user_mood = None
        self.recommended_tracks = []

    def set_user_mood(self, mood):
        self.user_mood = mood

    def get_mood_playlists(self):
        playlists = self.sp.search(q=f'mood:{self.user_mood}', type='playlist', limit=10)
        return playlists['playlists']['items']

    def get_recommended_tracks(self):
        if not self.recommended_tracks:
            playlists = self.get_mood_playlists()
            for playlist in playlists:
                tracks = self.sp.playlist_tracks(playlist['id'])['items']
                self.recommended_tracks.extend([track['track']['id'] for track in tracks])
            random.shuffle(self.recommended_tracks)
        return self.recommended_tracks[:10]

if __name__ == '__main__':
    app = MoodTunesApp()
    app.set_user_mood('happy')
    print(app.get_recommended_tracks())