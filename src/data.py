import json
import xlrd

ERROR_CTYPE = 5

def clean_tariff_rate(value):
    if isinstance(value, float):
        value = f"{round(value * 100, 2)}%"  # Assuming the value is a percentage
    return value

def excel_to_json(
    input_file: str, output_file: str, sheet_name: str = "Sheet1"
):
    workbook = xlrd.open_workbook(input_file)
    
    # List all sheet names and print them for debugging
    sheet_names = workbook.sheet_names()
    print(f"Sheet names in the workbook: {sheet_names}")
    
    if sheet_name not in sheet_names:
        raise ValueError(f"No sheet named '{sheet_name}' found in the workbook.")
    
    worksheet = workbook.sheet_by_name(sheet_name)

    data = []

    for row_number, row in enumerate(worksheet.get_rows()):
        if row_number == 0:  # Skip the header row
            continue

        if any(item.ctype == ERROR_CTYPE for item in row):
            print(f"Row {row_number}: Failed row with code {row[0].value}")
            continue

        # Extract data from rows with added type checks
        commodity = str(row[0].value).strip() if row[0].value else None
        description = str(row[1].value).strip() if row[1].value else None
        cet_duty_rate = clean_tariff_rate(row[2].value) if row[2].value else None
        ukgt_duty_rate = clean_tariff_rate(row[3].value) if row[3].value else None
        change = str(row[4].value).strip() if len(row) > 4 and row[4].value else None
        trade_remedy_applies = str(row[5].value).strip() if len(row) > 5 and row[5].value else None
        cet_applies_until_trade_remedy_transition_reviews_concluded = str(row[6].value).strip() if len(row) > 6 and row[6].value else None
        suspension_applies = str(row[7].value).strip() if len(row) > 7 and row[7].value else None
        atq_applies = str(row[8].value).strip() if len(row) > 8 and row[8].value else None
        product_specific_rule_of_origin = str(row[9].value).strip() if len(row) > 9 and row[9].value else None
        vat_rate = clean_tariff_rate(row[10].value) if len(row) > 10 and row[10].value else None  # Extract VAT Rate

        # Skip rows with essential missing data
        if not commodity or not description:
            print(f"Row {row_number}: Missing essential data (commodity or description).")
            continue

        # Append to data list
        data.append(
            {
                "commodity": commodity,
                "description": description,
                "cet_duty_rate": cet_duty_rate,
                "ukgt_duty_rate": ukgt_duty_rate,
                "change": change,
                "trade_remedy_applies": trade_remedy_applies,
                "cet_applies_until_trade_remedy_transition_reviews_concluded": cet_applies_until_trade_remedy_transition_reviews_concluded,
                "suspension_applies": suspension_applies,
                "atq_applies": atq_applies,
                "product_specific_rule_of_origin": product_specific_rule_of_origin,
                "vat_rate": vat_rate,  # Add VAT Rate to JSON structure
            }
        )

    # Write to JSON
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    input_file = r"D:\ai project\global-uk-tariffv1\global-uk-tariff.xlsx"
    output_file = r"D:\ai project\global-uk-tariffv1\data.json"
    excel_to_json(input_file, output_file)
