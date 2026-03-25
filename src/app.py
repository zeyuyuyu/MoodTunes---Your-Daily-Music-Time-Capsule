import spotipy
from spotipy.oauth2 import SpotifyOAuth
from textblob import TextBlob
import datetime
import json
import os

class MoodTunes:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri='http://localhost:8888/callback',
            scope='playlist-modify-public user-top-reads'
        ))
        self.user_id = self.sp.current_user()['id']

    def analyze_mood(self, journal_entry):
        analysis = TextBlob(journal_entry)
        # Get polarity (-1 to 1) and subjectivity (0 to 1)
        mood_score = analysis.sentiment.polarity
        intensity = analysis.sentiment.subjectivity
        
        return {
            'mood_score': mood_score,
            'intensity': intensity
        }

    def get_music_features(self, mood):
        # Map mood score to musical attributes
        if mood['mood_score'] > 0.3:
            # Happy/Upbeat
            return {'valence': (0.7, 1.0), 'energy': (0.6, 1.0)}
        elif mood['mood_score'] < -0.3:
            # Sad/Melancholic
            return {'valence': (0.0, 0.4), 'energy': (0.2, 0.5)}
        else:
            # Neutral/Balanced
            return {'valence': (0.4, 0.7), 'energy': (0.4, 0.7)}

    def create_mood_playlist(self, journal_entry):
        # Analyze mood from journal
        mood = self.analyze_mood(journal_entry)
        features = self.get_music_features(mood)
        
        # Get recommendations based on user's top tracks
        top_tracks = self.sp.current_user_top_tracks(limit=5, time_range='short_term')
        seed_tracks = [track['id'] for track in top_tracks['items']]
        
        recommendations = self.sp.recommendations(
            seed_tracks=seed_tracks,
            target_valence=sum(features['valence'])/2,
            target_energy=sum(features['energy'])/2,
            limit=20
        )

        # Create new playlist
        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        playlist_name = f'MoodTunes - {date_str}'
        playlist = self.sp.user_playlist_create(
            self.user_id,
            playlist_name,
            description=f'Generated based on your mood on {date_str}'
        )

        # Add tracks to playlist
        track_uris = [track['uri'] for track in recommendations['tracks']]
        self.sp.playlist_add_items(playlist['id'], track_uris)

        return {
            'playlist_id': playlist['id'],
            'playlist_url': playlist['external_urls']['spotify'],
            'mood_analysis': mood,
            'track_count': len(track_uris)
        }

    def save_mood_history(self, journal_entry, playlist_data):
        history = {
            'date': datetime.datetime.now().isoformat(),
            'journal_entry': journal_entry,
            'mood_score': playlist_data['mood_analysis']['mood_score'],
            'playlist_url': playlist_data['playlist_url']
        }
        
        try:
            with open('mood_history.json', 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = []
            
        data.append(history)
        
        with open('mood_history.json', 'w') as f:
            json.dump(data, f, indent=2)

def main():
    mood_tunes = MoodTunes()
    journal_entry = input('How are you feeling today? Write a few sentences: ')
    
    try:
        playlist_data = mood_tunes.create_mood_playlist(journal_entry)
        mood_tunes.save_mood_history(journal_entry, playlist_data)
        
        print(f'\
Created your mood-based playlist! 🎵')
        print(f'Playlist URL: {playlist_data["playlist_url"]}')
        print(f'Mood score: {playlist_data["mood_analysis"]["mood_score"]:.2f}')
        print(f'Number of tracks: {playlist_data["track_count"]}')
        
    except Exception as e:
        print(f'Error creating playlist: {str(e)}')

if __name__ == '__main__':
    main()