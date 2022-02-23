from django.db import models


class Uploadfolder(models.Model):
    File_to_upload = models.FileField(upload_to='main/exel/')
