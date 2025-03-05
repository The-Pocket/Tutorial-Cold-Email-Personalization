import csv
import argparse
import os
import json
from flow import cold_outreach_flow

def main():
    """
    Batch processing script for the Cold Outreach Opener Generator.
    Processes multiple people from a CSV file and generates personalized opening messages.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process multiple cold outreach targets from a CSV file.')
    parser.add_argument('--input', default='input.csv', help='Input CSV file (default: input.csv)')
    parser.add_argument('--output', default='output.csv', help='Output CSV file (default: output.csv)')
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        return
    
    # Hardcoded personalization factors
    personalization_factors = [
        {
            "name": "personal_connection",
            "description": "Check if target person has Columbia University affiliation",
            "action": "If they do, mention shared connection to Columbia"
        },
        {
            "name": "recent_promotion",
            "description": "Check if target person was recently promoted",
            "action": "If they were, congratulate them on their new role"
        },
        {
            "name": "recent_talks",
            "description": "Check if target person gave talks recently",
            "action": "If they did, mention enjoying their insights"
        }
    ]
    
    # Extract factor names for later use
    factor_names = [factor["name"] for factor in personalization_factors]
    print(factor_names)
    
    # Hardcoded style preference
    style = "Be concise, specific, and casual in 30 words or less. For example: 'Heard about your talk on the future of space exploration—loved your take on creating a more sustainable path for space travel.'"
    
    # Read input CSV
    input_data = []
    with open(args.input, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 'first_name' in row and 'last_name' in row and 'keywords' in row:
                input_data.append(row)
    
    if not input_data:
        print(f"Error: No valid data found in '{args.input}'. CSV should have columns: first_name, last_name, keywords")
        return
    
    # Process each person
    results = []
    total = len(input_data)
    for i, person in enumerate(input_data, 1):
        print(f"\nProcessing {i}/{total}: {person['first_name']} {person['last_name']}")
        
        # Prepare input data
        shared = {
            "input": {
                "first_name": person['first_name'],
                "last_name": person['last_name'],
                "keywords": person['keywords'],
                "personalization_factors": personalization_factors,
                "style": style
            }
        }
        
        # Run the flow
        try:
            cold_outreach_flow.run(shared)
            
            # Prepare result row
            # Extract URLs as comma-separated string
            urls = [result.get("link", "") for result in shared.get("search_results", []) if "link" in result]
            url_string = ",".join(urls)
            
            # Extract personalization details
            personalization_data = {}
            for factor_name, details in shared.get("personalization", {}).items():
                personalization_data[factor_name + "_actionable"] = str(details.get("actionable", False))
                personalization_data[factor_name + "_details"] = details.get("details", "")
            
            result = {
                'first_name': person['first_name'],
                'last_name': person['last_name'],
                'keywords': person['keywords'],
                'opening_message': shared.get("output", {}).get("opening_message", ""),
                'search_results': url_string,
                **personalization_data  # Add all personalization fields
            }
            results.append(result)
            
            # Display the result
            print(f"Generated opener: {result['opening_message']}")
            
        except Exception as e:
            print(f"Error processing {person['first_name']} {person['last_name']}: {str(e)}")
            # Add failed row with error message
            results.append({
                'first_name': person['first_name'],
                'last_name': person['last_name'],
                'keywords': person['keywords'],
                'opening_message': f"ERROR: {str(e)}",
                'search_results': "",
                # Include empty personalization fields for consistency with successful rows
                **{f"{factor}_actionable": "False" for factor in factor_names},
                **{f"{factor}_details": "" for factor in factor_names}
            })
    
    # Write results to output CSV
    if results:
        # Determine all field names by examining all the result rows
        all_fields = set()
        for result in results:
            all_fields.update(result.keys())
        
        fieldnames = ['first_name', 'last_name', 'keywords', 'opening_message', 'search_results']
        # Add personalization fields in a specific order
        for factor in factor_names:
            if f"{factor}_actionable" in all_fields:
                fieldnames.append(f"{factor}_actionable")
            if f"{factor}_details" in all_fields:
                fieldnames.append(f"{factor}_details")
        
        with open(args.output, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\nProcessing complete. Results written to '{args.output}'")
    else:
        print("\nNo results to write.")

if __name__ == "__main__":
    main() 