"""
Main Streamlit Dashboard for Legal RAG Validation System
Run with: streamlit run dashboard/app.py

Now with integrated structured logging support!
"""

import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.database.connection import get_session
from dashboard.utils.data_fetcher import DashboardDataFetcher

# Import logging utilities
from validation.logging_config import setup_logging, get_logger
from validation.correlation_id import correlation_context

# Setup logging (once at module load)
setup_logging(log_level="INFO", console_log_level="WARNING")
logger = get_logger(__name__)

st.set_page_config(
    page_title="Legal RAG Validation Dashboard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize Streamlit session state"""
    if 'db_session' not in st.session_state:
        st.session_state.db_session = get_session()
        st.session_state.data_fetcher = DashboardDataFetcher(st.session_state.db_session)
        logger.info("Dashboard session initialized")
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()


def render_sidebar():
    """Render sidebar with filters and navigation"""
    st.sidebar.title("⚖️ Legal RAG Dashboard")
    st.sidebar.markdown("---")

    # Time range selector
    st.sidebar.subheader("📅 Time Range")
    time_range = st.sidebar.selectbox(
        "Select period",
        options=['Last 24 Hours', 'Last 7 Days', 'Last 30 Days'],
        index=1
    )

    days = 1 if time_range == 'Last 24 Hours' else (7 if time_range == 'Last 7 Days' else 30)

    st.sidebar.markdown("---")

    # Navigation
    st.sidebar.subheader("🧭 Navigation")
    page = st.sidebar.radio(
        "Go to",
        options=['Overview', 'Review Queue', 'Logs'],  # Added Logs page
        index=0
    )

    st.sidebar.markdown("---")

    # Refresh button
    if st.sidebar.button("Refresh Data", use_container_width=True):
        st.session_state.last_refresh = datetime.now()
        logger.info("Dashboard refreshed", extra={'data': {'timestamp': datetime.now().isoformat()}})
        st.rerun()

    st.sidebar.caption(f"Last refreshed: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

    return days, page


def render_overview_page(data_fetcher, days):
    """Render overview dashboard page"""
    st.markdown("# 📊 Validation Overview")

    metrics = data_fetcher.get_kpi_metrics(days=days)

    # First row: Volume metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Validations", f"{metrics['total_validations']:,}")

    with col2:
        st.metric("Pass Rate", f"{metrics['pass_rate']:.1f}%",
                  delta=f"{metrics['pass_count']:,} passed")

    with col3:
        st.metric("Review Queue", f"{metrics['review_count']:,}",
                  delta=f"{metrics['review_rate']:.1f}% of total")

    with col4:
        st.metric("Auto-Rejected", f"{metrics['reject_count']:,}",
                  delta=f"{metrics['reject_rate']:.1f}% of total")

    st.markdown("---")

    # Second row: Quality metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Avg Synthesis Score", f"{metrics['avg_synthesis_score']:.3f}")

    with col2:
        st.metric("Avg Citation Score", f"{metrics['avg_citation_score']:.3f}")

    with col3:
        hallucination_pct = metrics['avg_hallucination_rate'] * 100
        st.metric("Avg Hallucination Rate", f"{hallucination_pct:.2f}%")

    st.markdown("---")

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Decision Breakdown")
        decision_df = data_fetcher.get_decision_breakdown(days=days)

        if not decision_df.empty:
            import plotly.express as px

            colors = {'pass': '#28A745', 'review': '#FFC107', 'reject': '#DC3545'}

            fig = px.pie(decision_df, values='count', names='decision',
                        color='decision', color_discrete_map=colors, hole=0.4)
            fig.update_layout(showlegend=True, height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")

    with col2:
        st.subheader("Priority Distribution")
        priority_df = data_fetcher.get_priority_breakdown(days=days)

        if not priority_df.empty:
            import plotly.graph_objects as go

            # Complete color mapping
            priority_colors = {
                'critical': '#DC3545',
                'high': '#FD7E14',
                'medium': '#FFC107',
                'low': '#28A745',
                'auto_reject': '#6C757D'
            }

            # Get color for each priority (with fallback)
            colors = [priority_colors.get(p, '#999999') for p in priority_df['priority']]

            # Create bar chart using graph_objects
            fig = go.Figure(data=[
                go.Bar(
                    x=priority_df['priority'],
                    y=priority_df['count'],
                    marker_color=colors,
                    text=priority_df['count'],
                    textposition='outside'
                )
            ])

            fig.update_layout(
                showlegend=False,
                height=350,
                xaxis_title="Priority Level",
                yaxis_title="Count"
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No review queue items")


def render_logs_page():
    """Render logs viewer page"""
    st.markdown("# 📋 Validation Logs")
    
    st.markdown("""
    View structured logs from the validation system. All logs are stored in JSON format 
    with correlation IDs for request tracking.
    """)
    
    # Log file selector
    log_dir = Path("logs")
    if not log_dir.exists():
        st.warning("⚠️ Logs directory not found. Run some validations first!")
        return
    
    log_files = sorted(log_dir.glob("validation.log*"), reverse=True)
    
    if not log_files:
        st.warning("⚠️ No log files found. Run some validations first!")
        return
    
    # File selector
    selected_file = st.selectbox(
        "Select log file",
        options=[f.name for f in log_files],
        index=0
    )
    
    log_file = log_dir / selected_file
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Filters")
        
    with col2:
        if st.button("🔄 Refresh Logs", use_container_width=True):
            st.rerun()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_level_filter = st.multiselect(
            "Log Level",
            options=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            default=['INFO', 'WARNING', 'ERROR']
        )
    
    with col2:
        module_filter = st.text_input("Module (contains)", placeholder="e.g., synthesis")
    
    with col3:
        correlation_id_filter = st.text_input("Correlation ID", placeholder="e.g., val_1760...")
    
    # Load and display logs
    try:
        import json
        
        logs = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
        
        # Apply filters
        filtered_logs = logs
        
        if log_level_filter:
            filtered_logs = [log for log in filtered_logs if log.get('level') in log_level_filter]
        
        if module_filter:
            filtered_logs = [log for log in filtered_logs 
                           if module_filter.lower() in log.get('module', '').lower()]
        
        if correlation_id_filter:
            filtered_logs = [log for log in filtered_logs 
                           if correlation_id_filter in log.get('correlation_id', '')]
        
        # Display count
        st.markdown(f"**Showing {len(filtered_logs):,} of {len(logs):,} log entries**")
        
        # Display options
        show_raw = st.checkbox("Show raw JSON", value=False)
        max_entries = st.slider("Max entries to display", 10, 200, 50)
        
        # Display logs
        if filtered_logs:
            st.markdown("---")
            
            for i, log in enumerate(filtered_logs[:max_entries]):
                # Color-code by level
                level_colors = {
                    'DEBUG': '🔵',
                    'INFO': '🟢',
                    'WARNING': '🟡',
                    'ERROR': '🔴'
                }
                
                level_icon = level_colors.get(log.get('level', ''), '⚪')
                
                with st.expander(
                    f"{level_icon} {log.get('timestamp', 'N/A')} - {log.get('message', 'No message')}"
                ):
                    if show_raw:
                        st.json(log)
                    else:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**Level:** {log.get('level', 'N/A')}")
                            st.markdown(f"**Module:** {log.get('module', 'N/A')}")
                            st.markdown(f"**Function:** {log.get('function', 'N/A')}")
                        
                        with col2:
                            st.markdown(f"**Timestamp:** {log.get('timestamp', 'N/A')}")
                            if log.get('correlation_id'):
                                st.markdown(f"**Correlation ID:** `{log.get('correlation_id')}`")
                        
                        st.markdown(f"**Message:** {log.get('message', 'N/A')}")
                        
                        if log.get('data'):
                            st.markdown("**Data:**")
                            st.json(log.get('data'))
                        
                        if log.get('exc_info'):
                            st.markdown("**Stack Trace:**")
                            st.code(log.get('exc_info'), language='python')
        else:
            st.info("No logs match the selected filters")
    
    except Exception as e:
        st.error(f"Error reading log file: {e}")
        logger.error(f"Dashboard log viewer error: {e}", exc_info=True)


def main():
    """Main dashboard application"""
    with correlation_context(prefix="dash") as corr_id:
        logger.debug(
            "Dashboard page load",
            extra={
                'correlation_id': corr_id,
                'data': {'timestamp': datetime.now().isoformat()}
            }
        )
        
        init_session_state()
        days, page = render_sidebar()
        data_fetcher = st.session_state.data_fetcher

        if page == 'Overview':
            render_overview_page(data_fetcher, days)
        elif page == 'Review Queue':
            from dashboard.components.review_queue import render_review_queue_page
            render_review_queue_page(data_fetcher, days)
        elif page == 'Logs':
            render_logs_page()


if __name__ == "__main__":
    main()
