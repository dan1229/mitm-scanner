from django.contrib import admin

# Register your models here.
from mitm.models import NfsServer


class NfsServerAdmin(admin.ModelAdmin):
    fields = ('ip_address', 'mount_point')


admin.site.register(NfsServer, NfsServerAdmin)