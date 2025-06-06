import os
from dotenv import load_dotenv
from twilio.rest import Client
from app import create_app

# Cargar variables de entorno
load_dotenv()

# Crear la app de Flask
app = create_app()

def realizar_llamada():
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )

    # Lanzar llamada usando la ruta que devuelve el XML con el audio generado
    llamada = client.calls.create(
        to=os.getenv("DESTINATION_PHONE"),
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        url=f"{os.getenv('BASE_URL')}/twilio/verificacion" # <- ESTA ES TU NUEVA RUTA
    )

    print(f"Llamada iniciada con SID: {llamada.sid}")

if __name__ == "__main__":
    # Primero lanza la llamada
    realizar_llamada()
    # Luego corre tu servidor Flask
    app.run(port=5000)
