# HubSpot

The HubSpot integration expects the following fields in the payload:

- `is-contact` (boolean)
- `properties.hs_object_id.value` (string)
- `properties.firstname.value` (string)
- `properties.lastname.value` (string)
- `properties.email.value` (string)
- `properties.phone.value` (string)
- `properties.state.value` (string)
- `properties.city.value` (string)
- `properties.zip.value` (string)
- `properties.dealer_id.value` (string) (or `properties.hubspot_owner_id.value`)
- `properties.hs_analytics_last_url.value` (string)

Any other fields within the `properties` object will be added as a note to the prospect.
