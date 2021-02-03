from django.db import models

# Create your models here.

class Interfaces(models.Model):

    name = models.CharField(
        'Interface Name',
         max_length = 20
    )

    class meta:
        verbose_name = 'Interface'
        verbose_name_plural = 'Interfaces'

    def __str__(self):
        return self.name
    

class Vlan(models.Model):
    
    name = models.CharField(
        'Vlan Name',
         max_length = 40
    )

    network = models.CharField(
        'Network',
         max_length = 40
    )

    mask = models.CharField(
        'Mask',
         max_length = 40
    )

    gateway = models.CharField(
        'Gateway',
         max_length = 40,
         blank = True
    )

    number = models.CharField(
        'Number',
         max_length = 5
    )

    interfaces = models.ManyToManyField(Interfaces)

    def __str__(self):
        return self.name + ' - ' + self.network

    

    



   
