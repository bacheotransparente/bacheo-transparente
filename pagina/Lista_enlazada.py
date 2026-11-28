# Importa la funcion leer reportes de .conexion_sheets
from .conexion_sheets import (leer_reportes,agregar_reporte, eliminar_reporte)

# ENCABEZADOS DE GOOGLE SHEETS

# Diccionario que contiene los encabezados de las pestañas de google sheets
COLUMNAS = {
    "Por confirmar": ["ID", "Fecha", "Nombre", "Numero de telefono","Colonia", "Codigo postal", "Calle", "Referencia","Estado"],
    "Confirmados": ["ID", "Fecha", "Nombre", "Numero de telefono","Colonia", "Codigo postal", "Calle", "Referencia","Estado", "Largo", "Ancho", "Profundidad","Forma", "Latitud", "Longitud", "Prioridad","Ultima actualizacion"],
    "En reparacion": ["ID", "Fecha", "Nombre", "Numero de telefono","Colonia", "Codigo postal", "Calle", "Referencia","Estado", "Largo", "Ancho", "Profundidad","Forma", "Latitud", "Longitud", "Material", "Prioridad","Ultima actualizacion", "Costo estimado"],
    "Reparados": ["ID", "Fecha", "Nombre", "Numero de telefono","Colonia", "Codigo postal", "Calle", "Referencia","Estado", "Largo", "Ancho", "Profundidad","Forma", "Latitud", "Longitud","Material", "Prioridad","Ultima actualizacion", "Costo estimado","Gastos adicionales", "Costo final"],
    "Rechazados": ["ID", "Fecha", "Nombre", "Numero de telefono","Colonia", "Codigo postal", "Calle", "Referencia","Estado", "Ultima actualizacion"]
}
# Clase nodo
class Nodo:
    """Nodos"""
    def __init__(self, dato):
        # Guarda los datos del reporte
        self.dato = dato
        # Apunta al siguiente nodo
        self.siguiente = None

# Clase lista enlazada
class ListaEnlazada:
    """Lista enlazada de baches"""
    def __init__(self):
        # Primer nodo
        self.cabeza = None
        # Ultimo nodo
        self.cola = None

    # Agrega un nuevo bache al final de la lista
    def agregar(self, dato):
        # Crea un nuevo nodo
        nuevo_nodo = Nodo(dato)
        # Si la lista esta vacia
        if self.cabeza is None:
            # El nuevo nodo sera la cabeza y la cola
            self.cabeza = nuevo_nodo
            self.cola = nuevo_nodo
        else:
            # Conecta el ultimo nodo con el nuevo
            self.cola.siguiente = nuevo_nodo
            # El nuevo se convierte en la cola
            self.cola = nuevo_nodo

    # Busca un bache mediante su ID
    def buscar(self, id_bache):
        actual = self.cabeza
        # Mientras haya registros
        while actual is not None:
            # Compara los ID con el que se busca
            if str(actual.dato["ID"]) == str(id_bache):
                # Devuelve el reporte encontrado
                return actual.dato
            # Avanza al siguiente nodo
            actual = actual.siguiente
        # Devuelve none si no encuentra el reporte
        return None

    # Elimina un bache mediante su ID
    def eliminar(self, id_bache):
        actual = self.cabeza
        anterior = None
        # Mientras haya registros
        while actual is not None:
            # Compara los ID con el que se busca
            if str(actual.dato["ID"]) == str(id_bache):
                # Si no hay nodo anterior, el primero se elimina
                if anterior is None:
                    # El siguiente es la nueva cabeza
                    self.cabeza = actual.siguiente
                else:
                    # Conecta el nodo anterior con el siguiente
                    anterior.siguiente = actual.siguiente
                # Si se elimina el ultimo nodo
                if actual == self.cola:
                    # El anteior sera la nueva cola
                    self.cola = anterior
                # Devuelve los datos eliminados
                return actual.dato
            # El nodo actual se convierte en el anterior
            anterior = actual
            # Avanza al siguiente nodo
            actual = actual.siguiente
        return None

# Convierte un registro de google sheets en un diccionario, conservando los nombres originales de las columnas
def convertir_a_diccionario(fila, columnas):
    # Diccionario donde se guardara el reporte
    bache = {}
    # Relaciona cada encabezado con su dato
    for posicion, columna in enumerate(columnas):
        # Si existe un dato en esa posicion
        if posicion < len(fila):
            # Relaciona el encabezado con su dato
            bache[columna] = fila[posicion]
        else:
            # Conserva las celdas vacias
            bache[columna] = ""
    return bache

# CLASE SISTEMA BACHES
class SistemaBaches:
    """Administra los reportes mediante cinco listas enlazadas"""
    def __init__(self, ID_archivo, pestañas):
        # Guarda el ID del archivo de google sheets
        self.ID_archivo = ID_archivo
        # Crea un lsta para cada pestaña
        self.listas = {nombre:ListaEnlazada() for nombre in pestañas}

    # Lee las cinco pestañas de google sheets y carga los reportes en sus listas correspondientes
    def cargar_reportes(self):
        # Define la ultima columna de cada pestaña para que lea hasta esa
        ultima_columna = {
            "Por confirmar": "I",
            "Confirmados": "Q",
            "En reparacion": "S",
            "Reparados": "U",
            "Rechazados": "J"
        }
        # Recorre las listas creadas para cada pestaña
        for nombre_hoja, lista in self.listas.items():
            # Lee los reportes de la pestaña actual
            filas = leer_reportes(nombre_hoja,ultima_columna[nombre_hoja],self.ID_archivo)
            # Recorre las filas encontradas
            for fila in filas:
                # Convierte cada fila en un diccionario
                bache = convertir_a_diccionario(fila,COLUMNAS[nombre_hoja])
                # Agrega el reporte a su lista correspondiente
                lista.agregar(bache)

    # Mueve un reporte entre pestañas del mismo archivo de google sheets
    def mover_bache(self, id_bache, destino, nuevo_estado, fecha="", material= "", gastos_adicionales="", costo_estimado = 0, costo_final = 0):
        # Busca el reporte en las listas del sistema actual
        for nombre_origen, lista_origen in self.listas.items():
            # Busca el reporte mediante su ID
            bache = lista_origen.buscar(id_bache)
            # Si el bache existe
            if bache is not None:
                # Actualiza el estado del reporte
                bache["Estado"] = nuevo_estado
                #Si el destino es en reparacion, actualiza lo siguientes datos
                if destino == "En reparacion":
                    bache["Ultima actualizacion"] = fecha
                    bache["Material"] = material
                    bache["Costo estimado"] = costo_estimado
                # Si el destino es en reparados, actualiza lo siguientes datos
                if destino == "Reparados":
                    bache["Ultima actualizacion"] = fecha
                    bache["Gastos adicionales"] = gastos_adicionales
                    bache["Costo final"] = costo_final
                # Guarda el reporte en el destino
                guardado = agregar_reporte(destino, bache,COLUMNAS[destino],self.ID_archivo)
                # Si se guardo bien
                if guardado:
                    # Eliminar el registro del origen
                    eliminado = eliminar_reporte(nombre_origen,id_bache,self.ID_archivo)
                    if eliminado:
                        lista_origen.eliminar(id_bache)
                        self.listas[destino].agregar(bache)
                        return True
                return False
        return False

    # Transfiere un reporte a otro archivo de google sheets
    def transferir_bache(self, id_bache, sistema_destino, nombre_destino, nuevo_estado):
        # Busca el reporte en las listas del archivo de orogen
        for nombre_origen, lista_origen in self.listas.items():
            # Busca el bache por medio de su ID
            bache = lista_origen.buscar(id_bache)
            # Si el bache existe
            if bache is not None:
                # Actualiza el estado del reporte
                bache["Estado"] = nuevo_estado
                # Guarda el reporte en el archivo de destino
                guardado = agregar_reporte(nombre_destino,bache,COLUMNAS[nombre_destino],sistema_destino.ID_archivo)
                if guardado:
                    # Elimina el reporte del archivo de origen
                    eliminado = eliminar_reporte(nombre_origen,id_bache,self.ID_archivo)
                    if eliminado:
                        # Actualiza las listas enlazadas
                        lista_origen.eliminar(id_bache)
                        sistema_destino.listas[nombre_destino].agregar(bache)
                        return True
                return False
        return False
