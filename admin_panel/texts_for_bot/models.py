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


class SendedMessages(models.Model):
    send_date = models.DateTimeField()
    success_send = models.CharField(max_length=100, null=True, blank=True)
    not_send = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.title


class PlannedMessages(models.Model):
    planned_date = models.DateTimeField()
    planned_msg_text = models.CharField(max_length=1000)
    #status = models.CharField(max_length=30, default='Не отправлено')

    def __str__(self):
        return self.title
