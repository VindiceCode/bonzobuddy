import customtkinter as ctk
import tkinter.messagebox as messagebox
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..state.app_state import AppStateManager


class AddOrganizationPopup(ctk.CTkToplevel):
    def __init__(self, parent, state_manager: 'AppStateManager'):
        super().__init__(parent)
        self.state_manager = state_manager
        
        self.title("Add Organization")
        self.geometry("400x300")
        self.resizable(False, False)
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(self, text="Add New Organization", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        
        # Organization Name
        ctk.CTkLabel(self, text="Name:").grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.name_entry = ctk.CTkEntry(self, placeholder_text="e.g., Starters Demo")
        self.name_entry.grid(row=1, column=1, padx=20, pady=10, sticky="ew")
        
        # Organization ID
        ctk.CTkLabel(self, text="Organization ID:").grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.id_entry = ctk.CTkEntry(self, placeholder_text="e.g., 12578")
        self.id_entry.grid(row=2, column=1, padx=20, pady=10, sticky="ew")
        
        # Owner ID
        ctk.CTkLabel(self, text="Owner ID:").grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.owner_id_entry = ctk.CTkEntry(self, placeholder_text="e.g., 17920")
        self.owner_id_entry.grid(row=3, column=1, padx=20, pady=10, sticky="ew")
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=4, column=0, columnspan=2, padx=20, pady=20, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=self.destroy, fg_color="#607D8B", hover_color="#546E7A")
        cancel_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        save_btn = ctk.CTkButton(button_frame, text="Save", command=self.save_organization, fg_color="#4CAF50", hover_color="#45a049")
        save_btn.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Focus on first field
        self.name_entry.focus()
    
    def save_organization(self):
        name = self.name_entry.get().strip()
        org_id = self.id_entry.get().strip()
        owner_id = self.owner_id_entry.get().strip()
        
        if not all([name, org_id, owner_id]):
            messagebox.showerror("Error", "All fields are required")
            return
        
        try:
            self.state_manager.add_organization(org_id, name, owner_id)
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e))


class EditOrganizationPopup(ctk.CTkToplevel):
    def __init__(self, parent, state_manager: 'AppStateManager'):
        super().__init__(parent)
        self.state_manager = state_manager
        
        if not state_manager.state.selected_organization:
            self.destroy()
            return
        
        self.title("Edit Organization")
        self.geometry("400x300")
        self.resizable(False, False)
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(self, text="Edit Organization", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        
        # Get current values
        org = state_manager.state.selected_organization
        
        # Organization Name
        ctk.CTkLabel(self, text="Name:").grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.name_entry = ctk.CTkEntry(self)
        self.name_entry.insert(0, org.name)
        self.name_entry.grid(row=1, column=1, padx=20, pady=10, sticky="ew")
        
        # Organization ID
        ctk.CTkLabel(self, text="Organization ID:").grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.id_entry = ctk.CTkEntry(self)
        self.id_entry.insert(0, org.id)
        self.id_entry.grid(row=2, column=1, padx=20, pady=10, sticky="ew")
        
        # Owner ID
        ctk.CTkLabel(self, text="Owner ID:").grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.owner_id_entry = ctk.CTkEntry(self)
        self.owner_id_entry.insert(0, org.owner_id)
        self.owner_id_entry.grid(row=3, column=1, padx=20, pady=10, sticky="ew")
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=4, column=0, columnspan=2, padx=20, pady=20, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=self.destroy, fg_color="#607D8B", hover_color="#546E7A")
        cancel_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        save_btn = ctk.CTkButton(button_frame, text="Save", command=self.save_organization, fg_color="#4CAF50", hover_color="#45a049")
        save_btn.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Focus on first field
        self.name_entry.focus()
    
    def save_organization(self):
        name = self.name_entry.get().strip()
        org_id = self.id_entry.get().strip()
        owner_id = self.owner_id_entry.get().strip()
        
        if not all([name, org_id, owner_id]):
            messagebox.showerror("Error", "All fields are required")
            return
        
        try:
            self.state_manager.update_organization(org_id, name, owner_id)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))


class AddWebhookPopup(ctk.CTkToplevel):
    def __init__(self, parent, state_manager: 'AppStateManager'):
        super().__init__(parent)
        self.state_manager = state_manager
        
        self.title("Add Webhook")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(self, text="Add New Webhook", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=20)
        
        # Integration selection frame
        self.integration_frame = ctk.CTkScrollableFrame(self)
        self.integration_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        self.selected_integration = None
        self.create_integration_tiles()
        
        # URL entry frame
        url_frame = ctk.CTkFrame(self)
        url_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        url_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(url_frame, text="Webhook URL:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.url_entry = ctk.CTkEntry(url_frame, placeholder_text="https://...")
        self.url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=self.destroy, fg_color="#607D8B", hover_color="#546E7A")
        cancel_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.save_btn = ctk.CTkButton(button_frame, text="Save", command=self.save_webhook, state="disabled", fg_color="#4CAF50", hover_color="#45a049")
        self.save_btn.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
    
    def create_integration_tiles(self):
        """Create integration selection tiles dynamically from filesystem."""
        # Get categories and integrations from PayloadService
        categories_and_integrations = self.state_manager.payload_service.get_categories_and_integrations()
        
        row = 0
        for category, integrations in categories_and_integrations.items():
            if not integrations:  # Skip empty categories
                continue
                
            # Convert category name for display
            category_display = category.replace('_', ' ').title()
            
            # Category header
            category_label = ctk.CTkLabel(
                self.integration_frame, 
                text=category_display, 
                font=ctk.CTkFont(size=16, weight="bold")
            )
            category_label.grid(row=row, column=0, columnspan=3, padx=10, pady=(10, 5), sticky="w")
            row += 1
            
            # Integration tiles
            col = 0
            for integration in sorted(integrations):
                btn = ctk.CTkButton(
                    self.integration_frame,
                    text=integration,
                    command=lambda integ=integration: self.select_integration(integ),
                    width=150,
                    height=40
                )
                btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
                
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
            
            if col > 0:  # If we didn't fill the last row
                row += 1
    
    def select_integration(self, integration: str):
        """Handle integration selection."""
        self.selected_integration = integration
        
        # Update button states - highlight selected
        for widget in self.integration_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton) and widget.cget("text") == integration:
                widget.configure(fg_color="#1565C0")
            elif isinstance(widget, ctk.CTkButton):
                widget.configure(fg_color=None)
        
        self.save_btn.configure(state="normal")
    
    def save_webhook(self):
        """Save the webhook."""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showerror("Error", "Webhook URL is required")
            return
        
        if not self.selected_integration:
            messagebox.showerror("Error", "Please select an integration")
            return
        
        # Use the new naming convention: "{Integration} for {Organization}"
        org_name = self.state_manager.state.selected_organization.name
        webhook_name = f"{self.selected_integration} for {org_name}"
        
        try:
            self.state_manager.add_webhook(webhook_name, url)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))


class SetAdminPasswordPopup(ctk.CTkToplevel):
    def __init__(self, parent, state_manager: 'AppStateManager'):
        super().__init__(parent)
        self.state_manager = state_manager
        
        self.title("Set Admin Password")
        self.geometry("450x300")
        self.resizable(False, False)
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        
        # Title and description
        title_label = ctk.CTkLabel(
            self, 
            text="Set Admin Password", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        
        description_label = ctk.CTkLabel(
            self,
            text="This password is used for impersonating users in the Bonzo platform.\nIt will be stored securely in your system keychain.",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        description_label.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20))
        
        # Check if password already exists
        existing_password = self.state_manager.keyring_service.get_admin_password()
        if existing_password:
            status_label = ctk.CTkLabel(
                self,
                text="✓ Admin password is currently set",
                font=ctk.CTkFont(size=12),
                text_color="green"
            )
            status_label.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 10))
        
        # Password entry
        ctk.CTkLabel(self, text="Password:").grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.password_entry = ctk.CTkEntry(self, show="*", placeholder_text="Enter admin password")
        self.password_entry.grid(row=3, column=1, padx=20, pady=10, sticky="ew")
        
        # Confirm password entry
        ctk.CTkLabel(self, text="Confirm:").grid(row=4, column=0, padx=20, pady=10, sticky="w")
        self.confirm_entry = ctk.CTkEntry(self, show="*", placeholder_text="Confirm password")
        self.confirm_entry.grid(row=4, column=1, padx=20, pady=10, sticky="ew")
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=5, column=0, columnspan=2, padx=20, pady=20, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=self.destroy, fg_color="#607D8B", hover_color="#546E7A")
        cancel_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        save_btn = ctk.CTkButton(button_frame, text="Save", command=self.save_admin_password, fg_color="#4CAF50", hover_color="#45a049")
        save_btn.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Focus on password field
        self.password_entry.focus()
    
    def save_admin_password(self):
        """Save the admin password."""
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        
        if not password:
            messagebox.showerror("Error", "Password cannot be empty")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        try:
            self.state_manager.keyring_service.set_admin_password(password)
            messagebox.showinfo("Success", "Admin password saved successfully")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save admin password: {e}")