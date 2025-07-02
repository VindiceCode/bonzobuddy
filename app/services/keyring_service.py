import keyring
from typing import Optional


class KeyringService:
    SERVICE_NAME = "BonzoBuddy"
    ADMIN_PASSWORD_KEY = "admin_password"
    
    def set_admin_password(self, password: str) -> None:
        """Store the global admin password for Bonzo platform impersonation."""
        keyring.set_password(self.SERVICE_NAME, self.ADMIN_PASSWORD_KEY, password)
    
    def get_admin_password(self) -> Optional[str]:
        """Retrieve the global admin password."""
        return keyring.get_password(self.SERVICE_NAME, self.ADMIN_PASSWORD_KEY)
    
    def delete_admin_password(self) -> None:
        """Delete the stored admin password."""
        try:
            keyring.delete_password(self.SERVICE_NAME, self.ADMIN_PASSWORD_KEY)
        except keyring.errors.PasswordDeleteError:
            # Password doesn't exist, which is fine
            pass
    
    def has_admin_password(self) -> bool:
        """Check if admin password is set."""
        return self.get_admin_password() is not None
    
    # Legacy methods for backwards compatibility during transition
    def set_password(self, org_id: str, password: str) -> None:
        """Legacy method - now sets admin password globally."""
        self.set_admin_password(password)
    
    def get_password(self, org_id: str) -> Optional[str]:
        """Legacy method - now gets admin password globally."""
        return self.get_admin_password()
    
    def delete_password(self, org_id: str) -> None:
        """Legacy method - now deletes admin password globally."""
        self.delete_admin_password()