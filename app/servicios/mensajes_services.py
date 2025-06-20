from app.repositorios.twilio_repo import crear_respuesta_twilio
from datetime import datetime
from app.servicios.ubicacion_service import geocodificar_direccion
from app.servicios.ubicacion_service import asignar_sucursal
from flask_caching import Cache

pedidos = {}
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(None)

def es_respuesta_afirmativa(respuesta):
    afirmativas = ["sí", "si", "sí es correcto", "si es correcto", "correcto", "claro", "ok"]
    return respuesta.lower() in afirmativas

def procesar_mensaje(from_number, incoming_msg, guardar_func):
    response = crear_respuesta_twilio()
    msg = response.message()
    clave_pedido = f"{from_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    if from_number not in pedidos:
        pedidos[from_number] = {"estado": "esperando_pedido"}
        msg.body("¡Hola! ¿Qué pizza deseas ordenar?\n1. Hawaiana\n2. Pepperoni\n3. Vegetariana")
    else:
        estado = pedidos[from_number]["estado"]

        if estado == "esperando_pedido":
            opciones = {"1": "Hawaiana", "2": "Pepperoni", "3": "Vegetariana"}
            if incoming_msg in opciones:
                pedidos[from_number]["pedido"] = opciones[incoming_msg]
                pedidos[from_number]["estado"] = "esperando_nombre"
                msg.body(f"Has elegido: {opciones[incoming_msg]}. Ahora, indícanos tu nombre completo.")
            else:
                msg.body("Por favor, elige una opción válida (1-3).")

        elif estado == "esperando_nombre":
            pedidos[from_number]["nombre"] = incoming_msg
            pedidos[from_number]["estado"] = "esperando_direccion"
            msg.body("Gracias. Ahora, por favor indícanos tu dirección completa.")

        elif estado == "esperando_direccion":
            direccion = incoming_msg
            coordenadas = cache.get(direccion) or geocodificar_direccion(direccion)
            if coordenadas:
                cache.set(direccion, coordenadas)
                sucursal = asignar_sucursal(*coordenadas)
                if sucursal:
                    pedidos[from_number]["direccion"] = direccion
                    pedidos[from_number]["sucursal"] = sucursal
                    pedidos[from_number]["estado"] = "esperando_referencias"
                    msg.body(f"Tu dirección pertenece a {sucursal}. Añade referencias o escribe 'Sin referencias'.")
                else:
                    msg.body("No encontramos una sucursal para tu ubicación. Verifica la dirección.")
            else:
                msg.body("No pudimos ubicar tu dirección. Intenta de nuevo.")

        elif estado == "esperando_referencias":
            pedidos[from_number]["referencias"] = incoming_msg
            pedidos[from_number]["estado"] = "confirmacion"
            datos = pedidos[from_number]
            msg.body(f"Confirma tu pedido:\n- {datos['pedido']}\n- {datos['nombre']}\n- {datos['direccion']}\n"
                     f"- Referencias: {incoming_msg}\n¿Es correcto? (Sí/No)")

        elif estado == "confirmacion":
            if es_respuesta_afirmativa(incoming_msg):
                guardar_func(clave_pedido, pedidos[from_number])  # función inyectada
                msg.body("¡Gracias! Tu pedido ha sido confirmado 🎉")
                del pedidos[from_number]
            else:
                pedidos[from_number]["estado"] = "esperando_direccion"
                msg.body("Por favor, indícanos nuevamente tu dirección.")

    return str(response)
