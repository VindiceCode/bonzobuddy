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
- `user_id` (integer)
- `notes` (string or array of strings)
- `external_id` (string)

### Mortgage Fields
- All fields from `MortgageFieldsService`
- `dwelling_use` (string, alias for `property_use`)
- `prospect_company` (string, alias for `company_name`)

### Insurance Fields
- All fields from `InsuranceFieldsService`

### Recruiting Fields
- All fields from `RecruitingFieldsService`

### Custom Fields
- `custom_` prefixed fields

### Contact People
- `coborrower` (object)
- `listing_agent` (object)
- `buyer_agent` (object)

### Loan Fields
- `loan` (object)
