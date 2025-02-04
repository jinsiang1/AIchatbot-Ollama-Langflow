from django.db import models

# Create your models here.

class chathistory(models.Model):
    session_id = models.CharField(max_length=255)  # Assuming session IDs are hex strings
    user_message = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.session_id} at {self.timestamp}"
