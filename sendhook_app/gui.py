# gui.py
import customtkinter as ctk
import json
import requests
from data_manager import DataManager
from payload_generator import PayloadGenerator

# --- Appearance ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Bonzo Buddy")
        self.geometry("1400x800")

        self.data_manager = DataManager()
        self.selected_org_id = None
        self.current_payload = None
        self.pending_prospect = None # Holds newly generated prospect until successfully sent

        # --- Fonts ---
        self.title_font = ctk.CTkFont(size=20, weight="bold")
        self.label_font = ctk.CTkFont(size=16, weight="bold")
        self.button_font = ctk.CTkFont(size=15, weight="bold")
        self.list_font = ctk.CTkFont(size=16)
        self.mono_font = ctk.CTkFont(family="monospace", size=14)

        # --- Main Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # --- Column 1: Organizations ---
        self.org_frame = ctk.CTkFrame(self, border_width=2)
        self.org_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.org_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.org_frame, text="Step 1: Select Organization", font=self.title_font).grid(row=0, column=0, padx=15, pady=15, sticky="w")
        self.org_list = ctk.CTkScrollableFrame(self.org_frame)
        self.org_list.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")
        self.add_org_button = ctk.CTkButton(self.org_frame, text="Add Organization", command=self.add_org_window, font=self.button_font, height=40, corner_radius=8)
        self.add_org_button.grid(row=2, column=0, padx=15, pady=15, sticky="ew")

        # --- Column 2: Webhooks & Prospects ---
        self.webhook_frame = ctk.CTkFrame(self, border_width=2)
        self.webhook_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        self.webhook_frame.grid_columnconfigure((0, 1), weight=1)
        self.webhook_frame.grid_rowconfigure(1, weight=1)
        self.webhook_frame.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self.webhook_frame, text="Step 2: Select Webhook", font=self.title_font).grid(row=0, column=0, columnspan=2, padx=15, pady=15, sticky="w")
        self.webhook_list = ctk.CTkScrollableFrame(self.webhook_frame)
        self.webhook_list.grid(row=1, column=0, columnspan=2, padx=15, pady=15, sticky="nsew")
        
        self.add_webhook_button = ctk.CTkButton(self.webhook_frame, text="Add Webhook", command=self.add_webhook_window, font=self.button_font, height=40, corner_radius=8)
        self.add_webhook_button.grid(row=2, column=0, padx=(15, 5), pady=10, sticky="ew")
        self.delete_webhook_button = ctk.CTkButton(self.webhook_frame, text="Delete Webhook", command=self.delete_selected_webhook, fg_color="#D32F2F", hover_color="#B71C1C", font=self.button_font, height=40, corner_radius=8)
        self.delete_webhook_button.grid(row=2, column=1, padx=(5, 15), pady=10, sticky="ew")

        ctk.CTkLabel(self.webhook_frame, text="Existing Prospects", font=self.title_font).grid(row=3, column=0, columnspan=2, padx=15, pady=15, sticky="w")
        self.prospect_list = ctk.CTkScrollableFrame(self.webhook_frame)
        self.prospect_list.grid(row=4, column=0, columnspan=2, padx=15, pady=15, sticky="nsew")

        # --- Column 3: Action & Payload Viewer ---
        self.action_frame = ctk.CTkFrame(self, border_width=2)
        self.action_frame.grid(row=0, column=2, padx=(0, 20), pady=20, sticky="nsew")
        self.action_frame.grid_columnconfigure((0, 1), weight=1)
        self.action_frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self.action_frame, text="Step 3: Generate & Send", font=self.title_font).grid(row=0, column=0, columnspan=2, padx=15, pady=15, sticky="w")
        self.generate_new_button = ctk.CTkButton(self.action_frame, text="Generate New Prospect", command=self.generate_new_payload, font=self.button_font, height=40, corner_radius=8)
        self.generate_new_button.grid(row=1, column=0, padx=(15, 5), pady=15, sticky="ew")
        self.send_existing_button = ctk.CTkButton(self.action_frame, text="Use Selected Prospect", command=self.generate_existing_payload, font=self.button_font, height=40, corner_radius=8)
        self.send_existing_button.grid(row=1, column=1, padx=(5, 15), pady=15, sticky="ew")

        self.payload_viewer = ctk.CTkTextbox(self.action_frame, wrap="word", font=self.mono_font)
        self.payload_viewer.grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="nsew")

        self.send_button = ctk.CTkButton(self.action_frame, text="Send Payload", command=self.send_payload, font=self.button_font, height=50, corner_radius=8)
        self.send_button.grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")

        self.populate_org_list()
        self.set_initial_state()

    def set_initial_state(self):
        self.set_frame_state(self.webhook_frame, "disabled")
        self.set_frame_state(self.action_frame, "disabled")

    def set_frame_state(self, frame, state):
        for child in frame.winfo_children():
            if isinstance(child, (ctk.CTkButton, ctk.CTkScrollableFrame, ctk.CTkTextbox, ctk.CTkOptionMenu)):
                child.configure(state=state)

    def populate_org_list(self):
        for widget in self.org_list.winfo_children():
            widget.destroy()
        self.orgs = self.data_manager.get_organizations()
        self.selected_org_radio_var = ctk.StringVar()
        for org in self.orgs:
            ctk.CTkRadioButton(self.org_list, text=org["name"], variable=self.selected_org_radio_var, value=org["id"], command=self.org_selected, font=self.list_font).pack(anchor="w", padx=10, pady=10)

    def org_selected(self):
        self.selected_org_id = self.selected_org_radio_var.get()
        self.set_frame_state(self.webhook_frame, "normal")
        self.set_frame_state(self.action_frame, "disabled")
        self.populate_webhook_list()
        self.populate_prospect_list()
        self.payload_viewer.delete("1.0", "end")
        self.pending_prospect = None

    def webhook_selected(self):
        self.set_frame_state(self.action_frame, "normal")
        self.payload_viewer.delete("1.0", "end")
        self.pending_prospect = None

    def populate_webhook_list(self):
        for widget in self.webhook_list.winfo_children():
            widget.destroy()
        if not self.selected_org_id: return
        self.webhooks = self.data_manager.get_webhooks_for_org(self.selected_org_id)
        self.selected_webhook_radio_var = ctk.StringVar()
        for webhook in self.webhooks:
            ctk.CTkRadioButton(self.webhook_list, text=webhook["name"], variable=self.selected_webhook_radio_var, value=webhook["name"], command=self.webhook_selected, font=self.list_font).pack(anchor="w", padx=10, pady=10)

    def populate_prospect_list(self):
        for widget in self.prospect_list.winfo_children():
            widget.destroy()
        if not self.selected_org_id: return
        self.prospects = self.data_manager.get_prospects_for_org(self.selected_org_id)
        self.selected_prospect_radio_var = ctk.StringVar()
        for prospect in self.prospects:
            ctk.CTkRadioButton(self.prospect_list, text=f"{prospect['firstName']} {prospect['lastName']}", variable=self.selected_prospect_radio_var, value=prospect['email'], font=self.list_font).pack(anchor="w", padx=10, pady=10)

    def add_org_window(self):
        if hasattr(self, 'org_window') and self.org_window.winfo_exists():
            self.org_window.focus()
            return

        self.org_window = ctk.CTkToplevel(self)
        self.org_window.title("Add New Organization")
        self.org_window.geometry("400x200")

        ctk.CTkLabel(self.org_window, text="Organization Name:", font=self.label_font).pack(pady=(10,0))
        org_name_entry = ctk.CTkEntry(self.org_window, width=250)
        org_name_entry.pack(pady=(0,10))

        ctk.CTkLabel(self.org_window, text="Organization ID:", font=self.label_font).pack()
        org_id_entry = ctk.CTkEntry(self.org_window, width=250)
        org_id_entry.pack(pady=(0,10))

        def save():
            name = org_name_entry.get()
            org_id = org_id_entry.get()
            if name and org_id:
                self.data_manager.add_organization(name, org_id)
                self.populate_org_list()
                self.org_window.destroy()

        save_button = ctk.CTkButton(self.org_window, text="Save", command=save, font=self.button_font, height=35, corner_radius=8)
        save_button.pack(side="left", padx=20, pady=10, expand=True)
        
        cancel_button = ctk.CTkButton(self.org_window, text="Cancel", command=self.org_window.destroy, font=self.button_font, height=35, corner_radius=8)
        cancel_button.pack(side="right", padx=20, pady=10, expand=True)

    def add_webhook_window(self):
        if not self.selected_org_id: return
        if hasattr(self, 'webhook_window') and self.webhook_window.winfo_exists():
            self.webhook_window.focus()
            return

        self.webhook_window = ctk.CTkToplevel(self)
        self.webhook_window.title("Add New Webhook")
        self.webhook_window.geometry("400x300")

        ctk.CTkLabel(self.webhook_window, text="Integration Category:", font=self.label_font).pack(pady=(10,0))
        categories = self.data_manager.get_integration_categories()
        category_var = ctk.StringVar(value=categories[0])
        category_dropdown = ctk.CTkOptionMenu(self.webhook_window, values=categories, variable=category_var, command=self.update_integration_dropdown, font=self.button_font)
        category_dropdown.pack(pady=(0,10))

        ctk.CTkLabel(self.webhook_window, text="Integration:", font=self.label_font).pack()
        self.integration_var = ctk.StringVar()
        self.integration_dropdown = ctk.CTkOptionMenu(self.webhook_window, variable=self.integration_var, font=self.button_font)
        self.integration_dropdown.pack(pady=(0,10))
        self.update_integration_dropdown(categories[0])

        ctk.CTkLabel(self.webhook_window, text="Webhook URL:", font=self.label_font).pack()
        webhook_url_entry = ctk.CTkEntry(self.webhook_window, width=350)
        webhook_url_entry.pack(pady=(0,10))

        def save():
            integration = self.integration_var.get()
            url = webhook_url_entry.get()
            if integration and url:
                org_name = [org['name'] for org in self.orgs if org['id'] == self.selected_org_id][0]
                webhook_name = f"{integration} for {org_name}"
                self.data_manager.add_webhook(self.selected_org_id, webhook_name, url)
                self.populate_webhook_list()
                self.webhook_window.destroy()

        save_button = ctk.CTkButton(self.webhook_window, text="Save", command=save, font=self.button_font, height=35, corner_radius=8)
        save_button.pack(side="left", padx=20, pady=10, expand=True)
        
        cancel_button = ctk.CTkButton(self.webhook_window, text="Cancel", command=self.webhook_window.destroy, font=self.button_font, height=35, corner_radius=8)
        cancel_button.pack(side="right", padx=20, pady=10, expand=True)

    def update_integration_dropdown(self, selected_category):
        integrations = self.data_manager.get_integrations_for_category(selected_category)
        self.integration_dropdown.configure(values=integrations)
        if integrations:
            self.integration_var.set(integrations[0])

    def delete_selected_webhook(self):
        if not self.selected_org_id: return
        selected_webhook = self.selected_webhook_radio_var.get()
        if not selected_webhook: return
        
        self.data_manager.delete_webhook(self.selected_org_id, selected_webhook)
        self.populate_webhook_list()
        print(f"Webhook '{selected_webhook}' deleted.")

    def generate_new_payload(self):
        if not self.selected_org_id: return
        selected_webhook_name = self.selected_webhook_radio_var.get()
        if not selected_webhook_name: return

        org_id = self.selected_org_id
        prospect_index = self.data_manager.get_next_prospect_index(org_id)
        
        first_name = "Test"
        last_name = f"Prospect{prospect_index}"
        email = f"{first_name.lower()}.{last_name.lower()}@test.com"
        phone = f"555-555-{prospect_index:04d}"

        self.pending_prospect = {"firstName": first_name, "lastName": last_name, "email": email, "phone": phone}
        self._generate_and_display_payload(selected_webhook_name, first_name, last_name, email, phone)

    def generate_existing_payload(self):
        if not self.selected_org_id: return
        selected_prospect_email = self.selected_prospect_radio_var.get()
        if not selected_prospect_email: return
        selected_webhook_name = self.selected_webhook_radio_var.get()
        if not selected_webhook_name: return

        self.pending_prospect = None # Clear any pending prospect
        prospect_data = [p for p in self.prospects if p['email'] == selected_prospect_email][0]
        self._generate_and_display_payload(selected_webhook_name, prospect_data['firstName'], prospect_data['lastName'], prospect_data['email'], prospect_data['phone'])

    def _generate_and_display_payload(self, webhook_name, first_name, last_name, email, phone):
        integration = webhook_name.split(" for ")[0]
        category = self.find_category_for_integration(integration)
        if not category: return

        generator = PayloadGenerator(self.selected_org_id, 0)
        self.current_payload = generator.generate_payload(integration, category, first_name, last_name, email, phone)
        
        self.payload_viewer.delete("1.0", "end")
        self.payload_viewer.insert("1.0", json.dumps(self.current_payload, indent=4))

    def find_category_for_integration(self, integration_name):
        for category in self.data_manager.get_integration_categories():
            if integration_name in self.data_manager.get_integrations_for_category(category):
                return category
        return None

    def send_payload(self):
        if not self.current_payload:
            print("Error: No payload generated.")
            return
        selected_webhook_name = self.selected_webhook_radio_var.get()
        if not selected_webhook_name:
            print("Error: No webhook selected.")
            return
            
        webhook_url = [wh['url'] for wh in self.webhooks if wh['name'] == selected_webhook_name][0]

        try:
            response = requests.post(webhook_url, json=self.current_payload, timeout=10)
            print(f"Payload sent to {webhook_url}")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")

            if response.status_code == 200 and self.pending_prospect:
                self.data_manager.store_prospect(self.selected_org_id, self.pending_prospect)
                print(f"Success! Prospect '{self.pending_prospect['firstName']} {self.pending_prospect['lastName']}' saved.")
                self.populate_prospect_list()
            elif response.status_code != 200:
                print(f"Error: Received status {response.status_code}. Prospect not saved.")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
        finally:
            # Clear the pending prospect regardless of outcome
            self.pending_prospect = None

if __name__ == "__main__":
    app = App()
    app.mainloop()