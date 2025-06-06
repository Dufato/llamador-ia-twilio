import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generar_audio(texto, archivo_salida="static/audio_llamada.mp3"):
    response = openai.audio.speech.create(
        model="tts-1",
        voice="nova",  # También puedes probar "shimmer", "echo", etc.
        input=texto
    )

    # Guardar audio en un archivo accesible
    with open(archivo_salida, "wb") as f:
        f.write(response.content)
