# Monitorbase Integration Mapping

This document outlines how the Monitorbase webhook payload is mapped to the Bonzo data model. Monitorbase is treated as a specialized inbound lead source.

---

### Full Monitorbase Payload Example
```json
{
  "source": "string",
  "lo_email": "string (required for routing)",
  "lo_name": "string",
  "lo_alt_id": "string",
  "first_name": "string",
  "last_name": "string",
  "address": "string",
  "city": "string",
  "state": "string",
  "zip": "string",
  "custom_1": "string",
  "custom_2": "string",
  "custom_3": "string",
  "custom_4": "string",
  "custom_5": "string",
  "home_phone": "string",
  "cell_phone": "string",
  "work_phone": "string",
  "email": "string",
  "url": "string",
  "loan_id": "string",
  "loan_number": "string",
  "prospect_id": "string",
  "alt_id": "string",
  "type": "enum [Inquiry, Migration, Predictive, Listing, Portfolio, Insurance, Equity]",
  "alert_intel": "string",
  "alert_intel_category": "string",
  "alert_id": "string",
  "alert_date": "string",
  "alert_intel_id": "integer",
  "alert_intel_playbook_url": "string",
  "tags": "array[string]",
  "import_type": "string",
  "created_at": "string",
  "brokers": "array[broker_object]",
  "current_ltv": "string",
  "home_value": "string"
}
```

---

### Mapping to Bonzo Data Model

#### 1. Prospect Core Fields
These fields are mapped directly to the primary Bonzo Prospect record.

| Monitorbase Field | Bonzo Prospect Field | Notes                               |
|-------------------|----------------------|-------------------------------------|
| `first_name`      | `first_name`         |                                     |
| `last_name`       | `last_name`          |                                     |
| `email`           | `email`              |                                     |
| `cell_phone`      | `phone`              | `cell_phone` is prioritized.        |
| `home_phone`      | `secondary_phone`    | Mapped if `cell_phone` is present.  |
| `work_phone`      | `work_phone`         |                                     |
| `tags`            | `tags`               | Appended to the prospect's tags.    |

#### 2. Lead Source View Fields
These fields are mapped to the standardized **Lead Source View**.

| Monitorbase Field | Lead Source View Field        | Notes                               |
|-------------------|-------------------------------|-------------------------------------|
| `source`          | `lead_source_name`            | Value will be 'Monitorbase'.        |
| `address`         | `subject_property_address`    |                                     |
| `city`            | `subject_property_city`       |                                     |
| `state`           | `subject_property_state`      |                                     |
| `zip`             | `subject_property_zip`        |                                     |

#### 3. Monitorbase Alert View Fields
This is a specialized data view that extends the Lead Source View for Monitorbase-specific data.

| Monitorbase Field          | Monitorbase View Field     | Type  | Notes                                     |
|----------------------------|----------------------------|-------|-------------------------------------------|
| `type`                     | `alert_type`               | Enum  | The core reason for the alert.            |
| `alert_id`                 | `alert_id`                 | String|                                           |
| `alert_date`               | `alert_date`               | Date  |                                           |
| `alert_intel`              | `alert_intel`              | String|                                           |
| `alert_intel_category`     | `alert_intel_category`     | String|                                           |
| `alert_intel_id`           | `alert_intel_id`           | Integer|                                          |
| `alert_intel_playbook_url` | `alert_intel_playbook_url` | String|                                           |
| `current_ltv`              | `current_ltv`              | String|                                           |
| `home_value`               | `home_value`               | String|                                           |

**`alert_type` Enum Values:**
- `Inquiry`
- `Migration`
- `Predictive`
- `Listing`
- `Portfolio`
- `Insurance`
- `Equity`

#### 4. Loan Origination System (LOS) View Fields
These fields are mapped to the standardized **LOS View**.

| Monitorbase Field | LOS View Field   | Notes                               |
|-------------------|------------------|-------------------------------------|
| `loan_id`         | `transaction_id` | `loan_id` is prioritized.           |
| `loan_number`     | `transaction_id` | Used if `loan_id` is not present.   |

#### 5. Routing and Unmapped Fields
- **Routing Fields**: `lo_email`, `lo_name`, and `lo_alt_id` are used for routing logic within Bonzo but are not stored on the prospect record.
- **Custom Fields**: `custom_1` through `custom_5` can be mapped to custom fields in Bonzo during the webhook setup.
- **Unmapped**: `url`, `prospect_id`, `alt_id`, `import_type`, `created_at`, and `brokers` are not currently mapped to standard fields.