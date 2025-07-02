from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Webhook(BaseModel):
    name: str
    url: str


class Organization(BaseModel):
    id: str
    name: str
    owner_id: str
    webhooks: List[Webhook] = Field(default_factory=list)


class Prospect(BaseModel):
    firstName: str
    lastName: str
    email: str
    phone: str


class OrganizationProspects(BaseModel):
    next_prospect_index: int = 1
    prospects: List[Prospect] = Field(default_factory=list)


class GeneratedProspectsData(BaseModel):
    data: Dict[str, OrganizationProspects] = Field(default_factory=dict)
    
    def get_org_prospects(self, org_id: str) -> OrganizationProspects:
        if org_id not in self.data:
            self.data[org_id] = OrganizationProspects()
        return self.data[org_id]


class AppState(BaseModel):
    selected_organization: Optional[Organization] = None
    selected_webhook_index: Optional[int] = None
    selected_prospect: Optional[Prospect] = None
    pending_prospect: Optional[Prospect] = None
    generated_payload: Optional[str] = None
    payload_editable: bool = False
    available_profiles: List[str] = Field(default_factory=list)
    selected_profile: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True