from flow import cold_outreach_flow

def main():
    """
    Main function to run the Cold Outreach Opener Generator application.
    """
    # Sample input data
    shared = {
        "input": {
            "first_name": "Elon",
            "last_name": "Musk",
            "keywords": "Tesla",
            "personalization_factors": [
                {
                    "name": "personal_connection",
                    "description": "Check if the target person is from the University of Pennsylvania",
                    "action": "If they are, say 'Go Quakers!'"
                },
                {
                    "name": "recent_achievement",
                    "description": "Check if the target person was recently promoted",
                    "action": "If they were, say 'Congratulations on your recent promotion...'"
                },
                {
                    "name": "shared_interest",
                    "description": "Check if the target person is interested in sustainable energy",
                    "action": "If they are, say 'I've been following your work on sustainable energy...'"
                },
                {
                    "name": "recent_talks",
                    "description": "Check if the target person gave a recent talk",
                    "action": "If they did, say 'I heard you gave a recent talk on...'"
                }
            ],
            "style": """Be concise, specific, and casual in 30 words or less. For example:
'Heard about your talk on the future of space exploration—loved your take on creating a more sustainable path for space travel.'"""
        }
    }

    print("Generating personalized cold outreach opener...")
    print(f"Target person: {shared['input']['first_name']} {shared['input']['last_name']}")
    print(f"Keywords: {shared['input']['keywords']}")
    print(f"Style: {shared['input']['style']}")
    print("\nSearching the web for information...")
    
    # Run the flow
    cold_outreach_flow.run(shared)
    
    # Display the results
    print("\n--- PERSONALIZATION INSIGHTS ---")
    if shared.get("personalization"):
        for factor, details in shared["personalization"].items():
            print(f"\n• {factor.upper()}:")
            print(f"  Details: {details['details']}")
            print(f"  Action: {details['action']}")
    else:
        print("No personalization factors were actionable.")
    
    print("\n--- GENERATED OPENING MESSAGE ---")
    print(shared["output"]["opening_message"])

if __name__ == "__main__":
    main()