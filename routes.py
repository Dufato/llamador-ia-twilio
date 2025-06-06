import os
from flask import Blueprint, request, Response, send_file, current_app
from twilio.twiml.voice_response import VoiceResponse
from openai import OpenAI
import uuid

main = Blueprint('main', __name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Ruta para servir archivos de audio por nombre único
@main.route("/static/<filename>")
def serve_audio(filename):
    audio_path = os.path.join(current_app.root_path, "..", "static", filename)
    return send_file(audio_path, mimetype="audio/mpeg")

# Función para generar y guardar audio desde texto
def generar_audio_openai(texto, nombre_archivo):
    respuesta = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=texto
    )
    ruta = os.path.join(current_app.root_path, "..", "static", nombre_archivo)
    with open(ruta, "wb") as f:
        f.write(respuesta.content)
    return f"https://77fb-190-20-96-224.ngrok-free.app/static/{nombre_archivo}"

# Ruta para iniciar la llamada
@main.route("/twilio/verificacion", methods=["POST"])
def verificacion():
    texto = "¿Me comunico con Duban Dreyfus? Por favor responde sí o no después del beep."
    nombre_archivo = f"pregunta_{uuid.uuid4().hex}.mp3"
    url_audio = generar_audio_openai(texto, nombre_archivo)

    response = VoiceResponse()
    response.play(url_audio)
    response.redirect("/twilio/esperando_respuesta?intento=1", method="POST")
    return Response(str(response), mimetype="text/xml")

# Captura la respuesta del usuario con STT
@main.route("/twilio/esperando_respuesta", methods=["POST"])
def esperando_respuesta():
    intento = int(request.args.get("intento", 1))
    response = VoiceResponse()
    gather = response.gather(
        input="speech",
        action=f"/twilio/veredicto?intento={intento}",
        method="POST",
        language="es-ES",
        timeout=4
    )
    return Response(str(response), mimetype="text/xml")

# Analiza la respuesta y actúa
@main.route("/twilio/veredicto", methods=["POST"])
def veredicto():
    intento = int(request.args.get("intento", 1))
    speech_result = request.form.get("SpeechResult", "").strip().lower()
    print(f"🗣️ Usuario dijo: {speech_result}")

    # GPT analiza la respuesta
    prompt = f"""
Actúa como un asistente telefónico chileno. Evalúa si el siguiente texto indica una respuesta afirmativa, negativa o incomprensible a la pregunta "¿Hablo con Duban Dreyfus?". 
También considera si el usuario pide que repitas la pregunta (por ejemplo: "qué?", "cómo?", "aló?", "quién?").

Responde SOLO con una de estas tres opciones:
- afirmativo
- negativo
- repetir
    Texto del usuario: "{speech_result}"
    """

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Eres un asistente que entiende modismos chilenos y respuestas ambiguas."},
            {"role": "user", "content": prompt}
        ]
    )

    resultado = completion.choices[0].message.content.strip().lower()
    print(f"🔎 GPT interpretó como: {resultado}")

    # Preparar respuesta de voz (OpenAI)
    if resultado == "afirmativo":
        texto_respuesta = "Hola Duban, que tengas un día filete."
    elif resultado == "negativo":
        texto_respuesta = "Disculpa las molestias. Que tengas un buen día."
    elif resultado == "repetir" and intento == 1:
        texto_respuesta = "Disculpa, repito: ¿Me comunico con Duban Dreyfus? Por favor responde sí o no después del beep."
        response = VoiceResponse()
        url_audio = generar_audio_openai(texto_respuesta, f"repetir_{uuid.uuid4().hex}.mp3")
        response.play(url_audio)
        response.redirect("/twilio/esperando_respuesta?intento=2", method="POST")
        return Response(str(response), mimetype="text/xml")
    else:
        texto_respuesta = "Lo siento, no entendí tu respuesta. Hasta luego."

    url_audio_final = generar_audio_openai(texto_respuesta, f"respuesta_{uuid.uuid4().hex}.mp3")
    response = VoiceResponse()
    response.play(url_audio_final)
    response.hangup()
    return Response(str(response), mimetype="text/xml")
