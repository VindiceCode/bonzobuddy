# LeadPops

The LeadPops integration expects the following fields in the payload:

- `first_name` (string)
- `last_name` (string)
- `email` (string)
- `phone` (string)
- `address` (string)
- `city` (string)
- `state` (string)
- `notes` (string or array of strings)

Additionally, it can accept any fields from the `MortgageFieldsService`, `InsuranceFieldsService`, and `RecruitingFieldsService`. It also supports a `coborrower` object with the same fields as the main prospect.
