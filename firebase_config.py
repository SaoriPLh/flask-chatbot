import firebase_admin
from firebase_admin import credentials, db

# Ruta al archivo JSON descargado desde Firebase
cred = credentials.Certificate("bdpedidos-4a3df-firebase-adminsdk-vpox8-26f56219dc.json")

# URL de tu Realtime Database
DATABASE_URL = "https://bdpedidos-4a3df-default-rtdb.firebaseio.com/"

# Inicializa Firebase
firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})
