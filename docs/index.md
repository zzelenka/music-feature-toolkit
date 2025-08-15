# Music Feature Toolkit

Bienvenido. Este proyecto combina:

1. Verificación avanzada de Spotify (OAuth, refresh, fallbacks)  
2. Consulta de BPM y Key vía **GetSongBPM**  
3. Base para análisis y generación de playlists.

## Objetivo
Crear un conjunto modular de scripts para explorar características musicales (energía, tempo, tonalidad) y apoyar la curación algorítmica de playlists.

## Créditos y Backlink
Datos de BPM y tonalidad por cortesía de <a href="https://getsongbpm.com" rel="nofollow" target="_blank">GetSongBPM.com</a>

## Componentes
- `spotify_check.py`: Diagnóstico y extracción básica de features (energía relativa) vía Spotify.
- `getsongbpm_client.py`: Cliente sencillo para recuperar BPM y tonalidad.

## Uso Rápido
```bash
pip install -r requirements.txt
python spotify_check.py
python getsongbpm_client.py --artist "Daft Punk" --track "Harder Better Faster Stronger"
```

## Enlaces
- Repo: https://github.com/zzelenka/music-feature-toolkit
- Página: https://zzelenka.github.io/music-feature-toolkit/

## Roadmap
- Integrar caché local
- Export combinado (Spotify + GetSongBPM)
- Fallback AcousticBrainz
- UI mínima (Streamlit) para consultas manuales

---
Proyecto en construcción.
