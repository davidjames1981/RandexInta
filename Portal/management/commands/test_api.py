import os
import json
import requests
from django.core.management.base import BaseCommand
from dotenv import load_dotenv

class Command(BaseCommand):
    help = 'Test API connectivity'

    def handle(self, *args, **options):
        # Load local environment variables
        env_path = os.path.join(os.getcwd(), '.env.local')
        load_dotenv(env_path)

        api_host = os.getenv('API_HOST')
        warehouse = os.getenv('WAREHOUSE')
        api_url = f"{api_host}/api/full-order/"

        self.stdout.write(f"\nTesting API Connection:")
        self.stdout.write(f"API Host: {api_host}")
        self.stdout.write(f"Warehouse: {warehouse}")
        self.stdout.write(f"Full URL: {api_url}")

        # Test payload
        payload = {
            "name": "TEST_ORDER",
            "warehouse": warehouse,
            "order_type": 3,
            "order_lines": [
                {
                    "line_number": 1,
                    "item": "TEST_ITEM",
                    "quantity": 1
                }
            ]
        }

        self.stdout.write("\nTest Payload:")
        self.stdout.write(json.dumps(payload, indent=2))

        try:
            self.stdout.write("\nAttempting API connection...")
            response = requests.post(
                api_url,
                json=payload,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )

            self.stdout.write(f"Response Status Code: {response.status_code}")
            self.stdout.write("Response Headers:")
            self.stdout.write(json.dumps(dict(response.headers), indent=2))

            try:
                response_json = response.json()
                self.stdout.write("Response Body:")
                self.stdout.write(json.dumps(response_json, indent=2))
            except json.JSONDecodeError:
                self.stdout.write(f"Response Text: {response.text}")

        except requests.exceptions.Timeout:
            self.stdout.write(self.style.ERROR("\nError: API request timed out after 30 seconds"))

        except requests.exceptions.ConnectionError as e:
            self.stdout.write(self.style.ERROR(f"\nError: Could not connect to API"))
            self.stdout.write(f"Details: {str(e)}")

            # Try to get more connection information
            import socket
            try:
                host = api_host.split('://')[1].split(':')[0]
                port = 8000
                sock = socket.create_connection((host, port), timeout=5)
                self.stdout.write(self.style.SUCCESS(f"Socket connection successful to {host}:{port}"))
                sock.close()
            except Exception as sock_e:
                self.stdout.write(self.style.ERROR(f"Socket connection failed: {str(sock_e)}"))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"\nError: Request failed"))
            self.stdout.write(f"Details: {str(e)}") 