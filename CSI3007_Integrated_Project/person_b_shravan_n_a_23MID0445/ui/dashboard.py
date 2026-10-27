"""Streamlit dashboard for Person B's subscription manager."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

import pandas as pd
import plotly.express as px
import streamlit as st

from config import settings
from ui.api_client import ApiError, client
from ui.theme import apply_theme

PAGES = [
    "Overview",
    "Subscriptions",
    "Payments",
    "Renewals",
    "Integrations",
    "Project info",
]
STATUSES = ["active", "paused", "cancelled", "expired"]
CYCLES = ["weekly", "monthly", "quarterly", "yearly", "custom"]
PAYMENT_METHODS = ["upi", "card", "cash", "net_banking", "other"]
PALETTE = ["#4f46e5", "#0ea5e9", "#f59e0b", "#10b981", "#ef4444", "#64748b"]


def _money(value, currency: str = "INR") -> str:
    try:
        number = Decimal(str(value or "0"))
    except Exception:
        number = Decimal("0")
    symbol = "₹" if currency == "INR" else f"{currency} "
    return f"{symbol}{number:,.2f}"


def _when(value: str | None) -> str:
    if not value:
        return "Never"
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y, %H:%M")
    except ValueError:
        return value


def _flash(level: str, message: str) -> None:
    st.session_state["b_flash"] = (level, message)


def _show_flash() -> None:
    item = st.session_state.pop("b_flash", None)
    if not item:
        return
    level, message = item
    {"success": st.success, "warning": st.warning, "error": st.error, "info": st.info}[
        level
    ](message)


def _api_error(exc: ApiError) -> None:
    st.error(exc.message)
    if exc.details:
        st.json(exc.details)


def _style_figure(fig, height: int = 330):
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=12, t=42, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
        font=dict(family="sans serif", size=12),
    )
    return fig


def _sidebar() -> str:
    with st.sidebar:
        st.markdown("## :material/autorenew: Subscription manager")
        st.caption("Shravan N A · 23MID0445")
        page = st.radio(
            "Navigation", PAGES, label_visibility="collapsed", key="b_nav"
        )
        st.divider()
        try:
            client.health()
            st.success("API online", icon=":material/check_circle:")
        except ApiError as exc:
            st.error("API offline", icon=":material/cloud_off:")
            st.caption(exc.message)
        st.caption(f"Backend: `{settings.api_base_url}`")
        st.link_button(
            "Open API docs",
            f"{settings.api_base_url}/docs",
            icon=":material/menu_book:",
            width="stretch",
        )
        st.divider()
        st.caption("Person B · 23MID0445")
        st.caption("Recurring costs are estimates. Actual payments are separate records.")
    return page


def _subscription_table(items: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Service": item["service_name"],
                "Category": item["category"],
                "Amount": float(item["amount"]),
                "Currency": item["currency"],
                "Cycle": item["billing_cycle"],
                "Next renewal": item["next_renewal_date"],
                "Status": item["status"],
                "Monthly eq.": float(item["monthly_equivalent"]),
                "Yearly eq.": float(item["yearly_equivalent"]),
                "Overdue": item["is_overdue"],
            }
            for item in items
        ]
    )


def page_overview() -> None:
    st.title("Subscription overview")
    st.caption("Expected recurring costs, actual payments, and the renewal horizon.")
    try:
        summary = client.summary()
        upcoming = client.upcoming(30)
    except ApiError as exc:
        _api_error(exc)
        return

    with st.container(horizontal=True):
        st.metric("Active subscriptions", summary["active_subscriptions"], border=True)
        st.metric(
            "Expected monthly",
            _money(summary["expected_monthly_recurring"]),
            border=True,
        )
        st.metric("Yearly projection", _money(summary["yearly_projection"]), border=True)
        st.metric(
            "Actual paid this month",
            _money(summary["actual_payments_this_month"]),
            border=True,
        )
    if summary["overdue"]:
        st.warning(
            f"{summary['overdue']} active subscription(s) have an overdue renewal date. "
            "Review the renewals page.",
            icon=":material/schedule:",
        )
    st.caption(
        "Expected recurring cost ≠ actual payment. Actual totals include only manually "
        "recorded payment history; no payment provider is connected."
    )

    if summary["active_subscriptions"] == 0:
        st.info(
            "No active subscriptions yet. Add one on the subscriptions page to populate projections.",
            icon=":material/info:",
        )
        return

    col1, col2 = st.columns(2)
    with col1, st.container(border=True):
        st.subheader("Recurring cost by category")
        categories = pd.DataFrame(summary["by_category"])
        if categories.empty:
            st.info("No INR category totals yet.")
        else:
            categories["monthly"] = categories["monthly"].astype(float)
            fig = px.pie(
                categories,
                names="category",
                values="monthly",
                hole=0.48,
                color_discrete_sequence=PALETTE,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(
                _style_figure(fig, 340),
                alt="Expected monthly subscription cost by category",
                key="b_category_pie",
            )
    with col2, st.container(border=True):
        st.subheader("Subscriptions by billing cycle")
        cycles = pd.DataFrame(summary["by_cycle"])
        if cycles.empty:
            st.info("No billing-cycle data yet.")
        else:
            cycles["monthly"] = cycles["monthly"].astype(float)
            fig = px.bar(
                cycles,
                x="cycle",
                y="subscriptions",
                color="cycle",
                color_discrete_sequence=PALETTE,
                text="subscriptions",
            )
            fig.update_layout(xaxis_title="", yaxis_title="Active subscriptions", showlegend=False)
            st.plotly_chart(
                _style_figure(fig, 340),
                alt="Number of active subscriptions by billing cycle",
                key="b_cycle_bar",
            )

    with st.container(border=True):
        st.subheader("Next 30 days")
        records = upcoming["upcoming_records"][:8]
        if not records:
            st.info("No renewals are due in the next 30 days.")
        else:
            st.dataframe(
                _subscription_table(records),
                hide_index=True,
                alt="Subscriptions due for renewal in the next 30 days",
                column_config={
                    "Amount": st.column_config.NumberColumn(format="%.2f"),
                    "Next renewal": st.column_config.DateColumn(),
                    "Monthly eq.": st.column_config.NumberColumn(format="%.2f"),
                    "Yearly eq.": st.column_config.NumberColumn(format="%.2f"),
                    "Overdue": st.column_config.CheckboxColumn(),
                },
            )
        st.caption(
            f"{upcoming['counts']['upcoming']} upcoming · "
            f"{upcoming['counts']['overdue']} overdue · "
            f"{len(upcoming['reminders'])} pending reminders"
        )


def _subscription_create_form(categories: list[str]) -> dict | None:
    with st.form("b_add_subscription", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            service = st.text_input("Service name", max_chars=160)
            category = st.text_input("Category", value="Entertainment", max_chars=60)
            amount = st.number_input(
                "Billing amount",
                min_value=0.01,
                value=499.00,
                step=10.0,
                format="%.2f",
            )
            currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"])
            cycle = st.selectbox("Billing cycle", CYCLES)
            custom_days = st.number_input(
                "Custom interval (days)",
                min_value=1,
                value=30,
                step=1,
                help="Used only when the billing cycle is custom.",
            )
        with col2:
            start = st.date_input("Start date", value=date.today())
            payment = st.selectbox("Payment method", PAYMENT_METHODS, index=1)
            status = st.selectbox("Status", STATUSES)
            reminder_days = st.slider("Remind me (days before)", 0, 60, 7)
            notes = st.text_area("Notes", height=100)
        submitted = st.form_submit_button(
            "Add subscription", type="primary", icon=":material/add:"
        )
    if not submitted:
        return None
    if not service.strip() or not category.strip():
        st.error("Service name and category are required.")
        return None
    payload = {
        "service_name": service.strip(),
        "category": category.strip(),
        "amount": f"{amount:.2f}",
        "currency": currency,
        "billing_cycle": cycle,
        "start_date": start.isoformat(),
        "payment_method": payment,
        "status": status,
        "notes": notes.strip(),
        "reminder_days_before": reminder_days,
    }
    if cycle == "custom":
        payload["custom_interval_days"] = int(custom_days)
    return payload


def page_subscriptions() -> None:
    st.title("Subscriptions")
    st.caption("Create, search, update and remove recurring services.")
    try:
        categories = client.categories()
        all_items = client.subscriptions()
    except ApiError as exc:
        _api_error(exc)
        return

    with st.expander("Add a subscription", icon=":material/add_circle:"):
        payload = _subscription_create_form(categories)
        if payload:
            try:
                created = client.create_subscription(payload)
                _flash(
                    "success",
                    f"Added {created['service_name']} · {created['billing_cycle']} · "
                    f"₹{created['amount']}.",
                )
                st.rerun()
            except ApiError as exc:
                _api_error(exc)

    with st.container(border=True):
        st.subheader("Filter and sort")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            search = st.text_input("Search", type="search")
        with col2:
            status = st.selectbox("Status", ["All"] + STATUSES)
        with col3:
            existing_categories = sorted({item["category"] for item in all_items})
            category_filter = st.selectbox("Category", ["All"] + existing_categories)
        with col4:
            sort_by = st.selectbox(
                "Sort by",
                ["next_renewal_date", "service_name", "amount", "created_at"],
            )
        sort_order = st.segmented_control("Order", ["asc", "desc"], default="asc")
    try:
        items = client.subscriptions(
            status=None if status == "All" else status,
            category=None if category_filter == "All" else category_filter,
            search=search or None,
            sort_by=sort_by,
            sort_order=sort_order or "asc",
        )
    except ApiError as exc:
        _api_error(exc)
        return

    if not items:
        st.info("No subscriptions match the current filters.")
        return
    st.caption(f"{len(items)} subscription records")
    st.dataframe(
        _subscription_table(items),
        hide_index=True,
        alt="Filtered subscription records",
        column_config={
            "Amount": st.column_config.NumberColumn(format="%.2f"),
            "Next renewal": st.column_config.DateColumn(),
            "Monthly eq.": st.column_config.NumberColumn(format="%.2f"),
            "Yearly eq.": st.column_config.NumberColumn(format="%.2f"),
            "Overdue": st.column_config.CheckboxColumn(),
        },
    )

    with st.expander("Edit or delete a subscription", icon=":material/edit:"):
        labels = {
            item["id"]: f"#{item['id']} · {item['service_name']} · {item['status']}"
            for item in items
        }
        selected_id = st.selectbox(
            "Subscription",
            list(labels),
            format_func=lambda value: labels[value],
            key="b_sub_edit_select",
        )
        selected = next(item for item in items if item["id"] == selected_id)
        with st.form(f"b_edit_subscription_{selected_id}"):
            col1, col2 = st.columns(2)
            with col1:
                service = st.text_input(
                    "Service name",
                    value=selected["service_name"],
                    key=f"b_edit_service_{selected_id}",
                )
                category = st.text_input(
                    "Category",
                    value=selected["category"],
                    key=f"b_edit_category_{selected_id}",
                )
                amount = st.number_input(
                    "Billing amount",
                    min_value=0.01,
                    value=float(selected["amount"]),
                    format="%.2f",
                    key=f"b_edit_amount_{selected_id}",
                )
                cycle = st.selectbox(
                    "Billing cycle",
                    CYCLES,
                    index=CYCLES.index(selected["billing_cycle"]),
                    key=f"b_edit_cycle_{selected_id}",
                )
                custom_days = st.number_input(
                    "Custom interval (days)",
                    min_value=1,
                    value=int(selected["custom_interval_days"] or 30),
                    key=f"b_edit_custom_{selected_id}",
                )
            with col2:
                start = st.date_input(
                    "Start date",
                    value=date.fromisoformat(selected["start_date"]),
                    key=f"b_edit_start_{selected_id}",
                )
                next_date = st.date_input(
                    "Next renewal date",
                    value=date.fromisoformat(selected["next_renewal_date"]),
                    key=f"b_edit_next_{selected_id}",
                )
                status_value = st.selectbox(
                    "Status",
                    STATUSES,
                    index=STATUSES.index(selected["status"]),
                    key=f"b_edit_status_{selected_id}",
                )
                reminder_days = st.slider(
                    "Remind me (days before)",
                    0,
                    60,
                    int(selected["reminder_days_before"]),
                    key=f"b_edit_reminder_{selected_id}",
                )
                notes = st.text_area(
                    "Notes",
                    value=selected["notes"],
                    key=f"b_edit_notes_{selected_id}",
                )
            save = st.form_submit_button("Update subscription", icon=":material/save:")
        if save:
            payload = {
                "service_name": service,
                "category": category,
                "amount": f"{amount:.2f}",
                "billing_cycle": cycle,
                "start_date": start.isoformat(),
                "next_renewal_date": next_date.isoformat(),
                "status": status_value,
                "notes": notes,
                "reminder_days_before": reminder_days,
            }
            if cycle == "custom":
                payload["custom_interval_days"] = int(custom_days)
            try:
                client.update_subscription(selected_id, payload)
                _flash("success", "Subscription updated.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)

        col_advance, col_delete = st.columns(2)
        with col_advance:
            if st.button(
                "Advance one renewal",
                icon=":material/fast_forward:",
                key=f"b_advance_{selected_id}",
            ):
                try:
                    advanced = client.advance_renewal(selected_id)
                    _flash(
                        "success",
                        f"Next renewal moved to {advanced['next_renewal_date']}.",
                    )
                    st.rerun()
                except ApiError as exc:
                    _api_error(exc)
        with col_delete:
            confirm = st.checkbox(
                "Confirm deletion", key=f"b_delete_confirm_{selected_id}"
            )
            if st.button(
                "Delete subscription",
                disabled=not confirm,
                icon=":material/delete:",
                key=f"b_delete_{selected_id}",
            ):
                try:
                    client.delete_subscription(selected_id)
                    _flash("success", "Subscription and its related local records deleted.")
                    st.rerun()
                except ApiError as exc:
                    _api_error(exc)


def page_payments() -> None:
    st.title("Payments")
    st.caption(
        "Record actual payments and review history. No payment is processed automatically."
    )
    try:
        subscriptions = client.subscriptions()
        history = client.payments()
    except ApiError as exc:
        _api_error(exc)
        return
    if not subscriptions:
        st.info("Add a subscription before recording a payment.")
        return

    labels = {
        item["id"]: f"{item['service_name']} · {item['amount']} {item['currency']}"
        for item in subscriptions
    }
    selected_id = st.selectbox(
        "Subscription", list(labels), format_func=lambda value: labels[value]
    )
    selected = next(item for item in subscriptions if item["id"] == selected_id)
    if "b_idem_key" not in st.session_state:
        st.session_state["b_idem_key"] = str(uuid.uuid4())

    with st.container(border=True):
        st.subheader("Record an actual payment")
        with st.form(f"b_payment_form_{selected_id}"):
            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input(
                    "Amount paid",
                    min_value=0.01,
                    value=float(selected["amount"]),
                    format="%.2f",
                    key=f"b_pay_amount_{selected_id}",
                )
                paid_on = st.date_input(
                    "Paid on",
                    value=date.today(),
                    max_value=date.today(),
                    key=f"b_pay_date_{selected_id}",
                )
                period = st.text_input(
                    "Billing period (YYYY-MM)",
                    value=date.today().strftime("%Y-%m"),
                    key=f"b_pay_period_{selected_id}",
                )
            with col2:
                method = st.selectbox(
                    "Payment method",
                    PAYMENT_METHODS,
                    index=PAYMENT_METHODS.index(selected["payment_method"])
                    if selected["payment_method"] in PAYMENT_METHODS
                    else 4,
                    key=f"b_pay_method_{selected_id}",
                )
                reference = st.text_input(
                    "Reference", max_chars=120, key=f"b_pay_ref_{selected_id}"
                )
                idem = st.text_input(
                    "Idempotency key",
                    value=st.session_state["b_idem_key"],
                    key=f"b_pay_idem_{selected_id}",
                    help="Repeated submissions with the same key return the existing payment.",
                )
                notes = st.text_area(
                    "Notes", height=80, key=f"b_pay_notes_{selected_id}"
                )
            submitted = st.form_submit_button(
                "Record payment", type="primary", icon=":material/receipt_long:"
            )
        if submitted:
            try:
                result = client.record_payment(
                    {
                        "subscription_id": selected_id,
                        "amount": f"{amount:.2f}",
                        "paid_on": paid_on.isoformat(),
                        "billing_period": period,
                        "payment_method": method,
                        "reference": reference,
                        "notes": notes,
                        "idempotency_key": idem,
                    }
                )
                if result["deduplicated"]:
                    _flash(
                        "warning",
                        "This payment was already recorded; no duplicate was created.",
                    )
                else:
                    _flash("success", "Actual payment recorded.")
                st.session_state["b_idem_key"] = str(uuid.uuid4())
                st.rerun()
            except ApiError as exc:
                _api_error(exc)

    st.subheader("Payment history")
    if not history:
        st.info("No actual payments have been recorded yet.")
        return
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Date": item["paid_on"],
                    "Service": item["service_name"],
                    "Period": item["billing_period"],
                    "Amount": float(item["amount"]),
                    "Currency": item["currency"],
                    "Method": item["payment_method"],
                    "Reference": item["reference"],
                }
                for item in history
            ]
        ),
        hide_index=True,
        alt="Recorded subscription payment history",
        column_config={
            "Amount": st.column_config.NumberColumn(format="%.2f"),
            "Date": st.column_config.DateColumn(),
        },
    )
    with st.expander("Delete a payment record", icon=":material/delete:"):
        payment_labels = {
            item["id"]: f"#{item['id']} · {item['service_name']} · {item['paid_on']}"
            for item in history
        }
        payment_id = st.selectbox(
            "Payment",
            list(payment_labels),
            format_func=lambda value: payment_labels[value],
            key="b_payment_delete_select",
        )
        confirm = st.checkbox(
            "Confirm deletion", key=f"b_payment_delete_confirm_{payment_id}"
        )
        if st.button(
            "Delete payment",
            disabled=not confirm,
            icon=":material/delete:",
            key=f"b_payment_delete_{payment_id}",
        ):
            try:
                client.delete_payment(payment_id)
                _flash("success", "Payment deleted.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)


def page_renewals() -> None:
    st.title("Renewals and reminders")
    st.caption("Overdue renewals are shown separately from upcoming renewals.")
    days = st.slider("Upcoming horizon (days)", 0, 120, settings.upcoming_days)
    try:
        data = client.upcoming(days)
    except ApiError as exc:
        _api_error(exc)
        return
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button(
            "Refresh reminders", icon=":material/notifications_active:", width="stretch"
        ):
            try:
                result = client.refresh_reminders()
                _flash("success", f"Created {result['created']} new renewal reminder(s).")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)
    with col2:
        st.caption(
            f"As of {data['as_of']} · {data['counts']['overdue']} overdue · "
            f"{data['counts']['upcoming']} upcoming"
        )

    st.subheader("Overdue renewals")
    if not data["overdue_records"]:
        st.success("No overdue active renewals.", icon=":material/check_circle:")
    else:
        st.dataframe(
            _subscription_table(data["overdue_records"]),
            hide_index=True,
            alt="Overdue subscription renewals",
            column_config={
                "Amount": st.column_config.NumberColumn(format="%.2f"),
                "Next renewal": st.column_config.DateColumn(),
                "Monthly eq.": st.column_config.NumberColumn(format="%.2f"),
                "Yearly eq.": st.column_config.NumberColumn(format="%.2f"),
                "Overdue": st.column_config.CheckboxColumn(),
            },
        )
    st.subheader(f"Upcoming in {days} days")
    if not data["upcoming_records"]:
        st.info("No upcoming renewals in this horizon.")
    else:
        st.dataframe(
            _subscription_table(data["upcoming_records"]),
            hide_index=True,
            alt="Upcoming subscription renewals",
            column_config={
                "Amount": st.column_config.NumberColumn(format="%.2f"),
                "Next renewal": st.column_config.DateColumn(),
                "Monthly eq.": st.column_config.NumberColumn(format="%.2f"),
                "Yearly eq.": st.column_config.NumberColumn(format="%.2f"),
                "Overdue": st.column_config.CheckboxColumn(),
            },
        )
    st.subheader("Pending reminders")
    if not data["reminders"]:
        st.info("No pending reminders. Use “Refresh reminders” to create due reminders.")
    else:
        for reminder in data["reminders"]:
            col_text, col_action = st.columns([3, 1])
            with col_text:
                st.markdown(
                    f"**{reminder['service_name']}** renews on "
                    f"{reminder['renewal_date']} "
                    f"({reminder['days_until_renewal']} days)."
                )
            with col_action:
                if st.button(
                    "Dismiss",
                    key=f"b_dismiss_{reminder['id']}",
                    icon=":material/notifications_off:",
                    width="stretch",
                ):
                    try:
                        client.dismiss_reminder(reminder["id"])
                        _flash("success", "Reminder dismissed.")
                        st.rerun()
                    except ApiError as exc:
                        _api_error(exc)


def page_integrations() -> None:
    st.title("Person A integration")
    st.caption(
        "Push subscription expense records to Person A over authenticated HTTP. "
        "Person B remains fully functional when Person A is offline."
    )
    check_remote = st.toggle("Check live connectivity", value=True, key="b_check_remote")
    try:
        status = client.integration_status(check_remote=check_remote)
    except ApiError as exc:
        _api_error(exc)
        return
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Last result", status["status"].title())
        col2.metric("Last success", _when(status["last_success_at"]))
        col3.metric("Records sent", status["records_sent"])
        st.caption(f"Destination: `{status['api_url']}` · last period: {status['last_period'] or '—'}")
        if status.get("remote_health"):
            if status["remote_health"]["reachable"]:
                st.success("Person A API reachable", icon=":material/link:")
            else:
                st.warning(
                    "Person A is unreachable. Local subscription data is preserved and you can retry later.",
                    icon=":material/link_off:",
                )
        if status["last_error"]:
            st.error(f"Last error: {status['last_error']}", icon=":material/error:")

    with st.container(border=True):
        st.subheader("Push a period to Person A")
        period = st.text_input(
            "Billing period (YYYY-MM)",
            value=date.today().strftime("%Y-%m"),
            key="b_sync_period",
        )
        col_push, col_preview = st.columns(2)
        with col_push:
            if st.button(
                "Sync now",
                type="primary",
                icon=":material/sync:",
                width="stretch",
            ):
                with st.spinner("Sending authenticated payload to Person A…"):
                    try:
                        result = client.sync_person_a(period)
                        _flash(
                            "success",
                            f"Person A accepted {result['records_sent']} subscription "
                            f"record(s) for {result['period']}.",
                        )
                        st.rerun()
                    except ApiError as exc:
                        _api_error(exc)
        with col_preview:
            if st.button(
                "Preview payload",
                icon=":material/data_object:",
                width="stretch",
            ):
                try:
                    payload = client.payload(period)
                    st.session_state["b_payload_preview"] = payload
                except ApiError as exc:
                    _api_error(exc)
        if st.session_state.get("b_payload_preview"):
            with st.expander("Last previewed payload", expanded=True):
                st.json(st.session_state["b_payload_preview"])
    st.info(
        "Request timeout: 5s · up to 2 retries · `X-API-Key` authentication · "
        "stable external ID `sub:<subscription_id>:<period>` prevents duplicates in Person A.",
        icon=":material/info:",
    )
    with st.expander("Known limitation", icon=":material/warning:"):
        st.write(
            "Subscription expense records are monthly recurring-cost shares or manually recorded "
            "payments. Person B is not a payment processor and never claims a charge was executed "
            "automatically. Estimated rows remain marked as estimates in Person A."
        )


def page_project_info() -> None:
    st.title("Project information")
    st.markdown("### Smart Subscription Manager")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        col1.metric("Owner", "Shravan N A")
        col2.metric("Registration no.", "23MID0445")
        st.write(
            "A standalone application for recurring subscriptions, expected monthly/yearly "
            "costs, renewal dates, reminders, actual payment history, and an authenticated "
            "expense-data push to Person A."
        )
    st.subheader("Billing-cycle rules")
    st.markdown(
        "- **Weekly:** amount × 52 per year\n"
        "- **Monthly:** amount × 12 per year\n"
        "- **Quarterly:** amount × 4 per year\n"
        "- **Yearly:** amount per year\n"
        "- **Custom:** amount × 365 ÷ interval-days per year\n"
        "- Monthly equivalents divide the annual projection by 12 and round to two decimals."
    )
    st.subheader("Known limitations")
    st.markdown(
        "- Single-user, local academic application with no login.\n"
        "- Summaries are reported per currency; the dashboard headline totals are INR and no FX conversion is applied.\n"
        "- One actual payment is allowed per subscription per billing period in this scope, which also prevents duplicate external requests.\n"
        "- No payment provider is integrated; all actual payments are user-recorded facts.\n"
        "- Development API keys are stored in the local `.env` file."
    )
    st.caption(f"Database file: `{settings.project_dir / 'data' / 'person_b.db'}`")
    st.code(
        "python -m uvicorn api:app --host 127.0.0.1 --port 8002\n"
        "streamlit run app.py --server.port 8502",
        language="powershell",
    )


def main() -> None:
    st.set_page_config(
        page_title="Subscription Manager · Person B",
        page_icon=":material/autorenew:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()  # Glassmorphism design system (separate theme module)
    page = _sidebar()
    _show_flash()
    pages = {
        "Overview": page_overview,
        "Subscriptions": page_subscriptions,
        "Payments": page_payments,
        "Renewals": page_renewals,
        "Integrations": page_integrations,
        "Project info": page_project_info,
    }
    pages[page]()
    st.caption(
        "Person B · Shravan N A (23MID0445) · Smart Subscription Manager"
    )
