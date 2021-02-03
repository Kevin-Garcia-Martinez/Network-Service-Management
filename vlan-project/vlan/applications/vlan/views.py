from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.views.generic.edit import FormView
from django.urls import reverse_lazy

from django.views.generic import (
    ListView,
    UpdateView,
    TemplateView,
    CreateView,
    DeleteView,
)

# Importamos los modelos locales
from .models import Interfaces, Vlan
from .forms import VlanForm, NewVlanForm
from .utils import (
    getDataVlan,
    getVlanGateway,
    createVlanGNS3,
    assignInterfacesVlan,
    deleteVlanGNS3,
    createSubInterfaz,
    deleteSubInterfaz
)

from .conexion import make_ssh_conexion

address_1 = '192.168.1.11'
address_2 = '192.168.1.12'
address_3 = '192.168.1.13'
address_4 = '192.168.1.1'


class VlanSearchView(FormView):

    template_name = 'vlan/index.html'
    form_class  = VlanForm
    success_url = reverse_lazy('vlan_app:vlan-menu')

    def form_valid(self, form):
        print(' ======== FORM VALID ========')

        ssh_user = form.cleaned_data['ssh_user']
        ssh_pass = form.cleaned_data['ssh_pass']

        global session_1
        session_1 = make_ssh_conexion( address_1, ssh_user, ssh_pass )

        global session_2
        session_2 = make_ssh_conexion( address_2, ssh_user, ssh_pass )

        global session_3
        session_3 = make_ssh_conexion( address_3, ssh_user, ssh_pass )

        global session_4
        session_4 = make_ssh_conexion( address_4, ssh_user, ssh_pass )

        val = getDataVlan( session_1 )
        if val:
            print('All the data was saved in the database')

        return super(VlanSearchView,self).form_valid(form)

class VlanListView(ListView):
    template_name = 'vlan/vlan_list.html'
    model = Vlan
    context_object_name = 'vlans'
    ordering = 'id'


class VlanView(TemplateView):
    template_name = 'vlan/vlan_menu.html'


class VlanUpdateView(UpdateView):
    template_name = 'vlan/vlan_update.html'
    model = Vlan
    success_url = reverse_lazy('vlan_app:vlan-list')
    fields = (
        'interfaces',
    )

    def form_valid(self, form):
        print(' ======== FORM VALID ========')
        vlan = form.save( commit = False )
         # Setting up all the interfaces in all the switches
        interfaces = list()
        for interface in form.cleaned_data['interfaces']:
            interfaces.append(interface)
        vlan_number = vlan.number
        print(f'VLAN number: { vlan_number }')
        # Assigning all the interfaces for the VLAN
        command_interfaces = [ f'int {interface}' for interface in interfaces]
        assignInterfacesVlan( session_1, command_interfaces, vlan_number)
        assignInterfacesVlan( session_2, command_interfaces, vlan_number)
        assignInterfacesVlan( session_3, command_interfaces, vlan_number)
        print('All the interfaces were created successfully in GNS3')
        # Retrieving only the Vlan One
        Vlan.objects.get(
            number = '1'
        ).interfaces.remove(*interfaces)

        return super( VlanUpdateView, self ).form_valid(form)


class VlanCreateView(CreateView):
    template_name = 'vlan/vlan_create.html'
    model = Vlan
    form_class = NewVlanForm
    success_url = reverse_lazy('vlan_app:vlan-list')

    def form_valid(self, form):
        print(' ======== FORM VALID ========')
        vlan = form.save( commit = False )
        network = vlan.network
        vlan_gateway = getVlanGateway( network )
        vlan.gateway = vlan_gateway
        vlan.save()
        # Setting up all the interfaces in all the switches
        interfaces = list()
        for interface in form.cleaned_data['interfaces']:
            interfaces.append(interface)

        vlan_number = form.cleaned_data['number']
        vlan_name   = form.cleaned_data['name']
        vlan_mask   = form.cleaned_data['mask']
        # Creating the Vlan in GNS3
        createVlanGNS3( session_1, vlan_number, vlan_name, vlan_gateway, vlan_mask )
        print('Vlan created successfully in GNS3')
        # Assigning all the interfaces for the VLAN
        command_interfaces = [ f'int {interface}' for interface in interfaces]
        assignInterfacesVlan( session_1, command_interfaces, vlan_number)
        assignInterfacesVlan( session_2, command_interfaces, vlan_number)
        assignInterfacesVlan( session_3, command_interfaces, vlan_number)
        print('All the interfaces were created successfully in GNS3')
        createSubInterfaz( session_4, vlan_number, vlan_gateway, vlan_mask )
        print('The subinterfaz in the router was created successfully')
        # Retrieving only the Vlan One
        Vlan.objects.get(
            number = '1'
        ).interfaces.remove(*interfaces)

        return super( VlanCreateView, self ).form_valid(form)


class VlanDeleteView(DeleteView):
    template_name = 'vlan/vlan_delete.html'
    model = Vlan
    success_url = reverse_lazy('vlan_app:vlan-list')

    # Recuperamos el objeto que al que se hace referencia en la URL
    def get_object(self):
        #Obtenemos el 'pk' que se manda en la URL a través del diccionario kwargs
        id_ = self.kwargs.get('pk')
        return get_object_or_404( Vlan, id = id_ )

    def delete(self,request,*args,**kwargs):
        # Obtenemos el objeto que se especifica en la url
        self.object = self.get_object()
        # Obtenemos todas las interfaces ligadas a esta VLAN
        interfaces = self.object.interfaces.all()
        command_interfaces = [ f'int {interface}' for interface in interfaces ]
        # Eliminamos la VLAN de GNS3
        vlan_number = self.object.number
        deleteVlanGNS3( session_1, vlan_number )
        print(f'The vlan {vlan_number} was deleted successfully')
        # Asignamos las interfaces de esta VLAN a la VLAN 1
        if interfaces:
            assignInterfacesVlan( session_1, command_interfaces )
            assignInterfacesVlan( session_2, command_interfaces )
            assignInterfacesVlan( session_3, command_interfaces )
            print('All the interfaces of this Vlan were returned to their original one')
        else:
            print('No interfaces detected')

        deleteSubInterfaz( session_4, vlan_number )
        print('The subinterfaz in the router was deleted successfully')
        # Adding the interfaces of this Vlan to the original one
        Vlan.objects.get(
            number = '1'
        ).interfaces.add(*interfaces)

        # Eliminamos el objeto del modelo de la BD
        self.object.delete()

        return HttpResponseRedirect( self.success_url )

