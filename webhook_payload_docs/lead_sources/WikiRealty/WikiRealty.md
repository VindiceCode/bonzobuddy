# WikiRealty

The WikiRealty integration expects the following fields in the payload:

- `first_name` (string)
- `last_name` (string)
- `email` (string)
- `phone` (string)
- `address` (string)
- `city` (string)
- `state` (string)
- `notes` (string or array of strings)

Additionally, it can accept any fields from the `MortgageFieldsService`, `InsuranceFieldsService`, and `RecruitingFieldsService`. Custom fields can be included by prefixing the field name with `custom_`.
