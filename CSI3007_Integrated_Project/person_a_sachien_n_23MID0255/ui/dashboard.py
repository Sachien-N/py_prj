"""Polished Streamlit dashboard for Person A.

All data access goes through the FastAPI backend. This module does not import
the ORM models or the database session.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pandas as pd
import plotly.express as px
import streamlit as st

from config import settings
from ui.api_client import ApiError, client
from ui.theme import apply_theme

PAGES = [
    "Overview",
    "Expenses",
    "Budgets",
    "Categories",
    "Reports & CSV",
    "Integrations",
    "Project info",
]
PAYMENT_METHODS = ["upi", "card", "cash", "net_banking", "other"]
TRANSACTION_TYPES = ["expense", "refund"]
PALETTE = ["#0f766e", "#0ea5e9", "#f59e0b", "#8b5cf6", "#ef4444", "#64748b"]


def _money(value: str | float | Decimal | None, currency: str = "INR") -> str:
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
        parsed = datetime.fromisoformat(value)
        return parsed.strftime("%d %b %Y, %H:%M")
    except ValueError:
        return value


def _date_range(value) -> tuple[date, date]:
    if isinstance(value, (tuple, list)):
        if len(value) == 2:
            return value[0], value[1]
        if value:
            return value[0], value[0]
    today = date.today()
    return today.replace(day=1), today


def _flash(level: str, message: str) -> None:
    st.session_state["a_flash"] = (level, message)


def _show_flash() -> None:
    item = st.session_state.pop("a_flash", None)
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


def _style_figure(fig, height: int = 340):
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
        st.markdown("## :material/account_balance_wallet: Expense manager")
        st.caption("Sachien N · 23MID0255")
        page = st.radio(
            "Navigation",
            PAGES,
            label_visibility="collapsed",
            key="a_nav",
        )
        st.divider()
        try:
            health = client.health()
            st.success(f"API online · {health.get('database', 'ok')}", icon=":material/check_circle:")
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
        st.caption("Person A · 23MID0255")
        st.caption("All figures in the dashboard are INR unless labelled otherwise.")
    return page


def _kpi_row(summary: dict, budget: dict | None) -> None:
    remaining = budget["remaining"] if budget and budget["total_budget"] != "0.00" else None
    with st.container(horizontal=True):
        st.metric("Total spending", _money(summary["total_expenses"]), border=True)
        st.metric("Refunds", _money(summary["total_refunds"]), border=True)
        st.metric("Net spending", _money(summary["net_spending"]), border=True)
        st.metric(
            "Budget remaining",
            _money(remaining) if remaining is not None else "No budget",
            border=True,
        )


def _expense_dataframe(items: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "Date": item["expense_date"],
                "Merchant": item["merchant"],
                "Category": item["category"],
                "Type": item["transaction_type"],
                "Amount (₹)": float(item["amount"]),
                "Payment": item["payment_method"],
                "Source": item["source_app"],
                "Estimated": item["is_estimated"],
            }
            for item in items
        ]
    )
    return frame


def page_overview() -> None:
    st.title("Financial overview")
    st.caption("A combined view of local spending, refunds, budgets and imported expenses.")
    today = date.today()
    selected = st.date_input(
        "Overview date range",
        value=(today.replace(day=1), today),
        key="a_overview_dates",
    )
    start, end = _date_range(selected)
    month = end.strftime("%Y-%m")
    try:
        summary = client.summary(start, end)
        budget = client.budget_overview(month)
        report = client.monthly_report(month, 6)
        integrations = client.integration_status(check_remote=False)
        recent = client.expenses(start_date=start, end_date=end, limit=8)
    except ApiError as exc:
        _api_error(exc)
        return

    _kpi_row(summary, budget)
    if budget["alerts"]:
        st.warning(
            f"{len(budget['alerts'])} budget(s) exceeded for {month}. Review the budgets page.",
            icon=":material/warning:",
        )

    if summary["transaction_count"] == 0:
        st.info(
            "No expenses in this range yet. Add an expense or import a CSV to populate the dashboard.",
            icon=":material/info:",
        )
        return

    col_left, col_right = st.columns(2)
    with col_left, st.container(border=True):
        st.subheader("Spending by category")
        category_frame = pd.DataFrame(summary["by_category"])
        if category_frame.empty:
            st.info("No category totals yet.")
        else:
            category_frame["net"] = category_frame["net"].astype(float)
            fig = px.pie(
                category_frame,
                names="category",
                values="net",
                hole=0.48,
                color_discrete_sequence=PALETTE,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(
                _style_figure(fig, 360),
                alt="Net spending share by expense category",
                key="a_category_pie",
            )
    with col_right, st.container(border=True):
        st.subheader("Six-month trend")
        trend = pd.DataFrame(report["monthly_trend"])
        for column in ("expenses", "refunds", "net"):
            trend[column] = trend[column].astype(float)
        fig = px.line(
            trend,
            x="month",
            y=["expenses", "refunds", "net"],
            markers=True,
            color_discrete_sequence=["#0f766e", "#f59e0b", "#0ea5e9"],
        )
        fig.update_layout(yaxis_title="Amount (₹)", xaxis_title="")
        st.plotly_chart(
            _style_figure(fig, 360),
            alt="Monthly expenses, refunds and net spending over six months",
            key="a_trend_line",
        )

    col_a, col_b = st.columns(2)
    with col_a, st.container(border=True):
        st.subheader("Budget vs actual")
        budget_rows = budget["budgets"]
        if not budget_rows:
            st.info("No budgets configured for this month.")
        else:
            frame = pd.DataFrame(
                [
                    {
                        "Budget": item["category"] or "Overall",
                        "Budget amount": float(item["amount"]),
                        "Spent": float(item["spent"]),
                    }
                    for item in budget_rows
                ]
            ).melt(id_vars="Budget", var_name="Measure", value_name="Amount")
            fig = px.bar(
                frame,
                x="Budget",
                y="Amount",
                color="Measure",
                barmode="group",
                color_discrete_sequence=["#94a3b8", "#0f766e"],
            )
            fig.update_layout(yaxis_title="Amount (₹)", xaxis_title="")
            st.plotly_chart(
                _style_figure(fig, 320),
                alt="Budgeted amount versus actual spending by budget scope",
                key="a_budget_compare",
            )
    with col_b, st.container(border=True):
        st.subheader("Imported expenses")
        if not summary["integrated"]:
            st.info("No subscription or electricity expenses have been imported yet.")
        for item in summary["integrated"]:
            label = "Person B · subscriptions" if item["source_app"] == "person_b" else "Person C · electricity"
            st.metric(label, _money(item["total"]), f"{item['count']} records", border=True)
        st.caption("Imported records are read-only here and deduplicated by source + external ID.")
        for source in integrations["sources"]:
            st.caption(
                f"{source['label']}: **{source['status']}** · last success {_when(source['last_success_at'])}"
            )

    with st.container(border=True):
        st.subheader("Recent transactions")
        if not recent:
            st.info("No transactions in the selected range.")
        else:
            st.dataframe(
                _expense_dataframe(recent),
                hide_index=True,
                alt="Most recent expense and refund records",
                column_config={
                    "Amount (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Date": st.column_config.DateColumn(),
                    "Estimated": st.column_config.CheckboxColumn(),
                },
            )


def _expense_form(
    prefix: str, categories: list[str], initial: dict | None = None
) -> dict | None:
    initial = initial or {}
    category_options = ["Auto categorize"] + categories
    initial_category = initial.get("category") or "Auto categorize"
    if initial_category not in category_options:
        category_options.append(initial_category)
    initial_payment = initial.get("payment_method", "upi")
    initial_type = initial.get("transaction_type", "expense")
    initial_date = date.today()
    if initial.get("expense_date"):
        initial_date = date.fromisoformat(str(initial["expense_date"])[:10])
    with st.form(f"{prefix}_expense_form", clear_on_submit=(prefix == "add")):
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input(
                "Amount (₹)",
                min_value=0.01,
                value=float(initial.get("amount", 250.00)),
                step=10.0,
                format="%.2f",
                key=f"{prefix}_amount",
            )
            spent_on = st.date_input(
                "Date", value=initial_date, key=f"{prefix}_date"
            )
            merchant = st.text_input(
                "Merchant",
                value=initial.get("merchant", ""),
                placeholder="e.g. Zomato, Metro, Apollo",
                key=f"{prefix}_merchant",
            )
            category = st.selectbox(
                "Category",
                category_options,
                index=category_options.index(initial_category),
                key=f"{prefix}_category",
            )
        with col2:
            payment = st.selectbox(
                "Payment method",
                PAYMENT_METHODS,
                index=PAYMENT_METHODS.index(initial_payment),
                key=f"{prefix}_payment",
            )
            tx_type = st.selectbox(
                "Transaction type",
                TRANSACTION_TYPES,
                index=TRANSACTION_TYPES.index(initial_type),
                key=f"{prefix}_type",
            )
            description = st.text_area(
                "Description",
                value=initial.get("description", ""),
                height=90,
                key=f"{prefix}_description",
            )
            refund_of = st.number_input(
                "Refund of expense ID (0 = none)",
                min_value=0,
                value=int(initial.get("refund_of_expense_id") or 0),
                step=1,
                key=f"{prefix}_refund_of",
                help="Optional link to the original expense for refund validation.",
            )
        submitted = st.form_submit_button(
            "Save expense", type="primary", icon=":material/save:"
        )
    if not submitted:
        return None
    if not merchant.strip():
        st.error("Merchant is required.")
        return None
    payload = {
        "amount": f"{amount:.2f}",
        "expense_date": spent_on.isoformat(),
        "merchant": merchant.strip(),
        "payment_method": payment,
        "description": description.strip(),
        "transaction_type": tx_type,
        "currency": "INR",
        "auto_categorize": True,
    }
    if category != "Auto categorize":
        payload["category"] = category
    if tx_type == "refund" and refund_of:
        payload["refund_of_expense_id"] = int(refund_of)
    return payload


def page_expenses() -> None:
    st.title("Expenses")
    st.caption("Record, search, correct and remove expenses and refunds.")
    try:
        categories = [item["name"] for item in client.categories()]
        expenses = client.expenses(limit=500)
    except ApiError as exc:
        _api_error(exc)
        return

    with st.expander("Add an expense", expanded=False, icon=":material/add_circle:"):
        payload = _expense_form("add", categories)
        if payload:
            try:
                created = client.create_expense(payload)
                _flash(
                    "success",
                    f"Saved #{created['id']} · {created['merchant']} · ₹{created['amount']}.",
                )
                st.rerun()
            except ApiError as exc:
                _api_error(exc)

    with st.container(border=True):
        st.subheader("Filters")
        col1, col2, col3 = st.columns(3)
        with col1:
            search = st.text_input("Search merchant or description", type="search")
            selected_category = st.selectbox("Category", ["All"] + categories)
        with col2:
            tx_filter = st.selectbox("Type", ["All"] + TRANSACTION_TYPES)
            source_filter = st.selectbox(
                "Source", ["All", "local", "person_b", "person_c"]
            )
        with col3:
            dates = st.date_input(
                "Date range",
                value=(date.today().replace(day=1), date.today()),
                key="a_expense_filter_dates",
            )
        start, end = _date_range(dates)
        try:
            expenses = client.expenses(
                start_date=start,
                end_date=end,
                search=search or None,
                category=None if selected_category == "All" else selected_category,
                transaction_type=None if tx_filter == "All" else tx_filter,
                source_app=None if source_filter == "All" else source_filter,
                limit=500,
            )
        except ApiError as exc:
            _api_error(exc)
            return

    if not expenses:
        st.info("No matching expenses. Adjust the filters or add a record.")
        return
    total = sum(
        Decimal(item["amount"]) * (1 if item["transaction_type"] == "expense" else -1)
        for item in expenses
    )
    st.caption(f"{len(expenses)} records · net ₹{total:,.2f} in the selected view")
    st.dataframe(
        _expense_dataframe(expenses),
        hide_index=True,
        alt="Filtered expense and refund records",
        column_config={
            "Amount (₹)": st.column_config.NumberColumn(format="₹%.2f"),
            "Date": st.column_config.DateColumn(),
            "Estimated": st.column_config.CheckboxColumn(),
        },
    )

    with st.expander("Edit or delete a record", icon=":material/edit:"):
        labels = {
            item["id"]: f"#{item['id']} · {item['expense_date']} · {item['merchant']} · ₹{item['amount']}"
            for item in expenses
        }
        selected_id = st.selectbox(
            "Select expense",
            list(labels),
            format_func=lambda value: labels[value],
            key="a_edit_select",
        )
        try:
            selected = client.expense(selected_id)
        except ApiError as exc:
            _api_error(exc)
            return
        if selected["source_app"] != "local":
            st.warning(
                "This record was imported from another application and is read-only here. "
                "Change it at the source and synchronise again.",
                icon=":material/lock:",
            )
            return
        edit_payload = _expense_form(f"edit_{selected_id}", categories, selected)
        if edit_payload:
            edit_payload.pop("auto_categorize", None)
            try:
                client.update_expense(selected_id, edit_payload)
                _flash("success", f"Updated expense #{selected_id}.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)
        confirm = st.checkbox(
            f"I understand deleting #{selected_id} cannot be undone",
            key=f"a_delete_confirm_{selected_id}",
        )
        if st.button(
            "Delete expense",
            disabled=not confirm,
            icon=":material/delete:",
            key=f"a_delete_button_{selected_id}",
        ):
            try:
                client.delete_expense(selected_id)
                _flash("success", f"Deleted expense #{selected_id}.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)


def page_budgets() -> None:
    st.title("Budgets")
    st.caption("Set an overall monthly cap and/or category caps. Usage is based on net spending.")
    selected_month = st.date_input(
        "Budget month", value=date.today(), key="a_budget_month"
    )
    if isinstance(selected_month, (tuple, list)):
        selected_month = selected_month[0]
    month = selected_month.strftime("%Y-%m")
    try:
        overview = client.budget_overview(month)
        categories = [item["name"] for item in client.categories()]
    except ApiError as exc:
        _api_error(exc)
        return

    with st.container(horizontal=True):
        st.metric("Total budget", _money(overview["total_budget"]), border=True)
        st.metric("Net spent", _money(overview["total_spent"]), border=True)
        st.metric("Remaining", _money(overview["remaining"]), border=True)
        st.metric("Usage", f"{overview['usage_percent']:.1f}%", border=True)
    if overview["budget_count"] == 0:
        st.info(
            "No budget is configured for this month. Add an overall budget for a single cap, "
            "or category budgets for finer control."
        )
    elif overview["exceeded"]:
        st.error(
            f"Budget exceeded by {_money(abs(Decimal(overview['remaining'])))} for {month}.",
            icon=":material/error:",
        )
    else:
        st.success("Spending is within the configured budget.", icon=":material/check_circle:")
    if overview["budgets"]:
        progress_rows = pd.DataFrame(
            [
                {
                    "Scope": item["category"] or "Overall",
                    "Used": min(float(item["usage_percent"]) / 100, 1.0),
                    "Usage %": item["usage_percent"],
                    "Spent": float(item["spent"]),
                    "Budget": float(item["amount"]),
                }
                for item in overview["budgets"]
            ]
        )
        for _, row in progress_rows.iterrows():
            st.progress(
                float(row["Used"]),
                text=f"{row['Scope']} · {row['Usage %']:.1f}% · ₹{row['Spent']:,.2f} of ₹{row['Budget']:,.2f}",
            )
        fig = px.bar(
            progress_rows,
            x="Scope",
            y=["Budget", "Spent"],
            barmode="group",
            color_discrete_sequence=["#94a3b8", "#0f766e"],
        )
        fig.update_layout(yaxis_title="Amount (₹)", xaxis_title="")
        st.plotly_chart(
            _style_figure(fig),
            alt="Budget and spending by scope for the selected month",
            key="a_budget_page_chart",
        )

    with st.expander("Add a budget", icon=":material/add:"):
        with st.form("a_add_budget"):
            scope = st.selectbox("Budget scope", ["Overall"] + categories)
            amount = st.number_input(
                "Monthly amount (₹)", min_value=1.0, value=5000.0, step=100.0, format="%.2f"
            )
            notes = st.text_input("Notes", max_chars=240)
            submitted = st.form_submit_button(
                "Create budget", type="primary", icon=":material/save:"
            )
        if submitted:
            payload = {
                "month": month,
                "amount": f"{amount:.2f}",
                "notes": notes.strip(),
            }
            if scope != "Overall":
                payload["category"] = scope
            try:
                client.create_budget(payload)
                _flash("success", f"Budget saved for {month}.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)

    if overview["budgets"]:
        with st.expander("Edit or delete a budget", icon=":material/edit:"):
            labels = {
                item["id"]: f"{item['category'] or 'Overall'} · {item['month']} · ₹{item['amount']}"
                for item in overview["budgets"]
            }
            selected_id = st.selectbox(
                "Budget",
                list(labels),
                format_func=lambda value: labels[value],
                key="a_budget_edit_select",
            )
            selected = next(item for item in overview["budgets"] if item["id"] == selected_id)
            with st.form(f"a_edit_budget_{selected_id}"):
                new_amount = st.number_input(
                    "Monthly amount (₹)",
                    min_value=1.0,
                    value=float(selected["amount"]),
                    step=100.0,
                    format="%.2f",
                    key=f"a_budget_amount_{selected_id}",
                )
                new_notes = st.text_input(
                    "Notes",
                    value=selected["notes"],
                    max_chars=240,
                    key=f"a_budget_notes_{selected_id}",
                )
                save = st.form_submit_button("Update budget", icon=":material/save:")
            if save:
                try:
                    client.update_budget(
                        selected_id,
                        {"amount": f"{new_amount:.2f}", "notes": new_notes.strip()},
                    )
                    _flash("success", "Budget updated.")
                    st.rerun()
                except ApiError as exc:
                    _api_error(exc)
            confirm = st.checkbox(
                "Confirm deletion", key=f"a_budget_delete_confirm_{selected_id}"
            )
            if st.button(
                "Delete budget",
                disabled=not confirm,
                icon=":material/delete:",
                key=f"a_budget_delete_{selected_id}",
            ):
                try:
                    client.delete_budget(selected_id)
                    _flash("success", "Budget deleted.")
                    st.rerun()
                except ApiError as exc:
                    _api_error(exc)


def page_categories() -> None:
    st.title("Categories")
    st.caption("Categories own the keyword rules used by automatic categorization.")
    try:
        categories = client.categories(include_inactive=True)
    except ApiError as exc:
        _api_error(exc)
        return
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Name": item["name"],
                    "Description": item["description"],
                    "Keywords": ", ".join(item["keywords"]),
                    "Priority": item["priority"],
                    "Active": item["is_active"],
                }
                for item in categories
            ]
        ),
        hide_index=True,
        alt="Configured expense categories and keyword rules",
        column_config={
            "Priority": st.column_config.ProgressColumn(min_value=0, max_value=100),
            "Active": st.column_config.CheckboxColumn(),
        },
    )

    add_col, edit_col = st.columns(2)
    with add_col, st.container(border=True):
        st.subheader("Add category")
        with st.form("a_add_category"):
            name = st.text_input("Name", max_chars=60)
            description = st.text_input("Description", max_chars=240)
            keywords = st.text_area(
                "Keywords (comma-separated)", height=90, placeholder="cafe, bakery, food"
            )
            color = st.color_picker("Colour", "#0f766e")
            priority = st.slider("Priority", 0, 100, 50)
            submitted = st.form_submit_button(
                "Create category", type="primary", icon=":material/add:"
            )
        if submitted:
            try:
                client.create_category(
                    {
                        "name": name,
                        "description": description,
                        "keywords": [part.strip() for part in keywords.split(",") if part.strip()],
                        "color": color,
                        "priority": priority,
                    }
                )
                _flash("success", f"Category “{name}” created.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)

    with edit_col, st.container(border=True):
        st.subheader("Edit category")
        labels = {item["id"]: item["name"] for item in categories}
        selected_id = st.selectbox(
            "Category", list(labels), format_func=lambda value: labels[value], key="a_cat_select"
        )
        selected = next(item for item in categories if item["id"] == selected_id)
        with st.form(f"a_edit_category_{selected_id}"):
            new_name = st.text_input(
                "Name", value=selected["name"], max_chars=60, key=f"a_cat_name_{selected_id}"
            )
            new_description = st.text_input(
                "Description",
                value=selected["description"],
                max_chars=240,
                key=f"a_cat_desc_{selected_id}",
            )
            new_keywords = st.text_area(
                "Keywords (comma-separated)",
                value=", ".join(selected["keywords"]),
                height=90,
                key=f"a_cat_keywords_{selected_id}",
            )
            new_color = st.color_picker(
                "Colour", selected["color"], key=f"a_cat_color_{selected_id}"
            )
            new_priority = st.slider(
                "Priority",
                0,
                100,
                int(selected["priority"]),
                key=f"a_cat_priority_{selected_id}",
            )
            active = st.checkbox(
                "Active", value=selected["is_active"], key=f"a_cat_active_{selected_id}"
            )
            save = st.form_submit_button("Update category", icon=":material/save:")
        if save:
            try:
                client.update_category(
                    selected_id,
                    {
                        "name": new_name,
                        "description": new_description,
                        "keywords": [
                            part.strip()
                            for part in new_keywords.split(",")
                            if part.strip()
                        ],
                        "color": new_color,
                        "priority": new_priority,
                        "is_active": active,
                    },
                )
                _flash("success", "Category updated.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)
        confirm = st.checkbox(
            "Confirm deletion", key=f"a_cat_delete_confirm_{selected_id}"
        )
        if st.button(
            "Delete category",
            disabled=not confirm,
            icon=":material/delete:",
            key=f"a_cat_delete_{selected_id}",
        ):
            try:
                client.delete_category(selected_id)
                _flash("success", "Category deleted.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)


def page_reports() -> None:
    st.title("Reports and CSV")
    st.caption("Monthly reports, interactive charts, exports and validated imports.")
    selected = st.date_input("Report month", value=date.today(), key="a_report_month")
    if isinstance(selected, (tuple, list)):
        selected = selected[0]
    month = selected.strftime("%Y-%m")
    months = st.slider("Months in trend", 3, 12, 6, key="a_report_months")
    try:
        report = client.monthly_report(month, months)
    except ApiError as exc:
        _api_error(exc)
        return
    summary = report["summary"]
    with st.container(horizontal=True):
        st.metric("Total spending", _money(summary["total_expenses"]), border=True)
        st.metric("Refunds", _money(summary["total_refunds"]), border=True)
        st.metric("Net", _money(summary["net_spending"]), border=True)
        st.metric("Transactions", summary["transaction_count"], border=True)

    col1, col2 = st.columns(2)
    with col1, st.container(border=True):
        st.subheader("Daily net spending")
        daily = pd.DataFrame(report["daily_trend"])
        if daily.empty:
            st.info("No transactions in this month.")
        else:
            daily["net"] = daily["net"].astype(float)
            fig = px.area(daily, x="date", y="net", color_discrete_sequence=["#0f766e"])
            fig.update_layout(yaxis_title="Net (₹)", xaxis_title="")
            st.plotly_chart(
                _style_figure(fig),
                alt="Daily net spending for the selected month",
                key="a_daily_area",
            )
    with col2, st.container(border=True):
        st.subheader("Monthly comparison")
        trend = pd.DataFrame(report["monthly_trend"])
        for column in ("expenses", "refunds", "net"):
            trend[column] = trend[column].astype(float)
        fig = px.bar(
            trend,
            x="month",
            y=["expenses", "refunds"],
            barmode="group",
            color_discrete_sequence=["#0f766e", "#f59e0b"],
        )
        fig.update_layout(yaxis_title="Amount (₹)", xaxis_title="")
        st.plotly_chart(
            _style_figure(fig),
            alt="Monthly expenses and refunds comparison",
            key="a_monthly_bars",
        )

    with st.container(border=True):
        st.subheader("Category summary")
        cats = pd.DataFrame(summary["by_category"])
        if cats.empty:
            st.info("No category data for this month.")
        else:
            st.dataframe(
                cats.rename(
                    columns={
                        "category": "Category",
                        "expense": "Expenses (₹)",
                        "refund": "Refunds (₹)",
                        "net": "Net (₹)",
                    }
                )[["Category", "Expenses (₹)", "Refunds (₹)", "Net (₹)"]],
                hide_index=True,
                alt="Category summary for the selected month",
                column_config={
                    "Expenses (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Refunds (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Net (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                },
            )

    col_export, col_import = st.columns(2)
    with col_export, st.container(border=True):
        st.subheader("Export")
        st.caption("Exports the selected month as a UTF-8 CSV with spreadsheet-safe text.")
        try:
            start = date.fromisoformat(report["period_start"])
            end = date.fromisoformat(report["period_end"])
            csv_bytes = client.export_csv(start_date=start, end_date=end)
            st.download_button(
                "Download monthly expenses CSV",
                data=csv_bytes,
                file_name=f"expenses_{month}.csv",
                mime="text/csv",
                icon=":material/download:",
                width="stretch",
            )
        except ApiError as exc:
            _api_error(exc)
    with col_import, st.container(border=True):
        st.subheader("Import")
        st.caption(
            "Required columns: date, amount, merchant. Optional: category, payment_method, "
            "description, transaction_type, currency. Invalid rows reject the whole file."
        )
        uploaded = st.file_uploader(
            "Expense CSV", type=["csv"], key="a_csv_uploader", label_visibility="collapsed"
        )
        if uploaded is not None and st.button(
            "Validate and import", icon=":material/upload_file:"
        ):
            try:
                result = client.import_csv(uploaded.name, uploaded.getvalue())
                _flash("success", result["message"])
                st.rerun()
            except ApiError as exc:
                _api_error(exc)


def page_integrations() -> None:
    st.title("Integrations")
    st.caption(
        "Person A receives authenticated REST pushes from Person B and Person C. "
        "Manual sync pulls the same documented payloads. No databases are shared."
    )
    check_remote = st.toggle("Check live connectivity", value=True, key="a_check_remote")
    try:
        status = client.integration_status(check_remote=check_remote)
    except ApiError as exc:
        _api_error(exc)
        return

    for source in status["sources"]:
        with st.container(border=True):
            col_info, col_action = st.columns([2, 1])
            with col_info:
                st.subheader(source["label"])
                st.caption(f"Source key: `{source['source']}` · {source['api_url']}")
                state_col, success_col, items_col = st.columns(3)
                state_col.metric("Last sync", source["status"].title())
                success_col.metric("Last success", _when(source["last_success_at"]))
                items_col.metric(
                    "Imported / updated",
                    f"{source['items_imported']} / {source['items_updated']}",
                )
                if source.get("remote_health"):
                    health = source["remote_health"]
                    if health["reachable"]:
                        st.success("Remote API reachable", icon=":material/link:")
                    else:
                        st.warning(
                            "Remote API currently unreachable. Last successful local data is preserved.",
                            icon=":material/link_off:",
                        )
                if source["last_error"]:
                    st.caption(f"Last error: {source['last_error']}")
            with col_action:
                label = (
                    "Sync subscriptions"
                    if source["source"] == "person_b"
                    else "Sync electricity"
                )
                if st.button(
                    label,
                    icon=":material/sync:",
                    key=f"a_sync_{source['source']}",
                    width="stretch",
                ):
                    with st.spinner(f"Pulling from {source['source']}…"):
                        try:
                            if source["source"] == "person_b":
                                result = client.sync_subscriptions()
                            else:
                                result = client.sync_electricity()
                            _flash(
                                "success",
                                f"Imported {result['records_imported']} and updated "
                                f"{result['records_updated']} records.",
                            )
                            st.rerun()
                        except ApiError as exc:
                            _api_error(exc)
                st.caption("Request timeout: 5s · up to 2 retries · idempotent external IDs")

    st.info(
        "A failed sync never writes placeholder amounts. The timestamp above shows the latest "
        "successful import, and the source applications continue to work while Person A is offline.",
        icon=":material/info:",
    )
    with st.expander("How the integration contract works", icon=":material/description:"):
        st.markdown(
            "**Authentication:** `X-API-Key` header with the configured development key.  \n"
            "**Person B push:** `POST http://127.0.0.1:8001/integrations/subscriptions/sync`  \n"
            "**Person C push:** `POST http://127.0.0.1:8001/integrations/electricity/sync`  \n"
            "**Deduplication:** unique `(source_app, external_id)` in Person A. Repeated records update, never duplicate.  \n"
            "**Failure handling:** connection errors return HTTP 503, the attempt is logged, and no data is fabricated."
        )
        st.caption("See the root README and integration_tests/ for complete JSON examples.")


def page_project_info() -> None:
    st.title("Project information")
    st.markdown("### Smart Expense Categorization and Budget Manager")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        col1.metric("Owner", "Sachien N")
        col2.metric("Registration no.", "23MID0255")
        st.write(
            "A personal finance application for expense capture, configurable keyword-based "
            "automatic categorization, monthly budgets, refund-aware net spending, CSV data "
            "exchange, and authenticated REST integration with the subscription and electricity "
            "projects."
        )
    st.subheader("Architecture")
    st.markdown(
        "- **Frontend:** Streamlit dashboard; all requests go through HTTP.\n"
        "- **Backend:** FastAPI + SQLAlchemy; Pydantic validation.\n"
        "- **Database:** separate SQLite file, never shared with Person B or Person C.\n"
        "- **Integration:** JSON over HTTP with `X-API-Key` authentication and external-ID deduplication.\n"
        "- **Money:** Decimal in the backend; amounts serialized as two-decimal strings."
    )
    st.subheader("Technology")
    st.write("Python 3.11+ · Streamlit · FastAPI · SQLAlchemy · SQLite · Pydantic · Plotly · pandas")
    st.subheader("Known limitations")
    st.markdown(
        "- This is a single-user local academic application; there is no user login or multi-tenant isolation.\n"
        "- Development API keys are stored in the local `.env` file and must be replaced for any shared deployment.\n"
        "- Multi-currency records are stored, but budgets and the main dashboard total are INR-only; no FX conversion is performed.\n"
        "- Imported external rows are read-only in Person A and must be corrected at their source."
    )
    st.caption(f"Database file: `{settings.project_dir / 'data' / 'person_a.db'}`")
    st.code(
        "python -m uvicorn api:app --host 127.0.0.1 --port 8001\n"
        "streamlit run app.py --server.port 8501",
        language="powershell",
    )


def main() -> None:
    st.set_page_config(
        page_title="Expense Manager · Person A",
        page_icon=":material/account_balance_wallet:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()  # Claymorphism design system (separate theme module)
    page = _sidebar()
    _show_flash()
    pages = {
        "Overview": page_overview,
        "Expenses": page_expenses,
        "Budgets": page_budgets,
        "Categories": page_categories,
        "Reports & CSV": page_reports,
        "Integrations": page_integrations,
        "Project info": page_project_info,
    }
    pages[page]()
    st.caption(
        "Person A · Sachien N (23MID0255) · Smart Expense Categorization and Budget Manager"
    )
