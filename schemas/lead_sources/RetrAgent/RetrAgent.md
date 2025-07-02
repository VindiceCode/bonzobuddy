# RETR (Agent)

The RETR (Agent) integration expects the following fields in the payload:

- `FirstName` (string)
- `LastName` (string)
- `Email` (string)
- `Phone` (string)
- `NickName` (string)
- `Tags` (string, comma-separated)

It also supports the following suggested fields, which will be mapped to custom fields:

- `RetrProfileURL` (text)
- `BuyerCt_12Mo` (numeric)
- `BuyerVol_12Mo` (numeric)
- `SellerCt_12Mo` (numeric)
- `SellerVol_12Mo` (numeric)
- `LoanOfficerCt_12Mo` (numeric)
- `LoanCt_Conventional_12Mo` (numeric)
- `LoanCt_VA_12Mo` (numeric)
- `LoanCt_FHA_12Mo` (numeric)
- `RETRAgentId` (numeric)
