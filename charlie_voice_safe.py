import os

def falar(texto, *args, **kwargs):
    # Se estiver mudo ou ElevenLabs desativado → apenas loga
    tts_mode = os.getenv("CHARLIE_TTS_MODE", "auto").lower()
    eleven_on = os.getenv("ELEVENLABS_ENABLED", "true").lower() not in ("0","false","no")

    if tts_mode == "mute" or not eleven_on:
        print(f"📝 [MUTE] {texto}")
        return

    # Caso contrário, tenta usar o charlie_voice real
    try:
        from charlie_voice import falar as _falar
        return _falar(texto, *args, **kwargs)
    except Exception as e:
        print(f"📝 [MUTE_FALLBACK] {texto} (motivo: {e})")
        return
