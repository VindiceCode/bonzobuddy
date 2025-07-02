from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union, List
from enum import Enum


class SchemaNodeType(str, Enum):
    """Types of schema nodes."""
    STATIC = "static"
    DYNAMIC = "dynamic"
    OBJECT = "object"


class DynamicFieldType(str, Enum):
    """Dynamic field types that map to prospect data."""
    FIRST_NAME = "firstName"
    LAST_NAME = "lastName"
    EMAIL = "email"
    PHONE = "phone"


class SchemaNode(BaseModel):
    """
    Represents a single node in a payload schema.
    
    This is the Pydantic-native representation of schema fields,
    replacing the old JSON format with type-safe models.
    """
    # Core field properties
    type: str  # "string", "integer", "object", etc.
    
    # Value sources (mutually exclusive)
    static: Optional[Any] = None  # Static value
    dynamic: Optional[DynamicFieldType] = None  # Maps to prospect data
    
    # For object types
    properties: Optional[Dict[str, 'SchemaNode']] = None
    
    @property
    def node_type(self) -> SchemaNodeType:
        """Determine the node type based on the field configuration."""
        if self.dynamic is not None:
            return SchemaNodeType.DYNAMIC
        elif self.properties is not None:
            return SchemaNodeType.OBJECT
        else:
            return SchemaNodeType.STATIC
    
    def get_value(self, prospect_data: Dict[str, Any]) -> Any:
        """
        Generate the value for this node based on its type.
        
        Args:
            prospect_data: Dictionary with keys like 'firstName', 'lastName', etc.
        
        Returns:
            The value for this field in the generated payload
        """
        if self.node_type == SchemaNodeType.DYNAMIC:
            return prospect_data.get(self.dynamic.value)
        elif self.node_type == SchemaNodeType.STATIC:
            return self.static
        elif self.node_type == SchemaNodeType.OBJECT:
            if not self.properties:
                return {}
            
            result = {}
            for field_name, field_node in self.properties.items():
                result[field_name] = field_node.get_value(prospect_data)
            return result
        
        return None


class IntegrationSchema(BaseModel):
    """
    Represents a complete payload schema for an integration.
    
    This replaces the need to parse JSON schema files at runtime.
    """
    # Metadata
    name: str  # e.g., "zillow_simple", "mmi_mortgage"
    category: str  # e.g., "lead_sources", "internal_integrations"
    integration: str  # e.g., "Zillow", "Mmi" 
    profile: Optional[str] = None  # e.g., "simple", "mortgage" (None for single-schema integrations)
    
    # Schema definition
    fields: Dict[str, SchemaNode]
    
    # Optional metadata
    description: Optional[str] = None
    
    def generate_payload(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete payload using this schema and prospect data.
        
        Args:
            prospect_data: Dictionary with prospect info
            
        Returns:
            Complete payload dictionary ready for JSON serialization
        """
        payload = {}
        for field_name, field_node in self.fields.items():
            payload[field_name] = field_node.get_value(prospect_data)
        return payload
    
    @classmethod
    def from_json_file(cls, file_path: str, category: str, integration: str, profile: Optional[str] = None) -> 'IntegrationSchema':
        """
        Create an IntegrationSchema from a legacy JSON schema file.
        
        This method provides backwards compatibility during the migration.
        """
        import json
        from pathlib import Path
        
        with open(file_path, 'r') as f:
            schema_data = json.load(f)
        
        # Convert JSON schema format to Pydantic models
        fields = {}
        for field_name, field_def in schema_data.items():
            fields[field_name] = cls._convert_json_field(field_def)
        
        # Extract name from filename
        file_stem = Path(file_path).stem
        
        return cls(
            name=file_stem,
            category=category,
            integration=integration,
            profile=profile,
            fields=fields
        )
    
    @classmethod
    def _convert_json_field(cls, field_def: Dict[str, Any]) -> SchemaNode:
        """Convert old JSON field definition to SchemaNode."""
        node_kwargs = {
            "type": field_def.get("type", "string")
        }
        
        # Handle static values
        if "static" in field_def:
            node_kwargs["static"] = field_def["static"]
        
        # Handle dynamic values
        if "dynamic" in field_def:
            try:
                node_kwargs["dynamic"] = DynamicFieldType(field_def["dynamic"])
            except ValueError:
                # If the dynamic type is not recognized, treat as static
                node_kwargs["static"] = f"UNKNOWN_DYNAMIC:{field_def['dynamic']}"
        
        # Handle nested objects
        if "properties" in field_def:
            properties = {}
            for prop_name, prop_def in field_def["properties"].items():
                properties[prop_name] = cls._convert_json_field(prop_def)
            node_kwargs["properties"] = properties
        
        return SchemaNode(**node_kwargs)


class SchemaInfo(BaseModel):
    """
    Lightweight schema information for discovery and UI purposes.
    """
    category: str
    integration: str
    profile: Optional[str] = None
    file_path: str
    
    @property
    def display_name(self) -> str:
        """Display name for UI (just the integration name)."""
        return self.integration
    
    @property
    def profile_display_name(self) -> str:
        """Display name for profile dropdown."""
        return self.profile or "default"


# Enable forward references
SchemaNode.model_rebuild()