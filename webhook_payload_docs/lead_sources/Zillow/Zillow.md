# Zillow

The Zillow integration expects a `type` field in the payload, which can be one of the following: "simple", "quote", "longForm", or "propertyPreapproval".

### Common Fields

- `sender.firstName` (string)
- `sender.lastName` (string)
- `sender.emailAddress` (string)
- `sender.phoneNumber` (string)
- `recipient.firstName` (string)
- `recipient.lastName` (string)
- `recipient.phoneNumber` (string)
- `recipient.emailAddress` (string)
- `details.agentFirstName` (string)
- `details.agentLastName` (string)
- `details.agentPhoneNumber` (string)
- `details.agentEmailAddress` (string)
- `details.creditScoreHigh` (numeric)
- `details.creditScoreLow` (numeric)

### `quote` Type Fields

- `details.loanAmount` (numeric)
- `details.downPayment` (numeric)
- `details.desiredPrograms` (array or string)
- `details.loanPurpose` (string)
- `details.propertyValue` (numeric)
- `details.stateAbbreviation` (string)
- `details.zipCode` (string)
- `details.hasBankruptcy` (boolean)
- `details.hasForeclosure` (boolean)

### `longForm` Type Fields

- `details.loanAmount` (numeric)
- `details.downPayment` (numeric)
- `details.loanPurpose` (string)
- `details.propertyValue` (numeric)
- `details.city` (string)
- `details.stateAbbreviation` (string)
- `details.zipCode` (string)
- `details.county` (string)
- `details.hasBankruptcy` (boolean)
- `details.hasAgent` (boolean)

### `propertyPreapproval` Type Fields

- `details.loanAmount` (numeric)
- `details.downPayment` (numeric)
- `details.propertyValue` (numeric)
- `details.propertyAddress` (string)
- `details.city` (string)
- `details.stateAbbreviation` (string)
- `details.zipCode` (string)
