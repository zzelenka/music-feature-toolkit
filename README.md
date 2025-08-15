# Music Feature Toolkit (Spotify + GetSongBPM)

Herramientas en Python para:
1. Verificar y diagnosticar credenciales de Spotify (incluye flujos OAuth, fallback y análisis de energía de un artista)
2. Consultar BPM y tonalidad usando la API de **GetSongBPM** (cumpliendo su requisito de backlink / crédito)
3. Base para futuros módulos de análisis y creación de playlists.

> Créditos obligatorios: Este proyecto utiliza datos de BPM y key proporcionados por [GetSongBPM.com](https://getsongbpm.com) — enlace requerido por sus términos.

## Requisitos
- Python 3.8+
- Credenciales en tu panel de desarrollador Spotify (CLIENT ID / CLIENT SECRET)
- Redirect URI registrado (ej: `http://localhost:8080/callback`)

## Instalación
```bash
pip install -r requirements.txt
```

## Configura tu `.env`
Crea un archivo `.env` (basado en `.env.example`):
```
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=http://localhost:8080/callback
SPOTIFY_REFRESH_TOKEN=
```
`SPOTIFY_REFRESH_TOKEN` puedes dejarlo vacío la primera vez. El script te mostrará uno tras autorizar.

## Uso
```bash
python spotify_check.py
```
El script intentará:
1. Usar un refresh token si existe.
2. Si no, lanzar el flujo Authorization Code para obtener tokens de usuario y un refresh token.
3. Si falla lo anterior, usar Client Credentials (solo endpoints públicos) y hacer una búsqueda de ejemplo.

## Resultado Esperado
- Datos de tu perfil si el token es de usuario.
- O un mensaje de búsqueda pública exitosa con un artista de ejemplo.

## Guardar el Refresh Token
Copia el valor que imprime y pégalo en tu `.env` como `SPOTIFY_REFRESH_TOKEN` para futuras ejecuciones sin reautorizar.

## Problemas Comunes
- `INVALID_CLIENT`: verifica ID y Secret.
- `redirect_uri_mismatch`: asegúrate que coincide EXACTAMENTE con el registrado en el dashboard.
- Navegador no se abre: copia la URL que se imprime y pégala manualmente.

## Seguridad
No compartas tu refresh token ni tu client secret. Puedes revocar permisos desde tu cuenta de Spotify.

---
## API GetSongBPM

La API pública requiere una API key y un backlink obligatorio. Añade en tu `.env`:
```
GETSONGBPM_API_KEY=tu_api_key
```
Ejemplo de uso (script `getsongbpm_client.py` que añadiremos):
```bash
python getsongbpm_client.py --artist "Daft Punk" --track "Harder Better Faster Stronger"
```
Devuelve BPM y tonalidad si la base de datos lo contiene.

## Backlink / Créditos
Incluye en tu página (GitHub Pages) un enlace visible: 
`Datos de BPM y tonalidad por cortesía de GetSongBPM.com` enlazando a https://getsongbpm.com

## Roadmap breve
- [ ] Exportar análisis combinado (Spotify audio features + GetSongBPM) a CSV
- [ ] Caché local para evitar repetir requests
- [ ] Módulo de normalización de tonalidades (enharmónicos)
- [ ] Integración con AcousticBrainz (fallback libre)

---
Proyecto en evolución. Script original generado automáticamente y extendido.
