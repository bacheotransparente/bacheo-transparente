"""
URL configuration for bacheo_transparente project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# Permite utilizar el administrador de Django
from django.contrib import admin
# Permite crear direcciones para la pagina web
from django.urls import path
# Permite mostrar pagina de inicio y procesar los reportes
from pagina.views import inicio, guardar_reporte, presupuesto_transparencia, acceso_administrativo, administrativo, \
    por_confirmar, confirmados, en_reparacion, reparados, rechazados, a_reparacion, a_reparados, a_confirmados, descargar_reparados, \
    consultar_reporte

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", inicio, name="inicio"),
    path("Inicio.html", inicio, name="inicio"),
    path("reportar-bache.html", guardar_reporte, name="guardar_reporte"),
    path("presupuesto-transparencia.html", presupuesto_transparencia, name="presupuesto"),
    path("acceso-administrativo.html", acceso_administrativo, name="acceso_administrativo"),
    path("Administrativo.html", administrativo, name="administrativo"),
    path("por-confirmar.html", por_confirmar, name="por_confirmar"),
    path("confirmados.html", confirmados, name="confirmados"),
    path("en-reparacion.html", en_reparacion, name="en_reparacion"),
    path("reparados.html", reparados, name="reparados"),
    path("rechazados.html", rechazados, name="rechazados"),
    path("a_reparacion/",a_reparacion, name="a_reparacion"),
    path("a_reparados/", a_reparados, name="a_reparados"),
    path("a_confirmados", a_confirmados, name = "a_confirmados"),
    path("descargar_reparados/<str:sistema>/", descargar_reparados, name = "descargar_reparados"),
    path("presupuesto_transparencia", presupuesto_transparencia, name="presupuesto_transparencia"),
    path("consultar_reporte/", consultar_reporte, name="consultar_reporte"),
]

