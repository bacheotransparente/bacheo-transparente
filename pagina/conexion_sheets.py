# CONEXION CON GOOGLE SHEETS

# Conecta con google sheets
from googleapiclient.discovery import build
# Utiliza una llave de acceso para ingresar a la cuenta
from google.oauth2 import service_account
# Permite que se trabaje con rutas
import os

# Permisos para consultar y modificar google sheets
permisos = ["https://www.googleapis.com/auth/spreadsheets"]
# Obtiene la ruta principal del proyecto
# Obtiene la ruta principal del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#Si estamos trabajando en Render
if os.path.exists("/etc/secrets/Credenciales_google.json"):
    # Utiliza el archivo privado guardado en Render
    archivo_credenciales = "/etc/secrets/Credenciales_google.json"
else:
    # Si estamos en PyCharm, usa el archivo local
    archivo_credenciales = os.path.join(
        BASE_DIR,
        "credenciales",
        "Credenciales_google.json"
    )
# Rutas de los archivos de google sheets
ID_confirmados = "1YUM0vvmvemZrzFdinXMIXJ3dcyWe6yM3yS_Pjn3j2xU"
ID_alcaldia = "1ypAQoIlqcLxMcbJ8glwAmcYCYn3V_t9s89TGB2iJxp4"
ID_SOBSE = "11YdTLmbcZbLbQKjmwkGWLKuQJefXaXoieOkOZno762E"
#Aqui se revisan los permisos y el archivo con las credenciales
credenciales = service_account.Credentials.from_service_account_file(archivo_credenciales, scopes=permisos)
#Aqui especifico que quiero crear una conexion con google sheets (servicio) y v4 (version), añaniendo las credenciales para que se pueda usar
servicio = build("sheets", "v4", credentials=credenciales)
#Dentro del servicio de google sheets, quiero trabajar especificamente con hojas de calculo
hojas_calculo = servicio.spreadsheets()


# Leer los reportes de baches de cualquiero hoja
def leer_reportes(nombre_hoja, ultima_columna, ID_archivo ):
    # Rango que se va a usar
    rango = f"'{nombre_hoja}'!A2:{ultima_columna}"
    # Consulta los registros de google sheets del rango
    reportes = hojas_calculo.values().get(spreadsheetId=ID_archivo,range=rango).execute()
    # Regresa las filas encontradas
    return reportes.get("values", [])

# Agregar reporte a google sheets al final de la pestaña
def agregar_reporte(nombre_hoja, datos, columnas, ID_archivo ):
    # Organiza los datos respetando el orden de los campos, si algun campo esta vacio se guarda asi
    fila = [datos.get(columna, "") for columna in columnas]
    # Inserta el reporte al final de la pestaña
    hojas_calculo.values().append(spreadsheetId=ID_archivo, range=f"'{nombre_hoja}'!A1",valueInputOption="RAW",insertDataOption="INSERT_ROWS",body={"values": [fila]}).execute()
    return True

# Buscar un reporte por medio de su ID
def buscar_fila(nombre_hoja, id_bache, ID_archivo ):
    # Consulta los ID de la primera columna
    resultado = hojas_calculo.values().get(spreadsheetId=ID_archivo,range=f"'{nombre_hoja}'!A2:A" ).execute()
    # Obtiene los ID encontrados
    identificadores = resultado.get("values", [])
    # Recorre los ID , start = 2 le dice que comience desde la fila 2
    for posicion, identificador in enumerate(identificadores, start=2):
        # Compara los ID como texto
        if identificador and str(identificador[0]) == str(id_bache):
            return posicion
    # El reporte no esta en esa pestaña
    return None

# Elimina un fila usando el ID del repoirte
def eliminar_reporte(nombre_hoja, id_bache, ID_archivo):
    # Busca la fila donde se encuentra el reporte
    fila = buscar_fila(nombre_hoja, id_bache, ID_archivo)
    # Si no encontr el reporte
    if fila is None:
        return False
    # Consulta la informacuion de las pestañas
    informacion = hojas_calculo.get(spreadsheetId=ID_archivo).execute()
    id_hoja = 0
    # Recorre las pestañas del archivo de google sheets
    for hoja in informacion["sheets"]:
        # Consulta las propiedas para saber su nombre de la pestaña
        propiedades = hoja["properties"]
        # Si su nombre es igual a la pestaña que se busca
        if propiedades["title"] == nombre_hoja:
            # Obtiene su ID
            id_hoja = propiedades["sheetId"]
            break
    # Si la pestaña no existe
    if id_hoja is None:
        return False
    # Entonces elimina la fila completa
    hojas_calculo.batchUpdate(spreadsheetId=ID_archivo,body={"requests": [{"deleteDimension": {"range": {"sheetId": id_hoja,"dimension": "ROWS","startIndex": fila - 1,"endIndex": fila}}}]}).execute()
    return True

# Actualiza los gastos acumulados y el presupuesto restante
def actualizar_presupuesto(sistema, costo_final):
    # Ver que archivo de google sheets es el que se actualiza
    if sistema == "ALCALDIA":
        ID_archivo = ID_alcaldia
    else:
        ID_archivo = ID_SOBSE
    # Consultar los gastos acumulados actualizados
    consulta_gastos_acumulados = hojas_calculo.values().get(spreadsheetId=ID_archivo,range="Presupuesto!B2").execute()
    # Si la celda esta vacia, comenzar desde cero
    gastos_acumulados = consulta_gastos_acumulados.get("values", [])
    gastos_acumulados_actuales = (float(gastos_acumulados[0][0]) if gastos_acumulados else 0)
    # Sumar el costo final del bache
    gastos_acumulados_actualizados = (gastos_acumulados_actuales + float(costo_final))
    # Guardar el nuevo total en Google Sheets
    hojas_calculo.values().update(spreadsheetId=ID_archivo,range="Presupuesto!B2",valueInputOption="USER_ENTERED",body={"values": [[gastos_acumulados_actualizados]]}).execute()


