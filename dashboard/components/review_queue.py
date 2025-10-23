"""
Review queue interface component.
Week 5 Day 5 Part 2: Review Queue
"""

import streamlit as st
from datetime import datetime
from typing import Optional

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.models.validation_result_model import ValidationResult
from dashboard.utils.review_actions import ReviewActions


def render_review_queue_page(data_fetcher, days: int):
    """Render the review queue page"""
    
    st.markdown("# 📋 Review Queue")
    st.markdown("Items requiring human review, sorted by priority")
    st.markdown("---")
    
    # Get review actions handler
    review_actions = ReviewActions(data_fetcher.db)
    
    # Filters in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Status",
            options=['pending', 'approved', 'rejected', 'revision_requested', 'all'],
            index=0
        )
    
    with col2:
        priority_filter = st.selectbox(
            "Priority",
            options=['all', 'critical', 'high', 'medium', 'low'],
            index=0
        )
    
    with col3:
        limit = st.selectbox(
            "Items to show",
            options=[10, 25, 50, 100],
            index=1
        )
    
    st.markdown("---")
    
    # Get review queue items
    queue_items = get_review_queue_items(
        data_fetcher.db,
        status=status_filter if status_filter != 'all' else None,
        priority=priority_filter if priority_filter != 'all' else None,
        limit=limit
    )
    
    # Show stats
    stats = review_actions.get_review_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Pending", stats['pending'])
    with col2:
        st.metric("Approved", stats['approved'])
    with col3:
        st.metric("Rejected", stats['rejected'])
    with col4:
        st.metric("Needs Revision", stats['revision_requested'])
    
    st.markdown("---")
    
    # Show queue items
    if not queue_items:
        st.info(f"No items found with status='{status_filter}' and priority='{priority_filter}'")
        return
    
    st.markdown(f"**Found {len(queue_items)} items**")
    
    # Display each item
    for item in queue_items:
        render_review_item(item, review_actions)


def get_review_queue_items(
    db_session,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 25
):
    """Fetch review queue items from database"""
    from sqlalchemy import and_
    
    filters = [ValidationResult.decision == 'review']
    
    if status:
        filters.append(ValidationResult.review_status == status)
    
    if priority:
        filters.append(ValidationResult.priority == priority)
    
    items = db_session.query(ValidationResult).filter(
        and_(*filters)
    ).order_by(
        ValidationResult.created_at.desc()
    ).limit(limit).all()
    
    # Sort by priority
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'auto_reject': 4}
    items.sort(key=lambda x: (priority_order.get(x.priority, 99), x.created_at))
    
    return items


def render_review_item(item: ValidationResult, review_actions: ReviewActions):
    """Render a single review item with expandable details"""
    
    # Priority badge color
    priority_colors = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢',
        'auto_reject': '⚫'
    }
    
    status_colors = {
        'pending': '⏳',
        'approved': '✅',
        'rejected': '❌',
        'revision_requested': '🔄'
    }
    
    priority_badge = priority_colors.get(item.priority, '⚪')
    status_badge = status_colors.get(item.review_status, '❓')
    
    # Create expander with summary
    with st.expander(
        f"{priority_badge} {status_badge} ID: {item.id} | Priority: {item.priority.upper()} | "
        f"Created: {item.created_at.strftime('%Y-%m-%d %H:%M')}"
    ):
        # Display validation details
        st.markdown("### 📝 Query")
        st.text(item.query)
        
        st.markdown("### 💬 Answer")
        st.text_area("Generated Answer", item.answer, height=150, key=f"answer_{item.id}", disabled=True)
        
        st.markdown("---")
        
        # Validation scores
        col1, col2, col3 = st.columns(3)
        
        with col1:
            score_color = "🟢" if item.synthesis_score >= 0.7 else "🔴"
            st.metric(
                "Synthesis Score",
                f"{item.synthesis_score:.3f}",
                delta=f"{score_color} Target: 0.700"
            )
        
        with col2:
            score_color = "🟢" if item.citation_score >= 0.75 else "🔴"
            st.metric(
                "Citation Score",
                f"{item.citation_score:.3f}",
                delta=f"{score_color} Target: 0.750"
            )
        
        with col3:
            hall_pct = item.hallucination_rate * 100
            score_color = "🟢" if hall_pct <= 5.0 else "🔴"
            st.metric(
                "Hallucination Rate",
                f"{hall_pct:.2f}%",
                delta=f"{score_color} Target: ≤5%"
            )
        
        st.markdown("---")
        
        # Citation details
        if item.total_citations > 0:
            st.markdown("### 📚 Citation Details")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Citations", item.total_citations)
            with col2:
                st.metric("Verified", item.verified_citations)
            with col3:
                st.metric("Interpretation", item.interpretation_citations)
        
        st.markdown("---")
        
        # Show existing feedback if any
        if item.reviewer_feedback:
            st.markdown("### 💭 Previous Feedback")
            st.info(f"**{item.reviewer_id}** ({item.reviewed_at.strftime('%Y-%m-%d %H:%M')}): {item.reviewer_feedback}")
            st.markdown("---")
        
        # Action buttons and feedback form
        if item.review_status == 'pending':
            st.markdown("### ✍️ Review Actions")
            
            # Reviewer ID
            reviewer_id = st.text_input(
                "Your Name/ID",
                key=f"reviewer_{item.id}",
                placeholder="e.g., john.doe@lawfirm.com"
            )
            
            # Feedback
            feedback = st.text_area(
                "Feedback/Comments",
                key=f"feedback_{item.id}",
                placeholder="Add your review comments here...",
                height=100
            )
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("✅ Approve", key=f"approve_{item.id}", use_container_width=True):
                    if not reviewer_id:
                        st.error("Please enter your name/ID")
                    else:
                        success = review_actions.approve_answer(
                            item.id, reviewer_id, feedback if feedback else None
                        )
                        if success:
                            st.success("✅ Approved!")
                            st.rerun()
                        else:
                            st.error("Failed to approve")
            
            with col2:
                if st.button("❌ Reject", key=f"reject_{item.id}", use_container_width=True):
                    if not reviewer_id:
                        st.error("Please enter your name/ID")
                    elif not feedback:
                        st.error("Feedback required for rejection")
                    else:
                        success = review_actions.reject_answer(
                            item.id, reviewer_id, feedback
                        )
                        if success:
                            st.success("❌ Rejected!")
                            st.rerun()
                        else:
                            st.error("Failed to reject")
            
            with col3:
                if st.button("🔄 Request Revision", key=f"revise_{item.id}", use_container_width=True):
                    if not reviewer_id:
                        st.error("Please enter your name/ID")
                    elif not feedback:
                        st.error("Feedback required for revision")
                    else:
                        success = review_actions.request_revision(
                            item.id, reviewer_id, feedback
                        )
                        if success:
                            st.success("🔄 Revision requested!")
                            st.rerun()
                        else:
                            st.error("Failed to request revision")
            
            with col4:
                if st.button("⏭️ Skip", key=f"skip_{item.id}", use_container_width=True):
                    st.info("Skipped to next item")
        
        else:
            # Already reviewed
            st.success(f"Status: {item.review_status.upper().replace('_', ' ')}")
