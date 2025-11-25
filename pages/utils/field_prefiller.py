import streamlit as st

def render_field_prefiller(field_label: str, session_key: str, suggested_value: str, help_text: str = None):
    """
    Renders a UI component to pre-fill a text input field with a suggested value.

    This component displays a text input and a button. When the button is clicked,
    the text input is populated with the suggested value.

    Args:
        field_label (str): The display name for the field (e.g., "Invoice Number").
        session_key (str): The key used to store the field's value in st.session_state.
        suggested_value (str): The value to suggest (e.g., the uploaded filename).
        help_text (str, optional): A tooltip to display for the button. Defaults to None.
    """
    # --- START: feature_field_prefiller ---
    
    col1, col2 = st.columns([3, 1])

    with col1:
        # Ensure the key exists in session_state before creating the text_input
        if session_key not in st.session_state:
            st.session_state[session_key] = ""
        
        # The text input field that the user can edit
        st.session_state[session_key] = st.text_input(
            field_label, 
            value=st.session_state[session_key]
        )

    with col2:
        # The button to apply the suggestion
        st.write(" ") # Adds vertical space to align the button
        if st.button(f"Use Filename", key=f"prefill_{session_key}", help=help_text):
            st.session_state[session_key] = suggested_value
            st.rerun() # Rerun to update the text_input with the new value

    # --- END: feature_field_prefiller ---
