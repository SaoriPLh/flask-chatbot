import firebase_admin
from firebase_admin import credentials, db
from app.config import FIREBASE_CONFIG, DATABASE_URL

import asyncio

# Creamos la configuración de Firebase desde las variables de entorno

# Inicializar Firebase si aún no se ha inicializado
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CONFIG)
    firebase_admin.initialize_app(cred, {
        "databaseURL": DATABASE_URL
    })



async def guardar_en_firebase_async(clave_pedido, datos):
    try:
        await asyncio.to_thread(
            db.reference(f"pedidos/{clave_pedido}").set,
            datos
        )
        print(f" Pedido guardado exitosamente: {clave_pedido}")
    except Exception as e:
        print(f"Error guardando en Firebase: {e}")
