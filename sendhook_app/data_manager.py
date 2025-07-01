# data_manager.py
import json
import os

ORG_WEBHOOKS_FILE = "org_webhooks.json"
GENERATED_PROSPECTS_FILE = "generated_prospects.json"
WEBHOOK_DOCS_DIR = "webhook_payload_docs"

class DataManager:
    def __init__(self):
        self._initialize_data_files()

    def _initialize_data_files(self):
        if not os.path.exists(ORG_WEBHOOKS_FILE):
            with open(ORG_WEBHOOKS_FILE, 'w') as f:
                json.dump({"organizations": []}, f, indent=4)
        if not os.path.exists(GENERATED_PROSPECTS_FILE):
            with open(GENERATED_PROSPECTS_FILE, 'w') as f:
                json.dump({}, f, indent=4)

    def get_organizations(self):
        with open(ORG_WEBHOOKS_FILE, 'r') as f:
            return json.load(f).get("organizations", [])

    def get_webhooks_for_org(self, org_id):
        orgs = self.get_organizations()
        for org in orgs:
            if org.get("id") == org_id:
                return org.get("webhooks", [])
        return []

    def get_prospects_for_org(self, org_id):
        with open(GENERATED_PROSPECTS_FILE, 'r') as f:
            data = json.load(f)
            return data.get(org_id, {}).get("prospects", [])

    def get_integration_categories(self):
        return [d for d in os.listdir(WEBHOOK_DOCS_DIR) if os.path.isdir(os.path.join(WEBHOOK_DOCS_DIR, d))]

    def get_integrations_for_category(self, category):
        return [d for d in os.listdir(os.path.join(WEBHOOK_DOCS_DIR, category)) if os.path.isdir(os.path.join(WEBHOOK_DOCS_DIR, category, d))]

    def add_organization(self, name, org_id):
        with open(ORG_WEBHOOKS_FILE, 'r+') as f:
            data = json.load(f)
            data["organizations"].append({"id": org_id, "name": name, "webhooks": []})
            f.seek(0)
            json.dump(data, f, indent=4)
        
        with open(GENERATED_PROSPECTS_FILE, 'r+') as f:
            data = json.load(f)
            data[org_id] = {"next_prospect_index": 1, "prospects": []}
            f.seek(0)
            json.dump(data, f, indent=4)

    def add_webhook(self, org_id, webhook_name, webhook_url):
        with open(ORG_WEBHOOKS_FILE, 'r+') as f:
            data = json.load(f)
            for org in data["organizations"]:
                if org["id"] == org_id:
                    org["webhooks"].append({"name": webhook_name, "url": webhook_url})
                    break
            f.seek(0)
            json.dump(data, f, indent=4)

    def delete_webhook(self, org_id, webhook_name):
        with open(ORG_WEBHOOKS_FILE, 'r+') as f:
            data = json.load(f)
            for org in data["organizations"]:
                if org["id"] == org_id:
                    org["webhooks"] = [wh for wh in org["webhooks"] if wh["name"] != webhook_name]
                    break
            f.seek(0)
            json.dump(data, f, indent=4)

    def get_next_prospect_index(self, org_id):
        with open(GENERATED_PROSPECTS_FILE, 'r') as f:
            data = json.load(f)
            return data.get(org_id, {}).get("next_prospect_index", 1)

    def store_prospect(self, org_id, prospect_data):
        with open(GENERATED_PROSPECTS_FILE, 'r+') as f:
            data = json.load(f)
            data[org_id]["prospects"].append(prospect_data)
            data[org_id]["next_prospect_index"] += 1
            f.seek(0)
            json.dump(data, f, indent=4)
