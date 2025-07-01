# Unbounce

The Unbounce integration expects a `data_json` field in the payload, which is a JSON string containing the lead data. The following fields are extracted from the JSON data:

- `first_name` (array, first element is used)
- `last_name` (array, first element is used)
- `email` (array, first element is used)
- `phone` (array, first element is used)
- `address` (array, first element is used)
- `city` (array, first element is used)
- `state` (array, first element is used)

Custom fields can be included by prefixing the field name with `custom_`.
