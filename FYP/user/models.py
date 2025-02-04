from django.db import models

# Create your models here.
from django.db import models

class pdfdocument(models.Model):
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    upload_date = models.DateTimeField(auto_now_add=True)
    astra_id = models.CharField(max_length=255, unique=True)  # Astra DB document ID
