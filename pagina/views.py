from django.shortcuts import render
# Generar identificadores unicos
import uuid
# Importa la clase que administra las listas enlazadas
from .Lista_enlazada import SistemaBaches, COLUMNAS
# Importa las funciones e identificadores de google sheets
from .conexion_sheets import (agregar_reporte, ID_alcaldia, ID_SOBSE, ID_confirmados)
# Permite trabajar con informacion geografica
import geopandas as gpd
# Crear el punto con las coordenadas del bache
from shapely.geometry import Point


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

# CREAR LOS SISTEMAS DE LISTAS ENLAZADAS

def obtener_sistema(tipo="GENERAL"):
    sistemas = {
        "GENERAL": (ID_confirmados, ["Por confirmar", "Rechazados"]),
        "ALCALDIA": (ID_alcaldia, ["Confirmados", "En reparacion", "Reparados"]),
        "SOBSE": (ID_SOBSE, ["Confirmados", "En reparacion", "Reparados"])
    }
    id_hoja, estados = sistemas[tipo]
    sistema = SistemaBaches(id_hoja, estados)
    sistema.cargar_reportes()
    return sistema

# GUARDAR UN REPORTE CIUDADANO

def guardar_reporte(request):
    # Comprueba si el ciudadano envió el formulario.
    if request.method == "POST":
        # Genera un identificador único.
        id_bache = str(uuid.uuid4())[:8].upper()
        # Organiza los datos recibidos del formulario.
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
        # Obtiene el sistema general y carga los reportes existentes
        general = obtener_sistema("GENERAL")
        # Guarda el reporte en Google Sheets.
        guardado = agregar_reporte("Por confirmar",bache,COLUMNAS["Por confirmar"],ID_confirmados)
        if guardado:
            # Agrega el reporte a la lista enlazada.
            general.listas["Por confirmar"].agregar(bache)
            # Muestra el identificador generado.
            return render(request,"pagina/confirmar-reporte.html",{"id_bache": id_bache})
    return render(request, "pagina/Reportar-bache.html")

# PASAR UN REPORTE DE POR CONFIRMAR A CONFIRMADO Y A QUIEN LE CORRESPONDA SU REPARACION

def a_confirmados (request):
    if request.method == "POST":
        # Se obtiene e ID
        id_bache = request.POST.get("ID", "")
        # Se busca el reporte en el sistema GENERAL
        general = obtener_sistema("GENERAL")
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
        # Convertir el punto al sistema de coordenadas EPSG:32614
        punto = gpd.GeoSeries([Point(longitud, latitud)],crs="EPSG:4326")
        vialidad_primaria = vialidades_primarias.geometry.intersects(punto).any()
        # Si el bache esta sobre una vialidad primaria
        if vialidad_primaria:
            institucion = "SOBSE"
        else:
            institucion = "ALCALDIA"
        # Actualiza los datos administrativos del reporte
        bache["Largo"] = largo
        bache["Ancho"] = ancho
        bache["Profundidad"] = profundidad
        bache["Forma"] = forma
        bache["Latitud"] = latitud
        bache["Longitud"] = longitud
        bache["Ultima actualizacion"] = fecha
        destino = obtener_sistema("ALCALDIA")
        movido = general.transferir_bache(id_bache, destino, "Confirmados", "Confirmado")
        if movido:
            return render(request, "pagina/decision-registrada.html")

# PASAR UN REPORTE DE CONFIRMADOS A EN REPARACION

def a_reparacion(request):
    if request.method == "POST":
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
        # Relaciona los valores del formulario con el nombre del material
        materiales = {"1": "Mezcla asfáltica templada","2": "Mezcla bituminosa en frío (Perma-Patch o similar)"}
        # Obtiene el nombre del material seleccionado
        material = materiales[material]
        # Mueve el reporte a en reparacion
        movido = sistema.mover_bache(id_bache,"En reparacion","En reparacion",fecha,material)
        if movido:
            return render(request, "pagina/decision-registrada.html", )
        return render(request, "pagina/decision-noregistrada.html")

# PASAR UN REPORTE DE EN REPARACION A REPARADOS

def a_reparados(request):
    if request.method == "POST":
        if "ID-alcaldia" in request.POST:
            id_bache =request.POST.get("ID-alcaldia", "")
            fecha = request.POST.get("fecha-alcaldia", "")
            gastos_adicionales = request.POST.get("gastos_adicionales-alcaldia", "")
            sistema = obtener_sistema("ALCALDIA")
        else:
            id_bache = request.POST.get("ID-SOBSE", "")
            fecha = request.POST.get("fecha-SOBSE", "")
            gastos_adicionales = request.POST.get("gastos_adicionales-SOBSE", "")
            sistema = obtener_sistema("SOBSE")
        # Mueve el reporte a reparados
        movido = sistema.mover_bache(id_bache,"Reparados","Reparado",fecha,gastos_adicionales=gastos_adicionales)
        if movido:
            return render(request, "pagina/decision-registrada.html", )
        return render(request, "pagina/decision-noregistrada.html")



