from typing import List, Optional, Callable
from ..models.core import AppState, Organization, Prospect
from ..services.data_service import DataService
from ..services.keyring_service import KeyringService
from ..services.payload_service import PayloadService


class AppStateManager:
    def __init__(self, base_path: str = "."):
        self.state = AppState()
        self.data_service = DataService(base_path)
        self.keyring_service = KeyringService()
        self.payload_service = PayloadService(f"{base_path}/schemas")
        
        # List of callbacks to notify when state changes
        self._update_callbacks: List[Callable[[], None]] = []
    
    def add_update_callback(self, callback: Callable[[], None]) -> None:
        """Add a callback to be called when state is updated."""
        self._update_callbacks.append(callback)
    
    def _notify_update(self) -> None:
        """Notify all registered callbacks that state has been updated."""
        for callback in self._update_callbacks:
            callback()
    
    def load_initial_data(self) -> None:
        """Load initial data from files."""
        # This doesn't change the UI state, so no notification needed
        pass
    
    def get_organizations(self) -> List[Organization]:
        """Get all organizations from data service."""
        return self.data_service.get_organizations()
    
    def select_organization(self, organization: Organization) -> None:
        """Select an organization and update UI state."""
        self.state.selected_organization = organization
        self.state.selected_webhook_index = None
        self.state.selected_prospect = None
        self.state.pending_prospect = None
        self.state.generated_payload = None
        self.state.payload_editable = False
        self.state.selected_profile = None
        self.state.available_profiles = []
        self._notify_update()
    
    def select_webhook(self, webhook_index: int) -> None:
        """Select a webhook and update UI state."""
        if not self.state.selected_organization:
            return
        
        if 0 <= webhook_index < len(self.state.selected_organization.webhooks):
            self.state.selected_webhook_index = webhook_index
            self.state.selected_prospect = None
            self.state.pending_prospect = None
            self.state.generated_payload = None
            self.state.payload_editable = False
            self.state.selected_profile = None
            
            # Load available profiles for this webhook
            webhook = self.state.selected_organization.webhooks[webhook_index]
            self.state.available_profiles = self.payload_service.get_integration_profiles(webhook.name)
            
            self._notify_update()
    
    def select_prospect(self, prospect: Prospect) -> None:
        """Select an existing prospect."""
        self.state.selected_prospect = prospect
        self.state.pending_prospect = None
        self._notify_update()
    
    def generate_new_prospect(self) -> Prospect:
        """Generate a new prospect for the selected organization."""
        if not self.state.selected_organization:
            raise ValueError("No organization selected")
        
        # Get current prospects data
        prospects_data = self.data_service.get_generated_prospects_data()
        org_prospects = prospects_data.get_org_prospects(self.state.selected_organization.id)
        
        # Generate new prospect
        index = org_prospects.next_prospect_index
        prospect = Prospect(
            firstName=f"Prospect{index}",
            lastName="Test",
            email=f"prospect{index}@example.com",
            phone=f"555-000-{index:04d}"
        )
        
        # Set as pending prospect (not saved yet)
        self.state.pending_prospect = prospect
        self.state.selected_prospect = None
        
        self._notify_update()
        return prospect
    
    def generate_payload(self, prospect: Optional[Prospect] = None, profile: Optional[str] = None) -> str:
        """Generate payload for selected webhook and prospect."""
        if not self.state.selected_organization or self.state.selected_webhook_index is None:
            raise ValueError("No organization or webhook selected")
        
        webhook = self.state.selected_organization.webhooks[self.state.selected_webhook_index]
        target_prospect = prospect or self.state.selected_prospect or self.state.pending_prospect
        
        if not target_prospect:
            raise ValueError("No prospect available for payload generation")
        
        # Generate payload
        payload_dict = self.payload_service.generate_payload(webhook.name, target_prospect, profile)
        payload_json = json.dumps(payload_dict, indent=2)
        
        self.state.generated_payload = payload_json
        self.state.selected_profile = profile
        
        self._notify_update()
        return payload_json
    
    def set_payload_editable(self, editable: bool) -> None:
        """Toggle payload edit mode."""
        self.state.payload_editable = editable
        self._notify_update()
    
    def update_payload(self, payload: str) -> None:
        """Update the generated payload."""
        self.state.generated_payload = payload
        # Don't notify update for payload text changes to avoid interfering with editing
    
    def save_prospect_after_successful_send(self) -> None:
        """Save pending prospect after successful webhook send."""
        if not self.state.pending_prospect or not self.state.selected_organization:
            return
        
        # Get current prospects data
        prospects_data = self.data_service.get_generated_prospects_data()
        org_prospects = prospects_data.get_org_prospects(self.state.selected_organization.id)
        
        # Add prospect to saved list
        org_prospects.prospects.append(self.state.pending_prospect)
        org_prospects.next_prospect_index += 1
        
        # Save to file
        self.data_service.save_generated_prospects_data(prospects_data)
        
        # Clear pending prospect
        self.state.pending_prospect = None
        self._notify_update()
    
    def add_organization(self, org_id: str, name: str, owner_id: str) -> None:
        """Add a new organization."""
        organizations = self.get_organizations()
        
        # Check if org_id already exists
        for org in organizations:
            if org.id == org_id:
                raise ValueError(f"Organization with ID '{org_id}' already exists")
        
        new_org = Organization(id=org_id, name=name, owner_id=owner_id)
        organizations.append(new_org)
        
        self.data_service.save_organizations(organizations)
        self._notify_update()
    
    def update_organization(self, org_id: str, name: str, owner_id: str) -> None:
        """Update an existing organization."""
        organizations = self.get_organizations()
        
        for org in organizations:
            if org.id == self.state.selected_organization.id:
                org.id = org_id
                org.name = name
                org.owner_id = owner_id
                break
        
        self.data_service.save_organizations(organizations)
        
        # Update selected organization
        if self.state.selected_organization:
            self.state.selected_organization.id = org_id
            self.state.selected_organization.name = name
            self.state.selected_organization.owner_id = owner_id
        
        self._notify_update()
    
    def add_webhook(self, name: str, url: str) -> None:
        """Add webhook to selected organization."""
        if not self.state.selected_organization:
            raise ValueError("No organization selected")
        
        organizations = self.get_organizations()
        
        for org in organizations:
            if org.id == self.state.selected_organization.id:
                from ..models.core import Webhook
                new_webhook = Webhook(name=name, url=url)
                org.webhooks.append(new_webhook)
                
                # Update state as well
                self.state.selected_organization.webhooks.append(new_webhook)
                break
        
        self.data_service.save_organizations(organizations)
        self._notify_update()
    
    def delete_webhook(self, webhook_index: int) -> None:
        """Delete webhook from selected organization."""
        if not self.state.selected_organization:
            return
        
        if 0 <= webhook_index < len(self.state.selected_organization.webhooks):
            organizations = self.get_organizations()
            
            for org in organizations:
                if org.id == self.state.selected_organization.id:
                    del org.webhooks[webhook_index]
                    del self.state.selected_organization.webhooks[webhook_index]
                    break
            
            self.data_service.save_organizations(organizations)
            
            # Reset webhook selection if deleted webhook was selected
            if self.state.selected_webhook_index == webhook_index:
                self.state.selected_webhook_index = None
                self.state.selected_prospect = None
                self.state.pending_prospect = None
                self.state.generated_payload = None
                self.state.payload_editable = False
                self.state.selected_profile = None
                self.state.available_profiles = []
            
            self._notify_update()
    
    def get_existing_prospects(self) -> List[Prospect]:
        """Get existing prospects for selected organization."""
        if not self.state.selected_organization:
            return []
        
        prospects_data = self.data_service.get_generated_prospects_data()
        org_prospects = prospects_data.get_org_prospects(self.state.selected_organization.id)
        return org_prospects.prospects


# Import json here to avoid circular imports
import json