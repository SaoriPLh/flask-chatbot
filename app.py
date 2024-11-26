from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from firebase_config import db
from datetime import datetime
import ubicaciones  # Importar funciones de ubicaciones.py

app = Flask(__name__)

# Diccionario temporal para almacenar pedidos
pedidos = {}

# Función para validar respuestas afirmativas
def es_respuesta_afirmativa(respuesta):
    afirmativas = ["sí", "si", "sí es correcto", "si es correcto", "correcto", "claro", "ok"]
    return respuesta.lower() in afirmativas

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    incoming_msg = request.form.get('Body').strip()
    from_number = request.form.get('From')
    response = MessagingResponse()
    msg = response.message()

    # Generar clave única basada en tiempo
    clave_pedido = f"{from_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Si es un nuevo cliente
    if from_number not in pedidos:
        pedidos[from_number] = {"estado": "esperando_pedido"}
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
            try:
                coordenadas = ubicaciones.geocodificar_direccion(direccion)

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
            except Exception as e:
                print(f"Error procesando la dirección: {e}")
                msg.body("Hubo un error al procesar tu dirección. Por favor intenta nuevamente.")

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
                # Guardar en Firebase
                try:
                    db.reference(f"pedidos/{clave_pedido}").set(pedidos[from_number])
                    msg.body("¡Gracias! Tu pedido ha sido confirmado y será preparado pronto. 😊")
                    del pedidos[from_number]  # Limpiar el estado
                except Exception as e:
                    print(f"Error guardando en Firebase: {e}")
                    msg.body("Hubo un problema al guardar tu pedido. Por favor intenta nuevamente.")
            else:
                pedidos[from_number]["estado"] = "esperando_direccion"
                msg.body("Por favor, indícanos nuevamente tu dirección.")

    return str(response)

if __name__ == '__main__':
    app.run(debug=True)  