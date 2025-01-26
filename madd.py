import requests
import pandas as pd

# Base URL for the API
base_url = "https://www.trade-tariff.service.gov.uk/api/v2/"

# Define headers (no authentication required for this endpoint)
headers = {
    'Content-Type': 'application/json'
}

# Function to get all sections (using the correct endpoint)
def get_sections():
    response = requests.get(f"{base_url}sections", headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get('data', [])
    else:
        print(f"Error fetching sections: {response.status_code}")
        return []

# Function to get commodity codes for a section
def get_commodity_codes(section_id):
    response = requests.get(f"{base_url}sections/{section_id}/commodity_codes", headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get('data', [])
    else:
        print(f"Error fetching commodity codes for section {section_id}: {response.status_code}")
        return []

# Function to get detailed information for a commodity
def get_commodity_details(commodity_id):
    response = requests.get(f"{base_url}commodities/{commodity_id}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get('data', {})
    else:
        print(f"Error fetching commodity details for {commodity_id}: {response.status_code}")
        return {}

# Function to get the rules of origin for a specific subheading and country code
def get_rules_of_origin(subheading, country_code):
    response = requests.get(f"{base_url}rules_of_origin_schemes/{subheading}/{country_code}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get('data', [])
    else:
        print(f"Error fetching rules of origin for {subheading}, {country_code}: {response.status_code}")
        return []

# Function to extract all commodity codes, descriptions, and rules of origin
def extract_commodity_data(country_code):
    all_commodity_data = []

    # Get the list of all sections
    sections = get_sections()

    if not sections:
        print("No sections found or error in fetching sections.")
        return

    # Iterate through each section and get commodity codes
    for section in sections:
        section_id = section.get('id', 'N/A')
        section_description = section.get('description', 'No Description')  # Fallback if no description available

        # Fetch commodity codes for the section
        commodity_codes = get_commodity_codes(section_id)

        if not commodity_codes:
            print(f"No commodity codes found for section {section_description} ({section_id})")
            continue

        # Fetch details for each commodity code
        for code in commodity_codes:
            commodity_id = code.get('id', 'N/A')
            subheading = code.get('code', '')[:6]  # Get the first 6 digits for subheading
            commodity_data = {
                'Commodity Code': code.get('code', 'N/A'),
                'Description': code.get('description', 'No Description')
            }

            # Get detailed information for each commodity
            commodity_details = get_commodity_details(commodity_id)

            # Merge commodity details into the commodity_data
            if commodity_details:
                commodity_data.update({
                    'Full Description': commodity_details.get('description', 'No Description'),
                })

            # Get the Rules of Origin for the commodity subheading and country
            rules_of_origin = get_rules_of_origin(subheading, country_code)

            # Add the rules of origin to the data
            if rules_of_origin:
                commodity_data['Rules of Origin'] = ', '.join(rule.get('scheme', 'N/A') for rule in rules_of_origin)
            else:
                commodity_data['Rules of Origin'] = 'No Rules Found'

            all_commodity_data.append(commodity_data)

    if not all_commodity_data:
        print("No commodity data found.")
        return

    # Convert the data to a pandas DataFrame
    df = pd.DataFrame(all_commodity_data)

    # Save the data to an Excel file
    df.to_excel('commodity_codes_with_rules.xlsx', index=False)
    print("Data has been saved to 'commodity_codes_with_rules.xlsx'.")

# Main function to extract and save commodity data
if __name__ == "__main__":
    country_code = "FR"  # Example country code (France)
    extract_commodity_data(country_code)
