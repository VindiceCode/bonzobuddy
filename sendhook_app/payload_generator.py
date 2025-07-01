# payload_generator.py
import json
import os

WEBHOOK_DOCS_DIR = "webhook_payload_docs"

class PayloadGenerator:
    def __init__(self, org_id, prospect_index):
        self.org_id = org_id
        self.prospect_index = prospect_index

    def _get_dynamic_value(self, dynamic_type, first_name, last_name, email, phone):
        if dynamic_type == "firstName":
            return first_name
        if dynamic_type == "lastName":
            return last_name
        if dynamic_type == "email":
            return email
        if dynamic_type == "phone":
            return phone
        return None

    def _generate_from_schema(self, schema, first_name, last_name, email, phone):
        payload = {}
        for key, value in schema.items():
            if "type" not in value: continue

            if value["type"] == "object":
                payload[key] = self._generate_from_schema(value["properties"], first_name, last_name, email, phone)
            elif "dynamic" in value:
                payload[key] = self._get_dynamic_value(value["dynamic"], first_name, last_name, email, phone)
            elif "static" in value:
                payload[key] = value["static"]
        return payload

    def generate_payload(self, integration, category, first_name, last_name, email, phone):
        schema_path = os.path.join(WEBHOOK_DOCS_DIR, category, integration, f"{integration.lower()}_schema.json")
        if not os.path.exists(schema_path):
            # Fallback for Zillow's unique schema name
            if integration.lower() == 'zillow':
                schema_path = os.path.join(WEBHOOK_DOCS_DIR, category, integration, "zillow_schema.json")
            else:
                raise FileNotFoundError(f"Schema not found for {integration}")

        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        return self._generate_from_schema(schema, first_name, last_name, email, phone)
