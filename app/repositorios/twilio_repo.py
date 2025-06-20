from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import os

# Inicializar el cliente Twilio (si quisieras enviar mensajes reales)
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

def crear_respuesta_twilio():
    """Devuelve un objeto MessagingResponse limpio."""
    return MessagingResponse()

def enviar_sms(numero_destino, mensaje):
    """Envia un SMS real (si quisieras usarlo)."""
    return twilio_client.messages.create(
        body=mensaje,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        to=numero_destino
    )
