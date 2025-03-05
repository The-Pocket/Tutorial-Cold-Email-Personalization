import streamlit as st
import logging
import sys
from flow import cold_outreach_flow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("streamlit_app")

# Function to validate minimum length
def validate_min_length(text, min_length, field_name):
    if text and len(text) < min_length:
        return f"{field_name} must be at least {min_length} characters."
    return None

def main():
    st.set_page_config(
        page_title="Cold Outreach Opener Generator",
        page_icon="✉️",
        layout="wide"
    )
    
    st.title("Cold Outreach Opener Generator")
    st.write("Generate personalized opening messages for cold outreach emails based on web search results.")
    
    # Sidebar for detailed app description
    with st.sidebar:
        st.subheader("About")
        st.write("""
        This app automatically generates personalized opening messages for cold outreach emails 
        based on web search results. It uses LLMs and web search to find relevant information 
        about the target person.
        """)
        st.write("---")
        st.subheader("How it works:")
        st.write("""
        1. Enter details about the target person
        2. Define personalization factors to look for
        3. Set your preferred message style
        4. Click "Generate Opening" to search the web and generate a personalized message
        """)
    
    # Main interface - inputs
    col1, col2 = st.columns([1, 1])
    
    # Error message containers
    error_container = st.empty()
    errors = []
    
    with col1:
        st.subheader("Target Person Information")
        
        # Create two columns for first name and last name
        name_col1, name_col2 = st.columns(2)
        
        with name_col1:
            first_name = st.text_input("First Name (1-30 chars)", "Elon", max_chars=30)
            if err := validate_min_length(first_name, 1, "First name"):
                errors.append(err)
        
        with name_col2:
            last_name = st.text_input("Last Name (1-30 chars)", "Musk", max_chars=30)
            if err := validate_min_length(last_name, 1, "Last name"):
                errors.append(err)
            
        keywords = st.text_input("Keywords (max 100 chars)", "Tesla", max_chars=100)
        
        st.subheader("Message Style")
        style = st.text_area("Style Preferences (10-500 chars)", """Be concise, specific, and casual in 30 words or less. For example: 'Heard about your talk on the future of space exploration—loved your take on creating a more sustainable path for space travel.'""", height=150, max_chars=500)
        if err := validate_min_length(style, 10, "Style preferences"):
            errors.append(err)
    
    with col2:
        st.subheader("Personalization Factors")
        st.write("Define what personal information to look for and how to use it in your message (1-5 factors allowed).")
        
        # Initialize session state for personalization factors if not exists
        if 'personalization_factors' not in st.session_state:
            st.session_state.personalization_factors = [
                {
                    "name": "personal_connection",
                    "description": "Check if the target person is from the University of Pennsylvania",
                    "action": "If they are, say 'Go Quakers!'"
                },
                {
                    "name": "recent_achievement",
                    "description": "Check if the target person was recently promoted",
                    "action": "Say 'Congratulations on your recent promotion...'"
                },
            ]
        
        # Display existing factors
        for i, factor in enumerate(st.session_state.personalization_factors):
            with st.expander(f"Factor {i+1}: {factor['name']}", expanded=False):
                factor_name = st.text_input("Name (5-30 chars)", factor["name"], key=f"name_{i}", max_chars=30)
                if err := validate_min_length(factor_name, 5, f"Factor {i+1} name"):
                    errors.append(err)
                    
                factor_desc = st.text_input("Description (10-100 chars)", factor["description"], key=f"desc_{i}", max_chars=100)
                if err := validate_min_length(factor_desc, 10, f"Factor {i+1} description"):
                    errors.append(err)
                    
                factor_action = st.text_input("Action (10-100 chars)", factor["action"], key=f"action_{i}", max_chars=100)
                if err := validate_min_length(factor_action, 10, f"Factor {i+1} action"):
                    errors.append(err)
                
                # Create two columns for buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Update", key=f"update_{i}", use_container_width=True):
                        # Validate minimum lengths before updating
                        if (len(factor_name) >= 5 and len(factor_desc) >= 10 and len(factor_action) >= 10):
                            st.session_state.personalization_factors[i] = {
                                "name": factor_name,
                                "description": factor_desc,
                                "action": factor_action
                            }
                            st.success("Factor updated!")
                        else:
                            st.error("Please fix validation errors before updating.")
                
                with col2:
                    if st.button("Remove", key=f"remove_{i}", type="primary", use_container_width=True):
                        st.session_state.personalization_factors.pop(i)
                        st.rerun()
        
        # Add new factor (if we're under the maximum of 5)
        if len(st.session_state.personalization_factors) < 5:
            with st.expander("Add New Factor", expanded=False):
                new_name = st.text_input("Name (5-30 chars)", "shared_interest", key="new_name", max_chars=30)
                if err := validate_min_length(new_name, 5, "New factor name"):
                    errors.append(err)
                    
                new_desc = st.text_input("Description (10-100 chars)", "Check if the target person is interested in...", key="new_desc", max_chars=100)
                if err := validate_min_length(new_desc, 10, "New factor description"):
                    errors.append(err)
                    
                new_action = st.text_input("Action (10-100 chars)", "Say 'I've been following your work on...'", key="new_action", max_chars=100)
                if err := validate_min_length(new_action, 10, "New factor action"):
                    errors.append(err)
                
                if st.button("Add Factor", type="primary", use_container_width=True):
                    # Validate minimum lengths before adding
                    if (len(new_name) >= 5 and len(new_desc) >= 10 and len(new_action) >= 10):
                        st.session_state.personalization_factors.append({
                            "name": new_name,
                            "description": new_desc,
                            "action": new_action
                        })
                        st.success("Factor added!")
                        st.rerun()
                    else:
                        st.error("Please fix validation errors before adding.")
        else:
            st.warning("Maximum of 5 personalization factors reached. Remove one to add a new factor.")

    # Display validation errors if any
    if errors:
        error_container.error("\n".join(errors))
    
    # Check factor count
    if len(st.session_state.personalization_factors) < 1:
        error_container.error("At least 1 personalization factor is required.")
        generate_disabled = True
    else:
        generate_disabled = bool(errors)
    
    # Generate button
    if st.button("Generate Opening", type="primary", use_container_width=True, disabled=generate_disabled):
        if not first_name or not last_name:
            st.error("Please provide at least the person's first and last name.")
            return
        
        # Create the shared data structure
        shared = {
            "input": {
                "first_name": first_name,
                "last_name": last_name,
                "keywords": keywords,
                "personalization_factors": st.session_state.personalization_factors,
                "style": style
            }
        }
        
        # Show progress
        with st.spinner("Searching the web for information about the target person..."):
            # Create a status area
            status_area = st.empty()
            log_area = st.empty()
            
            # Create a custom log handler to display logs in Streamlit
            log_messages = []
            class StreamlitLogHandler(logging.Handler):
                def emit(self, record):
                    log_messages.append(self.format(record))
                    log_text = "\n".join(log_messages[-10:])  # Show last 10 messages
                    log_area.code(log_text, language="bash")
            
            # Add the custom handler to the logger
            streamlit_handler = StreamlitLogHandler()
            streamlit_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            logging.getLogger().addHandler(streamlit_handler)
            
            try:
                # Run the flow
                cold_outreach_flow.run(shared)
                
                # Remove the custom handler
                logging.getLogger().removeHandler(streamlit_handler)
                
            except Exception as e:
                status_area.error(f"An error occurred: {str(e)}")
                logging.getLogger().removeHandler(streamlit_handler)
                st.error(f"Failed to generate opening message: {str(e)}")
                return
        
        # Display results
        if "output" in shared and "opening_message" in shared["output"]:
            st.success(shared["output"]["opening_message"])
            
            # Display personalization details
            if "personalization" in shared and shared["personalization"]:
                st.subheader("Personalization Details Found")
                for factor_name, details in shared["personalization"].items():
                    with st.expander(f"Factor: {factor_name}"):
                        st.write(f"**Details:** {details['details']}")
                        st.write(f"**Action:** {details['action']}")
            else:
                st.info("No personalization factors were found for this person.")
        else:
            st.warning("No opening message was generated. Check the logs for details.")

if __name__ == "__main__":
    main() 