import requests
from shapely.geometry import Point, Polygon
from flask_caching import Cache

app.config['CACHE_TYPE'] = 'simple'
cache = Cache(app)

# Tu clave de la API de Google Maps
GOOGLE_MAPS_API_KEY = "AIzaSyDv4CHMb9xSvtd0fWO0vvKo9KsvOcIKQy8"

# Polígono para Sucursal 1 basado en el JSON
sucursal1_area = Polygon([
    (-97.09986445767333, 18.850998953148604),
    (-97.1002273042205, 18.850982083411747),
    (-97.10058665613998, 18.85093163667608),
    (-97.10093905246761, 18.85084809880122),
    (-97.10128109924172, 18.850732274351213),
    (-97.10160950219633, 18.850585278844324),
    (-97.10192109849305, 18.85040852800743),
    (-97.10221288718644, 18.850203724138744),
    (-97.10248205812854, 18.849972839710247),
    (-97.10272601903469, 18.849718098367926),
    (-97.10294242044944, 18.84944195351287),
    (-97.10312917837217, 18.849147064669754),
    (-97.10328449432485, 18.848836271870358),
    (-97.10340687266839, 18.848512568299007),
    (-97.10349513500098, 18.848179071463512),
    (-97.10354843150057, 18.847838993169347),
    (-97.1035662491014, 18.847495608586318),
    (-97.10354841642732, 18.847152224705784),
    (-97.10349510543372, 18.8468121484921),
    (-97.10340682974336, 18.84647865503512),
    (-97.10328443969168, 18.846154956010494),
    (-97.10312911413035, 18.845844168751295),
    (-97.10294234906775, 18.845549286228945),
    (-97.10272594325632, 18.845273148232316),
    (-97.10248198086556, 18.845018414022526),
    (-97.10221281140804, 18.84478753672656),
    (-97.10192102711136, 18.844582739716298),
    (-97.10160943795451, 18.84440599520017),
    (-97.10128104460854, 18.84425900523348),
    (-97.10093900954259, 18.844143185330196),
    (-97.1005866265727, 18.844059650833852),
    (-97.10022728914724, 18.84400920617867),
    (-97.09986445767333, 18.843992337144304)
])

# Polígono para Sucursal 2 basado en el JSON
sucursal2_area = Polygon([
    (-97.13373745763738, 18.84417142615634),
    (-97.1340055413539, 18.844158961766045),
    (-97.13427104315923, 18.84412168863958),
    (-97.13453140601192, 18.844059965753875),
    (-97.1347841223704, 18.843974387560618),
    (-97.13502675834596, 18.843865778260323),
    (-97.13525697714606, 18.843735183863476),
    (-97.13547256158165, 18.84358386211517),
    (-97.13567143542224, 18.84341327038048),
    (-97.13585168339235, 18.843225051607117),
    (-97.13601156961722, 18.843021018500803),
    (-97.13614955433962, 18.8428031360658),
    (-97.13626430874739, 18.84257350267872),
    (-97.13635472776836, 18.842334329878163),
    (-97.13641994070996, 18.842087921064657),
    (-97.13645931964086, 18.841836649316324),
    (-97.13647248543435, 18.841582934533804),
    (-97.13645931141512, 18.841329220134657),
    (-97.13641992457458, 18.841077949521722),
    (-97.13635470434342, 18.840831542551996),
    (-97.13626427893308, 18.840592372232756),
    (-97.1361495192817, 18.84036274186917),
    (-97.13601153066294, 18.84014486288364),
    (-97.13585164203872, 18.839940833520227),
    (-97.13567139325843, 18.839752618639352),
    (-97.13547252022802, 18.839582030797146),
    (-97.13525693819179, 18.839430712791742),
    (-97.13502672328805, 18.839300121844374),
    (-97.13478409255609, 18.83919151556757),
    (-97.13453138258697, 18.839105939855624),
    (-97.13427102702384, 18.839044218813708),
    (-97.13400553312815, 18.839006946822636),
    (-97.13373745763738, 18.83899448281572)
])

# Lista de sucursales con sus polígonos
sucursales = {
    "sucursal1": sucursal1_area,
    "sucursal2": sucursal2_area
}
@cache.cached(timeout=300)
# Función para convertir dirección en coordenadas
def geocodificar_direccion(direccion):
    try:
        start_time = time.time()  # Inicia el temporizador
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={direccion}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                location = data['results'][0]['geometry']['location']
                end_time = time.time()
                print(f"Geocodificación completada en {end_time - start_time:.2f} segundos")
                return location['lat'], location['lng']
        end_time = time.time()
        print(f"Geocodificación fallida en {end_time - start_time:.2f} segundos")
        return None
    except Exception as e:
        print(f"Error al geocodificar dirección: {e}")
        return None

def asignar_sucursal(lat, lng):
    start_time = time.time()  # Inicia el temporizador
    punto_cliente = Point(lng, lat)  # Shapely usa (longitud, latitud)
    for nombre_sucursal, area in sucursales.items():
        if area.contains(punto_cliente):
            end_time = time.time()
            print(f"Asignación de sucursal completada en {end_time - start_time:.2f} segundos")
            return nombre_sucursal
    end_time = time.time()
    print(f"Asignación de sucursal fallida en {end_time - start_time:.2f} segundos")
    return None
