from django.db import models

# Create your models here.


class NfsServer(models.Model):
    ip_address = models.CharField(max_length=15, default="127.0.0.1")
    mount_point = models.CharField(max_length=100, default="/mnt/")

    @property
    def mount_url(self):
        return 'nfs://' + self.ip_address + self.mount_point

    def __str__(self):
        return self.ip_address + ":" + self.mount_point
