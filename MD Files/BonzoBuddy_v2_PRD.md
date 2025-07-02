# Bonzo Buddy v2: Project Requirements Document (PRD)

## 1. Vision & Core Purpose

Bonzo Buddy v2 will be a professional-grade, local desktop application for testing webhook integrations. It will be rebuilt from the ground up using modern Python best practices to be more robust, maintainable, and developer-friendly. The core functionality will remain the same as v1, but the underlying architecture will be significantly improved to be more scalable and reliable.

## 2. Core Principles & Technology

*   **Technology Stack:**
    *   **Language:** Python (>=3.10)
    *   **Package Management:** `uv` with a `pyproject.toml` file.
    *   **Data Modeling:** `Pydantic` for all data structures. This is non-negotiable and will be the foundation of the application's data layer.
    *   **GUI Library:** `customtkinter` for a modern, dark-mode UI.
    *   **Credential Management:** `keyring` for secure password storage.

*   **Architectural Principles:**
    *   **Pydantic-First:** All data (organizations, webhooks, prospects) will be loaded into and passed around as Pydantic models, not raw dictionaries. This ensures type safety and data validation throughout the app.
    *   **Clear Separation of Concerns:** The application logic will be strictly separated into distinct layers: UI, State Management, and Services (Data, Payload Generation).
    *   **Single Source of Truth:** The UI will be a direct reflection of a centralized `AppState`. All user actions will modify the state, and the UI will react to those changes.

## 3. Proposed Project Structure

The project will be organized into a clean, modular structure within the `bonzobuddy` directory.

```
bonzobuddy/
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   └── core.py         # Pydantic models for Org, Webhook, Prospect, etc.
│   ├── services/
│   │   ├── __init__.py
│   │   ├── data_service.py   # Handles loading/saving JSON files.
│   │   ├── keyring_service.py# Handles secure password storage.
│   │   └── payload_service.py# Handles schema loading and payload generation.
│   ├── state/
│   │   └── app_state.py      # Manages the application's current state.
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py    # The main App class and its layout.
│   │   └── popups.py         # Classes for all Toplevel popup windows.
│   └── main.py             # The application entry point.
├── schemas/                  # NEW top-level dir for all integration schemas.
│   ├── crm/
│   ├── internal_integrations/
│   └── lead_sources/
├── .gitignore
├── BonzoBuddyNewReadme.md
├── org_webhooks.json         # User-specific data
├── generated_prospects.json  # User-specific data
├── pyproject.toml
└── README.md
```

## 4. Pydantic Data Models (`app/models/core.py`)

This is the new foundation. The following Pydantic models must be created:

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Webhook(BaseModel):
    name: str
    url: str

class Organization(BaseModel):
    id: str
    name: str
    owner_id: str
    webhooks: List[Webhook] = []

class Prospect(BaseModel):
    firstName: str
    lastName: str
    email: str
    phone: str

class AppState(BaseModel):
    # Holds the currently selected items in the UI
    selected_organization: Optional[Organization] = None
    selected_webhook_index: Optional[int] = None
    selected_prospect: Optional[Prospect] = None
    # ... and any other state needed by the UI
```

## 5. Service Layer (`app/services/`)

*   **`DataService`**:
    *   Reads `org_webhooks.json` and `generated_prospects.json`.
    *   **Crucially, it must parse the raw JSON into the Pydantic models defined above.**
    *   Contains methods like `get_organizations() -> List[Organization]`, `save_organizations(orgs: List[Organization])`, etc.
    *   All file writing operations **must** be atomic (write to temp file, then rename) to prevent corruption.

*   **`PayloadService`**:
    *   Responsible for finding and loading the correct `_schema.json` file from the `schemas/` directory.
    *   The `generate_payload` method will take a schema path and a `Prospect` model and return a dictionary.

## 6. UI Layer (`app/ui/`)

*   **`main_window.py`**:
    *   The main `App` class will initialize and hold an instance of `AppState` and the services.
    *   All UI rendering functions (`populate_org_list`, etc.) will read directly from the `AppState` object.
    *   All user actions (e.g., `on_org_selected`) will call methods that first update the `AppState`, and then call a central `update_ui()` method to re-render the necessary components. This enforces the "single source of truth" principle.

*   **`popups.py`**:
    *   Each popup (Add Org, Add Webhook, etc.) will be its own class inheriting from `customtkinter.CTkToplevel`, ensuring proper lifecycle management and fixing the `grab_set` error definitively.

## 7. Development Plan (Todo List)

1.  **Project Setup:** Create the new directory structure as defined above. Move the existing `schemas/` directory (currently `webhook_payload_docs`).
2.  **Define Pydantic Models:** Create the `app/models/core.py` file with all necessary Pydantic models.
3.  **Implement Services:**
    *   Build `DataService` to read/write JSON and parse it into Pydantic models.
    *   Build `PayloadService` to work with the new schema location.
    *   Build `KeyringService`.
4.  **Implement State Management:** Create the `AppState` class and a simple manager class in `app/state/app_state.py`.
5.  **Build the UI:**
    *   Create the `main_window.py` with the three-column layout.
    *   Connect all UI elements to read from the `AppState`.
    *   Implement UI action handlers to update the `AppState` and trigger UI refreshes.
    *   Refactor all popups into their own classes in `ui/popups.py`.
6.  **Final Polish:** Ensure all features from v1 (profile selection, custom schemas, etc.) are correctly implemented in the new architecture.

## 8. Feature Spotlight: "Open in Bonzo" Workflow

This feature is a critical quality-of-life enhancement that directly connects the testing tool to the Bonzo platform.

### 8.1. Data Capture

*   The **"Add Organization"** and **"Edit Organization"** dialogs **must** include a mandatory field for the **`owner_id`**.
*   This `owner_id` is the unique identifier for a *user* in the Bonzo system (e.g., `17920`).
*   This ID is stored within the `Organization` Pydantic model and persisted in the `org_webhooks.json` file.

### 8.2. UI Implementation

*   In the main UI's first column, there will be two distinct, Bonzo-themed buttons:
    1.  **"Open Team in Bonzo"**
    2.  **"Open Owner in Bonzo"**
*   Both buttons **must** be disabled by default and only become active when an organization is selected from the list.

### 8.3. Functional Logic

*   **"Open Team in Bonzo" Button:**
    *   When clicked, the application retrieves the `id` from the currently selected `Organization` object in the `AppState`.
    *   It constructs a URL string using an f-string: `f"https://platform.getbonzo.com/admin/teams/{org.id}/details"`
    *   It then uses Python's built-in `webbrowser.open_new_tab()` function to open this URL in the user's default web browser.

*   **"Open Owner in Bonzo" Button:**
    *   When clicked, the application retrieves the `owner_id` from the currently selected `Organization` object in the `AppState`.
    *   It constructs a URL string using an f-string, including the static query parameters: `f"https://platform.getbonzo.com/admin/users/{org.owner_id}?search=&role=&permission=&status=&tag=&active=&page=1&team_permission=&business_ids=&enterprise_id=&list_id=&per_page=50"`
    *   It then uses `webbrowser.open_new_tab()` to open this URL.
*   **Error Handling:** If the `owner_id` is missing for the selected organization, a message will be printed to the console, and the browser will not be opened.
