# MMI

The MMI integration expects the following fields in the payload:

- `firstname` (string)
- `lastname` (string)
- `email` (string)
- `phone` (string)
- `state` (string)
- `type` (string, "Real Estate" or "Mortgage")
- `company` (string)
- `notes` (string)
- `nmls_id` (string)
- `fastfacts` (string)
- `oppapp` (string)
- `google` (string)
- `linkedIn` (string)
- `branch_address` (string)

### Agent-Specific Fields

If `type` is "Real Estate", the following fields are also expected:

- `agent_active_volume` (numeric)
- `agent_active_listings` (numeric)
- `agent_rolling_buyside_volume` (numeric)
- `agent_rolling_buyside_transactions` (numeric)
- `agent_ytd_buyside_transactions` (numeric)
- `agent_ytd_buyside_volume` (numeric)
- `agent_rolling_listside_volume` (numeric)
- `agent_rolling_listside_transactions` (numeric)
- `agent_ytd_listside_transactions` (numeric)
- `agent_ytd_listside_volume` (numeric)

### Loan Officer-Specific Fields

If `type` is "Mortgage", the following fields are also expected:

- `lo_ytd_volume` (numeric)
- `lo_ytd_transactions` (numeric)
- `lo_ytd_trans_purch_percent` (string)
- `lo_ytd_trans_refi_percent` (string)
- `lo_ytd_trans_other_percent` (string)
- `lo_ytd_type_conv_percent` (string)
- `lo_ytd_type_fha_percent` (string)
- `lo_ytd_type_va_percent` (string)
- `lo_ytd_type_other_percent` (string)
- `lo_rolling_volume` (numeric)
- `lo_rolling_transactions` (numeric)
- `lo_rolling_trans_purch_percent` (string)
- `lo_rolling_trans_refi_percent` (string)
- `lo_rolling_trans_other_percent` (string)
- `lo_rolling_type_other_percent` (string)
- `lo_rolling_type_conv_percent` (string)
- `lo_rolling_type_fha_percent` (string)
- `lo_rolling_type_va_percent` (string)