from django.contrib import admin
from .models import Interfaces, Vlan
# Register your models here.
admin.site.register(Interfaces)
admin.site.register(Vlan)