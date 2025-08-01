# Loansifter

The Loansifter integration expects an XML payload. The following fields are extracted from the `Result` element:

- `Request.LeadInformation.ConsumerContactInformation.FirstName` (string)
- `Request.LeadInformation.ConsumerContactInformation.LastName` (string)
- `Request.LeadInformation.ConsumerContactInformation.EmailAddress.val` (string)
- `Request.LeadInformation.ConsumerContactInformation.ContactPhone.val` (string)
- `Request.LeadInformation.ConsumerContactInformation.ContactAddress` (string)
- `Request.LeadInformation.ConsumerContactInformation.ContactCity` (string)
- `Request.LeadInformation.ConsumerContactInformation.ContactState` (string)
- `Request.LeadInformation.ConsumerContactInformation.ContactZip` (string)
- `Request.LeadInformation.ConsumerProfileInformation.DateOfBirth` (string, format: YYYY-MM-DD)
- `Request.LeadInformation.LoanInformation.LoanAmount` (numeric)
- `Request.LeadInformation.LoanInformation.DownPayment` (numeric)
- `Request.LeadInformation.ConsumerProfileInformation.Credit.SelfCreditRating.val` (string)
- `Request.LeadInformation.LoanInformation.LoanRequestType.val` (string)
- `Request.LeadInformation.ProductInformation.PropertyInformation.PropertyValue` (numeric)
- `Request.LeadInformation.ProductInformation.PropertyInformation.PropertyCity` (string)
- `Request.LeadInformation.ProductInformation.PropertyInformation.PropertyState` (string)
- `Request.LeadInformation.ProductInformation.PropertyInformation.PropertyZip` (string)
- `Request.LeadInformation.ProductInformation.PropertyInformation.PropertyCounty` (string)
- `Request.LeadInformation.ConsumerProfileInformation.ProductProfileInformation.FoundHome` (string, "Y" or "N")
- `Request.LeadInformation.ConsumerProfileInformation.Credit.Bankruptcy.val` (string)
- `Request.LeadInformation.ConsumerProfileInformation.Credit.Foreclosure.val` (string)
- `Request.LeadInformation.ConsumerProfileInformation.ProductProfileInformation.WorkingWithAgent` (string, "Y" or "N")
- `Request.LeadInformation.ConsumerProfileInformation.ProductProfileInformation.PropertyPurchasePrice` (numeric)
- `Request.LeadInformation.TrackingNumber` (string)
