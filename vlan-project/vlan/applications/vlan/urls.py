from django.urls import path
# Importamos las vistas 
from . import views

app_name = 'vlan_app'

urlpatterns = [
     # URL de la página principal
    path(
         '', 
         views.VlanSearchView.as_view(),
         name = 'vlan-index',
    ), 
    path(
         'listAllVlans/', 
         views.VlanListView.as_view(),
         name = 'vlan-list',
    ), 
    path(
         'vlanUpdate/<int:pk>/', 
         views.VlanUpdateView.as_view(),
         name = 'vlan-update',
    ), 
    path(
         'vlanMenu/', 
         views.VlanView.as_view(),
         name = 'vlan-menu',
    ),
    path(
         'vlanCreate/', 
         views.VlanCreateView.as_view(),
         name = 'vlan-create',
    ),  
    path(
        'vlanDelete/<int:pk>/',
        views.VlanDeleteView.as_view(),
        name='vlan-delete'
    ),
]