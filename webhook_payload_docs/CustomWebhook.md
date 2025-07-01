# Custom Webhook

The Custom Webhook integration is a generic parser that can handle any JSON or XML payload. The data is passed through the `handleFieldMapping` method, which allows for custom field mapping in the webhook configuration.

The only field that is automatically added is `source`, which is set to `custom_webhook`.
