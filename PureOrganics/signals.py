from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.management import call_command
from django.apps import apps


@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        subject = 'Welcome to Pure Organics'
        message = f'Hi {instance.username}, thank you for registering at Pure Organics.'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [instance.email]
        send_mail(subject, message, email_from, recipient_list)
# Function to export model data to JSON file
def export_to_json(model):
    model_name = model._meta.model_name
    app_label = model._meta.app_label
    file_path = f'/Users/nimishachowdarycherukuri/PycharmProjects/IADS/json/{model_name}_json.json'
    call_command('dumpdata', f'{app_label}.{model_name}', '--indent', '4', '--output', file_path)

# Loop through all models in the app and connect the post_save signal
for model in apps.get_app_config('PureOrganics').get_models():
    @receiver(post_save, sender=model)
    def model_post_save(sender, instance, **kwargs):
        export_to_json(sender)