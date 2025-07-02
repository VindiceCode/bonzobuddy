from typing import Dict, Any, List, Optional
from ..models.core import Prospect
from ..services.schema_registry import SchemaRegistry


class PayloadService:
    """
    Modern payload generation service using Pydantic schema models.
    
    This replaces the old file-based payload generation with a
    clean, type-safe approach using the SchemaRegistry.
    """
    
    def __init__(self, schemas_path: str = "schemas"):
        self.schema_registry = SchemaRegistry(schemas_path)
    
    def get_integration_profiles(self, webhook_name: str) -> List[str]:
        """
        Get available profiles for a webhook integration.
        
        Args:
            webhook_name: Webhook name (e.g., "Zillow for Starters Demo")
            
        Returns:
            List of profile names, empty if integration not found
        """
        integration, _ = self.schema_registry.resolve_webhook_name(webhook_name)
        if not integration:
            return []
        
        return self.schema_registry.get_profiles_for_integration(integration)
    
    def generate_payload(self, webhook_name: str, prospect: Prospect, profile: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate payload for given webhook and prospect.
        
        Args:
            webhook_name: Webhook name (e.g., "Zillow for Starters Demo")
            prospect: Prospect data
            profile: Optional profile name (e.g., "simple", "longForm")
            
        Returns:
            Generated payload dictionary
            
        Raises:
            ValueError: If webhook/integration cannot be resolved or schema not found
        """
        # Convert prospect to dictionary for schema processing
        prospect_data = {
            "firstName": prospect.firstName,
            "lastName": prospect.lastName,
            "email": prospect.email,
            "phone": prospect.phone
        }
        
        return self.schema_registry.generate_payload(webhook_name, prospect_data, profile)
    
    def save_custom_schema(self, webhook_name: str, schema_name: str, payload: Dict[str, Any]) -> None:
        """
        Save a custom schema based on an edited payload.
        
        Args:
            webhook_name: Webhook name to determine integration
            schema_name: Name for the custom schema
            payload: The payload structure to save as schema
            
        Raises:
            ValueError: If webhook cannot be resolved
        """
        integration, _ = self.schema_registry.resolve_webhook_name(webhook_name)
        if not integration:
            raise ValueError(f"Cannot resolve integration from webhook name: {webhook_name}")
        
        # Find the integration's category
        schema_info_by_category = self.schema_registry.get_schema_info_by_category()
        integration_category = None
        
        for category, schema_infos in schema_info_by_category.items():
            for schema_info in schema_infos:
                if schema_info.integration == integration:
                    integration_category = category
                    break
            if integration_category:
                break
        
        if not integration_category:
            raise ValueError(f"Cannot determine category for integration: {integration}")
        
        # Create custom schemas directory
        custom_schemas_path = self.schema_registry.schemas_path / integration_category / integration / "custom_schemas"
        custom_schemas_path.mkdir(exist_ok=True)
        
        # Convert payload to schema format
        schema_data = self._payload_to_schema(payload)
        
        # Save the custom schema
        schema_file = custom_schemas_path / f"{schema_name.lower().replace(' ', '_')}_schema.json"
        
        import json
        with open(schema_file, 'w') as f:
            json.dump(schema_data, f, indent=2)
    
    def _payload_to_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a payload back to schema format.
        
        This is a best-effort conversion for custom schema saving.
        Static values are preserved, but dynamic fields need to be
        manually updated by the user.
        """
        schema = {}
        
        for key, value in payload.items():
            if isinstance(value, dict):
                # Nested object
                schema[key] = {
                    "type": "object",
                    "properties": self._payload_to_schema(value)
                }
            elif isinstance(value, str):
                schema[key] = {
                    "type": "string",
                    "static": value
                }
            elif isinstance(value, int):
                schema[key] = {
                    "type": "integer", 
                    "static": value
                }
            elif isinstance(value, float):
                schema[key] = {
                    "type": "number",
                    "static": value
                }
            elif isinstance(value, bool):
                schema[key] = {
                    "type": "boolean",
                    "static": value
                }
            else:
                # Fallback for other types
                schema[key] = {
                    "type": "string",
                    "static": str(value)
                }
        
        return schema
    
    def get_categories_and_integrations(self) -> Dict[str, List[str]]:
        """
        Get all categories and their integrations for UI purposes.
        
        Returns:
            Dictionary mapping category names to lists of integration names
        """
        result = {}
        for category in self.schema_registry.get_categories():
            result[category] = self.schema_registry.get_integrations_for_category(category)
        return result
    
    def reload_schemas(self) -> None:
        """Reload all schemas from the filesystem."""
        self.schema_registry = SchemaRegistry(str(self.schema_registry.schemas_path))