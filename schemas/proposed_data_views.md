# Proposed Standardized Data Views

This document outlines a proposal for standardized data views to normalize data from various integration types within Bonzo. This will help create a more consistent and manageable data structure for prospects.

---

## 1. Lead Source View

This view is designed to standardize data from lead generation platforms. It captures the most common fields related to a new mortgage lead.

**Fields:**

-   `lead_source_name` (Enum): The name of the lead source.
    -   *Values*: `Zillow`, `LendingTree`, `Bankrate`, `Realtor.com`, `LeadPops`, `Unbounce`, `Leadpoint`, `LoanBright`, `Loansifter`, `WikiRealty`, `FreeRateUpdate`, `Mortech`, `Other`
-   `lead_id` (String): The unique identifier for the lead from the source platform.
-   `lead_message` (Text): Any message or notes provided by the prospect.
-   `ls_loan_purpose` (Enum): The reason for the loan.
    -   *Values*: `Purchase`, `Refinance`, `Cash-out Refinance`, `Home Equity`, `Other`
-   `ls_loan_type` (Enum): The type of loan program.
    -   *Values*: `Conventional`, `FHA`, `VA`, `USDA`, `ARM`, `Jumbo`, `Other`
-   `ls_loan_amount` (Numeric): The requested loan amount.
-   `subject_property_value` (Numeric): The estimated value of the subject property.
-   `subject_purchase_price` (Numeric): The purchase price of the property (for purchases).
-   `ls_down_payment` (Numeric): The down payment amount.
-   `ls_cash_out_amount` (Numeric): The amount of cash requested in a cash-out refinance.
-   `ls_interest_rate` (Numeric): The requested or quoted interest rate.
-   `credit_score_range` (Enum): The prospect's estimated credit score range.
    -   *Values*: `Excellent (720+)`, `Good (680-719)`, `Fair (620-679)`, `Poor (<620)`
-   `subject_property_type` (Enum): The type of property.
    -   *Values*: `Single Family`, `Condominium`, `Townhouse`, `Multi-Family`, `Manufactured Home`, `Land`
-   `subject_property_use` (Enum): How the prospect intends to use the property.
    -   *Values*: `Primary Residence`, `Second Home`, `Investment Property`
-   `subject_property_address` (String): The street address of the property.
-   `subject_property_city` (String): The city of the property.
-   `subject_property_state` (String): The state of the property.
-   `subject_property_zip` (String): The ZIP code of the property.
-   `subject_property_county` (String): The county of the property.
-   `found_home` (Boolean): Whether the prospect has already identified a property.
-   `working_with_agent` (Boolean): Whether the prospect is working with a real estate agent.
-   `agent_name` (String): The name of the real estate agent.
-   `agent_phone` (String): The phone number of the real estate agent.
-   `agent_email` (String): The email address of the real estate agent.
-   `bankruptcy_history` (Enum): Information about past bankruptcies.
    -   *Values*: `Yes, in the last 7 years`, `Yes, more than 7 years ago`, `No`
-   `foreclosure_history` (Enum): Information about past foreclosures.
    -   *Values*: `Yes, in the last 3 years`, `Yes, more than 3 years ago`, `No`
-   `household_income` (Numeric): The prospect's stated annual household income.
-   `military_status` (Boolean): Whether the prospect is a veteran or active military member.

---

## 2. Loan Origination System (LOS) View

This view is for integrations with systems like Refinder, which provide detailed data about existing or in-progress loans.

**Fields:**

-   `los_name` (Enum): The name of the Loan Origination System.
    -   *Values*: `Refinder`, `Encompass`, `Calyx Point`, `Byte`, `Other`
-   `transaction_id` (String): The unique identifier for the transaction in the LOS.
-   `recording_date` (Date): The date the mortgage was recorded.
-   `original_loan_amount` (Numeric): The original amount of the loan.
-   `original_interest_rate` (Numeric): The original interest rate of the loan.
-   `original_mortgage_type` (Enum): The original type of the mortgage.
    -   *Values*: `Conventional`, `FHA`, `VA`, `USDA`, `ARM`, `Jumbo`, `Other`
-   `current_loan_balance` (Numeric): The current outstanding balance of the loan.
-   `current_ltv` (Numeric): The current Loan-to-Value ratio.
-   `estimated_property_value` (Numeric): The current estimated value of the property.
-   `lendable_equity` (Numeric): The amount of equity available to be borrowed against.
-   `estimated_monthly_savings` (Numeric): The estimated potential savings from a refinance.
-   `benefit_classification` (String): A classification of the potential benefit (e.g., "Money Moves").
-   `payments_made` (Numeric): The number of payments made on the loan.

---

## 3. CRM View

This view is for integrations with CRM platforms like HubSpot or Insellerate, focusing on sales and marketing lifecycle data.

**Fields:**

-   `crm_name` (Enum): The name of the CRM.
    -   *Values*: `HubSpot`, `Insellerate`, `Salesforce`, `Zoho`, `Other`
-   `record_id` (String): The unique identifier for the record in the CRM.
-   `owner_id` (String): The ID of the user who owns the record in the CRM.
-   `owner_email` (String): The email of the record owner in the CRM.
-   `lifecycle_stage` (String): The current stage in the sales or marketing funnel (e.g., "Lead", "Opportunity", "Customer").
-   `lead_status` (String): The current status of the lead (e.g., "New", "Contacted", "Qualified").
-   `last_activity_date` (DateTime): The timestamp of the last interaction with the prospect.
-   `last_url_visited` (String): The last URL the prospect visited on a tracked website.

---

## 4. Monitorbase Alert View

This view is for our sister product, Monitorbase. It extends the standard **Lead Source View** with fields unique to Monitorbase's credit and life-event-based alerts.

**Fields:**

-   `alert_type` (Enum): The core reason for the alert, used for routing and automation.
    -   *Values*: `Inquiry`, `Migration`, `Predictive`, `Listing`, `Portfolio`, `Insurance`, `Equity`
-   `alert_id` (String): The unique identifier for the alert from Monitorbase.
-   `alert_date` (Date): The date the alert was generated.
-   `alert_intel` (String): The specific intelligence or reason for the alert (e.g., "Credit Inquiry", "Listing Found").
-   `alert_intel_category` (String): The broader category of the alert intel.
-   `alert_intel_id` (Integer): The ID associated with the specific alert intelligence.
-   `alert_intel_playbook_url` (String): A URL to a playbook or more information related to the alert.
-   `current_ltv` (String): The current Loan-to-Value ratio, as provided by Monitorbase.
-   `home_value` (String): The home value, as provided by Monitorbase.
