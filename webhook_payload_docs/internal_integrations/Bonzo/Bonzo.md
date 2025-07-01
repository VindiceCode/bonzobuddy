# Bonzo (General)

The Bonzo integration provides a general-purpose webhook parser that can handle a wide variety of fields.

### Prospect Fields

- `first_name` (string)
- `last_name` (string)
- `email` (string)
- `phone` (string)
- `address` (string)
- `city` (string)
- `state` (string)
- `zip` (string)
- `marital_status` (string)
- `prospect_type` (string)
- `unit_number` (string)
- `alias` (string)
- `birthday` (string, format: YYYY-MM-DD)
- `user_id` (integer, for enterprise accounts)
- `notes` (string or array of strings)
- `external_id` (string)

### Mortgage Fields

If the business has mortgage fields enabled, the following fields can be included:

- All fields from `MortgageFieldsService` (see codebase for details)
- `dwelling_use` (string, alias for `property_use`)
- `prospect_company` (string, alias for `company_name`)

### Insurance Fields

If the business has insurance fields enabled, all fields from `InsuranceFieldsService` can be included (see codebase for details).

### Recruiting Fields

If the business has recruiting fields enabled, all fields from `RecruitingFieldsService` can be included (see codebase for details).

### Custom Fields

Custom fields can be included by prefixing the field name with `custom_`. For example, a custom field named "Lead Source" would be sent as `custom_Lead_Source`.

### Contact People

Contact people (coborrower, listing agent, buyer agent) can be included as objects with the following keys:

- `first_name` (string)
- `last_name` (string)
- `email` (string)
- `phone` (string)
- `company_name` (string)

To unassign a contact person, send the field with a `null` value (e.g., `"coborrower": null`).

### Loan Fields

Loan information can be included in a `loan` object, with keys corresponding to the `Loan` model attributes.
