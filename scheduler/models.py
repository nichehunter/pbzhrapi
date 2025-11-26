from django.db import models
from django.utils.timezone import now

# Create your models here.


class JobLock(models.Model):
    name = models.CharField(max_length=255, unique=True)  # A unique name for the job
    locked_until = models.DateTimeField(default=now)  # The time until the lock is valid

    def __str__(self):
        return f"{self.name} (locked_until: {self.locked_until})" 