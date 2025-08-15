import os
import argparse
import requests
from dotenv import load_dotenv

BASE_URL = os.getenv("GETSONGBPM_BASE_URL", "https://api.getsongbpm.com").rstrip('/')

load_dotenv()
API_KEY = os.getenv("GETSONGBPM_API_KEY")

if not API_KEY:
    print("Falta GETSONGBPM_API_KEY en .env")


def request(endpoint: str, params: dict):
    params = {**params, 'api_key': API_KEY}
    r = requests.get(f"{BASE_URL}/{endpoint.lstrip('/')}", params=params, timeout=20)
    if r.status_code != 200:
        raise SystemError(f"HTTP {r.status_code}: {r.text}")
    return r.json()


def search_artist(name: str):
    return request('search/', {'type': 'artist', 'lookup': name})


def search_track(artist: str, track: str):
    return request('search/', {'type': 'both', 'lookup': f"{artist} {track}"})


def main():
    parser = argparse.ArgumentParser(description='Cliente simple GetSongBPM (BPM + Key).')
    parser.add_argument('--artist', required=True, help='Nombre del artista')
    parser.add_argument('--track', required=True, help='Título del track')
    args = parser.parse_args()

    if not API_KEY:
        return

    data = search_track(args.artist, args.track)

    results = data.get('search', []) if isinstance(data, dict) else []
    if not results:
        print('No se encontraron resultados.')
        return

    # Tomar el primer resultado
    item = results[0]
    bpm = item.get('tempo') or item.get('bpm')
    key = item.get('key') or item.get('tonality')
    print(f"Resultado: {item.get('artist','?')} - {item.get('song_title','?')}")
    print(f"BPM: {bpm} | Key: {key}")
    print("Crédito obligatorio: Datos de BPM y tonalidad por cortesía de https://getsongbpm.com")

if __name__ == '__main__':
    main()
