from django.db import models

# Create your models here.

class Poll(models.Model):
    title = models.CharField(max_length=255)
    datetime_created=models.DateTimeField(auto_now_add = True)
    poll_content = models.CharField(max_length = 255, null=True, blank=True)
    tag = models.CharField(max_length=255, null=True, blank=True)