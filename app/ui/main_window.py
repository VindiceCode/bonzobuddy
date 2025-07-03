import customtkinter as ctk
import webbrowser
import json
import requests
import tkinter.messagebox as messagebox
from typing import List, Optional

from ..state.app_state import AppStateManager
from ..models.core import Organization, Prospect
from .popups import AddOrganizationPopup, EditOrganizationPopup, AddWebhookPopup, SetAdminPasswordPopup


# Set appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class BonzoBuddyApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize app state manager
        self.state_manager = AppStateManager()
        self.state_manager.add_update_callback(self.update_ui)
        
        # Window setup
        self.title("Bonzo Buddy v2")
        self.geometry("1400x800")
        
        # Fonts
        self.title_font = ctk.CTkFont(size=20, weight="bold")
        self.label_font = ctk.CTkFont(size=16, weight="bold")
        self.button_font = ctk.CTkFont(size=15, weight="bold")
        self.list_font = ctk.CTkFont(size=16)
        self.mono_font = ctk.CTkFont(family="monospace", size=14)
        
        # Modern Color Scheme
        self.colors = {
            # Primary actions
            "primary": "#4CAF50",      # Green for main actions
            "primary_hover": "#45a049",
            
            # Secondary actions  
            "secondary": "#2196F3",    # Blue for secondary actions
            "secondary_hover": "#1976D2",
            
            # Warning/Delete actions
            "warning": "#FF5722",      # Red-orange for delete/warning
            "warning_hover": "#E64A19",
            
            # Bonzo brand colors
            "bonzo": "#FF6B35",        # Bonzo orange
            "bonzo_hover": "#E55A2B",
            
            # Special actions
            "accent": "#9C27B0",       # Purple for special features
            "accent_hover": "#7B1FA2",
            
            # Neutral actions
            "neutral": "#607D8B",      # Blue-grey for neutral actions
            "neutral_hover": "#546E7A",
            
            # Success
            "success": "#4CAF50",
            "success_hover": "#388E3C",
            
            # Selected state
            "selected": "#1565C0",     # Darker blue for selected items
            
            # Frames
            "frame_border": "#37474F"  # Dark grey for frame borders
        }
        
        # Create UI
        self.create_ui()
        self.update_ui()
    
    def create_ui(self) -> None:
        """Create the three-column UI layout."""
        # Main grid configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=2)
        self.grid_rowconfigure(0, weight=1)
        
        # Create columns
        self.create_organization_column()
        self.create_webhook_column()
        self.create_action_column()
    
    def create_organization_column(self) -> None:
        """Create the first column for organization management."""
        self.org_frame = ctk.CTkFrame(self, border_width=2, border_color=self.colors["frame_border"])
        self.org_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Configure grid
        self.org_frame.grid_columnconfigure(0, weight=1)
        self.org_frame.grid_rowconfigure(1, weight=1)
        
        # Title
        ctk.CTkLabel(
            self.org_frame, 
            text="Step 1: Select Organization", 
            font=self.title_font
        ).grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        # Organization list
        self.org_list_frame = ctk.CTkScrollableFrame(self.org_frame)
        self.org_list_frame.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(self.org_frame)
        buttons_frame.grid(row=2, column=0, padx=15, pady=15, sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        # Organization management buttons
        self.add_org_btn = ctk.CTkButton(
            buttons_frame,
            text="Add Organization",
            command=self.add_organization,
            font=self.button_font,
            height=40,
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"]
        )
        self.add_org_btn.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        self.edit_org_btn = ctk.CTkButton(
            buttons_frame,
            text="Edit Organization",
            command=self.edit_organization,
            font=self.button_font,
            height=40,
            state="disabled",
            fg_color=self.colors["secondary"],
            hover_color=self.colors["secondary_hover"]
        )
        self.edit_org_btn.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        self.delete_org_btn = ctk.CTkButton(
            buttons_frame,
            text="Delete Organization",
            command=self.delete_organization,
            font=self.button_font,
            height=40,
            state="disabled",
            fg_color=self.colors["warning"],
            hover_color=self.colors["warning_hover"]
        )
        self.delete_org_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Bonzo integration buttons
        self.open_team_btn = ctk.CTkButton(
            buttons_frame,
            text="Open Team in Bonzo",
            command=self.open_team_in_bonzo,
            font=self.button_font,
            height=40,
            state="disabled",
            fg_color=self.colors["bonzo"],
            hover_color=self.colors["bonzo_hover"]
        )
        self.open_team_btn.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        
        self.open_owner_btn = ctk.CTkButton(
            buttons_frame,
            text="Open Owner in Bonzo",
            command=self.open_owner_in_bonzo,
            font=self.button_font,
            height=40,
            state="disabled",
            fg_color=self.colors["bonzo"],
            hover_color=self.colors["bonzo_hover"]
        )
        self.open_owner_btn.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        # Admin password management buttons (always available)
        self.set_password_btn = ctk.CTkButton(
            buttons_frame,
            text="Set Admin Password",
            command=self.set_admin_password,
            font=self.button_font,
            height=40,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"]
        )
        self.set_password_btn.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        
        self.copy_password_btn = ctk.CTkButton(
            buttons_frame,
            text="Copy Admin Password",
            command=self.copy_admin_password,
            font=self.button_font,
            height=40,
            fg_color=self.colors["neutral"],
            hover_color=self.colors["neutral_hover"]
        )
        self.copy_password_btn.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
    
    def create_webhook_column(self) -> None:
        """Create the second column for webhook and prospect management."""
        self.webhook_frame = ctk.CTkFrame(self, border_width=2, border_color=self.colors["frame_border"])
        self.webhook_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        
        # Configure grid
        self.webhook_frame.grid_columnconfigure(0, weight=1)
        self.webhook_frame.grid_rowconfigure(1, weight=1)
        self.webhook_frame.grid_rowconfigure(3, weight=1)
        
        # Title
        ctk.CTkLabel(
            self.webhook_frame,
            text="Step 2: Select Webhook & Prospect",
            font=self.title_font
        ).grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        # Webhooks section
        self.webhook_list_frame = ctk.CTkScrollableFrame(self.webhook_frame)
        self.webhook_list_frame.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")
        
        # Webhook buttons
        webhook_buttons_frame = ctk.CTkFrame(self.webhook_frame)
        webhook_buttons_frame.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        webhook_buttons_frame.grid_columnconfigure(0, weight=1)
        webhook_buttons_frame.grid_columnconfigure(1, weight=1)
        
        self.add_webhook_btn = ctk.CTkButton(
            webhook_buttons_frame,
            text="Add Webhook",
            command=self.add_webhook,
            font=self.button_font,
            height=40,
            state="disabled",
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"]
        )
        self.add_webhook_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.delete_webhook_btn = ctk.CTkButton(
            webhook_buttons_frame,
            text="Delete Webhook",
            command=self.delete_webhook,
            font=self.button_font,
            height=40,
            state="disabled",
            fg_color=self.colors["warning"],
            hover_color=self.colors["warning_hover"]
        )
        self.delete_webhook_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Existing prospects section
        self.prospects_list_frame = ctk.CTkScrollableFrame(self.webhook_frame)
        self.prospects_list_frame.grid(row=3, column=0, padx=15, pady=15, sticky="nsew")
    
    def create_action_column(self) -> None:
        """Create the third column for payload generation and actions."""
        self.action_frame = ctk.CTkFrame(self, border_width=2, border_color=self.colors["frame_border"])
        self.action_frame.grid(row=0, column=2, padx=(0, 20), pady=20, sticky="nsew")
        
        # Configure grid
        self.action_frame.grid_columnconfigure(0, weight=1)
        self.action_frame.grid_rowconfigure(2, weight=1)
        
        # Title
        ctk.CTkLabel(
            self.action_frame,
            text="Step 3: Generate & Send Payload",
            font=self.title_font
        ).grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        # Profile selection (appears when multiple profiles available)
        self.profile_frame = ctk.CTkFrame(self.action_frame)
        self.profile_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        self.profile_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            self.profile_frame,
            text="Payload Profile:",
            font=self.label_font
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.profile_dropdown = ctk.CTkComboBox(
            self.profile_frame,
            values=[],
            state="disabled",
            command=self.on_profile_selected
        )
        self.profile_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Initially hide profile frame
        self.profile_frame.grid_remove()
        
        # Payload viewer
        self.payload_viewer = ctk.CTkTextbox(
            self.action_frame,
            font=self.mono_font,
            state="disabled"
        )
        self.payload_viewer.grid(row=2, column=0, padx=15, pady=15, sticky="nsew")
        
        # Action buttons
        actions_frame = ctk.CTkFrame(self.action_frame)
        actions_frame.grid(row=3, column=0, padx=15, pady=15, sticky="ew")
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)
        
        self.generate_new_btn = ctk.CTkButton(
            actions_frame,
            text="Generate New Prospect",
            command=self.generate_new_prospect,
            font=self.button_font,
            height=40,
            state="disabled",
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"]
        )
        self.generate_new_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.use_selected_btn = ctk.CTkButton(
            actions_frame,
            text="Use Selected Prospect",
            command=self.use_selected_prospect,
            font=self.button_font,
            height=40,
            state="disabled",
            fg_color=self.colors["secondary"],
            hover_color=self.colors["secondary_hover"]
        )
        self.use_selected_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.edit_payload_btn = ctk.CTkButton(
            actions_frame,
            text="Edit",
            command=self.toggle_payload_edit,
            font=self.button_font,
            height=40,
            state="disabled",
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"]
        )
        self.edit_payload_btn.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.send_payload_btn = ctk.CTkButton(
            actions_frame,
            text="Send Payload",
            command=self.send_payload,
            font=self.button_font,
            height=40,
            state="disabled",
            fg_color=self.colors["success"],
            hover_color=self.colors["success_hover"]
        )
        self.send_payload_btn.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.save_custom_btn = ctk.CTkButton(
            actions_frame,
            text="Save as Custom Schema",
            command=self.save_custom_schema,
            font=self.button_font,
            height=40,
            state="disabled",
            fg_color=self.colors["neutral"],
            hover_color=self.colors["neutral_hover"]
        )
        self.save_custom_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        # Initially hide custom save button
        self.save_custom_btn.grid_remove()
    
    def update_ui(self) -> None:
        """Update UI based on current state."""
        self.populate_organization_list()
        self.populate_webhook_list()
        self.populate_prospects_list()
        self.update_action_column()
        self.update_button_states()
    
    def populate_organization_list(self) -> None:
        """Populate the organization list."""
        # Clear existing widgets
        for widget in self.org_list_frame.winfo_children():
            widget.destroy()
        
        organizations = self.state_manager.get_organizations()
        
        for i, org in enumerate(organizations):
            is_selected = (self.state_manager.state.selected_organization and 
                         org.id == self.state_manager.state.selected_organization.id)
            
            btn = ctk.CTkButton(
                self.org_list_frame,
                text=f"{org.name} ({org.id})",
                command=lambda o=org: self.on_organization_selected(o),
                font=self.list_font,
                height=40,
                fg_color=self.colors["selected"] if is_selected else None
            )
            btn.grid(row=i, column=0, padx=5, pady=5, sticky="ew")
            self.org_list_frame.grid_columnconfigure(0, weight=1)
    
    def populate_webhook_list(self) -> None:
        """Populate the webhook list."""
        # Clear existing widgets
        for widget in self.webhook_list_frame.winfo_children():
            widget.destroy()
        
        if not self.state_manager.state.selected_organization:
            return
        
        webhooks = self.state_manager.state.selected_organization.webhooks
        
        for i, webhook in enumerate(webhooks):
            is_selected = self.state_manager.state.selected_webhook_index == i
            
            btn = ctk.CTkButton(
                self.webhook_list_frame,
                text=webhook.name,
                command=lambda idx=i: self.on_webhook_selected(idx),
                font=self.list_font,
                height=40,
                fg_color=self.colors["selected"] if is_selected else None
            )
            btn.grid(row=i, column=0, padx=5, pady=5, sticky="ew")
            self.webhook_list_frame.grid_columnconfigure(0, weight=1)
    
    def populate_prospects_list(self) -> None:
        """Populate the existing prospects list."""
        # Clear existing widgets
        for widget in self.prospects_list_frame.winfo_children():
            widget.destroy()
        
        if not self.state_manager.state.selected_organization:
            return
        
        # Add label
        ctk.CTkLabel(
            self.prospects_list_frame,
            text="Existing Prospects:",
            font=self.label_font
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        prospects = self.state_manager.get_existing_prospects()
        
        for i, prospect in enumerate(prospects):
            is_selected = (self.state_manager.state.selected_prospect and 
                         prospect.email == self.state_manager.state.selected_prospect.email)
            
            btn = ctk.CTkButton(
                self.prospects_list_frame,
                text=f"{prospect.firstName} {prospect.lastName} ({prospect.email})",
                command=lambda p=prospect: self.on_prospect_selected(p),
                font=self.list_font,
                height=40,
                fg_color=self.colors["selected"] if is_selected else None
            )
            btn.grid(row=i+1, column=0, padx=5, pady=5, sticky="ew")
            self.prospects_list_frame.grid_columnconfigure(0, weight=1)
    
    def update_action_column(self) -> None:
        """Update the action column based on state."""
        # Update profile dropdown
        profiles = self.state_manager.state.available_profiles
        if len(profiles) > 1:
            self.profile_dropdown.configure(values=profiles)
            self.profile_dropdown.configure(state="normal")
            self.profile_frame.grid()
        else:
            self.profile_frame.grid_remove()
        
        # Update payload viewer
        if self.state_manager.state.generated_payload:
            self.payload_viewer.configure(state="normal")
            self.payload_viewer.delete("1.0", "end")
            self.payload_viewer.insert("1.0", self.state_manager.state.generated_payload)
            
            if self.state_manager.state.payload_editable:
                self.payload_viewer.configure(state="normal")
                self.save_custom_btn.grid()
            else:
                self.payload_viewer.configure(state="disabled")
                self.save_custom_btn.grid_remove()
        else:
            self.payload_viewer.configure(state="normal")
            self.payload_viewer.delete("1.0", "end")
            self.payload_viewer.configure(state="disabled")
            self.save_custom_btn.grid_remove()
    
    def update_button_states(self) -> None:
        """Update button states based on current selections."""
        has_org = self.state_manager.state.selected_organization is not None
        has_webhook = self.state_manager.state.selected_webhook_index is not None
        has_payload = self.state_manager.state.generated_payload is not None
        has_prospect = (self.state_manager.state.selected_prospect is not None or 
                       self.state_manager.state.pending_prospect is not None)
        
        # Organization column buttons
        self.edit_org_btn.configure(state="normal" if has_org else "disabled")
        self.delete_org_btn.configure(state="normal" if has_org else "disabled")
        self.open_team_btn.configure(state="normal" if has_org else "disabled")
        self.open_owner_btn.configure(state="normal" if has_org else "disabled")
        
        # Admin password buttons are always enabled (global scope)
        self.set_password_btn.configure(state="normal")
        self.copy_password_btn.configure(state="normal")
        
        # Webhook column buttons
        self.add_webhook_btn.configure(state="normal" if has_org else "disabled")
        self.delete_webhook_btn.configure(state="normal" if has_webhook else "disabled")
        
        # Action column buttons
        self.generate_new_btn.configure(state="normal" if has_webhook else "disabled")
        self.use_selected_btn.configure(state="normal" if (has_webhook and self.state_manager.state.selected_prospect) else "disabled")
        self.edit_payload_btn.configure(state="normal" if has_payload else "disabled")
        self.send_payload_btn.configure(state="normal" if has_payload else "disabled")
        
        # Update edit button text
        if self.state_manager.state.payload_editable:
            self.edit_payload_btn.configure(text="Save")
        else:
            self.edit_payload_btn.configure(text="Edit")
    
    # Event handlers
    def on_organization_selected(self, organization: Organization) -> None:
        """Handle organization selection."""
        self.state_manager.select_organization(organization)
    
    def on_webhook_selected(self, webhook_index: int) -> None:
        """Handle webhook selection."""
        self.state_manager.select_webhook(webhook_index)
    
    def on_prospect_selected(self, prospect: Prospect) -> None:
        """Handle prospect selection."""
        self.state_manager.select_prospect(prospect)
    
    def on_profile_selected(self, profile: str) -> None:
        """Handle profile selection."""
        # Regenerate payload with new profile if we have a prospect
        if (self.state_manager.state.selected_prospect or 
            self.state_manager.state.pending_prospect):
            prospect = (self.state_manager.state.selected_prospect or 
                       self.state_manager.state.pending_prospect)
            try:
                self.state_manager.generate_payload(prospect, profile)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate payload: {e}")
    
    # Action methods
    def add_organization(self) -> None:
        """Open add organization dialog."""
        popup = AddOrganizationPopup(self, self.state_manager)
        popup.transient(self)
        popup.focus_set()
        self.after(100, popup.grab_set)  # Delayed grab_set to ensure window is visible
    
    def edit_organization(self) -> None:
        """Open edit organization dialog."""
        if not self.state_manager.state.selected_organization:
            return
        
        popup = EditOrganizationPopup(self, self.state_manager)
        popup.transient(self)
        popup.focus_set()
        self.after(100, popup.grab_set)  # Delayed grab_set to ensure window is visible
    
    def delete_organization(self) -> None:
        """Delete selected organization with confirmation."""
        if not self.state_manager.state.selected_organization:
            return
        
        org_name = self.state_manager.state.selected_organization.name
        webhook_count = len(self.state_manager.state.selected_organization.webhooks)
        
        # Show confirmation dialog
        confirm_msg = f"Are you sure you want to delete the organization '{org_name}'?"
        if webhook_count > 0:
            confirm_msg += f"\n\nThis will also delete {webhook_count} webhook(s) and all associated data."
        confirm_msg += "\n\nThis action cannot be undone."
        
        result = messagebox.askyesno("Confirm Delete", confirm_msg, icon="warning")
        if result:
            org_id = self.state_manager.state.selected_organization.id
            self.state_manager.delete_organization(org_id)
            messagebox.showinfo("Success", f"Organization '{org_name}' has been deleted.")
    
    def open_team_in_bonzo(self) -> None:
        """Open team page in Bonzo platform."""
        if not self.state_manager.state.selected_organization:
            return
        
        org_id = self.state_manager.state.selected_organization.id
        url = f"https://platform.getbonzo.com/admin/teams/{org_id}/details"
        webbrowser.open_new_tab(url)
    
    def open_owner_in_bonzo(self) -> None:
        """Open owner page in Bonzo platform."""
        if not self.state_manager.state.selected_organization:
            return
        
        owner_id = self.state_manager.state.selected_organization.owner_id
        if not owner_id:
            print("Error: No owner_id set for this organization")
            return
        
        url = f"https://platform.getbonzo.com/admin/users/{owner_id}?search=&role=&permission=&status=&tag=&active=&page=1&team_permission=&business_ids=&enterprise_id=&list_id=&per_page=50"
        webbrowser.open_new_tab(url)
    
    def set_admin_password(self) -> None:
        """Open admin password dialog."""
        popup = SetAdminPasswordPopup(self, self.state_manager)
        popup.transient(self)
        popup.focus_set()
        self.after(100, popup.grab_set)  # Delayed grab_set to ensure window is visible
    
    def copy_admin_password(self) -> None:
        """Copy admin password to clipboard."""
        password = self.state_manager.keyring_service.get_admin_password()
        
        if password:
            self.clipboard_clear()
            self.clipboard_append(password)
            messagebox.showinfo("Success", "Admin password copied to clipboard")
        else:
            messagebox.showwarning("Warning", "No admin password set. Please set an admin password first.")
    
    def add_webhook(self) -> None:
        """Open add webhook dialog."""
        if not self.state_manager.state.selected_organization:
            return
        
        popup = AddWebhookPopup(self, self.state_manager)
        popup.transient(self)
        popup.focus_set()
        self.after(100, popup.grab_set)  # Delayed grab_set to ensure window is visible
    
    def delete_webhook(self) -> None:
        """Delete selected webhook."""
        if self.state_manager.state.selected_webhook_index is None:
            return
        
        # Confirm deletion
        webhook = self.state_manager.state.selected_organization.webhooks[self.state_manager.state.selected_webhook_index]
        if messagebox.askyesno("Confirm Delete", f"Delete webhook '{webhook.name}'?"):
            self.state_manager.delete_webhook(self.state_manager.state.selected_webhook_index)
    
    def generate_new_prospect(self) -> None:
        """Generate a new prospect and payload."""
        try:
            prospect = self.state_manager.generate_new_prospect()
            profile = self.state_manager.state.selected_profile
            self.state_manager.generate_payload(prospect, profile)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate prospect: {e}")
    
    def use_selected_prospect(self) -> None:
        """Use selected existing prospect to generate payload."""
        if not self.state_manager.state.selected_prospect:
            return
        
        try:
            profile = self.state_manager.state.selected_profile
            self.state_manager.generate_payload(self.state_manager.state.selected_prospect, profile)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate payload: {e}")
    
    def toggle_payload_edit(self) -> None:
        """Toggle payload edit mode."""
        if self.state_manager.state.payload_editable:
            # Save changes
            current_text = self.payload_viewer.get("1.0", "end-1c")
            self.state_manager.update_payload(current_text)
            self.state_manager.set_payload_editable(False)
        else:
            # Enable editing
            self.state_manager.set_payload_editable(True)
    
    def send_payload(self) -> None:
        """Send payload to webhook."""
        if (not self.state_manager.state.generated_payload or 
            self.state_manager.state.selected_webhook_index is None):
            return
        
        webhook = self.state_manager.state.selected_organization.webhooks[self.state_manager.state.selected_webhook_index]
        payload_text = self.payload_viewer.get("1.0", "end-1c")
        
        try:
            # Send raw text as JSON body (no validation)
            response = requests.post(
                webhook.url, 
                data=payload_text,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            # Show response (all status codes)
            status_color = "green" if response.status_code == 200 else "red"
            result_text = f"Status: {response.status_code}\nURL: {webhook.url}\nResponse: {response.text[:1000]}"
            
            # Show response in appropriate dialog based on status
            if response.status_code == 200:
                messagebox.showinfo("Send Result", result_text)
                # If successful and we have a pending prospect, save it
                if self.state_manager.state.pending_prospect:
                    self.state_manager.save_prospect_after_successful_send()
                    messagebox.showinfo("Success", "Prospect saved successfully!")
            else:
                messagebox.showwarning("Webhook Response", result_text)
            
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")
    
    def save_custom_schema(self) -> None:
        """Save current payload as custom schema."""
        if not self.state_manager.state.generated_payload:
            return
        
        # Simple input dialog for schema name
        import tkinter.simpledialog as simpledialog
        schema_name = simpledialog.askstring("Save Custom Schema", "Enter schema name:")
        
        if schema_name:
            try:
                webhook = self.state_manager.state.selected_organization.webhooks[self.state_manager.state.selected_webhook_index]
                payload_text = self.payload_viewer.get("1.0", "end-1c")
                payload_dict = json.loads(payload_text)
                
                self.state_manager.payload_service.save_custom_schema(webhook.name, schema_name, payload_dict)
                messagebox.showinfo("Success", f"Custom schema '{schema_name}' saved!")
                
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Invalid JSON in payload")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save schema: {e}")
    
    def run(self) -> None:
        """Start the application."""
        self.mainloop()