from django.contrib import admin
from .models import User, Soldier, Equipment, InventoryLog

admin.site.register(User)
admin.site.register(Soldier)
admin.site.register(Equipment)
admin.site.register(InventoryLog)
