import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from ..models.schemas import IntegrationSchema, SchemaInfo


class SchemaRegistry:
    """
    Central registry for all webhook payload schemas.
    
    Follows the "convention over configuration" principle by discovering
    schemas dynamically from the filesystem structure.
    """
    
    def __init__(self, schemas_path: str = "schemas"):
        self.schemas_path = Path(schemas_path)
        
        # Registry storage
        self._schemas: Dict[str, Dict[str, IntegrationSchema]] = defaultdict(dict)
        self._schema_info: List[SchemaInfo] = []
        self._categories: Dict[str, List[str]] = defaultdict(list)
        
        # Load all schemas
        self._discover_schemas()
    
    def _discover_schemas(self) -> None:
        """
        Discover all schemas by scanning the filesystem.
        
        Follows the structure: schemas/{category}/{integration}/*_schema.json
        """
        if not self.schemas_path.exists():
            print(f"Warning: Schemas path {self.schemas_path} does not exist")
            return
        
        # Scan categories (top-level directories)
        for category_path in self.schemas_path.iterdir():
            if not category_path.is_dir() or category_path.name.startswith('.'):
                continue
            
            category = category_path.name
            
            # Scan integrations (second-level directories)
            for integration_path in category_path.iterdir():
                if not integration_path.is_dir() or integration_path.name.startswith('.'):
                    continue
                
                integration = integration_path.name
                self._categories[category].append(integration)
                
                # Find all schema files in this integration
                schema_files = list(integration_path.glob("*_schema.json"))
                
                for schema_file in schema_files:
                    try:
                        # Extract profile from filename
                        profile = self._extract_profile(schema_file.stem, integration)
                        
                        # Create schema info
                        schema_info = SchemaInfo(
                            category=category,
                            integration=integration,
                            profile=profile,
                            file_path=str(schema_file)
                        )
                        self._schema_info.append(schema_info)
                        
                        # Load the actual schema
                        schema = IntegrationSchema.from_json_file(
                            str(schema_file),
                            category=category,
                            integration=integration,
                            profile=profile
                        )
                        
                        # Store in registry
                        schema_key = f"{integration}_{profile}" if profile else integration
                        self._schemas[integration][schema_key] = schema
                        
                    except Exception as e:
                        print(f"Warning: Failed to load schema {schema_file}: {e}")
    
    def _extract_profile(self, filename_stem: str, integration: str) -> Optional[str]:
        """
        Extract profile name from schema filename.
        
        Examples:
        - zillow_simple_schema -> "simple"
        - mmi_mortgage_schema -> "mortgage"  
        - hubspot_schema -> None (single schema)
        """
        # Remove the integration prefix if present
        integration_lower = integration.lower()
        if filename_stem.lower().startswith(integration_lower + "_"):
            remaining = filename_stem[len(integration_lower) + 1:]
            
            # Remove _schema suffix if present
            if remaining.endswith("_schema"):
                remaining = remaining[:-7]
            
            return remaining if remaining else None
        
        # Check if it ends with _schema and remove it
        if filename_stem.endswith("_schema"):
            base_name = filename_stem[:-7]
            if base_name.lower() != integration_lower:
                return base_name
        
        return None
    
    def get_categories(self) -> List[str]:
        """Get all available categories."""
        return list(self._categories.keys())
    
    def get_integrations_for_category(self, category: str) -> List[str]:
        """Get all integrations in a category."""
        return self._categories.get(category, [])
    
    def get_all_integrations(self) -> List[str]:
        """Get all available integrations across all categories."""
        integrations = set()
        for category_integrations in self._categories.values():
            integrations.update(category_integrations)
        return sorted(integrations)
    
    def get_profiles_for_integration(self, integration: str) -> List[str]:
        """
        Get all available profiles for an integration.
        
        Returns empty list if integration not found.
        Returns ["default"] if integration has only one schema.
        """
        if integration not in self._schemas:
            return []
        
        profiles = []
        for schema_key, schema in self._schemas[integration].items():
            if schema.profile:
                profiles.append(schema.profile)
            else:
                profiles.append("default")
        
        return sorted(profiles)
    
    def get_schema(self, integration: str, profile: Optional[str] = None) -> Optional[IntegrationSchema]:
        """
        Get a specific schema by integration and profile.
        
        Args:
            integration: The integration name (e.g., "Zillow")
            profile: The profile name (e.g., "simple") or None for default
            
        Returns:
            IntegrationSchema or None if not found
        """
        if integration not in self._schemas:
            return None
        
        # If no profile specified, try to get the default or any available
        if profile is None:
            # First try to find a schema without a profile
            if integration in self._schemas[integration]:
                return self._schemas[integration][integration]
            
            # If not found, get the first available schema
            schemas = self._schemas[integration]
            if schemas:
                return next(iter(schemas.values()))
            
            return None
        
        # Look for specific profile
        schema_key = f"{integration}_{profile}"
        return self._schemas[integration].get(schema_key)
    
    def resolve_webhook_name(self, webhook_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Resolve a webhook name to (integration, profile).
        
        Handles the naming convention: "{Integration} for {Organization}"
        
        Examples:
        - "Zillow for Starters Demo" -> ("Zillow", None)
        - "MMI for Test Org" -> ("Mmi", None)
        
        Returns:
            (integration, profile) tuple or (None, None) if not resolvable
        """
        # Handle the standard naming convention: "{Integration} for {Organization}"
        if " for " in webhook_name:
            integration_part = webhook_name.split(" for ")[0].strip()
        else:
            # Fallback for webhook names that don't follow convention
            integration_part = webhook_name.strip()
        
        # Find matching integration (case-insensitive)
        for integration in self.get_all_integrations():
            if integration.lower() == integration_part.lower():
                return integration, None
        
        return None, None
    
    def get_schema_info_by_category(self) -> Dict[str, List[SchemaInfo]]:
        """Get schema info organized by category for UI purposes."""
        result = defaultdict(list)
        for schema_info in self._schema_info:
            result[schema_info.category].append(schema_info)
        return dict(result)
    
    def generate_payload(self, webhook_name: str, prospect_data: Dict[str, str], profile: Optional[str] = None) -> Dict[str, any]:
        """
        Generate a payload for a given webhook name and prospect data.
        
        Args:
            webhook_name: The webhook name (e.g., "Zillow for Starters Demo")
            prospect_data: Dictionary with prospect info
            profile: Optional profile override
            
        Returns:
            Generated payload dictionary
            
        Raises:
            ValueError: If webhook/integration cannot be resolved
        """
        integration, resolved_profile = self.resolve_webhook_name(webhook_name)
        
        if not integration:
            raise ValueError(f"Cannot resolve integration from webhook name: {webhook_name}")
        
        # Use provided profile or resolved profile
        target_profile = profile or resolved_profile
        
        schema = self.get_schema(integration, target_profile)
        if not schema:
            available_profiles = self.get_profiles_for_integration(integration)
            raise ValueError(f"No schema found for {integration} with profile {target_profile}. Available profiles: {available_profiles}")
        
        return schema.generate_payload(prospect_data)