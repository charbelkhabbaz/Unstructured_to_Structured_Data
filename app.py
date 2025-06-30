import streamlit as st
import os
import tempfile
import time
from data_extractors import DataExtractionManager
from ai_processor import DataStructuringPipeline
from utils import FileUtils, DataFormatter, DataExporter

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ============================================================================
# PAGE CONFIGURATION & STYLING
# ============================================================================
st.set_page_config(
    page_title="AI Data Structuring Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for theme persistence
if 'color_theme' not in st.session_state:
    st.session_state.color_theme = 'custom_blue'

# Color theme definitions
COLOR_THEMES = {
    'custom_blue': {
        'name': 'Pure Black & Grey Theme',
        'main_bg': 'linear-gradient(135deg, #000000 0%, #1a1a1a 50%, #000000 100%)',
        'sidebar_bg': 'linear-gradient(180deg, #000000 0%, #1a1a1a 100%)',
        'card_bg': 'rgba(30, 30, 30, 0.95)',
        'text_color': '#e0e0e0',
        'sidebar_text': '#e0e0e0',
        'primary_color': '#808080',
        'secondary_bg': '#404040'
    },
    'dark_blue': {
        'name': 'Professional Dark Blue',
        'main_bg': 'linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #1e3c72 100%)',
        'sidebar_bg': 'linear-gradient(180deg, #1e3c72 0%, #2a5298 100%)',
        'card_bg': 'rgba(255, 255, 255, 0.95)',
        'text_color': 'rgba(255, 255, 255, 0.9)',
        'sidebar_text': 'white',
        'primary_color': '#667eea',
        'secondary_bg': '#2a5298'
    },
    'dark_gray': {
        'name': 'Corporate Dark Gray',
        'main_bg': 'linear-gradient(135deg, #2c3e50 0%, #34495e 50%, #2c3e50 100%)',
        'sidebar_bg': 'linear-gradient(180deg, #2c3e50 0%, #34495e 100%)',
        'card_bg': 'rgba(255, 255, 255, 0.95)',
        'text_color': 'rgba(255, 255, 255, 0.9)',
        'sidebar_text': 'white',
        'primary_color': '#667eea',
        'secondary_bg': '#34495e'
    },
    'dark_green': {
        'name': 'Business Dark Green',
        'main_bg': 'linear-gradient(135deg, #1a4d2e 0%, #2d5a3d 50%, #1a4d2e 100%)',
        'sidebar_bg': 'linear-gradient(180deg, #1a4d2e 0%, #2d5a3d 100%)',
        'card_bg': 'rgba(255, 255, 255, 0.95)',
        'text_color': 'rgba(255, 255, 255, 0.9)',
        'sidebar_text': 'white',
        'primary_color': '#667eea',
        'secondary_bg': '#2d5a3d'
    },
    'light_blue': {
        'name': 'Light Professional Blue',
        'main_bg': 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 50%, #e3f2fd 100%)',
        'sidebar_bg': 'linear-gradient(180deg, #1976d2 0%, #1565c0 100%)',
        'card_bg': 'rgba(255, 255, 255, 0.95)',
        'text_color': 'rgba(0, 0, 0, 0.8)',
        'sidebar_text': 'white',
        'primary_color': '#667eea',
        'secondary_bg': '#1565c0'
    },
    'classic_white': {
        'name': 'Classic White',
        'main_bg': 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 50%, #f8f9fa 100%)',
        'sidebar_bg': 'linear-gradient(180deg, #6c757d 0%, #495057 100%)',
        'card_bg': 'rgba(255, 255, 255, 0.95)',
        'text_color': 'rgba(0, 0, 0, 0.8)',
        'sidebar_text': 'white',
        'primary_color': '#667eea',
        'secondary_bg': '#495057'
    }
}

# Get current theme
current_theme = COLOR_THEMES[st.session_state.color_theme]

# Load base CSS from file
load_css("style.css")

# Inject theme-specific variables
st.markdown(f"""
<style>
    :root {{
        --main-bg: {current_theme['main_bg']};
        --sidebar-bg: {current_theme['sidebar_bg']};
        --card-bg: {current_theme['card_bg']};
        --text-color: {current_theme['text_color']};
        --sidebar-text: {current_theme['sidebar_text']};
        --primary-color: {current_theme['primary_color']};
        --secondary-bg: {current_theme['secondary_bg']};
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER SECTION
# ============================================================================
st.markdown("""
<div class="main-header">
    <h1>🚀 AI Data Structuring Platform</h1>
    <p>Transform unstructured documents into structured, actionable data with advanced AI processing</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR: Enhanced Upload & Options
# ============================================================================
with st.sidebar:
    st.markdown("### 📁 File Upload")
    
    # Enhanced file uploader with better styling
    uploaded_file = st.file_uploader(
        "Choose a file to process",
        type=["pdf", "png", "jpg", "jpeg", "tiff", "bmp", "txt", "csv", "xlsx", "xls"],
        help="Supported formats: PDF, Images (PNG, JPG, TIFF, BMP), Text files, CSV, Excel"
    )
    
    if uploaded_file:
        st.success(f"✅ {uploaded_file.name} uploaded successfully!")
        
        # File info display
        file_size = len(uploaded_file.getvalue()) / 1024  # KB
        st.info(f"📊 File size: {file_size:.1f} KB")
    
    st.markdown("---")
    st.markdown("### ⚙️ Processing Options")
    
    # Output format selector with icons
    output_formats = st.multiselect(
    "📤 Export Formats",
    ["json", "csv", "excel", "summary"],
    default=["json", "summary"],
    help="Choose the formats for exporting the structured data"
)
    
    # Advanced options expander
    with st.expander("🔧 Advanced Options", expanded=False):
        custom_prompt = st.text_area(
            "🤖 Custom AI Prompt",
            placeholder="Enter custom instructions for the AI model...",
            help="Override default AI instructions for specific use cases"
        )
        
        # Processing speed options
        processing_mode = st.selectbox(
            "⚡ Processing Mode",
            ["Balanced", "Fast", "High Quality"],
            index=0,
            help="Choose processing speed vs quality trade-off"
        )
    
    st.markdown("---")
    st.markdown("### 🎨 Theme Settings")
    
    # Theme selector
    theme_options = {theme['name']: key for key, theme in COLOR_THEMES.items()}
    selected_theme_name = st.selectbox(
        "🎨 Choose Theme",
        options=list(theme_options.keys()),
        index=list(theme_options.values()).index(st.session_state.color_theme),
        help="Select your preferred color theme"
    )
    
    # Update theme if changed
    if theme_options[selected_theme_name] != st.session_state.color_theme:
        st.session_state.color_theme = theme_options[selected_theme_name]
        st.success(f"✅ Theme changed to: {selected_theme_name}")
        st.rerun()  # Rerun to apply new theme
    
    # Show current theme info
    current_theme_info = COLOR_THEMES[st.session_state.color_theme]
    st.info(f"🎨 Current: {current_theme_info['name']}")
    
    # Theme preview
    st.markdown("**Theme Preview:**")
    theme_preview = f"""
    <div style="
        background: {current_theme_info['main_bg']};
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        border: 2px solid rgba(255,255,255,0.3);
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: {current_theme_info['text_color']};
        font-weight: bold;
    ">
        {current_theme_info['name']}
    </div>
    """
    st.markdown(theme_preview, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Process button with enhanced styling
    process_btn = st.button(
        "🚀 Process Document",
        type="primary",
        use_container_width=True
    )

# ============================================================================
# MAIN CONTENT AREA
# ============================================================================
if uploaded_file and process_btn:
    # Create columns for better layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: File Preparation
        status_text.text("📋 Preparing file for processing...")
        progress_bar.progress(10)
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.read())
            file_path = tmp_file.name
        
        time.sleep(0.5)  # Small delay for UX
        
        # Step 2: File Validation
        status_text.text("🔍 Validating file...")
        progress_bar.progress(20)
        
        validation = FileUtils.validate_file(file_path)
        if not validation['valid']:
            st.error(f"❌ File validation error: {validation['error']}")
            progress_bar.progress(0)
        else:
            file_type = validation['file_type']
            st.success(f"✅ File validated: {uploaded_file.name} ({file_type.upper()})")
            
            time.sleep(0.5)
            
            # Step 3: Data Extraction
            status_text.text("📖 Extracting data from document...")
            progress_bar.progress(40)
            
            # Use caching for faster extraction
            @st.cache_data
            def extract_data_cached(file_path, file_type):
                extractor = DataExtractionManager()
                return extractor.extract_data(file_path, file_type)
            
            extracted_data = extract_data_cached(file_path, file_type)
            
            if 'error' in extracted_data:
                st.error(f"❌ Extraction error: {extracted_data['error']}")
                progress_bar.progress(0)
            else:
                st.success("✅ Data extraction completed!")
                progress_bar.progress(60)
                
                # Display extraction metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📄 Pages/Items", extracted_data.get('pages', 'N/A'))
                with col2:
                    st.metric("📝 Text Length", len(extracted_data.get('text', '')))
                    st.caption(f"{len(extracted_data.get('text', '')):,} characters")
                with col3:
                    st.metric("📊 File Size", f"{file_size:.1f} KB")
                with col4:
                    st.metric("🔧 Method", extracted_data.get('extraction_method', 'N/A'))
                
                time.sleep(0.5)
                
                # Step 4: AI Processing
                status_text.text("🤖 Processing with AI...")
                progress_bar.progress(80)
                
                # Use caching for AI processing
                @st.cache_data
                def process_with_ai_cached(extracted_data, output_formats, custom_prompt):
                    pipeline = DataStructuringPipeline()
                    return pipeline.process_document(
                        extracted_data,
                        output_format=output_formats,
                        custom_prompt=custom_prompt if custom_prompt.strip() else None
                    )
                
                results = process_with_ai_cached(extracted_data, output_formats, custom_prompt)
                
                if not results.get('success'):
                    st.error(f"❌ AI processing error: {results.get('error')}")
                    progress_bar.progress(0)
                else:
                    # Complete processing
                    status_text.text("✅ Processing completed!")
                    progress_bar.progress(100)
                    time.sleep(0.5)
                    status_text.empty()
                    progress_bar.empty()
                    
                    # ============================================================================
                    # RESULTS DISPLAY
                    # ============================================================================
                    st.markdown("## 📊 Processing Results")
                    
                    # Results overview in tabs
                    tab1, tab2, tab3, tab4, tab5 = st.tabs([
                        "📋 Structured Data", 
                        "🏷️ Entities", 
                        "📄 Classification", 
                        "📝 Summary", 
                        "💾 Export"
                    ])
                    
                    with tab1:
                        st.markdown("### Structured Data")
                        if "json" in output_formats:
                            st.json(results['structured_data'])
                        else:
                            st.code(results['structured_data'])
                    
                    with tab2:
                        st.markdown("### Named Entities")
                        entities_display = DataFormatter.format_entities_for_display(results.get('entities', {}))
                        st.code(entities_display)
                        
                        # Entity metrics
                        if results.get('entities') and not 'error' in results.get('entities', {}):
                            entities = results['entities']
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("👥 People", len(entities.get('persons', [])))
                            with col2:
                                st.metric("🏢 Organizations", len(entities.get('organizations', [])))
                            with col3:
                                st.metric("📍 Locations", len(entities.get('locations', [])))
                            with col4:
                                st.metric("📅 Dates", len(entities.get('dates', [])))
                    
                    with tab3:
                        st.markdown("### Document Classification")
                        classification_display = DataFormatter.format_classification_for_display(results.get('classification', {}))
                        st.code(classification_display)
                        
                        # Classification metrics
                        if results.get('classification') and not 'error' in results.get('classification', {}):
                            classification = results['classification']
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("📄 Document Type", classification.get('document_type', 'Unknown'))
                            with col2:
                                st.metric("🎯 Confidence", f"{classification.get('confidence', 0):.1%}")
                    
                    with tab4:
                        st.markdown("### Document Summary")
                        summary = results.get('summary', '')
                        st.info(summary)
                        
                        # Summary metrics
                        word_count = len(summary.split())
                        st.metric("📝 Summary Length", f"{word_count} words")
                    
                    with tab5:
                        st.markdown("### Export Results")
                        
                        # Export options
                        export_dir = tempfile.mkdtemp()
                        base_filename = os.path.splitext(os.path.basename(uploaded_file.name))[0]
                        exported_files = DataExporter.export_results(results, export_dir, base_filename, output_formats)
                        
                        # Export buttons in a grid
                        if exported_files:
                            st.success("✅ Files ready for download!")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                for label, path in list(exported_files.items())[:3]:
                                    st.download_button(
                                        label=f"📥 Download {label.upper()}",
                                        data=open(path, 'rb').read(),
                                        file_name=os.path.basename(path),
                                        mime="application/octet-stream"
                                    )
                            
                            with col2:
                                for label, path in list(exported_files.items())[3:]:
                                    st.download_button(
                                        label=f"📥 Download {label.upper()}",
                                        data=open(path, 'rb').read(),
                                        file_name=os.path.basename(path),
                                        mime="application/octet-stream"
                                    )
                        else:
                            st.warning("⚠️ No files available for export")
    
    # Clean up temporary file
    try:
        os.remove(file_path)
    except:
        pass

elif not uploaded_file:
    # ============================================================================
    # WELCOME SECTION
    # ============================================================================
    st.markdown("## 🎯 Welcome to AI Data Structuring Platform")
    
    # Feature overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ✨ Key Features
        
        🚀 **Fast Processing**
        - Optimized extraction algorithms
        - Cached AI processing
        - Real-time progress tracking
        
        🤖 **Advanced AI**
        - DeepSeek AI model integration
        - Multi-format output (JSON, CSV, Table)
        - Entity extraction & classification
        
        📁 **Multi-Format Support**
        - PDF documents
        - Images (OCR)
        - Text files
        - Spreadsheets (CSV, Excel)
        
        💾 **Export Options**
        - Multiple output formats
        - Batch processing ready
        - Professional formatting
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Processing Capabilities
        
        **Document Types:**
        - 📄 Invoices & Receipts
        - 📋 Forms & Applications
        - 📝 Reports & Documents
        - 📧 Emails & Correspondence
        - 📊 Data Tables & Lists
        
        **AI Analysis:**
        - 🏷️ Named Entity Recognition
        - 📄 Document Classification
        - 📝 Automatic Summarization
        - 🔍 Data Structure Detection
        
        **Output Formats:**
        - 📋 Structured JSON
        - 📊 CSV Data Tables
        - 📋 Formatted Tables
        - 📄 Complete Reports
        """)
    
    # Quick start guide
    st.markdown("---")
    st.markdown("### 🚀 Quick Start")
    st.info("""
    1. **Upload** a document using the sidebar
    2. **Select** your preferred output format
    3. **Configure** any advanced options if needed
    4. **Process** your document with one click
    5. **Download** your structured results
    """)

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; padding: 1rem;">
    <p>🚀 Powered by DeepSeek AI • Built with Streamlit • Professional Data Structuring Platform</p>
</div>
""", unsafe_allow_html=True) 