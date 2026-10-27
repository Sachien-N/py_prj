"""Streamlit dashboard for Person C's electricity monitoring project."""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pandas as pd
import plotly.express as px
import streamlit as st

from config import settings
from ui.api_client import ApiError, client
from ui.theme import apply_theme

PAGES = [
    "Overview",
    "Sockets",
    "Readings",
    "Tariffs",
    "Bills & verification",
    "Six-month analysis",
    "Exports",
    "Integrations",
    "Project info",
]
PAYMENT_METHODS = ["manual", "simulated", "adapter"]
PALETTE = ["#d97706", "#0ea5e9", "#10b981", "#8b5cf6", "#ef4444", "#64748b"]
COVERAGE_WARNING = (
    "Socket readings may not cover the entire household. Coverage is measured over observed "
    "reading intervals, not every appliance or circuit. All costs are estimates."
)


def _money(value, currency: str = "INR") -> str:
    try:
        number = Decimal(str(value or "0"))
    except Exception:
        number = Decimal("0")
    symbol = "₹" if currency == "INR" else f"{currency} "
    return f"{symbol}{number:,.2f}"


def _kwh(value) -> str:
    try:
        return f"{Decimal(str(value or '0')):,.3f} kWh"
    except Exception:
        return "—"


def _when(value: str | None) -> str:
    if not value:
        return "Never"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime(
            "%d %b %Y, %H:%M"
        )
    except ValueError:
        return value


def _flash(level: str, message: str) -> None:
    st.session_state["c_flash"] = (level, message)


def _show_flash() -> None:
    item = st.session_state.pop("c_flash", None)
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


def _date_range(value) -> tuple[date, date]:
    if isinstance(value, (tuple, list)):
        if len(value) == 2:
            return value[0], value[1]
        if value:
            return value[0], value[0]
    today = date.today()
    return today.replace(day=1), today


def _sidebar() -> str:
    with st.sidebar:
        st.markdown("## :material/bolt: Electricity monitor")
        st.caption("HARIHARAN S · 23MID0182")
        page = st.radio(
            "Navigation", PAGES, label_visibility="collapsed", key="c_nav"
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
        st.warning("Estimates only", icon=":material/info:")
        st.caption(
            "This app never claims TNEB/TANGEDCO issued an incorrect bill. Configured tariffs "
            "must be verified independently."
        )
    return page


def _socket_table(sockets: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Socket": item["name"],
                "Appliance": item["appliance"],
                "Rated W": float(item["rated_power_w"]),
                "Location": item["location"],
                "Active": item["is_active"],
                "Adapter": item["adapter_type"],
                "Simulated demo": item["is_demo"],
            }
            for item in sockets
        ]
    )


def page_overview() -> None:
    st.title("Electricity overview")
    st.caption("Observed socket consumption, estimated costs, and recorded bills.")
    today = date.today()
    selected = st.date_input(
        "Overview period",
        value=(today.replace(day=1), today),
        key="c_overview_dates",
    )
    start, end = _date_range(selected)
    try:
        sockets = client.sockets()
        daily = client.daily(start, end)
        by_socket = client.by_socket(start, end)
        estimate = client.period_estimate(start, end)
        cost_start = (start.replace(day=1) - timedelta(days=160)).replace(day=1)
        costs = client.monthly_costs(cost_start, end)
        bills = client.bills()
    except ApiError as exc:
        _api_error(exc)
        return

    with st.container(horizontal=True):
        st.metric("Monitored energy", _kwh(daily["total_energy_kwh"]), border=True)
        st.metric("Data coverage", f"{daily['data_coverage_pct']:.1f}%", border=True)
        st.metric(
            "Estimated cost",
            _money(estimate["estimated_cost"]) if estimate["estimated_cost"] else "No data",
            border=True,
        )
        st.metric("Active sockets", sum(1 for item in sockets if item["is_active"]), border=True)
    st.warning(COVERAGE_WARNING, icon=":material/warning:")
    if daily["simulated"]:
        st.info("The selected range includes simulated readings. Labels mark them explicitly.")

    if not sockets:
        st.info(
            "No sockets registered. Add a socket and readings, or generate demo data from the "
            "Integrations page.",
            icon=":material/electrical_services:",
        )
        return
    if not daily["total_energy_kwh"] or Decimal(daily["total_energy_kwh"]) == 0:
        st.info(
            "No usable reading intervals in this range. Add at least two readings with a time "
            "difference no larger than the configured maximum gap.",
            icon=":material/info:",
        )

    col1, col2 = st.columns(2)
    with col1, st.container(border=True):
        st.subheader("Daily consumption")
        frame = pd.DataFrame(daily["days"])
        frame["energy_kwh"] = pd.to_numeric(frame["energy_kwh"], errors="coerce")
        if frame["energy_kwh"].notna().any():
            fig = px.area(
                frame,
                x="date",
                y="energy_kwh",
                color_discrete_sequence=["#d97706"],
            )
            fig.update_layout(yaxis_title="Energy (kWh)", xaxis_title="")
            st.plotly_chart(
                _style_figure(fig),
                alt="Daily monitored socket energy consumption",
                key="c_daily_area",
            )
        else:
            st.info("No energy intervals to chart.")
    with col2, st.container(border=True):
        st.subheader("Consumption by socket")
        socket_frame = pd.DataFrame(by_socket["sockets"])
        if socket_frame.empty or socket_frame["energy_kwh"].isna().all():
            st.info("No per-socket intervals to chart.")
        else:
            socket_frame["energy_kwh"] = pd.to_numeric(
                socket_frame["energy_kwh"], errors="coerce"
            )
            socket_frame = socket_frame.dropna(subset=["energy_kwh"])
            fig = px.bar(
                socket_frame,
                x="name",
                y="energy_kwh",
                color="name",
                color_discrete_sequence=PALETTE,
                text_auto=".2f",
            )
            fig.update_layout(xaxis_title="", yaxis_title="Energy (kWh)", showlegend=False)
            st.plotly_chart(
                _style_figure(fig),
                alt="Energy consumption comparison by smart socket",
                key="c_socket_bar",
            )

    with st.container(border=True):
        st.subheader("Estimated monthly cost vs recorded bills")
        cost_frame = pd.DataFrame(costs["months"])
        cost_frame["estimated_cost"] = pd.to_numeric(
            cost_frame["estimated_cost"], errors="coerce"
        )
        bill_frame = pd.DataFrame(
            [
                {
                    "month": bill["billing_period_start"][:7],
                    "Actual bill": float(bill["bill_amount"]),
                }
                for bill in bills
            ]
        )
        merged = cost_frame[["month", "estimated_cost"]].rename(
            columns={"estimated_cost": "Estimated (configured tariff)"}
        )
        if not bill_frame.empty:
            merged = merged.merge(
                bill_frame.groupby("month", as_index=False)["Actual bill"].sum(),
                on="month",
                how="left",
            )
        if merged["Estimated (configured tariff)"].notna().any():
            plot_frame = merged.melt(
                id_vars="month", var_name="Measure", value_name="Amount"
            ).dropna()
            fig = px.bar(
                plot_frame,
                x="month",
                y="Amount",
                color="Measure",
                barmode="group",
                color_discrete_sequence=["#f59e0b", "#0f766e"],
            )
            fig.update_layout(
                xaxis_title="", yaxis_title="Amount (₹)", legend_title_text=""
            )
            st.plotly_chart(
                _style_figure(fig, 360),
                alt="Monthly estimated electricity cost compared with actual recorded bills",
                key="c_cost_bills",
            )
        else:
            st.info("Not enough reading/tariff data to estimate monthly costs.")
        st.caption(
            "Estimated costs apply the configured tariff (and its fixed/percentage components) "
            "to socket-estimated units. Actual bills are shown only where manually recorded."
        )

    if bills:
        with st.container(border=True):
            st.subheader("Recent bills")
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Reference": bill["bill_reference"],
                            "Period": f"{bill['billing_period_start']} → {bill['billing_period_end']}",
                            "Units": float(bill["billed_units"]),
                            "Amount (₹)": float(bill["bill_amount"]),
                            "Compared": bill["has_comparison"],
                        }
                        for bill in bills[:6]
                    ]
                ),
                hide_index=True,
                alt="Most recent recorded electricity bills",
                column_config={
                    "Units": st.column_config.NumberColumn(format="%.2f"),
                    "Amount (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Compared": st.column_config.CheckboxColumn(),
                },
            )


def page_sockets() -> None:
    st.title("Sockets and appliances")
    st.caption("Register the monitored circuits and their rated power.")
    try:
        sockets = client.sockets()
    except ApiError as exc:
        _api_error(exc)
        return

    with st.expander("Add a socket", icon=":material/add_circle:"):
        with st.form("c_add_socket"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Socket name", max_chars=120)
                appliance = st.text_input("Appliance", max_chars=120)
                rated = st.number_input(
                    "Rated power (W)", min_value=0.01, value=1000.0, step=50.0
                )
            with col2:
                location = st.text_input("Location", max_chars=120)
                active = st.checkbox("Active", value=True)
                adapter = st.selectbox(
                    "Adapter type", ["manual", "simulated", "future_vendor", "mqtt"]
                )
            submitted = st.form_submit_button(
                "Register socket", type="primary", icon=":material/add:"
            )
        if submitted:
            try:
                client.create_socket(
                    {
                        "name": name,
                        "appliance": appliance,
                        "rated_power_w": f"{rated:.2f}",
                        "location": location,
                        "is_active": active,
                        "adapter_type": adapter,
                    }
                )
                _flash("success", "Socket registered.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)

    if not sockets:
        st.info("No sockets registered yet.")
        return
    st.dataframe(
        _socket_table(sockets),
        hide_index=True,
        alt="Registered smart sockets and appliances",
        column_config={
            "Rated W": st.column_config.NumberColumn(format="%.2f W"),
            "Active": st.column_config.CheckboxColumn(),
            "Simulated demo": st.column_config.CheckboxColumn(),
        },
    )

    with st.expander("Edit or delete a socket", icon=":material/edit:"):
        labels = {
            item["id"]: f"#{item['id']} · {item['name']} · {item['appliance']}"
            for item in sockets
        }
        selected_id = st.selectbox(
            "Socket",
            list(labels),
            format_func=lambda value: labels[value],
            key="c_socket_edit",
        )
        selected = next(item for item in sockets if item["id"] == selected_id)
        with st.form(f"c_edit_socket_{selected_id}"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(
                    "Socket name", value=selected["name"], key=f"c_sock_name_{selected_id}"
                )
                appliance = st.text_input(
                    "Appliance",
                    value=selected["appliance"],
                    key=f"c_sock_app_{selected_id}",
                )
                rated = st.number_input(
                    "Rated power (W)",
                    min_value=0.01,
                    value=float(selected["rated_power_w"]),
                    key=f"c_sock_rated_{selected_id}",
                )
            with col2:
                location = st.text_input(
                    "Location",
                    value=selected["location"],
                    key=f"c_sock_location_{selected_id}",
                )
                active = st.checkbox(
                    "Active",
                    value=selected["is_active"],
                    key=f"c_sock_active_{selected_id}",
                )
                adapter = st.selectbox(
                    "Adapter type",
                    ["manual", "simulated", "future_vendor", "mqtt"],
                    index=["manual", "simulated", "future_vendor", "mqtt"].index(
                        selected["adapter_type"]
                    ),
                    key=f"c_sock_adapter_{selected_id}",
                )
            save = st.form_submit_button("Update socket", icon=":material/save:")
        if save:
            try:
                client.update_socket(
                    selected_id,
                    {
                        "name": name,
                        "appliance": appliance,
                        "rated_power_w": f"{rated:.2f}",
                        "location": location,
                        "is_active": active,
                        "adapter_type": adapter,
                    },
                )
                _flash("success", "Socket updated.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)
        confirm = st.checkbox(
            "Deleting a socket also deletes its readings",
            key=f"c_sock_delete_confirm_{selected_id}",
        )
        if st.button(
            "Delete socket",
            disabled=not confirm,
            icon=":material/delete:",
            key=f"c_sock_delete_{selected_id}",
        ):
            try:
                client.delete_socket(selected_id)
                _flash("success", "Socket and its readings deleted.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)


def page_readings() -> None:
    st.title("Readings")
    st.caption(
        "Readings are instantaneous power samples. Energy is computed between consecutive "
        "readings; gaps longer than the configured maximum are excluded."
    )
    try:
        sockets = client.sockets()
    except ApiError as exc:
        _api_error(exc)
        return
    if not sockets:
        st.info("Register a socket first.")
        return
    socket_labels = {item["id"]: f"{item['name']} ({item['appliance']})" for item in sockets}
    selected_socket = st.selectbox(
        "Active socket",
        list(socket_labels),
        format_func=lambda value: socket_labels[value],
        key="c_read_socket",
    )
    socket = next(item for item in sockets if item["id"] == selected_socket)

    col_add, col_sim = st.columns(2)
    with col_add, st.container(border=True):
        st.subheader("Add a manual reading")
        with st.form("c_add_reading"):
            left, right = st.columns(2)
            with left:
                day = st.date_input("Reading date", value=date.today())
                clock = st.time_input("Reading time", value=time(12, 0))
                power = st.number_input(
                    "Power (W)",
                    min_value=0.0,
                    max_value=100000.0,
                    value=float(socket["rated_power_w"]) * 0.5,
                    step=10.0,
                )
            with right:
                cumulative = st.checkbox("Accumulated energy is available")
                cumulative_value = st.number_input(
                    "Cumulative energy (kWh)",
                    min_value=0.0,
                    value=0.0,
                    step=0.1,
                    disabled=not cumulative,
                )
                notes = st.text_input("Notes", max_chars=240)
            submitted = st.form_submit_button(
                "Store reading", type="primary", icon=":material/save:"
            )
        if submitted:
            reading_at = datetime.combine(day, clock, tzinfo=settings.timezone)
            if reading_at > datetime.now(settings.timezone) + timedelta(minutes=5):
                st.error("Reading time cannot be in the future.")
            else:
                try:
                    result = client.create_reading(
                        {
                            "socket_id": selected_socket,
                            "reading_at": reading_at.isoformat(),
                            "power_w": f"{power:.2f}",
                            "cumulative_energy_kwh": (
                                f"{cumulative_value:.3f}" if cumulative else None
                            ),
                            "source": "manual",
                            "notes": notes,
                        }
                    )
                    _flash("success", f"Reading #{result['id']} stored.")
                    st.rerun()
                except ApiError as exc:
                    _api_error(exc)
    with col_sim, st.container(border=True):
        st.subheader("Generate simulated readings")
        st.caption("Clearly labelled simulated data for demonstrations. Not a real measurement.")
        with st.form("c_simulate"):
            days = st.slider("Days of history", 1, 90, 14)
            interval = st.select_slider(
                "Interval", options=[15, 30, 60, 120, 240], value=60
            )
            simulate = st.form_submit_button(
                "Generate simulation", icon=":material/auto_awesome:"
            )
        if simulate:
            try:
                result = client.simulate(selected_socket, days, interval)
                _flash(
                    "warning",
                    f"Created {result['created']} simulated readings. They are labelled simulated.",
                )
                st.rerun()
            except ApiError as exc:
                _api_error(exc)

    try:
        readings = client.readings(selected_socket, limit=500)
    except ApiError as exc:
        _api_error(exc)
        return
    st.subheader("Recent readings")
    if not readings:
        st.info("No readings for this socket yet.")
        return
    frame = pd.DataFrame(
        [
            {
                "ID": item["id"],
                "Timestamp": item["reading_at"],
                "Power (W)": float(item["power_w"]),
                "Cumulative kWh": (
                    float(item["cumulative_energy_kwh"])
                    if item["cumulative_energy_kwh"] is not None
                    else None
                ),
                "Source": item["source"],
                "Quality": item["quality_flag"],
                "Out of order": item["out_of_order"],
                "Simulated": item["is_simulated"],
            }
            for item in readings
        ]
    )
    st.dataframe(
        frame,
        hide_index=True,
        alt="Recent electricity readings for the selected socket",
        column_config={
            "Power (W)": st.column_config.NumberColumn(format="%.2f W"),
            "Cumulative kWh": st.column_config.NumberColumn(format="%.3f"),
            "Out of order": st.column_config.CheckboxColumn(),
            "Simulated": st.column_config.CheckboxColumn(),
        },
    )
    with st.expander("Delete a reading", icon=":material/delete:"):
        reading_labels = {
            item["id"]: f"#{item['id']} · {item['reading_at']} · {item['power_w']} W"
            for item in readings
        }
        reading_id = st.selectbox(
            "Reading",
            list(reading_labels),
            format_func=lambda value: reading_labels[value],
            key="c_reading_delete_select",
        )
        confirm = st.checkbox(
            "Confirm deletion", key=f"c_reading_delete_confirm_{reading_id}"
        )
        if st.button(
            "Delete reading",
            disabled=not confirm,
            icon=":material/delete:",
            key=f"c_reading_delete_{reading_id}",
        ):
            try:
                client.delete_reading(reading_id)
                _flash("success", "Reading deleted.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)


def _tariff_table(tariffs: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Name": item["name"],
                "Category": item["category"],
                "Effective from": item["effective_from"],
                "Effective to": item["effective_to"],
                "Verified": item["is_verified"],
                "Active": item["is_active"],
                "Source": item["source"],
            }
            for item in tariffs
        ]
    )


def page_tariffs() -> None:
    st.title("Tariff configurations")
    st.caption(
        "Rates are configuration records, not universal constants. Every estimate identifies "
        "the tariff used and whether it is verified."
    )
    try:
        tariffs = client.tariffs()
    except ApiError as exc:
        _api_error(exc)
        return
    st.warning(
        "The seeded tariff is an illustrative demonstration, not an official TNEB/TANGEDCO "
        "tariff order. Verify all rates, fixed charges, duties, subsidies and effective dates.",
        icon=":material/gavel:",
    )
    st.dataframe(
        _tariff_table(tariffs),
        hide_index=True,
        alt="Configured electricity tariff versions and verification status",
        column_config={
            "Verified": st.column_config.CheckboxColumn(),
            "Active": st.column_config.CheckboxColumn(),
            "Effective from": st.column_config.DateColumn(),
            "Effective to": st.column_config.DateColumn(),
        },
    )
    if tariffs:
        labels = {item["id"]: item["name"] for item in tariffs}
        selected_id = st.selectbox(
            "Inspect tariff",
            list(labels),
            format_func=lambda value: labels[value],
            key="c_tariff_inspect",
        )
        selected = next(item for item in tariffs if item["id"] == selected_id)
        with st.container(border=True):
            st.subheader(selected["name"])
            st.caption(
                f"Effective {selected['effective_from']} → "
                f"{selected['effective_to'] or 'open-ended'} · "
                f"verified: {selected['is_verified']} · source: {selected['source']}"
            )
            slab_frame = pd.DataFrame(selected["slabs"]).rename(
                columns={
                    "from_units": "From units",
                    "to_units": "To units",
                    "rate_per_unit": "Rate/unit",
                }
            )
            st.dataframe(
                slab_frame,
                hide_index=True,
                alt="Progressive tariff slabs",
            )
            if selected["components"]:
                st.dataframe(
                    pd.DataFrame(selected["components"]),
                    hide_index=True,
                    alt="Additional tariff charge components",
                )
            else:
                st.caption("No additional components configured.")
            with st.form(f"c_tariff_update_{selected_id}"):
                col1, col2 = st.columns(2)
                with col1:
                    active = st.checkbox(
                        "Active",
                        value=selected["is_active"],
                        key=f"c_tariff_active_{selected_id}",
                    )
                    verified = st.checkbox(
                        "Verified against an official tariff order",
                        value=selected["is_verified"],
                        key=f"c_tariff_verified_{selected_id}",
                    )
                with col2:
                    source = st.text_input(
                        "Tariff source",
                        value=selected["source"],
                        max_chars=500,
                        key=f"c_tariff_source_{selected_id}",
                    )
                    notes = st.text_area(
                        "Notes",
                        value=selected["notes"],
                        key=f"c_tariff_notes_{selected_id}",
                    )
                save = st.form_submit_button("Update metadata", icon=":material/save:")
            if save:
                try:
                    client.update_tariff(
                        selected_id,
                        {
                            "is_active": active,
                            "is_verified": verified,
                            "source": source,
                            "notes": notes,
                        },
                    )
                    _flash("success", "Tariff metadata updated.")
                    st.rerun()
                except ApiError as exc:
                    _api_error(exc)

    with st.expander("Add a new effective-dated tariff", icon=":material/add:"):
        st.caption(
            "Slab rows must be contiguous: each row's to_units must equal the next row's "
            "from_units. Leave the final to_units blank for an open-ended top slab."
        )
        with st.form("c_add_tariff"):
            name = st.text_input("Configuration name", max_chars=180)
            col1, col2 = st.columns(2)
            with col1:
                category = st.text_input("Billing category", value="domestic")
                effective_from = st.date_input("Effective from", value=date.today())
            with col2:
                source = st.text_input("Source / tariff order reference", max_chars=500)
                verified = st.checkbox("Verified against the official source")
            default_slabs = pd.DataFrame(
                [
                    {"from_units": "0", "to_units": "100", "rate_per_unit": "4.50"},
                    {"from_units": "100", "to_units": "200", "rate_per_unit": "6.00"},
                    {"from_units": "200", "to_units": "500", "rate_per_unit": "8.00"},
                    {"from_units": "500", "to_units": "", "rate_per_unit": "9.00"},
                ]
            )
            st.markdown("**Slabs**")
            edited_slabs = st.data_editor(
                default_slabs,
                num_rows="dynamic",
                hide_index=True,
                key="c_new_slabs",
                column_config={
                    "from_units": st.column_config.TextColumn("From units"),
                    "to_units": st.column_config.TextColumn("To units (blank = unlimited)"),
                    "rate_per_unit": st.column_config.TextColumn("Rate per unit (₹)"),
                },
            )
            default_components = pd.DataFrame(
                [
                    {"name": "Fixed monthly charge", "charge_type": "fixed_monthly", "amount": "50"},
                    {"name": "Electricity duty", "charge_type": "percent_of_energy", "amount": "5"},
                ]
            )
            st.markdown("**Additional components**")
            edited_components = st.data_editor(
                default_components,
                num_rows="dynamic",
                hide_index=True,
                key="c_new_components",
                column_config={
                    "name": st.column_config.TextColumn("Name"),
                    "charge_type": st.column_config.SelectboxColumn(
                        "Type",
                        options=["fixed_monthly", "per_unit", "percent_of_energy"],
                    ),
                    "amount": st.column_config.TextColumn("Amount / percent"),
                },
            )
            notes = st.text_area("Notes")
            submitted = st.form_submit_button(
                "Create tariff configuration", type="primary", icon=":material/add:"
            )
        if submitted:
            try:
                slabs = []
                for _, row in edited_slabs.iterrows():
                    if pd.isna(row["from_units"]) or str(row["from_units"]).strip() == "":
                        continue
                    to_value = row["to_units"]
                    slabs.append(
                        {
                            "from_units": str(row["from_units"]).strip(),
                            "to_units": (
                                None
                                if pd.isna(to_value) or str(to_value).strip() == ""
                                else str(to_value).strip()
                            ),
                            "rate_per_unit": str(row["rate_per_unit"]).strip(),
                        }
                    )
                components = []
                for _, row in edited_components.iterrows():
                    if pd.isna(row["name"]) or not str(row["name"]).strip():
                        continue
                    components.append(
                        {
                            "name": str(row["name"]).strip(),
                            "charge_type": str(row["charge_type"]).strip(),
                            "amount": str(row["amount"]).strip(),
                        }
                    )
                client.create_tariff(
                    {
                        "name": name,
                        "category": category,
                        "effective_from": effective_from.isoformat(),
                        "source": source,
                        "is_verified": verified,
                        "slabs": slabs,
                        "components": components,
                    }
                )
                _flash("success", "Tariff configuration created.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)
            except (TypeError, ValueError) as exc:
                st.error(f"Tariff form could not be parsed: {exc}")


def _bill_frame(bills: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Reference": item["bill_reference"],
                "Start": item["billing_period_start"],
                "End": item["billing_period_end"],
                "Billed units": float(item["billed_units"]),
                "Amount (₹)": float(item["bill_amount"]),
                "Bill date": item["bill_date"],
                "Compared": item["has_comparison"],
            }
            for item in bills
        ]
    )


def _show_comparison(result: dict) -> None:
    st.subheader("Comparison result")
    exceeds = result["exceeds_tolerance"]
    if exceeds:
        st.warning(
            f"Deviation exceeds the configured {result['tolerance_percent']}% tolerance. "
            "This triggers the six-month analysis. It does not prove a billing error.",
            icon=":material/warning:",
        )
    else:
        st.success(
            f"Deviation is within the configured {result['tolerance_percent']}% tolerance.",
            icon=":material/check_circle:",
        )
    with st.container(horizontal=True):
        st.metric("Socket-estimated units", result["estimated_units"], border=True)
        st.metric("Actual billed units", result["actual_units"], border=True)
        st.metric("Unit deviation", result["unit_deviation"], border=True)
        st.metric("Data coverage", f"{result['data_coverage_pct']}%", border=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Estimated cost", _money(result["estimated_cost"]), border=True)
    col2.metric("Actual bill amount", _money(result["actual_cost"]), border=True)
    col3.metric(
        "Cost deviation",
        _money(result["cost_deviation"]),
        delta=f"{result['percentage_deviation']}%" if result["percentage_deviation"] is not None else "undefined",
        border=True,
    )
    chart = pd.DataFrame(
        {
            "Measure": ["Configured-tariff estimate", "Actual bill"],
            "Amount": [float(result["estimated_cost"]), float(result["actual_cost"])],
        }
    )
    fig = px.bar(
        chart,
        x="Measure",
        y="Amount",
        color="Measure",
        color_discrete_sequence=["#f59e0b", "#0f766e"],
    )
    fig.update_layout(yaxis_title="Amount (₹)", xaxis_title="", showlegend=False)
    st.plotly_chart(
        _style_figure(fig, 320),
        alt="Configured-tariff estimate compared with actual electricity bill amount",
        key="c_comparison_bar",
    )
    if result.get("tariff"):
        st.caption(
            f"Tariff: **{result['tariff']['name']}** · effective {result['tariff']['effective_from']} · "
            f"verified: {result['tariff']['is_verified']} · source: {result['tariff']['source']}"
        )
    if result.get("warnings"):
        with st.expander("Warnings and assumptions", icon=":material/info:"):
            for warning in result["warnings"]:
                st.write(f"- {warning}")
    st.info(result["disclaimer"], icon=":material/policy:")


def page_bills() -> None:
    st.title("Bills and verification")
    st.caption(
        "Record the actual bill, then compare it with an estimate from monitored sockets and "
        "the configured tariff. A deviation is evidence to investigate, not proof of error."
    )
    try:
        bills = client.bills()
        tariffs = client.tariffs()
    except ApiError as exc:
        _api_error(exc)
        return

    add_tab, import_tab = st.tabs(["Add a bill", "Import CSV"])
    with add_tab:
        with st.form("c_add_bill"):
            col1, col2 = st.columns(2)
            with col1:
                reference = st.text_input("Bill reference", max_chars=120)
                period_start = st.date_input(
                    "Billing period start", value=date.today().replace(day=1)
                )
                period_end = st.date_input("Billing period end", value=date.today())
                bill_date = st.date_input("Bill date", value=date.today())
            with col2:
                units = st.number_input("Billed units", min_value=0.0, step=10.0)
                amount = st.number_input(
                    "Bill amount (₹)", min_value=0.0, step=10.0
                )
                fixed = st.number_input(
                    "Fixed charges in bill (₹)", min_value=0.0, step=5.0
                )
                other = st.number_input(
                    "Other charges in bill (₹)", min_value=0.0, step=5.0
                )
            source = st.text_input("Source", value="manual")
            notes = st.text_area("Notes")
            submitted = st.form_submit_button(
                "Save bill", type="primary", icon=":material/receipt_long:"
            )
        if submitted:
            try:
                client.create_bill(
                    {
                        "bill_reference": reference,
                        "billing_period_start": period_start.isoformat(),
                        "billing_period_end": period_end.isoformat(),
                        "billed_units": f"{units:.2f}",
                        "bill_amount": f"{amount:.2f}",
                        "fixed_charges": f"{fixed:.2f}",
                        "other_charges": f"{other:.2f}",
                        "bill_date": bill_date.isoformat(),
                        "source": source,
                        "notes": notes,
                    }
                )
                _flash("success", "Bill saved.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)
    with import_tab:
        st.caption(
            "Required columns: bill_reference, billing_period_start, billing_period_end, "
            "billed_units, bill_amount, bill_date. Optional: fixed_charges, other_charges, "
            "source, notes. Invalid rows reject the whole file."
        )
        uploaded = st.file_uploader("Bills CSV", type=["csv"], key="c_bill_csv")
        if uploaded is not None and st.button(
            "Validate and import bills", icon=":material/upload_file:"
        ):
            try:
                result = client.import_bills(uploaded.name, uploaded.getvalue())
                _flash("success", f"Imported {result['imported']} bills.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)

    if not bills:
        st.info("No bills recorded yet.")
        return
    st.dataframe(
        _bill_frame(bills),
        hide_index=True,
        alt="Recorded electricity bills",
        column_config={
            "Billed units": st.column_config.NumberColumn(format="%.2f"),
            "Amount (₹)": st.column_config.NumberColumn(format="₹%.2f"),
            "Start": st.column_config.DateColumn(),
            "End": st.column_config.DateColumn(),
            "Bill date": st.column_config.DateColumn(),
            "Compared": st.column_config.CheckboxColumn(),
        },
    )

    labels = {
        item["id"]: f"{item['bill_reference']} · {item['billing_period_start']} → {item['billing_period_end']}"
        for item in bills
    }
    selected_id = st.selectbox(
        "Select a bill",
        list(labels),
        format_func=lambda value: labels[value],
        key="c_bill_select",
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        tolerance = st.number_input(
            "Tolerance (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0
        )
    with col2:
        tariff_choice = st.selectbox(
            "Tariff override",
            ["Automatic (effective date)"] + [f"{item['id']} · {item['name']}" for item in tariffs],
        )
    with col3:
        st.write("")
        compare_clicked = st.button(
            "Compare bill",
            type="primary",
            icon=":material/compare_arrows:",
            width="stretch",
        )
    if compare_clicked:
        tariff_id = (
            None
            if tariff_choice == "Automatic (effective date)"
            else int(tariff_choice.split(" · ")[0])
        )
        try:
            result = client.compare(selected_id, tolerance, tariff_id)
            st.session_state["c_comparison"] = {"bill_id": selected_id, **result}
            st.rerun()
        except ApiError as exc:
            _api_error(exc)
    stored = st.session_state.get("c_comparison")
    if stored and stored["bill_id"] == selected_id:
        _show_comparison(stored)
        if stored.get("six_month_analysis"):
            analysis = stored["six_month_analysis"]
            st.info(
                "A six-month analysis was generated because the deviation exceeded tolerance. "
                "Open the six-month analysis page for the full evidence.",
                icon=":material/analytics:",
            )
            with st.expander("Quick six-month facts", expanded=False):
                for fact in analysis.get("observed_facts", [])[:5]:
                    st.write(f"- {fact}")
    with st.expander("Delete this bill", icon=":material/delete:"):
        confirm = st.checkbox(
            "Confirm deletion of the bill and its comparison",
            key=f"c_bill_delete_confirm_{selected_id}",
        )
        if st.button(
            "Delete bill",
            disabled=not confirm,
            icon=":material/delete:",
            key=f"c_bill_delete_{selected_id}",
        ):
            try:
                client.delete_bill(selected_id)
                st.session_state.pop("c_comparison", None)
                _flash("success", "Bill and comparison deleted.")
                st.rerun()
            except ApiError as exc:
                _api_error(exc)


def page_analysis() -> None:
    st.title("Six-month analysis")
    st.caption(
        "When a deviation exceeds tolerance, examine the preceding six months of available "
        "records. Missing data is reported, never invented."
    )
    try:
        bills = client.bills()
    except ApiError as exc:
        _api_error(exc)
        return
    if not bills:
        st.info("Record and compare a bill first.")
        return
    labels = {
        item["id"]: f"{item['bill_reference']} · {item['billing_period_start']} → {item['billing_period_end']}"
        for item in bills
    }
    selected_id = st.selectbox(
        "Bill to investigate",
        list(labels),
        format_func=lambda value: labels[value],
        key="c_analysis_bill",
    )
    tolerance = st.number_input(
        "Tolerance (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0
    )
    if st.button(
        "Run six-month analysis",
        type="primary",
        icon=":material/analytics:",
    ):
        with st.spinner("Aggregating readings and bills…"):
            try:
                result = client.analysis(selected_id, tolerance)
                st.session_state["c_analysis"] = {"bill_id": selected_id, **result}
            except ApiError as exc:
                _api_error(exc)
                return
    stored = st.session_state.get("c_analysis")
    if not stored or stored["bill_id"] != selected_id:
        st.info("Run the analysis to see observed evidence and possible explanations.")
        return
    if stored["insufficient_history"]:
        st.warning(
            "Insufficient historical data for a strong pattern comparison. The limited evidence "
            "is shown without fabricating missing months.",
            icon=":material/history_toggle_off:",
        )
    current = stored["current_period"]
    with st.container(horizontal=True):
        st.metric("Actual units", current["actual_units"], border=True)
        st.metric("Estimated units", current["estimated_units"], border=True)
        st.metric(
            "Percentage deviation",
            (
                f"{current['percentage_deviation']}%"
                if current["percentage_deviation"] is not None
                else "undefined"
            ),
            border=True,
        )
        st.metric("Coverage", f"{current['coverage_pct']}%", border=True)

    history = pd.DataFrame(stored["historical_months"])
    history["estimated_units_num"] = pd.to_numeric(
        history["estimated_units"], errors="coerce"
    )
    history["actual_units_num"] = pd.to_numeric(history["actual_units"], errors="coerce")
    col1, col2 = st.columns(2)
    with col1, st.container(border=True):
        st.subheader("Units: estimate vs bill")
        if history[["estimated_units_num", "actual_units_num"]].notna().any().any():
            plot = history.melt(
                id_vars="month",
                value_vars=["estimated_units_num", "actual_units_num"],
                var_name="Measure",
                value_name="Units",
            ).dropna()
            plot["Measure"] = plot["Measure"].map(
                {
                    "estimated_units_num": "Estimated",
                    "actual_units_num": "Actual bill",
                }
            )
            fig = px.bar(
                plot,
                x="month",
                y="Units",
                color="Measure",
                barmode="group",
                color_discrete_sequence=["#f59e0b", "#0f766e"],
            )
            fig.update_layout(xaxis_title="", legend_title_text="")
            st.plotly_chart(
                _style_figure(fig),
                alt="Historical monthly socket-estimated units compared with billed units",
                key="c_history_units",
            )
        else:
            st.info("No historical bill/reading pairs to chart.")
    with col2, st.container(border=True):
        st.subheader("Reading coverage by month")
        fig = px.bar(
            history,
            x="month",
            y="coverage_pct",
            color_discrete_sequence=["#0ea5e9"],
        )
        fig.update_layout(
            xaxis_title="", yaxis_title="Coverage (%)", yaxis_range=[0, 100]
        )
        st.plotly_chart(
            _style_figure(fig),
            alt="Socket reading coverage by historical month",
            key="c_history_coverage",
        )

    facts_tab, explanations_tab, data_tab = st.tabs(
        ["Observed facts", "Possible explanations", "Historical data"]
    )
    with facts_tab:
        for fact in stored["observed_facts"]:
            st.write(f"- {fact}")
        if stored["missing_reading_months"]:
            st.warning(
                "Missing reading months: " + ", ".join(stored["missing_reading_months"]),
                icon=":material/event_busy:",
            )
        if stored["incomplete_coverage_months"]:
            st.warning(
                "Coverage below 95%: " + ", ".join(stored["incomplete_coverage_months"]),
                icon=":material/signal_wifi_statusbar_connected_no_internet_4:",
            )
    with explanations_tab:
        st.caption(
            "These are possible explanations, not findings of fault or proof of an incorrect bill."
        )
        for explanation in stored["possible_explanations"]:
            st.write(f"- {explanation}")
    with data_tab:
        display_columns = [
            "month",
            "observed",
            "estimated_units",
            "actual_units",
            "estimated_cost",
            "actual_cost",
            "percentage_deviation",
            "coverage_pct",
            "bill_reference",
        ]
        st.dataframe(
            history[display_columns],
            hide_index=True,
            alt="Historical monthly readings, bills and deviations",
            column_config={
                "estimated_units": st.column_config.TextColumn("Estimated units"),
                "actual_units": st.column_config.TextColumn("Actual units"),
                "coverage_pct": st.column_config.ProgressColumn(
                    "Coverage", min_value=0, max_value=100, format="%.1f%%"
                ),
            },
        )
    st.error(stored["disclaimer"], icon=":material/policy:")


def page_exports() -> None:
    st.title("Exports")
    st.caption("Download consumption data, bill comparisons, or the Person A expense payload.")
    today = date.today()
    selected = st.date_input(
        "Export range",
        value=(today.replace(day=1), today),
        key="c_export_dates",
    )
    start, end = _date_range(selected)
    col1, col2, col3 = st.columns(3)
    with col1, st.container(border=True):
        st.subheader("Consumption CSV")
        st.caption("Daily kWh, coverage and simulated-data labels for the selected range.")
        try:
            data = client.export_consumption(start, end)
            st.download_button(
                "Download consumption CSV",
                data=data,
                file_name=f"consumption_{start}_{end}.csv",
                mime="text/csv",
                icon=":material/download:",
                width="stretch",
            )
        except ApiError as exc:
            _api_error(exc)
    with col2, st.container(border=True):
        st.subheader("Bill comparisons CSV")
        st.caption("All persisted comparisons with deviations, tolerance and coverage.")
        try:
            data = client.export_comparisons()
            st.download_button(
                "Download comparisons CSV",
                data=data,
                file_name="bill_comparisons.csv",
                mime="text/csv",
                icon=":material/download:",
                width="stretch",
            )
        except ApiError as exc:
            _api_error(exc)
    with col3, st.container(border=True):
        st.subheader("Electricity expenses JSON")
        st.caption("Monthly actual/estimated expense records supplied to Person A.")
        try:
            data = client.electricity_expenses(start, end)
            st.download_button(
                "Download expense JSON",
                data=json.dumps(data, indent=2),
                file_name=f"electricity_expenses_{start}_{end}.json",
                mime="application/json",
                icon=":material/download:",
                width="stretch",
            )
        except ApiError as exc:
            _api_error(exc)
    try:
        daily = client.daily(start, end)
        monthly = client.monthly(start, end)
    except ApiError as exc:
        _api_error(exc)
        return
    st.info(
        f"Selected range: {daily['total_energy_kwh']} kWh monitored, "
        f"{daily['data_coverage_pct']:.1f}% reading coverage.",
        icon=":material/insights:",
    )
    with st.expander("Monthly summary", expanded=True):
        st.dataframe(
            pd.DataFrame(monthly["months"]),
            hide_index=True,
            alt="Monthly energy consumption and coverage summary",
            column_config={
                "coverage_pct": st.column_config.ProgressColumn(
                    "Coverage", min_value=0, max_value=100, format="%.1f%%"
                )
            },
        )


def page_integrations() -> None:
    st.title("Person A integration and demo data")
    st.caption(
        "Send monthly electricity expense summaries over authenticated HTTP. Person C works "
        "independently when Person A is offline."
    )
    check_remote = st.toggle("Check live connectivity", value=True, key="c_remote")
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
        st.caption(f"Destination `{status['api_url']}` · last range {status['last_period'] or '—'}")
        if status.get("remote_health"):
            if status["remote_health"]["reachable"]:
                st.success("Person A API reachable", icon=":material/link:")
            else:
                st.warning(
                    "Person A is unreachable. Local readings and bills remain available.",
                    icon=":material/link_off:",
                )
        if status["last_error"]:
            st.error(status["last_error"], icon=":material/error:")

    today = date.today()
    selected = st.date_input(
        "Expense period",
        value=(today.replace(day=1) - timedelta(days=155), today),
        key="c_sync_dates",
    )
    start, end = _date_range(selected)
    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "Push electricity expenses to Person A",
            type="primary",
            icon=":material/sync:",
            width="stretch",
        ):
            with st.spinner("Sending authenticated payload…"):
                try:
                    result = client.sync_person_a(start, end)
                    _flash(
                        "success",
                        f"Person A accepted {result['records_sent']} monthly record(s).",
                    )
                    st.rerun()
                except ApiError as exc:
                    _api_error(exc)
    with col2:
        if st.button(
            "Preview payload",
            icon=":material/data_object:",
            width="stretch",
        ):
            try:
                st.session_state["c_payload"] = client.integration_payload(start, end)
            except ApiError as exc:
                _api_error(exc)
    if st.session_state.get("c_payload"):
        with st.expander("Last previewed payload", expanded=True):
            st.json(st.session_state["c_payload"])
    st.info(
        "Actual bills take precedence; otherwise configured-tariff estimates are sent and marked "
        "`is_estimate=true`. Stable external IDs `electricity:<YYYY-MM>` deduplicate in Person A.",
        icon=":material/info:",
    )

    st.divider()
    st.subheader("Simulated demonstration data")
    st.warning(
        "Demo generation creates explicitly simulated sockets, hourly readings and fake bills. "
        "They are labelled in every record and are not real measurements or TNEB bills.",
        icon=":material/science:",
    )
    with st.form("c_demo_seed"):
        months = st.slider("History months", 1, 9, 6)
        force = st.checkbox("Replace previous demo data only (force)")
        submitted = st.form_submit_button(
            "Generate demo data", icon=":material/auto_awesome:"
        )
    if submitted:
        with st.spinner("Generating simulated readings and bills…"):
            try:
                result = client.demo_seed(months, force)
                _flash(
                    "warning",
                    f"Generated {result['readings_created']} simulated readings and "
                    f"{result['bills_created']} simulated bills.",
                )
                st.rerun()
            except ApiError as exc:
                _api_error(exc)
    st.caption(
        "The adapter interface in `services/adapters/` is the extension point for future smart-plug "
        "vendor APIs or MQTT. No hardware or vendor integration is implemented or claimed."
    )


def page_project_info() -> None:
    st.title("Project information")
    st.markdown(
        "### Smart Home Electricity Monitoring and TNEB Electricity Bill Verification System"
    )
    with st.container(border=True):
        col1, col2 = st.columns(2)
        col1.metric("Owner", "HARIHARAN S")
        col2.metric("Registration no.", "23MID0182")
        st.write(
            "A standalone electricity monitoring application that ingests manual or simulated "
            "smart-socket readings, estimates interval energy and configurable tariffs, records "
            "actual bills, compares them with socket-based estimates, and investigates "
            "discrepancies using up to six months of available evidence."
        )
    st.subheader("Calculation method")
    st.markdown(
        "- **Energy:** previous reading power (W) × interval duration (h) ÷ 1000.\n"
        "- **Gaps:** intervals longer than the configured maximum are excluded and reported; they are not filled.\n"
        "- **Tariffs:** progressive slabs plus configurable fixed, per-unit and percentage components.\n"
        "- **Deviation:** actual minus estimate; percentage is cost deviation ÷ estimated cost, with zero handled explicitly.\n"
        "- **Coverage:** union of observed socket reading intervals over the requested period."
    )
    st.subheader("Important limitations")
    st.markdown(
        "- Socket readings may not cover every household circuit; coverage is temporal, not whole-home completeness.\n"
        "- The seeded tariff is illustrative and unverified. It is not an official TNEB/TANGEDCO tariff.\n"
        "- No smart-plug vendor API, MQTT broker or physical hardware is integrated. Manual and simulated adapters are implemented.\n"
        "- Estimates apply a fixed monthly charge once per selected period, which may not match a utility's proration.\n"
        "- The analysis never asserts that a utility bill is incorrect.\n"
        "- Single-user local academic application with no login."
    )
    st.caption(f"Database file: `{settings.project_dir / 'data' / 'person_c.db'}`")
    st.code(
        "python -m uvicorn api:app --host 127.0.0.1 --port 8003\n"
        "streamlit run app.py --server.port 8503",
        language="powershell",
    )
    st.subheader("Owners of the connected projects")
    st.write(
        "- Person A: Sachien N (23MID0255) — Smart Expense Categorization and Budget Manager\n"
        "- Person B: Shravan N A (23MID0445) — Smart Subscription Manager\n"
        "- Person C: HARIHARAN S (23MID0182) — Smart Electricity Monitoring"
    )


def main() -> None:
    st.set_page_config(
        page_title="Electricity Monitor · Person C",
        page_icon=":material/bolt:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()  # Neumorphism design system (separate theme module)
    page = _sidebar()
    _show_flash()
    pages = {
        "Overview": page_overview,
        "Sockets": page_sockets,
        "Readings": page_readings,
        "Tariffs": page_tariffs,
        "Bills & verification": page_bills,
        "Six-month analysis": page_analysis,
        "Exports": page_exports,
        "Integrations": page_integrations,
        "Project info": page_project_info,
    }
    pages[page]()
    st.caption(
        "Person C · HARIHARAN S (23MID0182) · Smart Home Electricity Monitoring and TNEB "
        "Bill Verification System"
    )
