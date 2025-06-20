from flask import Blueprint, request
from app.servicios.mensajes_service import procesar_mensaje
from app.repositorios.firebase_repo import guardar_en_firebase_async
import asyncio

whatsapp_bp = Blueprint("whatsapp", __name__)

@whatsapp_bp.route('/whatsapp', methods=['POST'])
def whatsapp_route():
    try:
        incoming_msg = request.form.get('Body', '').strip().lower()
        from_number = request.form.get('From')

        if not incoming_msg:
            return "Mensaje inválido", 400

        return procesar_mensaje(
            from_number,
            incoming_msg,
            lambda clave, datos: asyncio.run(guardar_en_firebase_async(clave, datos))
        )
    except Exception as e:
        print("Error:", e)
        return "Error interno del servidor", 500
