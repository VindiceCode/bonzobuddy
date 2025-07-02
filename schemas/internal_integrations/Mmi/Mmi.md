# MMI

The MMI integration has two payload variations, determined by the `type` field.

### Common Fields

- `firstname` (string)
- `lastname` (string)
- `email` (string)
- `phone` (string)
- `state` (string)
- `company` (string)
- `notes` (string)
- `nmls_id` (string)
- `fastfacts` (string)
- `oppapp` (string)
- `google` (string)
- `linkedIn` (string)
- `branch_address` (string)

### `Real Estate` Type Fields

- `type` (string, static: "Real Estate")
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

### `Mortgage` Type Fields

- `type` (string, static: "Mortgage")
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
