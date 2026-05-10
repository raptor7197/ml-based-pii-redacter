"""
Smart-Redact Streamlit Frontend
PII-Safe interface with tabbed layout, masked preview, and export functionality
"""

import base64
import json
import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Smart-Redact - PII Detection & Redaction",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Backend API configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .download-btn {
        display: inline-block;
        padding: 0.75rem 1.5rem;
        background-color: #1f77b4;
        color: white !important;
        text-decoration: none;
        border-radius: 0.5rem;
        font-weight: 600;
        text-align: center;
    }
    .download-btn:hover {
        background-color: #155a8a;
    }
    .masked-value {
        font-family: monospace;
        background-color: #f0f0f0;
        padding: 0.2rem 0.4rem;
        border-radius: 0.25rem;
    }
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 0.5rem 0;
    }
    .preview-container {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        background-color: #fafafa;
    }
    .original-masked {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
    .redacted-view {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    div[data-testid="stTab"] {
        font-size: 1.1rem;
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ==================== HELPER FUNCTIONS ====================


def check_backend_health():
    """Check if the backend service is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        return (
            response.status_code == 200,
            response.json() if response.status_code == 200 else None,
        )
    except:
        return False, None


def upload_file_to_backend(uploaded_file):
    """Upload file to the backend API for PII processing"""
    try:
        url = f"{BACKEND_URL}/api/upload"
        files = {
            "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
        }
        response = requests.post(url, files=files, timeout=120)

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {"error": response.json().get("detail", "Unknown error")}
    except requests.exceptions.ConnectionError:
        return False, {"error": "Cannot connect to backend service."}
    except requests.exceptions.Timeout:
        return False, {"error": "Request timed out."}
    except Exception as e:
        return False, {"error": str(e)}


def download_redacted_file(filename):
    """Download the redacted file from backend"""
    try:
        url = f"{BACKEND_URL}/api/download/{filename}"
        response = requests.get(url, timeout=30)
        return response.content if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Download failed: {str(e)}")
        return None


def get_processed_files_history():
    """Get list of all processed files"""
    try:
        url = f"{BACKEND_URL}/api/history"
        response = requests.get(url, timeout=10)
        return (
            response.json()
            if response.status_code == 200
            else {"files": [], "total": 0}
        )
    except:
        return {"files": [], "total": 0}


def create_download_button(
    file_content, filename, label="Download Redacted File", key=None
):
    """Create a download button for the redacted file"""
    b64 = base64.b64encode(file_content).decode()
    href = f'''
    <a href="data:application/octet-stream;base64,{b64}" download="{filename}" class="download-btn">
        {label}
    </a>
    '''
    st.markdown(href, unsafe_allow_html=True)


def get_file_type_icon(file_type):
    """Get icon for file type"""
    icons = {
        "pdf": "PDF",
        "docx": "Word",
        "doc": "Word",
        "xlsx": "Excel",
        "xls": "Excel",
        "jpg": "Image",
        "jpeg": "Image",
        "png": "Image",
        "tiff": "Image",
        "bmp": "Image",
    }
    return icons.get(file_type.lower(), "File")


def tab_upload():
    """Upload and processing tab"""
    st.subheader("Upload File for PII Processing")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "docx", "doc", "xlsx", "xls", "jpg", "jpeg", "png", "tiff", "bmp"],
        help="Upload a file to detect and redact PII",
        key="main_uploader",
    )

    if uploaded_file is not None:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**File:** `{uploaded_file.name}`")
        with col2:
            st.info(f"**Size:** {len(uploaded_file.getvalue()) / 1024:.1f} KB")
        with col3:
            st.info(f"**Type:** `{uploaded_file.type or 'Unknown'}`")

        st.markdown("---")

        if st.button("Process File", type="primary", use_container_width=True):
            with st.spinner("Processing file... PII is being detected and redacted."):
                success, result = upload_file_to_backend(uploaded_file)

                if success:
                    st.session_state["last_result"] = result
                    st.session_state["last_filename"] = uploaded_file.name
                    st.session_state["show_preview"] = True
                    st.success("Processing complete!")
                    st.rerun()
                else:
                    st.error(f"Error: {result.get('error', 'Processing failed')}")


# ==================== TAB: PREVIEW ====================


def tab_preview():
    """Side-by-side preview tab (masked original vs redacted)"""
    st.subheader("Content Preview")
    st.info(
        "**PII-Safe Mode**: Original content is shown with PII values partially masked. Redacted content shows final output."
    )

    result = st.session_state.get("last_result")

    if not result:
        st.warning("No file has been processed yet. Upload and process a file first.")
        return

    # Show basic info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "PII Entities",
            result.get("total_entities", result.get("total_pii_count", 0)),
        )
    with col2:
        st.metric("Confidence", f"{result.get('confidence', 0):.1f}%")
    with col3:
        st.metric("File Type", result.get("file_type", "unknown").upper())
    with col4:
        pages = result.get("pages_processed", 0)
        if pages > 0:
            st.metric("Pages", pages)
        else:
            st.metric("Status", "Done")

    # Entity types chart
    entity_types = result.get("entity_types", {})
    if entity_types:
        st.markdown("---")
        st.markdown("### PII Entity Distribution")
        df = pd.DataFrame([{"Type": k, "Count": v} for k, v in entity_types.items()])
        st.bar_chart(df.set_index("Type"))

    # Side-by-side preview
    st.markdown("---")
    st.markdown("### Content Preview")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("##### Original Content (PII Masked)")
        masked_text = result.get("masked_text", "")

        if masked_text:
            st.markdown(
                f'<div class="original-masked"><pre style="white-space: pre-wrap; font-size: 0.85rem; max-height: 500px; overflow-y: auto;">{masked_text}</pre></div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("No text content to preview (binary file or no extractable text)")

    with col_right:
        st.markdown("##### Redacted Content")

        if result.get("redacted_filename"):
            st.success(f"Redacted file ready: `{result['redacted_filename']}`")
            st.info(
                "Download the redacted file from the **Export** tab to view the final redacted content."
            )
        else:
            st.warning(
                "No redacted file generated (no PII found or file type doesn't support redaction)"
            )

    # PII Findings Table (masked values only)
    pii_findings = result.get("pii_findings", [])
    if pii_findings:
        st.markdown("---")
        st.markdown("### PII Findings (All Values Masked)")

        findings_df = pd.DataFrame(pii_findings)
        if not findings_df.empty:
            cols_to_show = []
            if "entity_type" in findings_df.columns:
                cols_to_show.append("entity_type")
            if "cell_ref" in findings_df.columns:
                cols_to_show.append("cell_ref")
            if "original_value" in findings_df.columns:
                cols_to_show.append("original_value")
            if "confidence" in findings_df.columns:
                cols_to_show.append("confidence")

            if cols_to_show:
                st.dataframe(findings_df[cols_to_show], use_container_width=True)


# ==================== TAB: HISTORY ====================


def tab_history():
    """History tab showing processed files"""
    st.subheader("Processed Files History")

    # Refresh button
    if st.button("Refresh", use_container_width=True):
        st.session_state.pop("history_cache", None)
        st.rerun()

    history = st.session_state.get("history_cache")
    if history is None:
        history = get_processed_files_history()
        st.session_state["history_cache"] = history

    if history.get("total", 0) == 0:
        st.info("No processed files yet. Upload and process a file to see it here.")
        return

    st.success(f"**{history['total']}** processed file(s) available")

    # Create dataframe
    files_data = []
    for f in history.get("files", []):
        files_data.append(
            {
                "File": f["filename"],
                "Type": f["file_type"].upper(),
                "Size": f["size_human"],
                "Processed": f["modified_human"],
                "Download": f["filename"],
            }
        )

    df = pd.DataFrame(files_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Download Files")

    for f in history.get("files", []):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            icon = get_file_type_icon(f["file_type"].replace(".", ""))
            st.write(f"{icon} **{f['filename']}**")
        with col2:
            st.write(f"_{f['size_human']}_")
        with col3:
            if f"download_{f['filename']}" in st.session_state:
                content = st.session_state[f"download_{f['filename']}"]
                create_download_button(
                    content,
                    f["filename"],
                    label="Save File",
                    key=f"btn_{f['filename']}",
                )
            else:
                if st.button(
                    "Prepare Download",
                    key=f"dl_hist_{f['filename']}",
                    help=f"Prepare {f['filename']}",
                ):
                    content = download_redacted_file(f["filename"])
                    if content:
                        st.session_state[f"download_{f['filename']}"] = content
                        st.rerun()
                    else:
                        st.error("Download failed")


# ==================== TAB: EXPORT ====================


def tab_export():
    """Export tab with prominent download button"""
    st.subheader("Export Redacted Files")

    result = st.session_state.get("last_result")

    if not result:
        st.warning("No file has been processed yet. Process a file first.")
        return

    # File info card
    st.markdown("---")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            f"### {get_file_type_icon(result.get('file_type', ''))} {st.session_state.get('last_filename', 'Unknown')}"
        )
        st.write(
            f"- **PII Entities Found:** {result.get('total_entities', result.get('total_pii_count', 0))}"
        )
        st.write(f"- **Confidence:** {result.get('confidence', 0):.1f}%")
        st.write(f"- **File Type:** {result.get('file_type', 'unknown').upper()}")

    with col2:
        if result.get("redacted_filename"):
            st.success("Ready for download")
        else:
            st.warning("No redacted file")

    # Download section
    st.markdown("---")

    if result.get("redacted_filename"):
        redacted_filename = result["redacted_filename"]

        st.markdown("#### Download Redacted File")

        with st.spinner("Preparing download..."):
            file_content = download_redacted_file(redacted_filename)

            if file_content:
                create_download_button(
                    file_content,
                    redacted_filename,
                    label=f"Download {redacted_filename}",
                    key="export_download",
                )

                # Also offer history access
                st.markdown("---")
                st.info(
                    "**Tip:** You can also access all processed files from the **History** tab."
                )
            else:
                st.error("Failed to download the file. Please check the backend logs.")
    else:
        st.warning("No redacted file is available for download.")
        st.info("This may happen if:")
        st.markdown("- No PII was detected in the file")
        st.markdown("- The file type doesn't support redaction (e.g., images)")


# ==================== MAIN APP ====================


def main():
    """Main application"""

    # Header
    st.markdown('<div class="main-header">Smart-Redact</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">PII Detection & Redaction System | Zero PII Exposure Mode</div>',
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:
        st.header("System Status")

        is_healthy, health_data = check_backend_health()

        if is_healthy:
            st.success("Backend Connected")
            st.write(f"**URL:** `{BACKEND_URL}`")
        else:
            st.error("Backend Not Connected")
            st.warning(f"Expected: `{BACKEND_URL}`")
            st.code(
                "cd backend && uvicorn app.api.main:app --host 0.0.0.0 --port 8000",
                language="bash",
            )

        st.markdown("---")
        st.markdown("### PII Types Detected")
        pii_types = [
            "Email Addresses",
            "Phone Numbers",
            "Social Security Numbers",
            "Credit Card Numbers",
            "IP Addresses",
            "URLs",
            "Dates of Birth",
            "Passport Numbers",
            "License Plates",
        ]
        for pii in pii_types:
            st.write(f"- {pii}")

        st.markdown("---")
        st.markdown("### Supported Formats")
        formats = [
            "PDF",
            "Word (.docx, .doc)",
            "Excel (.xlsx, .xls)",
            "Images (.jpg, .png, .tiff)",
        ]
        for fmt in formats:
            st.write(f"- {fmt}")

        st.markdown("---")
        st.caption("All PII values are masked before being sent to the frontend")

    # Check backend health
    if not is_healthy:
        st.error("Backend service is not available.")
        st.code(f"BACKEND_URL={BACKEND_URL} streamlit run app.py", language="bash")
        return

    # Main tabs
    tab_upload_tab, tab_preview_tab, tab_history_tab, tab_export_tab = st.tabs(
        ["Upload", "Preview", "History", "Export"]
    )

    with tab_upload_tab:
        tab_upload()

    with tab_preview_tab:
        tab_preview()

    with tab_history_tab:
        tab_history()

    with tab_export_tab:
        tab_export()

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #999; padding: 1rem;">
            <p><strong>Smart-Redact</strong> - PII-Safe Redaction System</p>
            <p>Backend: FastAPI | Frontend: Streamlit | Zero PII Exposure</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
