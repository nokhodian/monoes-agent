import requests
import json
import logging

logger = logging.getLogger(__name__)

class APIClient:
    BASE_URL = "http://apiv1.monoes.me"

    def __init__(self):
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def extract_test(self, config_name: str, html_content: str):
        """
        Test existing configs against the provided HTML.
        Returns a list of configs with their extraction scores.
        """
        url = f"{self.BASE_URL}/extracttest"
        payload = {
            "configName": config_name,
            "htmlContent": html_content
        }
        try:
            print(f"🌐 API Call: POST {url}")
            print(f"   Config Name: {config_name}")
            print(f"   HTML Length: {len(html_content)} chars")
            response = requests.post(url, headers=self.headers, json=payload)
            print(f"   Response Status: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            print(f"   Response: {len(result) if isinstance(result, list) else 'object'} items")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling extracttest: {e}")
            print(f"❌ API Error: {e}")
            return []

    def get_config(self, full_config_name: str):
        """
        Retrieve a specific config by its full name.
        """
        url = f"{self.BASE_URL}/configs/{full_config_name}"
        try:
            print(f"🌐 API Call: GET {url}")
            response = requests.get(url, headers={'Accept': 'application/json'})
            print(f"   Response Status: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            print(f"   ✅ Config retrieved successfully")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling get_config: {e}")
            print(f"❌ API Error: {e}")
            return None

    def generate_config(self, config_name: str, html_content: str, purpose: str, schema: dict):
        """
        Generate a new config based on the HTML and schema.
        """
        url = f"{self.BASE_URL}/generate-config"

        # Limit HTML content size (API might have limits)
        max_html_size = 500000  # 500KB
        if len(html_content) > max_html_size:
            print(f"⚠️  HTML content too large ({len(html_content)} chars), truncating to {max_html_size}")
            html_content = html_content[:max_html_size]

        payload = {
            "configName": config_name,
            "htmlContent": html_content,
            "purpose": purpose,
            "extractionSchema": schema
        }
        try:
            print(f"🌐 API Call: POST {url}")
            print(f"   Config Name: {config_name}")
            print(f"   Purpose: {purpose}")
            print(f"   HTML Length: {len(html_content)} chars")
            print(f"   Schema: {list(schema.keys()) if schema else 'empty'}")
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            print(f"   Response Status: {response.status_code}")
            if response.status_code == 422:
                print(f"   Response Body Length: {len(response.text) if response.text else 0}")
            response.raise_for_status()
            result = response.json()
            print(f"   ✅ Config generated successfully")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling generate_config: {e}")
            print(f"❌ API Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                response_text = getattr(e.response, 'text', None)
                print(f"   Response Body Length: {len(response_text) if response_text else 0}")
            return None
