import os
import base64
import json
import time
import webbrowser
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional, Tuple

import requests
from dotenv import load_dotenv

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
PROFILE_URL = "https://api.spotify.com/v1/me"
SEARCH_URL = "https://api.spotify.com/v1/search"
SCOPES = ["user-read-email", "user-read-private"]
AUDIO_FEATURES_URL = "https://api.spotify.com/v1/audio-features"
ARTIST_TOP_TRACKS_URL = "https://api.spotify.com/v1/artists/{id}/top-tracks"

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Minimal handler to capture the authorization code from Spotify redirect."""
    # Shared storage for code & state
    auth_code: Optional[str] = None
    auth_state: Optional[str] = None

    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        code = qs.get("code", [None])[0]
        state = qs.get("state", [None])[0]
        error = qs.get("error", [None])[0]

        if error:
            body = f"Autorización fallida: {error}".encode()
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        OAuthCallbackHandler.auth_code = code
        OAuthCallbackHandler.auth_state = state

        body = b"Autenticacion exitosa. Puedes volver a la terminal."
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # Silence logging
    def log_message(self, format, *args):  # noqa: A003
        return


def load_env():
    load_dotenv()
    cid = os.getenv("SPOTIFY_CLIENT_ID")
    secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8080/callback")
    refresh = os.getenv("SPOTIFY_REFRESH_TOKEN")
    if not cid or not secret:
        raise SystemExit("Faltan SPOTIFY_CLIENT_ID o SPOTIFY_CLIENT_SECRET en .env")
    return cid, secret, redirect, refresh


def build_auth_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(SCOPES),
        "state": state,
        "show_dialog": "false"
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    resp = requests.post(TOKEN_URL, data=data, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Error al obtener tokens: {resp.status_code} {resp.text}")
    return resp.json()


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    resp = requests.post(TOKEN_URL, data=data, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Error al refrescar token: {resp.status_code} {resp.text}")
    return resp.json()


def get_profile(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(PROFILE_URL, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Error al obtener perfil: {resp.status_code} {resp.text}")
    return resp.json()


def start_temporary_server(expected_state: str, host: str = "", port: int = 8080) -> Tuple[str, str]:
    OAuthCallbackHandler.auth_code = None
    OAuthCallbackHandler.auth_state = None

    httpd = HTTPServer((host, port), OAuthCallbackHandler)
    start_time = time.time()
    print("Esperando autorización (timeout 120s)...")
    while time.time() - start_time < 120:
        httpd.handle_request()
        if OAuthCallbackHandler.auth_code:
            if OAuthCallbackHandler.auth_state != expected_state:
                raise RuntimeError("State inválido (posible ataque CSRF).")
            return OAuthCallbackHandler.auth_code, OAuthCallbackHandler.auth_state
    raise TimeoutError("Timeout esperando la redirección de Spotify")


def client_credentials_token(client_id: str, client_secret: str) -> str:
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = {"grant_type": "client_credentials"}
    headers = {"Authorization": f"Basic {auth_header}", "Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(TOKEN_URL, data=data, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Error client credentials: {resp.status_code} {resp.text}")
    return resp.json()["access_token"]


def public_search_test(access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(SEARCH_URL, params={"q": "daft", "type": "artist", "limit": 1}, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Error búsqueda pública: {resp.status_code} {resp.text}")
    data = resp.json()
    artist = data.get("artists", {}).get("items", [{}])[0].get("name")
    print(f"Búsqueda pública OK. Ejemplo artista: {artist}")


def search_artist(access_token: str, query: str) -> Optional[dict]:
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(SEARCH_URL, params={"q": query, "type": "artist", "limit": 5}, headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"Error buscando artista '{query}': {resp.status_code}")
        return None
    items = resp.json().get("artists", {}).get("items", [])
    if not items:
        print(f"No se encontró artista para '{query}'")
        return None
    # Elegir el primer resultado
    return items[0]


def get_artist_top_tracks(access_token: str, artist_id: str, market: str = "US") -> list:
    headers = {"Authorization": f"Bearer {access_token}"}
    url = ARTIST_TOP_TRACKS_URL.format(id=artist_id)
    resp = requests.get(url, params={"market": market}, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Error top tracks: {resp.status_code} {resp.text}")
    return resp.json().get("tracks", [])


def get_audio_features(access_token: str, track_ids: list) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    features = {}
    # Spotify permite hasta 100 IDs por llamada
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        resp = requests.get(AUDIO_FEATURES_URL, params={"ids": ",".join(batch)}, headers=headers, timeout=30)
        if resp.status_code != 200:
            dbg = os.getenv("DEBUG_SPOTIFY")
            if dbg:
                print("[DEBUG] Falla batch audio-features", resp.status_code, resp.text[:300])
                print("[DEBUG] Primeros IDs:", batch[:5])
            # Devolver información del fallo para que el llamador intente fallback
            raise RuntimeError(f"BATCH_ERROR::{resp.status_code}::{resp.text}")
            
        for feat in resp.json().get("audio_features", []) or []:
            if feat and feat.get("id"):
                features[feat["id"]] = feat
    return features


def get_audio_feature_single(access_token: str, track_id: str) -> Optional[dict]:
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{AUDIO_FEATURES_URL}/{track_id}"
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        return None
    return resp.json()


def analyze_buerak_energy(access_token: str, artist_query: str = "buerak"):
    print("\n--- Analizando energía de canciones de Buerak ---")
    artist = search_artist(access_token, artist_query)
    if not artist and artist_query.lower() == "buerak":
        # Intentar posible nombre en ruso
        artist = search_artist(access_token, "Буерак")
    if not artist:
        print("No se pudo localizar el artista Buerak/Буерак")
        return
    artist_id = artist.get("id")
    artist_name = artist.get("name")
    print(f"Artista encontrado: {artist_name} (id={artist_id})")
    try:
        top_tracks = get_artist_top_tracks(access_token, artist_id, market="US")
    except Exception as e:
        print(f"Fallo obteniendo top tracks: {e}")
        return
    if not top_tracks:
        print("No hay top tracks disponibles para este artista.")
        return
    track_ids = [t.get("id") for t in top_tracks if t.get("id")]
    try:
        features_map = get_audio_features(access_token, track_ids)
    except RuntimeError as e:
        msg = str(e)
        if msg.startswith("BATCH_ERROR::403"):
            print("Batch audio features devolvió 403. Intentando fallback individual por pista...")
            features_map = {}
            for tid in track_ids:
                single = get_audio_feature_single(access_token, tid)
                if single:
                    features_map[tid] = single
                else:
                    print(f"  - Sin features para {tid}")
            # Si todavía vacío, intentar nuevo token client credentials por si el token de usuario tiene restricción
            if not features_map:
                try:
                    print("Intentando nuevo token client credentials para audio features...")
                    cc_token = client_credentials_token(os.getenv("SPOTIFY_CLIENT_ID"), os.getenv("SPOTIFY_CLIENT_SECRET"))
                    for tid in track_ids:
                        single = get_audio_feature_single(cc_token, tid)
                        if single:
                            features_map[tid] = single
                except Exception as e2:
                    print(f"Fallback client credentials también falló: {e2}")
            if not features_map:
                print("No se pudo obtener audio features (403 en batch y en individuales).")
                return
        else:
            print(f"Error obteniendo audio features: {msg}")
            return
    enriched = []
    for t in top_tracks:
        f = features_map.get(t.get("id"))
        if not f:
            continue
        enriched.append({
            "name": t.get("name"),
            "id": t.get("id"),
            "energy": f.get("energy"),
            "tempo": f.get("tempo"),
            "danceability": f.get("danceability"),
            "valence": f.get("valence"),
            "duration_ms": f.get("duration_ms")
        })
    if not enriched:
        print("No se pudieron obtener audio features.")
        return
    enriched.sort(key=lambda x: (x.get("energy") or 0), reverse=True)
    top3 = enriched[:3]
    print("Top 3 por energía:")
    for idx, tr in enumerate(top3, start=1):
        dur_sec = (tr["duration_ms"] or 0) / 1000
        print(f"{idx}. {tr['name']} | energy={tr['energy']:.3f} tempo={tr['tempo']:.1f} bpm danceability={tr['danceability']:.3f} valence={tr['valence']:.3f} duración={dur_sec:.1f}s")
    # Promedio general
    avg_energy = sum((t['energy'] or 0) for t in enriched) / len(enriched)
    print(f"Energía promedio top tracks: {avg_energy:.3f}")


def main():
    client_id, client_secret, redirect_uri, existing_refresh = load_env()
    state = os.urandom(8).hex()

    token_data = None

    if existing_refresh:
        try:
            print("Usando refresh token existente para renovar access token...")
            token_data = refresh_access_token(client_id, client_secret, existing_refresh)
        except Exception as e:
            print(f"Fallo al refrescar token: {e}. Intentando nuevo flujo OAuth...")

    if token_data is None:
        try:
            print("Iniciando flujo OAuth (authorization code) para obtener tokens de usuario...")
            auth_url = build_auth_url(client_id, redirect_uri, state)
            print(f"Abre este URL en tu navegador si no se abre automáticamente:\n{auth_url}\n")
            try:
                webbrowser.open(auth_url)
            except Exception:
                pass
            code, _ = start_temporary_server(state, port=urllib.parse.urlparse(redirect_uri).port or 8080)
            token_data = exchange_code_for_tokens(client_id, client_secret, code, redirect_uri)
            if 'refresh_token' in token_data:
                print("Refresh token obtenido. Guárdalo en tu .env como SPOTIFY_REFRESH_TOKEN para no repetir el login.")
                print(token_data['refresh_token'])
        except Exception as e:
            print(f"No se pudo completar flujo de usuario: {e}")

    if token_data is None:
        print("Usando fallback client credentials (solo endpoints públicos)...")
        access_token = client_credentials_token(client_id, client_secret)
        public_search_test(access_token)
        print("API funcionando (modo público) ✅")
        return

    access_token = token_data['access_token']
    # Probar perfil
    try:
        profile = get_profile(access_token)
        print("\n=== PERFIL ===")
        print(json.dumps({
            'id': profile.get('id'),
            'display_name': profile.get('display_name'),
            'email': profile.get('email'),
            'product': profile.get('product')
        }, ensure_ascii=False, indent=2))
        print("\nAPI funcionando correctamente (token de usuario) ✅")
        try:
            analyze_buerak_energy(access_token)
        except Exception as e:
            print(f"(Aviso) Falló análisis de energía: {e}")
    except Exception as e:
        print(f"Fallo al acceder a /me: {e}. Probando búsqueda pública...")
        public_search_test(access_token)
        print("API funcionando (token sin alcance de perfil) ✅")
        try:
            analyze_buerak_energy(access_token)
        except Exception as e2:
            print(f"(Aviso) Falló análisis de energía: {e2}")
if __name__ == "__main__":
    main()
