from django.core.management.base import BaseCommand
from dotenv import load_dotenv
import os
import subprocess

class Command(BaseCommand):
    help = 'Runs Celery with local environment settings'

    def add_arguments(self, parser):
        parser.add_argument('--pool', type=str, help='Pool implementation to use')

    def handle(self, *args, **options):
        # Load local environment variables
        env_path = os.path.join(os.getcwd(), '.env.local')
        load_dotenv(env_path)
        
        # Build command with optional pool argument
        command = ['celery', '-A', 'CompactNodeInt', 'worker', '-l', 'INFO']
        if options.get('pool'):
            command.extend(['--pool', options['pool']])
        
        # Run Celery worker
        subprocess.run(command) 