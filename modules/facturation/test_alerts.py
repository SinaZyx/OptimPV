"""Test the alert functionality in the Executive Dashboard"""

import streamlit as st
from datetime import datetime
from dashboard_data import DashboardDataProvider, AlertNotification, AlertLevel

# Initialize session state
if 'dashboard_alerts' not in st.session_state:
    st.session_state.dashboard_alerts = []

# Create a test alert
test_alert = AlertNotification(
    id="test_alert_1",
    title="Test Alert",
    message="This is a test alert to verify the dismiss functionality",
    level=AlertLevel.WARNING,
    metric_name="test_metric",
    current_value=100.0,
    threshold_value=90.0,
    created_at=datetime.now(),
    is_active=True,
    action_required=False,
    suggested_actions=["Action 1", "Action 2"]
)

# Add to session state if not already there
if not any(alert.id == test_alert.id for alert in st.session_state.dashboard_alerts):
    st.session_state.dashboard_alerts.append(test_alert)

# Create dashboard provider
dashboard_provider = DashboardDataProvider(None)

# Test get_active_alerts
st.write("## Testing Alert Functionality")
st.write(f"Number of alerts in session state: {len(st.session_state.dashboard_alerts)}")

alerts = dashboard_provider.get_active_alerts(limit=5)
st.write(f"Number of active alerts: {len(alerts)}")

# Display alerts
for alert in alerts:
    st.write(f"### Alert: {alert.title}")
    st.write(f"ID: {alert.id}")
    st.write(f"Message: {alert.message}")
    st.write(f"Level: {alert.level.value}")
    st.write(f"Is Active: {alert.is_active}")
    
    # Test dismiss button
    if st.button(f"Dismiss {alert.id}", key=f"test_dismiss_{alert.id}"):
        success = dashboard_provider.dismiss_alert(alert.id)
        if success:
            st.success(f"Alert {alert.id} dismissed successfully!")
            st.rerun()
        else:
            st.error(f"Failed to dismiss alert {alert.id}")

# Check if dismiss worked
st.write("---")
st.write("## Alert Status After Dismiss")
for alert in st.session_state.dashboard_alerts:
    st.write(f"Alert {alert.id}: is_active = {alert.is_active}")