import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any

from ..models.core import Organization, Webhook, GeneratedProspectsData, OrganizationProspects


class DataService:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.org_webhooks_file = self.base_path / "org_webhooks.json"
        self.generated_prospects_file = self.base_path / "generated_prospects.json"
        
        # Ensure files exist
        self._ensure_files_exist()
    
    def _ensure_files_exist(self) -> None:
        """Ensure required JSON files exist with default structure."""
        if not self.org_webhooks_file.exists():
            self._write_json_atomic(self.org_webhooks_file, [])
        
        if not self.generated_prospects_file.exists():
            self._write_json_atomic(self.generated_prospects_file, {})
    
    def _write_json_atomic(self, file_path: Path, data: Any) -> None:
        """Write JSON data atomically to prevent corruption."""
        with tempfile.NamedTemporaryFile(
            mode='w', 
            dir=file_path.parent, 
            delete=False,
            suffix='.tmp'
        ) as temp_file:
            json.dump(data, temp_file, indent=2)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        
        # Atomic rename
        os.rename(temp_file.name, file_path)
    
    def get_organizations(self) -> List[Organization]:
        """Load organizations from JSON and parse into Pydantic models."""
        try:
            with open(self.org_webhooks_file, 'r') as f:
                data = json.load(f)
            
            # Handle legacy format where orgs are wrapped in "organizations" key
            if isinstance(data, dict) and "organizations" in data:
                org_list = data["organizations"]
            elif isinstance(data, list):
                org_list = data
            else:
                return []
            
            organizations = []
            for org_data in org_list:
                # Skip if org_data is not a dict (malformed data)
                if not isinstance(org_data, dict):
                    continue
                    
                # Parse webhooks
                webhooks = [Webhook(**webhook) for webhook in org_data.get('webhooks', [])]
                
                # Create organization with parsed webhooks
                # Handle missing owner_id for legacy data
                org = Organization(
                    id=org_data['id'],
                    name=org_data['name'],
                    owner_id=org_data.get('owner_id', ''),  # Default to empty string for legacy data
                    webhooks=webhooks
                )
                organizations.append(org)
            
            return organizations
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return []
    
    def save_organizations(self, organizations: List[Organization]) -> None:
        """Save organizations to JSON file."""
        data = []
        for org in organizations:
            org_dict = {
                'id': org.id,
                'name': org.name,
                'owner_id': org.owner_id,
                'webhooks': [{'name': webhook.name, 'url': webhook.url} for webhook in org.webhooks]
            }
            data.append(org_dict)
        
        self._write_json_atomic(self.org_webhooks_file, data)
    
    def get_generated_prospects_data(self) -> GeneratedProspectsData:
        """Load generated prospects data from JSON."""
        try:
            with open(self.generated_prospects_file, 'r') as f:
                data = json.load(f)
            
            # Parse into Pydantic model
            prospects_data = GeneratedProspectsData(data={})
            for org_id, org_prospects_data in data.items():
                prospects_data.data[org_id] = OrganizationProspects(
                    next_prospect_index=org_prospects_data.get('next_prospect_index', 1),
                    prospects=[
                        {
                            'firstName': prospect['firstName'],
                            'lastName': prospect['lastName'],
                            'email': prospect['email'],
                            'phone': prospect['phone']
                        }
                        for prospect in org_prospects_data.get('prospects', [])
                    ]
                )
            
            return prospects_data
        except (FileNotFoundError, json.JSONDecodeError):
            return GeneratedProspectsData(data={})
    
    def save_generated_prospects_data(self, prospects_data: GeneratedProspectsData) -> None:
        """Save generated prospects data to JSON file."""
        data = {}
        for org_id, org_prospects in prospects_data.data.items():
            data[org_id] = {
                'next_prospect_index': org_prospects.next_prospect_index,
                'prospects': [
                    {
                        'firstName': prospect.firstName,
                        'lastName': prospect.lastName,
                        'email': prospect.email,
                        'phone': prospect.phone
                    }
                    for prospect in org_prospects.prospects
                ]
            }
        
        self._write_json_atomic(self.generated_prospects_file, data)