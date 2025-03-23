from django.core.management.commands.runserver import Command as RunserverCommand
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
import os

class Command(RunserverCommand):
    help = 'Runs the development server with local environment settings'

    def handle(self, *args, **options):
        # Load local environment variables
        env_path = os.path.join(os.getcwd(), '.env.local')
        load_dotenv(env_path)
        
        # Run the server with parent class
        super().handle(*args, **options) 