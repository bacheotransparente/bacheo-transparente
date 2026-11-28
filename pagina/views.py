from django.shortcuts import render
# Generar identificadores unicos
import uuid
# Importa la clase que administra las listas enlazadas
from .Lista_enlazada import SistemaBaches, COLUMNAS
# Importa las funciones e identificadores de google sheets
from .conexion_sheets import (agregar_reporte, ID_alcaldia, ID_SOBSE, ID_confirmados, actualizar_presupuesto, hojas_calculo)
# Permite trabajar con informacion geografica
import geopandas as gpd
# Crear el punto con las coordenadas del bache
from shapely.geometry import Point
# Permite utilizar el numero pi para calcular areas ovaladas
import math
import requests
from django.http import HttpResponse


def inicio(request):
    # Muestra la pagina principal
    return render(request, "pagina/Inicio.html")

def presupuesto_transparencia(request):
    return render(request, "pagina/presupuesto-transparencia.html")

def acceso_administrativo(request):
    return render(request, "pagina/acceso-administrativo.html")

def administrativo(request):
    return render(request, "pagina/Administrativo.html")

def por_confirmar(request):
    return render(request, "pagina/por-confirmar.html")

def confirmados(request):
    return render(request, "pagina/confirmados.html")

def en_reparacion(request):
    return render(request, "pagina/en-reparacion.html")

def reparados(request):
    return render(request, "pagina/reparados.html")

def rechazados(request):
    return render(request, "pagina/rechazados.html")

# DESCARGAR LA PESTAÑA DE REPARADOS

def descargar_reparados(request,sistema):
    # Ver de que sistema se tiene que descragar
    if sistema == "ALCALDIA":
        id_archivo = ID_alcaldia
    else:
        id_archivo = ID_SOBSE
    # Genera el enlace de descarga de la pestaña Reparados
    url = f"https://docs.google.com/spreadsheets/d/{id_archivo}/export?format=xlsx&gid=1729245307"
    archivo = requests.get(url)
    # Entregar el Excel al usuario
    respuesta = HttpResponse(archivo.content,content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    respuesta["Content-Disposition"] = 'attachment; filename="Reportes_Reparados.xlsx"'
    return respuesta

# CREAR LOS SISTEMAS DE LISTAS ENLAZADAS

def obtener_sistema(tipo="GENERAL"):
    # Diccionario que relaciona cada sistema, con su archivo y pestañas correspondientes
    sistemas = {
        "GENERAL": (ID_confirmados, ["Por confirmar", "Rechazados"]),
        "ALCALDIA": (ID_alcaldia, ["Confirmados", "En reparacion", "Reparados"]),
        "SOBSE": (ID_SOBSE, ["Confirmados", "En reparacion", "Reparados"])
    }
    # Obtiene el ID del archivo de google sheets y sus pestañas
    id_archivo, estados = sistemas[tipo]
    # Crea el sistema de lista enlazadas
    sistema = SistemaBaches(id_archivo, estados)
    # Toma los reportes del archivo
    sistema.cargar_reportes()
    return sistema

# GUARDAR UN REPORTE CIUDADANO

def guardar_reporte(request):
    # Comprueba que el formulario se envio
    if request.method == "POST":
        # Genera un ID unico de 8 caracteres
        id_bache = str(uuid.uuid4())[:8].upper()
        # Organiza los datos que se recibieron
        bache = {
            "ID": id_bache,
            "Fecha": request.POST.get("fecha", ""),
            "Nombre": request.POST.get("nombres", ""),
            "Numero de telefono": request.POST.get("telefono", ""),
            "Colonia": request.POST.get("colonia", ""),
            "Codigo postal": str(request.POST.get("codigo_postal", "")),
            "Calle": request.POST.get("calle", ""),
            "Referencia": request.POST.get("referencia", ""),
            "Estado": "Por confirmar"
        }
        # Obtiene el sistema general y toma los reportes existentes
        general = obtener_sistema("GENERAL")
        # Guarda el reporte en Google Sheets
        guardado = agregar_reporte("Por confirmar",bache,COLUMNAS["Por confirmar"],ID_confirmados)
        if guardado:
            # Agrega el reporte a la lista enlazada
            general.listas["Por confirmar"].agregar(bache)
            # Muestra el ID al usuario
        return render(request,"pagina/confirmar-reporte.html",{"id_bache": id_bache})
    return render(request, "pagina/reportar-bache.html")

# PASAR UN REPORTE DE POR CONFIRMAR A CONFIRMADO Y A QUIEN LE CORRESPONDA SU REPARACION

def a_confirmados (request):
    if request.method == "POST":
        # Se obtiene e ID
        id_bache = request.POST.get("ID", "")
        # Carga el sistema general
        general = obtener_sistema("GENERAL")
        # Busca el reporte en la pestaña por confirmar
        bache = general.listas["Por confirmar"].buscar(id_bache)
        # Si el bache no existe
        if bache is None:
            return render(request, "pagina/decision-noregistrada.html")
        # Se obtienen los datos del formulario
        fecha = request.POST.get("fecha", "")
        largo = request.POST.get("largo", "")
        ancho = request.POST.get("ancho", "")
        profundidad = request.POST.get("profundidad", "")
        latitud = float(request.POST.get("latitud", ""))
        longitud = float(request.POST.get("longitud",""))
        forma = request.POST.get("forma", "")
        formas = {"1": "Rectangular", "2": "Ovalada o irregular"}
        forma = formas[forma]
        # Se lee el archivo de vialidades primarias
        vialidades_primarias = gpd.read_file("Datos/VIALIDADES PRIMARIAS MH.gpkg")
        # Crea el punto, su sistema de coordenadas es EPSG:32614
        punto = gpd.GeoSeries([Point(longitud, latitud)],crs="EPSG:4326")
        # Verifica si esta en una vialidad primaria
        vialidad_primaria = vialidades_primarias.geometry.intersects(punto).any()
        # Si el bache esta sobre una vialidad primaria
        if vialidad_primaria:
            encargado = "SOBSE"
        else:
            encargado = "ALCALDIA"
        # Actualiza los datos que incorporan los administrativos al confirmar la existencia del bache
        bache["Largo"] = largo
        bache["Ancho"] = ancho
        bache["Profundidad"] = profundidad
        bache["Forma"] = forma
        bache["Latitud"] = latitud
        bache["Longitud"] = longitud
        bache["Ultima actualizacion"] = fecha
        # Crea el sistema
        destino = obtener_sistema(encargado)
        # Transfiere el bache a otro archivo de google sheets
        movido = general.transferir_bache(id_bache, destino, "Confirmados", "Confirmado")
        if movido:
            # Si la profundidad es mayor o igual a 7.6
            if float(profundidad) >= 7.6:
                return render(request, "pagina/revisar-administrativos.html")
            return render(request, "pagina/decision-registrada.html")
        return render(request, "pagina/salio-mal.html")

# PASAR UN REPORTE DE CONFIRMADOS A EN REPARACION

def a_reparacion(request):
    if request.method == "POST":
        # Si el formularioo es de la alcaldia
        if "ID-alcaldia" in request.POST:
            id_bache =request.POST.get("ID-alcaldia", "")
            fecha = request.POST.get("fecha-alcaldia", "")
            material = request.POST.get("material-alcaldia", "")
            sistema = obtener_sistema("ALCALDIA")
        else:
            id_bache = request.POST.get("ID-SOBSE", "")
            fecha = request.POST.get("fecha-SOBSE", "")
            material = request.POST.get("material-SOBSE", "")
            sistema = obtener_sistema("SOBSE")
        # Diccionario que relaciona los valores del formulario con el nombre del material
        materiales = {"1": "Mezcla asfáltica templada","2": "Mezcla bituminosa en frío (Perma-Patch o similar)"}
        # Obtiene el nombre del material seleccionado
        material = materiales[material]
        # Busca el bache en la lista de confirmados usando su ID
        bache = sistema.listas["Confirmados"]. buscar(id_bache)
        # Si el bache no existe
        if bache is None:
            return render(request, "pagina/decision-noregistrada.html")
        # Recupera las medidas, profindidad y forma que ingreso el administrativo
        largo = float(bache["Largo"])
        ancho = float(bache["Ancho"])
        profundidad = float(bache["Profundidad"])
        forma = bache["Forma"]
        # Si las medidas son negativas
        if largo <= 0 or ancho <= 0 or profundidad <= 0:
            return render(request, "pagina/decision-noregistrada.html")
        # Convierte las medidas de centimetros a metros
        largo_m = largo / 100
        ancho_m = ancho / 100
        # Calcula el area de acuerdo con a la forma seleccionada
        if forma == "Rectangular":
            area = largo_m * ancho_m
        elif forma == "Ovalada o irregular":
            area = (math.pi / 4) * largo_m * ancho_m
        else:
            return render(request, "pagina/decision-noregistrada.html")
        # Diccionario que define los precios por metro cuadrado segun el material
        precios = {
            "Mezcla asfáltica templada": {
                5: 399.60,
                7.5: 553.92
            },
            "Mezcla bituminosa en frío (Perma-Patch o similar)": {
                5: 2625.69,
                7.5: 3885.16
            }
        }
        # Selecciona el espesor de reparacion segun la profundidad
        if profundidad >= 7.6:
            costo_estimado = 0
        else:
            if profundidad <= 5:
                espesor = 5
            else:
                espesor = 7.5
            # Obtiene el precio unitario
            precio_unitario = precios[material][espesor]
            # Calcula el costo estimado de reparacion
            costo_estimado = round(area * precio_unitario, 2)
        # Mueve el reporte a en reparacion
        movido = sistema.mover_bache(id_bache,"En reparacion","En reparacion",fecha,material, costo_estimado= costo_estimado)
        if movido:
            if profundidad >= 7.6:
                return render(request, "pagina/revisar-administrativos.html")
            return render(request, "pagina/decision-registrada.html", )

# PASAR UN REPORTE DE EN REPARACION A REPARADOScd

def a_reparados(request):
    if request.method == "POST":
        if "ID-alcaldia" in request.POST:
            id_bache =request.POST.get("ID-alcaldia", "")
            fecha = request.POST.get("fecha-alcaldia", "")
            gastos_adicionales = request.POST.get("gastos_adicionales-alcaldia", "")
            sistema = obtener_sistema("ALCALDIA")
            nombre_sistema = "ALCALDIA"
        else:
            id_bache = request.POST.get("ID-SOBSE", "")
            fecha = request.POST.get("fecha-SOBSE", "")
            gastos_adicionales = request.POST.get("gastos_adicionales-SOBSE", "")
            sistema = obtener_sistema("SOBSE")
            nombre_sistema = "SOBSE"
        bache = sistema.listas["En reparacion"].buscar(id_bache)
        if bache is None:
            return render(request, "pagina/decision-noregistrada.html")
        total_adicionales = 0
        lineas = gastos_adicionales.strip().splitlines()
        for linea in lineas:
            descripcion, importe = linea.rsplit(":",1)
            total_adicionales += float(importe.strip())
        # Recupera el costo estimado desde el diccionario del bache
        costo_estimado = float(bache["Costo estimado"])
        costo_final = round(costo_estimado + total_adicionales, 2)
        # Mueve el reporte a reparados
        movido = sistema.mover_bache(id_bache,"Reparados","Reparado",fecha,gastos_adicionales=gastos_adicionales, costo_final = costo_final)
        if movido:
            presupuesto_actualizado = actualizar_presupuesto(nombre_sistema, costo_final)
            if presupuesto_actualizado:
                return render(request, "pagina/decision-registrada.html", )
        return render(request, "pagina/decision-registrada.html", )

# VISUALIZAR EL PRESUPUESTO INICIAL Y RESTANTE

def presupuesto_transparencia(request):
    # Consulta la informacion del presupuesto de la Alcaldia y SOBSE
    alcaldia = hojas_calculo.values().get(spreadsheetId=ID_alcaldia,range="Presupuesto!A2:C2").execute().get("values", [[]])[0]
    sobse = hojas_calculo.values().get(spreadsheetId=ID_SOBSE,range="Presupuesto!A2:C2").execute().get("values", [[]])[0]
    # Muestra los presupuesto en la pestaña
    return render(request, "pagina/presupuesto-transparencia.html", {
        "alcaldia_inicial": alcaldia[0],
        "alcaldia_restante": alcaldia[2],
        "sobse_inicial": sobse[0],
        "sobse_restante": sobse[2]
    })

# PERMITE CONSULTAR UN REPORTE POR MEDIO DE SU ID (CIUDADANO)

def consultar_reporte(request):
    # Inicializa variable
    resultado = None
    if request.method == "POST":
        # Recupera el ID
        id_bache = request.POST.get("id_bache")
        # Archivos y pestañas donde se buscara el reporte
        archivos = [
            (ID_alcaldia, ["Confirmados", "En reparacion", "Reparados"]),
            (ID_SOBSE, ["Confirmados", "En reparacion", "Reparados"]),
            (ID_confirmados, ["Por confirmar", "Rechazados"])
        ]
        # Recorre cada archivo
        for archivo, pestanas in archivos:
            # Recorre las pestañas
            for pestana in pestanas:
                # Consultar los reportes de la pestaña
                datos = hojas_calculo.values().get(spreadsheetId=archivo,range=f"'{pestana}'!A1:Z").execute().get("values", [])
                # Si no esta el reporte ahi, que continue en la siguiente
                if not datos:
                    continue
                # Obtiene los encabezados
                encabezados = datos[0]
                # Recorre los reportes desde la fila 1
                for fila in datos[1:]:
                    if fila[encabezados.index("ID")] == id_bache:
                        resultado = {
                            "estado": fila[encabezados.index("Estado")],
                            "actualizacion": fila[encabezados.index("Ultima actualizacion")]
                        }
                        break
                if resultado:
                    break
            if resultado:
                break
    return render(request, "pagina/Inicio.html", {"resultado": resultado,"buscado": request.method == "POST"})



