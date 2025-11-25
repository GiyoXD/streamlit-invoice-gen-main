import streamlit as st
import json
import os
from app import setup_page_auth

# --- Enhanced Authentication Setup ---
user_info = setup_page_auth(
    page_title="User Guide", 
    page_name="User Guide",
    layout="wide"
)

# --- Load Translation Function ---
def load_translations(language_code):
    """Load translations from JSON files"""
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # The translations folder is in the same directory as this script
        root_dir = script_dir
        file_path = os.path.join(root_dir, "translations", f"{language_code}.json")
        
        if os.path.exists(file_path):
            # Check if file is not empty
            if os.path.getsize(file_path) > 0:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                st.warning(f"Translation file {language_code}.json is empty, falling back to English")
        
        # Fallback to English if file doesn't exist or is empty
        fallback_path = os.path.join(root_dir, "translations", "en.json")
        if os.path.exists(fallback_path) and os.path.getsize(fallback_path) > 0:
            with open(fallback_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            st.error("Both translation file and English fallback are missing or empty")
    except Exception as e:
        st.error(f"Error loading translations: {e}")
        return {}

# --- Language Selection ---
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    language_options = {
        "English": "en",
        "ខ្មែរ (Khmer)": "km", 
        "中文 (Chinese)": "zh"
    }
    
    selected_language = st.selectbox(
        "🌐 Language / ភាសា / 语言",
        options=list(language_options.keys()),
        index=0
    )
    
    language_code = language_options[selected_language]

# Load translations
t = load_translations(language_code)

# --- Helper function to safely get translation ---
def get_text(key_path, default=""):
    """Safely get nested translation text"""
    keys = key_path.split('.')
    value = t
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default

# Main title
st.title(get_text("title", "📖 Invoice Management System - User Guide"))

# Create tabs for different sections
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    get_text("tabs.getting_started", "🏠 Getting Started"),
    get_text("tabs.dashboard", "📊 Dashboard"), 
    get_text("tabs.adding_invoices", "➕ Adding Invoices"),
    get_text("tabs.managing_data", "✏️ Managing Data"),
    get_text("tabs.header_mapping", "🔧 Header Mapping"),
    get_text("tabs.troubleshooting", "❓ Troubleshooting")
])

with tab1:
    st.header(get_text("getting_started.welcome_title", "🏠 Welcome to the Invoice Management System"))
    
    st.markdown(get_text("getting_started.what_is_system", "### What is this system?"))
    st.markdown(get_text("getting_started.system_desc", "This is an automated invoice processing system designed for leather manufacturing businesses. It converts your Excel data into professional invoices with multiple format options, handles both High-Quality and 2nd Layer leather processing, and maintains a complete database of all your invoice records."))
    
    st.markdown(get_text("getting_started.what_can_do", "### What can it do for you?"))
    features = get_text("getting_started.features", [])
    for feature in features:
        st.markdown(f"- {feature}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(get_text("getting_started.who_for", "🎯 Who is this for?"))
        who_list = get_text("getting_started.who_list", [])
        for item in who_list:
            st.markdown(f"- {item}")
    
    with col2:
        st.subheader(get_text("getting_started.benefits", "⚡ Key Benefits"))
        benefits_list = get_text("getting_started.benefits_list", [])
        for benefit in benefits_list:
            st.markdown(f"- {benefit}")
    
    st.markdown("---")
    
    st.subheader(get_text("getting_started.system_pages_overview", "🗂️ System Pages Overview"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(get_text("getting_started.main_pages_title", "#### 📄 Main Pages:"))
        main_pages = get_text("getting_started.main_pages_list", [
            "**`0_Generate Invoice.py`** - Main invoice generation (both leather types)",
            "**`1_Verify_Data_To_Insert.py`** - Manual data entry and amendments", 
            "**`997_Invoice Explorer.py`** - View and manage existing invoices"
        ])
        for page in main_pages:
            st.markdown(f"- {page}")
    
    with col2:
        st.markdown(get_text("getting_started.admin_pages_title", "#### 🛠️ Admin Pages:"))
        admin_pages = get_text("getting_started.admin_pages_list", [
            "**`998_Database_Manager.py`** - Backup and database management",
            "**`999_Guide.py`** - This user guide (current page)"
        ])
        for page in admin_pages:
            st.markdown(f"- {page}")
    
    st.info(get_text("getting_started.start_here_tip", "💡 **Start Here:** Most users should begin with `0_Generate Invoice.py` for processing Excel files."))
    
    st.markdown("---")
    
    st.subheader(get_text("getting_started.quick_start", "🚀 Quick Start - 3 Simple Steps"))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(get_text("getting_started.step1_title", "### Step 1: Prepare Your Excel File"))
        st.markdown(get_text("getting_started.step1_desc", "- Use your existing Excel format..."))
    
    with col2:
        st.markdown(get_text("getting_started.step2_title", "### Step 2: Upload & Process"))
        st.markdown(get_text("getting_started.step2_desc", "- Go to `0_Generate Invoice.py` page\n- Choose the appropriate tab (High-Quality or 2nd Layer)\n- Upload your Excel file\n- System automatically processes and validates"))
    
    with col3:
        st.markdown(get_text("getting_started.step3_title", "### Step 3: Review & Download"))
        st.markdown(get_text("getting_started.step3_desc", "- Review validation results\n- Add any optional overrides\n- Select invoice versions to generate\n- Download your completed invoices"))

with tab2:
    st.header(get_text("dashboard.title", "📊 Understanding the Dashboard"))
    
    st.markdown(get_text("dashboard.desc", "The Dashboard is your main control center..."))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(get_text("dashboard.key_metrics", "📈 Key Metrics"))
        metrics_list = get_text("dashboard.metrics_list", [])
        for metric in metrics_list:
            st.markdown(f"- {metric}")
        
        st.subheader(get_text("dashboard.date_filtering", "📅 Date Filtering"))
        date_filter_list = get_text("dashboard.date_filter_list", [])
        for filter_item in date_filter_list:
            st.markdown(f"- {filter_item}")
    
    with col2:
        st.subheader(get_text("dashboard.charts_graphs", "📊 Charts & Graphs"))
        charts_list = get_text("dashboard.charts_list", [])
        for chart in charts_list:
            st.markdown(f"- {chart}")
        
        st.subheader(get_text("dashboard.what_to_look", "🔍 What to Look For"))
        look_for_list = get_text("dashboard.look_for_list", [])
        for look_item in look_for_list:
            st.markdown(f"- {look_item}")

with tab3:
    st.header(get_text("adding_invoices.title", "➕ Adding New Invoices"))
    
    st.markdown(get_text("adding_invoices.desc", "The unified invoice generation system handles both High-Quality and 2nd Layer leather processing in one convenient interface."))
    
    st.subheader(get_text("adding_invoices.unified_interface", "🎯 Unified Invoice Generation Interface"))
    st.markdown(get_text("adding_invoices.location", "**Location:** Go to `0_Generate Invoice.py` page"))
    st.markdown(get_text("adding_invoices.tabs_description", "This page contains **two tabs** for different leather types:"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(get_text("adding_invoices.high_quality_tab", "#### 📋 Tab 1: For High-Quality Leather"))
        st.markdown(get_text("adding_invoices.process_label", "**Process:**"))
        high_quality_steps = get_text("adding_invoices.high_quality_steps", [
            "Upload your Excel file (.xlsx format)",
            "System automatically processes and validates data", 
            "Review validation results and missing fields",
            "Add optional overrides (Invoice No, Ref, Date, Containers)",
            "Select invoice versions (Normal, DAF, Combine)",
            "Generate and download final invoices as ZIP"
        ])
        for i, step in enumerate(high_quality_steps, 1):
            st.markdown(f"{i}. {step}")
        
        st.info(get_text("adding_invoices.high_quality_best_for", "✅ **Best for:** Complex invoices with multiple product lines"))
    
    with col2:
        st.markdown(get_text("adding_invoices.second_layer_tab", "#### 📋 Tab 2: For 2nd Layer Leather"))
        st.markdown(get_text("adding_invoices.process_label", "**Process:**"))
        second_layer_steps = get_text("adding_invoices.second_layer_steps", [
            "Upload your Excel file (.xlsx format)",
            "Enter invoice details (Reference, Date, Unit Price)",
            "System processes file and creates JSON data",
            "Review invoice summary with metrics",
            "Download generated documents and data as ZIP"
        ])
        for i, step in enumerate(second_layer_steps, 1):
            st.markdown(f"{i}. {step}")
        
        st.info(get_text("adding_invoices.second_layer_best_for", "✅ **Best for:** Simpler invoices with aggregated data"))
    
    st.markdown("---")
    
    st.subheader(get_text("adding_invoices.key_features", "🌟 Key Features of the Unified System"))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(get_text("adding_invoices.automatic_processing", "#### ⚡ Automatic Processing"))
        automatic_features = get_text("adding_invoices.automatic_features", [
            "- Real-time validation",
            "- Cambodia timezone support",
            "- Duplicate detection", 
            "- Smart invoice reference suggestions"
        ])
        for feature in automatic_features:
            st.markdown(feature)
    
    with col2:
        st.markdown(get_text("adding_invoices.flexible_overrides", "#### 🎛️ Flexible Overrides"))
        flexible_features = get_text("adding_invoices.flexible_features", [
            "- Custom invoice numbers",
            "- Date modifications",
            "- Container/truck information",
            "- Multiple output formats"
        ])
        for feature in flexible_features:
            st.markdown(feature)
    
    with col3:
        st.markdown(get_text("adding_invoices.complete_output", "#### 📦 Complete Output"))
        complete_features = get_text("adding_invoices.complete_features", [
            "- Multiple invoice versions",
            "- JSON data files", 
            "- ZIP packaging",
            "- Ready for distribution"
        ])
        for feature in complete_features:
            st.markdown(feature)
    
    st.markdown("---")
    
    st.subheader(get_text("adding_invoices.verification_title", "📋 Data Verification Process"))
    st.markdown(get_text("adding_invoices.verification_desc", "After processing, the system provides comprehensive validation:"))
    
    verification_features = get_text("adding_invoices.verification_features", [
        "**Automatic Field Validation:** System checks for all required data fields",
        "**Missing Data Alerts:** Clear warnings for any missing information", 
        "**Database Duplicate Check:** Prevents duplicate invoice numbers/references",
        "**Real-time Preview:** See exactly what will be generated before final processing",
        "**Cambodia Timezone:** All timestamps use Asia/Phnom_Penh timezone"
    ])
    for feature in verification_features:
        st.markdown(f"- {feature}")
    
    st.success(get_text("adding_invoices.pro_tip", "💡 **Pro Tip:** The unified interface eliminates the need to switch between different pages - everything is handled in one place!"))

with tab4:
    st.header(get_text("managing_data.title", "✏️ Managing Your Invoice Data"))
    
    st.markdown(get_text("managing_data.system_overview", "The system provides comprehensive tools for viewing, editing, and managing your invoice database. Here's how to use each component:"))
    
    st.markdown("---")
    
    st.subheader(get_text("managing_data.viewing_database", "🔍 Viewing Your Database"))
    st.markdown(get_text("managing_data.viewing_desc", "The `997_Invoice Explorer.py` page lets you:"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(get_text("managing_data.main_features", "#### 📊 Main Features:"))
        viewing_features = get_text("managing_data.viewing_features", [])
        for feature in viewing_features:
            st.markdown(f"- {feature}")
    
    with col2:
        st.markdown("#### 📤 Export Options:")
        export_features = get_text("managing_data.export_features", [
            "**Excel Export:** Download filtered data as .xlsx",
            "**CSV Export:** Export for external analysis",
            "**Summarized Reports:** Aggregate data by invoice",
            "**Detailed Reports:** Complete line-item data",
            "**Date Range Exports:** Export specific time periods"
        ])
        for feature in export_features:
            st.markdown(f"- {feature}")
    
    st.info("🕐 **Cambodia Timezone:** All timestamps display in Asia/Phnom_Penh timezone regardless of server location!")
    
    st.markdown(get_text("managing_data.action_buttons", "#### 🎛️ Invoice Action Buttons"))
    st.markdown(get_text("managing_data.action_buttons_desc", "Each invoice in the summary table has three action buttons:"))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(get_text("managing_data.view_button", "**📄 View Line Items**"))
        view_features = get_text("managing_data.view_features", [
            "- Shows detailed breakdown",
            "- All product lines displayed", 
            "- Read-only view",
            "- Click again to hide"
        ])
        for feature in view_features:
            st.markdown(feature)
    
    with col2:
        st.markdown(get_text("managing_data.edit_button", "**✏️ Edit This Invoice**"))
        edit_button_features = get_text("managing_data.edit_button_features", [
            "- Opens interactive editor",
            "- Modify any field values",
            "- Add/remove product lines", 
            "- Save changes to database"
        ])
        for feature in edit_button_features:
            st.markdown(feature)
    
    with col3:
        st.markdown(get_text("managing_data.void_button", "**🚫 Void Invoice**"))
        void_button_features = get_text("managing_data.void_button_features", [
            "- Marks invoice as cancelled",
            "- Requires confirmation",
            "- Excludes from totals",
            "- Can be reactivated later"
        ])
        for feature in void_button_features:
            st.markdown(feature)
    
    st.markdown("---")
    
    st.subheader(get_text("managing_data.direct_editing", "✏️ Direct Invoice Editing"))
    st.markdown(get_text("managing_data.direct_editing_location", "**Location:** `997_Invoice Explorer.py` (Invoice Summary Tab)"))
    
    st.markdown(get_text("managing_data.direct_editing_desc", "**The system provides powerful direct editing capabilities right in the Invoice Explorer!**"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(get_text("managing_data.how_to_edit", "#### 🎯 How to Edit Invoices:"))
        edit_steps = get_text("managing_data.edit_steps_detailed", [])
        for i, step in enumerate(edit_steps, 1):
            st.markdown(f"{i}. {step}")
    
    with col2:
        st.markdown(get_text("managing_data.edit_features", "#### ⚡ Edit Features:"))
        edit_features_list = get_text("managing_data.edit_features_list", [])
        for feature in edit_features_list:
            st.markdown(f"- {feature}")
    
    st.success("💡 **Pro Tip:** This is the fastest way to make quick corrections to existing invoices!")
    
    st.markdown("---")
    
    st.subheader(get_text("managing_data.json_upload", "📁 Adding & Amending via JSON Upload"))
    st.markdown(get_text("managing_data.json_upload_location", "**Location:** `1_Verify_Data_To_Insert.py`"))
    
    st.markdown("This page handles two main scenarios:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(get_text("managing_data.adding_new_data", "#### 🆕 Adding New Data:"))
        st.markdown(get_text("managing_data.adding_when_to_use", "**When to use:** You have JSON data from invoice generation that needs to be added to the database."))
        
        adding_steps = get_text("managing_data.adding_steps", [])
        for i, step in enumerate(adding_steps, 1):
            st.markdown(f"{i}. {step}")
    
    with col2:
        st.markdown(get_text("managing_data.amending_data", "#### 🔄 Amending Existing Data:"))
        st.markdown(get_text("managing_data.amending_when_to_use", "**When to use:** You need to update or correct existing invoice information."))
        
        amending_steps = get_text("managing_data.amending_steps", [])
        for i, step in enumerate(amending_steps, 1):
            st.markdown(f"{i}. {step}")
    
    st.warning(get_text("managing_data.amendment_warning", "⚠️ **Important:** Amendments update existing records. The system automatically archives the original data for safety."))
    
    st.markdown("---")
    
    st.subheader(get_text("managing_data.reprocessing", "🔄 Alternative: Re-processing with Overrides"))
    st.markdown(get_text("managing_data.reprocessing_location", "**Location:** `0_Generate Invoice.py`"))
    
    st.markdown(get_text("managing_data.reprocessing_when_to_use", "**When to use:** You want to regenerate invoices with different information (numbers, dates, containers)."))
    
    reprocess_steps = get_text("managing_data.reprocessing_steps", [])
    for i, step in enumerate(reprocess_steps, 1):
        st.markdown(f"{i}. {step}")
    
    st.info(get_text("managing_data.reprocessing_tip", "💡 **Pro Tip:** This method generates new files but doesn't automatically update the database. Use the Verify page to add the new data."))
    
    st.markdown("---")
    
    st.subheader(get_text("managing_data.status_management", "🗑️ Managing Invoice Status"))
    st.markdown(get_text("managing_data.voiding_desc", "**Location:** `997_Invoice Explorer.py` (Invoice Summary Tab)"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(get_text("managing_data.voiding_invoices_detailed", "#### 🚫 Voiding Invoices:"))
        st.markdown("**The system has built-in void functionality:**")
        voiding_steps = get_text("managing_data.voiding_steps", [])
        for i, step in enumerate(voiding_steps, 1):
            st.markdown(f"{i}. {step}")
        
        st.warning(get_text("managing_data.voiding_note", "⚠️ **Important:** Voiding is reversible - you can reactivate voided invoices if needed."))
    
    with col2:
        st.markdown(get_text("managing_data.status_tracking", "#### ♻️ Status Management:"))
        status_info = get_text("managing_data.status_info", [])
        for info in status_info:
            st.markdown(f"- {info}")
    
    st.info("💡 **Use Cases:** Void invoices for cancellations, corrections, or duplicate entries. Reactivate if voided by mistake.")
    
    st.markdown("---")
    
    st.subheader(get_text("managing_data.database_management", "💾 Database Management & Backup"))
    st.markdown(get_text("managing_data.database_location", "**Location:** `998_Database_Manager.py`"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(get_text("managing_data.backup_features", "#### 🔒 Backup Features:"))
        backup_features_list = get_text("managing_data.backup_features_list", [])
        for feature in backup_features_list:
            st.markdown(f"- {feature}")
        
        st.warning(get_text("managing_data.admin_warning", "⚠️ **Admin Only:** Backup operations require administrator access."))
    
    with col2:
        st.markdown(get_text("managing_data.safety_features", "#### 🛡️ Safety Features:"))
        safety_features_list = get_text("managing_data.safety_features_list", [])
        for feature in safety_features_list:
            st.markdown(f"- {feature}")
    
    st.success(get_text("managing_data.best_practice", "💡 **Best Practice:** Create regular backups before making major changes to your invoice database!"))

with tab5:
    st.header(get_text("header_mapping.title", "🔧 Excel Header Mapping Guide"))
    
    st.markdown(get_text("header_mapping.desc", "CRITICAL: Without proper header mapping..."))
    
    st.markdown(get_text("header_mapping.what_is_mapping", "### What is Header Mapping?"))
    st.markdown(get_text("header_mapping.mapping_desc", "The system needs to identify which columns..."))
    
    st.markdown(get_text("header_mapping.required_headers", "📋 Required Headers & Their Mappings"))
    st.markdown(get_text("header_mapping.required_headers_desc", "Your Excel file must contain these data types..."))
    
    header_mappings = get_text("header_mapping.header_mappings", [])
    for mapping in header_mappings:
        st.markdown(f"- {mapping}")
    
    st.markdown("---")
    
    st.subheader(get_text("header_mapping.common_issues_mapping", "⚠️ Common Header Issues"))
    mapping_issues = get_text("header_mapping.mapping_issues", [])
    for issue in mapping_issues:
        st.markdown(f"- {issue}")
    
    st.markdown("---")
    
    st.subheader(get_text("header_mapping.solutions_title", "✅ Solutions When Headers Don't Match"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(get_text("header_mapping.solution_option1", "#### Option 1: Edit Your Excel File (Recommended)"))
        solution1_steps = get_text("header_mapping.solution1_steps", [])
        for i, step in enumerate(solution1_steps, 1):
            st.markdown(f"{i}. {step}")
    
    with col2:
        st.markdown(get_text("header_mapping.solution_option2", "#### Option 2: Report to Administrator"))
        solution2_steps = get_text("header_mapping.solution2_steps", [])
        for i, step in enumerate(solution2_steps, 1):
            st.markdown(f"{i}. {step}")
    
    st.markdown("---")
    
    st.subheader(get_text("header_mapping.example_mapping", "📝 Example Header Mapping"))
    st.markdown(get_text("header_mapping.example_desc", "Here's an example of how to map..."))
    
    example_table = get_text("header_mapping.example_table", [])
    for example in example_table:
        st.markdown(f"- {example}")
    
    st.markdown("---")
    
    st.subheader(get_text("header_mapping.best_practices_headers", "💡 Best Practices for Excel Headers"))
    header_best_practices = get_text("header_mapping.header_best_practices", [])
    for practice in header_best_practices:
        st.markdown(f"- {practice}")
    
    st.markdown("---")
    
    st.subheader(get_text("header_mapping.admin_contact", "📞 Need Help with Mapping?"))
    admin_help = get_text("header_mapping.admin_help", [])
    for help_item in admin_help:
        st.markdown(f"- {help_item}")

with tab6:
    st.header(get_text("troubleshooting.title", "❓ Troubleshooting & FAQ"))
    
    st.subheader(get_text("troubleshooting.common_issues", "🚨 Common Issues"))
    
    with st.expander(get_text("troubleshooting.issue0_title", "🔧 MOST COMMON: Headers not recognized"), expanded=True):
        st.markdown(get_text("troubleshooting.issue0_desc", "**90% of problems are caused by incorrect column headers!**"))
        st.markdown(get_text("troubleshooting.issue0_solution", "**SOLUTION:** Check the Header Mapping tab in this guide for the exact headers needed."))
        st.markdown(get_text("troubleshooting.hq_headers_label", "**Required headers for High-Quality Leather:**"))
        hq_headers = get_text("troubleshooting.hq_headers_list", ["inv_no", "inv_date", "inv_ref", "po", "item", "pcs", "sqft", "pallet_count", "unit", "amount", "net", "gross", "cbm", "production_order_no"])
        for header in hq_headers:
            st.markdown(f"- `{header}`")
        st.markdown(get_text("troubleshooting.second_layer_note", "**For 2nd Layer Leather:** Headers are more flexible but must include PO, item descriptions, quantities, and weights."))
        st.info(get_text("troubleshooting.solution_tip", "💡 This solves 90% of processing problems!"))
    
    with st.expander(get_text("troubleshooting.issue1_title", "❌ My Excel file won't process")):
        st.markdown(get_text("troubleshooting.issue1_causes", "**Possible causes:**"))
        issue1_cause_list = get_text("troubleshooting.issue1_cause_list", [])
        for cause in issue1_cause_list:
            st.markdown(f"- {cause}")
        
        st.markdown(get_text("troubleshooting.issue1_solutions", "**Solutions:**"))
        issue1_solution_list = get_text("troubleshooting.issue1_solution_list", [])
        for solution in issue1_solution_list:
            st.markdown(f"- {solution}")
    
    with st.expander(get_text("troubleshooting.issue2_title", "⏳ Processing is taking too long")):
        st.markdown(get_text("troubleshooting.issue2_causes", "**This can happen when:**"))
        issue2_cause_list = get_text("troubleshooting.issue2_cause_list", [])
        for cause in issue2_cause_list:
            st.markdown(f"- {cause}")
        
        st.markdown(get_text("troubleshooting.issue2_solutions", "**Solutions:**"))
        issue2_solution_list = get_text("troubleshooting.issue2_solution_list", [])
        for solution in issue2_solution_list:
            st.markdown(f"- {solution}")
    
    with st.expander(get_text("troubleshooting.issue3_title", "🔍 I can't find my invoice")):
        st.markdown(get_text("troubleshooting.issue3_causes", "**Check these things:**"))
        issue3_cause_list = get_text("troubleshooting.issue3_cause_list", [])
        for cause in issue3_cause_list:
            st.markdown(f"- {cause}")
    
    with st.expander(get_text("troubleshooting.issue4_title", "💾 My data disappeared")):
        st.markdown(get_text("troubleshooting.issue4_desc", "**Don't panic! Your data might be:**"))
        issue4_cause_list = get_text("troubleshooting.issue4_cause_list", [])
        for cause in issue4_cause_list:
            st.markdown(f"- {cause}")
        
        st.markdown(get_text("troubleshooting.issue4_recovery", "**Recovery steps:**"))
        issue4_recovery_list = get_text("troubleshooting.issue4_recovery_list", [])
        for step in issue4_recovery_list:
            st.markdown(f"- {step}")
    
    with st.expander(get_text("troubleshooting.issue5_title", "🚫 No data processed / Empty results")):
        st.markdown(get_text("troubleshooting.issue5_desc", "**Excel file uploads but no invoices are created:**"))
        issue5_cause_list = get_text("troubleshooting.issue5_cause_list", [])
        for cause in issue5_cause_list:
            st.markdown(f"- {cause}")
        
        st.markdown(get_text("troubleshooting.issue5_solutions", "**SOLUTION:**"))
        issue5_solution_list = get_text("troubleshooting.issue5_solution_list", [])
        for solution in issue5_solution_list:
            st.markdown(f"- {solution}")
    
    st.subheader(get_text("troubleshooting.getting_help", "📞 Getting Help"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(get_text("troubleshooting.before_help", "#### Before Asking for Help:"))
        before_help_list = get_text("troubleshooting.before_help_list", [])
        for i, item in enumerate(before_help_list, 1):
            st.markdown(f"{i}. {item}")
    
    with col2:
        st.markdown(get_text("troubleshooting.when_contacting", "#### When Contacting Support:"))
        when_contacting_list = get_text("troubleshooting.when_contacting_list", [])
        for item in when_contacting_list:
            st.markdown(f"- {item}")
    
    st.markdown("---")
    
    st.subheader(get_text("troubleshooting.pro_tips", "💡 Pro Tips for Success"))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(get_text("troubleshooting.excel_tips", "#### Excel File Tips:"))
        excel_tips_list = get_text("troubleshooting.excel_tips_list", [])
        for tip in excel_tips_list:
            st.markdown(f"- {tip}")
    
    with col2:
        st.markdown(get_text("troubleshooting.data_tips", "#### Data Management:"))
        data_tips_list = get_text("troubleshooting.data_tips_list", [])
        for tip in data_tips_list:
            st.markdown(f"- {tip}")
    
    with col3:
        st.markdown(get_text("troubleshooting.system_tips", "#### System Usage:"))
        system_tips_list = get_text("troubleshooting.system_tips_list", [])
        for tip in system_tips_list:
            st.markdown(f"- {tip}")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>{get_text("footer.help_contact", "📧 Need more help? Contact your system administrator")}</p>
    <p>{get_text("footer.last_updated", "🔄 Last updated: JULY 2025")}</p>
</div>
""", unsafe_allow_html=True)
