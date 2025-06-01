# Quick Start Guide: Variable Mapping and Aliases

## Overview

This guide demonstrates how to use the new variable mapping and alias features in Templr.

## Step 1: Create a Template with Aliases

1. Navigate to `/templates` in the web interface
2. Click "Create New Template"
3. Fill in the basic template information:

   - **Name**: "Payment Notice"
   - **Slug**: "payment-notice"
   - **Description**: "Outstanding payment reminder template"

4. Add template variables with aliases:

   **Variable 1:**

   - Name: `customer_name`
   - Type: String
   - Aliases: `Customer_Name, customerName, Customer Name`

   **Variable 2:**

   - Name: `outstandingamount`
   - Type: Number
   - Aliases: `Outstanding_amount, outstanding-amount, OutstandingAmount, Outstanding Amount`

   **Variable 3:**

   - Name: `duedate`
   - Type: Date
   - Aliases: `Due_Date, due-date, DueDate, Due Date`

5. Use the template content from `sample_template.html`

## Step 2: Test with Different CSV Formats

The following CSV files will all work with the same template:

### Format 1: Underscore separated (test_data.csv)

```csv
customer_name,Outstanding_amount,Due_Date
John Doe,1500.50,2025-07-01
```

### Format 2: CamelCase (test_data_aliases.csv)

```csv
customerName,OutstandingAmount,due-date
Jane Smith,750.25,2025-06-15
```

### Format 3: Mixed case (test_data_mixed_case.csv)

```csv
CUSTOMER_NAME,outstanding_amount,DueDate
Sarah Connor,3000.00,2025-08-01
```

## Step 3: Upload and Test

1. Go to `/data-upload`
2. Upload any of the CSV files
3. Select your "payment-notice" template
4. The system will automatically map the columns to variables
5. Access rendered templates at: `/payment-notice/{identifier}`

## Benefits Demonstrated

✅ **Flexibility**: Same template works with different CSV column naming conventions
✅ **Case Insensitive**: `CUSTOMER_NAME`, `customer_name`, and `Customer_Name` all work
✅ **Alias Support**: Multiple naming patterns supported per variable
✅ **User Friendly**: No need to modify CSV files or create multiple templates
