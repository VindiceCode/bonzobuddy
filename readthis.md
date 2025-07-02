# Onboarding Guide: Understanding the Bonzo Buddy Schema System

Hey, welcome to the Bonzo Buddy project! We've designed a specific, convention-based system for managing webhook payload schemas. This guide will walk you through how it works and why it's set up this way.

## 1. The Core Principle: Convention over Configuration

The entire application is driven by the file and directory structure inside the `schemas/` directory. The app doesn't have a hardcoded list of integrations; it discovers them by reading this directory. This makes it incredibly easy to add new integrations without touching the application's core code.

## 2. Directory Structure

The `schemas/` directory is organized by the **type** of integration, which provides a clear separation of concerns:

```
schemas/
├── crm/
│   └── Hubspot/
│       ├── Hubspot.md
│       └── hubspot_schema.json
├── lead_sources/
│   ├── Mmi/
│   │   ├── Mmi.md
│   │   ├── mmi_mortgage_schema.json
│   │   └── mmi_real_estate_schema.json
│   └── Zillow/
│       ├── Zillow.md
│       ├── zillow_longForm_schema.json
│       ├── zillow_propertyPreapproval_schema.json
│       ├── zillow_quote_schema.json
│       └── zillow_simple_schema.json
└── ...
```

*   **Top-Level:** Categories of integrations (`crm`, `lead_sources`).
*   **Second-Level:** The specific integration partner (e.g., `Hubspot`, `Mmi`).
*   **Contents:** Each integration directory contains:
    *   A `.md` file with human-readable documentation.
    *   One or more `_schema.json` files that define the payload structure.

## 3. Handling Payload Variations (The "Why" Behind Multiple Schemas)

This is the most important concept. Many of our integration partners send different payload structures depending on the context. For example:

*   **MMI** sends different fields if the lead is a "Real Estate" agent versus a "Mortgage" loan officer.
*   **Zillow** sends different payloads for a `simple` inquiry versus a `longForm` lead.

Instead of creating one massive, complex schema with confusing conditional logic, we've adopted a cleaner approach: **one schema file per variation.**

*   `mmi_mortgage_schema.json` defines the exact payload for a mortgage lead.
*   `mmi_real_estate_schema.json` defines the exact payload for a real estate lead.

**How Bonzo Buddy Uses This:**
When you select a webhook in the Bonzo Buddy UI, the app checks how many `_schema.json` files exist in that integration's directory.
*   If there's only one, it just uses it.
*   If there are multiple, the **"Payload Profile" dropdown appears**, populated with the names of the variations (e.g., `mortgage`, `real_estate`). This allows you to easily select, generate, and test every possible payload format for that partner.

## 4. Dynamic Payload Generation

The `_schema.json` files are not just static examples; they are blueprints for dynamic data. The `payload_generator.py` service reads these schemas and looks for specific keys:

*   `"dynamic": "firstName"`: This tells the generator to insert a unique, dynamically generated first name.
*   `"dynamic": "email"`: Inserts the unique email for the current test prospect.
*   `"static": "SomeValue"`: For all other fields, it uses the hardcoded static value.

This ensures that every time you click "Generate New Prospect," you get a payload with unique contact information, which is essential for testing how Bonzo handles new, unique leads.

## 5. Extending the System: Custom Schemas

We've also built a workflow for discovery and documentation.

*   When you're in the UI, you can click the **"Edit"** button to manually change a generated payload.
*   If you discover a new payload format or want to test a specific edge case, you can then click **"Save as Custom Schema"**.
*   This will prompt you for a name (e.g., "Zillow with new field") and save your modified payload as a new schema file inside a special `custom_schemas/` subdirectory for that integration:
    ```
    schemas/lead_sources/Zillow/custom_schemas/zillow_with_new_field_schema.json
    ```
This provides a built-in mechanism for documenting new payload variations as they are discovered, making it easy to formalize them as official schemas later.

---

This system is designed to be robust, scalable, and easy for any developer to understand and extend. By following these conventions, we can keep Bonzo Buddy up-to-date and make it an invaluable tool for our team.
