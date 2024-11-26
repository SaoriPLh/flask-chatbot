import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from flask_caching import Cache
from datetime import datetime
import ubicaciones  # Importar funciones de ubicaciones.py
import os
import asyncio

# Cargar las variables desde el archivo .env
# (Esto ya no es necesario si usas secretos en Render)
# load_dotenv()

# Verifica que las variables críticas estén cargadas
# (Esto ya no es necesario si usas secretos en Render)
# if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or not os.getenv("DATABASE_URL"):
#     raise ValueError("Las variables de entorno necesarias no están configuradas.")

# En lugar de obtener la variable desde el .env, ahora obtienes el archivo desde /etc/secrets/
CREDENTIALS_PATH = "/etc/secrets/bdpedidos-4a3df-firebases-adminsdk-vpox8-26f56219dc.json"
DATABASE_URL = os.getenv("DATABASE_URL")  # Esta sigue siendo una variable de entorno si la usas

# Inicializa Firebase con las credenciales desde el archivo secreto en Render
cred = credentials.Certificate(CREDENTIALS_PATH)
firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'SimpleCache'
cache = Cache(app)

# Diccionario temporal para almacenar pedidos
pedidos = {}

# Función para validar respuestas afirmativas
def es_respuesta_afirmativa(respuesta):
    afirmativas = ["sí", "si", "sí es correcto", "si es correcto", "correcto", "claro", "ok"]
    return respuesta.lower() in afirmativas

# Función para manejar errores al escribir en Firebase
async def guardar_en_firebase_async(clave_pedido, datos):
    try:
        await asyncio.to_thread(db.reference(f"pedidos/{clave_pedido}").set, datos)
        print(f"Pedido guardado exitosamente: {clave_pedido}")
    except Exception as e:
        print(f"Error guardando en Firebase: {e}")

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    incoming_msg = request.form.get('Body').strip().lower()
    from_number = request.form.get('From')
    response = MessagingResponse()
    msg = response.message()

    # Generar clave única basada en tiempo
    clave_pedido = f"{from_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Si es un nuevo cliente
    if from_number not in pedidos:
        pedidos[from_number] = {"estado": "esperando_pedido"}  # Inicializa el pedido
        msg.body("¡Hola! Bienvenido a Henry's Pizzas. ¿Qué pizza deseas ordenar?\n"
                 "1. Pizza Hawaiana\n"
                 "2. Pizza Pepperoni\n"
                 "3. Pizza Vegetariana\n"
                 "Responde con el número correspondiente.")
    else:
        estado = pedidos[from_number]["estado"]

        if estado == "esperando_pedido":
            if incoming_msg in ["1", "2", "3"]:
                opciones_pizza = {
                    "1": "Pizza Hawaiana",
                    "2": "Pizza Pepperoni",
                    "3": "Pizza Vegetariana"
                }
                pedidos[from_number]["pedido"] = opciones_pizza[incoming_msg]
                pedidos[from_number]["estado"] = "esperando_nombre"
                msg.body(f"Has elegido: {opciones_pizza[incoming_msg]}.\n"
                         "Ahora, por favor indícanos tu nombre completo.")
            else:
                msg.body("Por favor, selecciona una opción válida:\n1. Hawaiana\n2. Pepperoni\n3. Vegetariana.")

        elif estado == "esperando_nombre":
            pedidos[from_number]["nombre"] = incoming_msg
            pedidos[from_number]["estado"] = "esperando_direccion"
            msg.body("Gracias. Ahora, por favor indícanos tu dirección completa (incluye municipio).")

        elif estado == "esperando_direccion":
            direccion = incoming_msg
            coordenadas = cache.get(direccion)

            if not coordenadas:
                coordenadas = ubicaciones.geocodificar_direccion(direccion)
                if coordenadas:
                    cache.set(direccion, coordenadas)

            if coordenadas:
                lat, lng = coordenadas
                sucursal = ubicaciones.asignar_sucursal(lat, lng)
                if sucursal:
                    pedidos[from_number]["direccion"] = direccion
                    pedidos[from_number]["sucursal"] = sucursal
                    pedidos[from_number]["estado"] = "esperando_referencias"
                    msg.body(f"Tu dirección pertenece a {sucursal}.\n"
                             "Si deseas, agrega referencias adicionales para facilitar la entrega (ejemplo: 'junto a la tienda X').\n"
                             "Si no tienes referencias, escribe 'Sin referencias'.")
                else:
                    msg.body("Lo siento, no encontramos una sucursal que atienda esa ubicación. Por favor verifica la dirección.")
            else:
                msg.body("No pude encontrar tu dirección en el mapa. Por favor verifica e ingrésala nuevamente (incluye municipio).")

        elif estado == "esperando_referencias":
            referencias = incoming_msg
            pedidos[from_number]["referencias"] = referencias
            pedidos[from_number]["estado"] = "confirmacion"
            msg.body(f"Por favor confirma tu pedido:\n"
                     f"- Pedido: {pedidos[from_number]['pedido']}\n"
                     f"- Nombre: {pedidos[from_number]['nombre']}\n"
                     f"- Dirección: {pedidos[from_number]['direccion']}\n"
                     f"- Referencias: {referencias}\n"
                     "¿Es correcto? Responde 'Sí' o 'No'.")

        elif estado == "confirmacion":
            if es_respuesta_afirmativa(incoming_msg):
                msg.body("¡Gracias! Tu pedido ha sido confirmado y será preparado pronto. 😊")
                
                # Ejecutar escritura asincrónica en Firebase
                asyncio.run(guardar_en_firebase_async(clave_pedido, pedidos[from_number]))
                
                # Limpia el estado del pedido
                del pedidos[from_number]
            else:
                pedidos[from_number]["estado"] = "esperando_direccion"
                msg.body("Por favor, indícanos nuevamente tu dirección.")

    return str(response)

if __name__ == '__main__':
    app.run(debug=True)
