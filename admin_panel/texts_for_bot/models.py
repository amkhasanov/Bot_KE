from django.db import models


class BotMessage(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)

    def __str__(self):
        return self.title

class ButtonText(models.Model):
    title = models.CharField(max_length=100)
    message_after_click = models.TextField(max_length=1000)

    def __str__(self):
        return self.title

