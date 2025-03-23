from django.core.management.base import BaseCommand
from dotenv import load_dotenv
import os
import subprocess

class Command(BaseCommand):
    help = 'Runs Celery beat with local environment settings'

    def handle(self, *args, **options):
        # Load local environment variables
        env_path = os.path.join(os.getcwd(), '.env.local')
        load_dotenv(env_path)
        
        # Run Celery beat
        subprocess.run(['celery', '-A', 'CompactNodeInt', 'beat', '-l', 'INFO']) 