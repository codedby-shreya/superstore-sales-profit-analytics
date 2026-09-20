"""
Superstore Sales & Profit Analytics Dashboard
=============================================
A comprehensive interactive Streamlit dashboard for analyzing
the Superstore retail dataset.
"""

import os
import io
import warnings
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Superstore Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .kpi-card {
        background-color: #f7f8fa;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px 20px;
        text-align: center;
        margin-bottom: 8px;
    }
    .kpi-label {
        font-size: 13px;
        color: #57606a;
        margin-bottom: 4px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 700;
        color: #1f2328;
        line-height: 1.2;
    }
    .kpi-sub {
        font-size: 12px;
        color: #57606a;
        margin-top: 4px;
    }
    .insight-box {
        background-color: #f7f8fa;
        border-left: 4px solid #3b82d4;
        border-radius: 4px;
        padding: 12px 16px;
        margin-bottom: 12px;
    }
    .section-header {
        font-size: 20px;
        font-weight: 600;
        color: #1f2328;
        margin-bottom: 4px;
        margin-top: 8px;
    }
    .negative-profit {
        color: #dc2626;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    """Auto-detect and load the CSV file from the project folder."""
    csv_files = [f for f in os.listdir(".") if f.lower().endswith(".csv")]
    if not csv_files:
        return None, None
    csv_path = csv_files[0]
    df = pd.read_csv(csv_path, encoding="latin1")
    return df, csv_path


# ─────────────────────────────────────────────
# DATA CLEANING
# ─────────────────────────────────────────────
@st.cache_data
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean the dataframe."""
    df = df.copy()

    # Convert date columns
    for col in ["Order Date", "Ship Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", errors="coerce")

    # Remove exact duplicate rows
    df = df.drop_duplicates()

    # Ensure numeric columns are numeric
    for col in ["Sales", "Profit", "Quantity", "Discount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# ─────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────
@st.cache_data
def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create analytical derived columns."""
    df = df.copy()

    if "Order Date" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Order Date"]):
        df["Year"] = df["Order Date"].dt.year
        df["Month"] = df["Order Date"].dt.month
        df["Month Name"] = df["Order Date"].dt.strftime("%b")
        df["Quarter"] = df["Order Date"].dt.quarter.apply(lambda q: f"Q{q}")
        df["Day of Week"] = df["Order Date"].dt.strftime("%A")

    if "Sales" in df.columns and "Profit" in df.columns:
        # Safe division — avoid divide by zero
        df["Profit Margin"] = df.apply(
            lambda r: (r["Profit"] / r["Sales"]) * 100 if r["Sales"] != 0 else 0,
            axis=1,
        )

    return df


# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
def render_sidebar(df: pd.DataFrame):
    """Render sidebar filters and return the filtered dataframe."""
    st.sidebar.title("Filters")
    st.sidebar.markdown("---")

    filtered = df.copy()

    def ms(label, col, df_ref):
        """Multiselect filter helper."""
        if col not in df_ref.columns:
            return []
        opts = sorted(df_ref[col].dropna().unique().tolist())
        return st.sidebar.multiselect(label, opts, default=opts)

    # Year filter
    if "Year" in df.columns:
        years = sorted(df["Year"].dropna().unique().tolist())
        sel_years = st.sidebar.multiselect("Year", years, default=years)
        if sel_years:
            filtered = filtered[filtered["Year"].isin(sel_years)]

    # Region
    if "Region" in df.columns:
        regions = sorted(df["Region"].dropna().unique().tolist())
        sel_reg = st.sidebar.multiselect("Region", regions, default=regions)
        if sel_reg:
            filtered = filtered[filtered["Region"].isin(sel_reg)]

    # State
    if "State" in df.columns:
        states = sorted(filtered["State"].dropna().unique().tolist())
        sel_state = st.sidebar.multiselect("State", states, default=states)
        if sel_state:
            filtered = filtered[filtered["State"].isin(sel_state)]

    # Category
    if "Category" in df.columns:
        cats = sorted(df["Category"].dropna().unique().tolist())
        sel_cat = st.sidebar.multiselect("Category", cats, default=cats)
        if sel_cat:
            filtered = filtered[filtered["Category"].isin(sel_cat)]

    # Sub-Category
    if "Sub-Category" in df.columns:
        subcats = sorted(filtered["Sub-Category"].dropna().unique().tolist())
        sel_sub = st.sidebar.multiselect("Sub-Category", subcats, default=subcats)
        if sel_sub:
            filtered = filtered[filtered["Sub-Category"].isin(sel_sub)]

    # Segment
    if "Segment" in df.columns:
        segs = sorted(df["Segment"].dropna().unique().tolist())
        sel_seg = st.sidebar.multiselect("Segment", segs, default=segs)
        if sel_seg:
            filtered = filtered[filtered["Segment"].isin(sel_seg)]

    # Ship Mode
    if "Ship Mode" in df.columns:
        modes = sorted(df["Ship Mode"].dropna().unique().tolist())
        sel_mode = st.sidebar.multiselect("Ship Mode", modes, default=modes)
        if sel_mode:
            filtered = filtered[filtered["Ship Mode"].isin(sel_mode)]

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Showing **{len(filtered):,}** of **{len(df):,}** rows")
    return filtered


# ─────────────────────────────────────────────
# KPI CALCULATION
# ─────────────────────────────────────────────
def calculate_kpis(df: pd.DataFrame) -> dict:
    """Compute top-level KPI values from the filtered dataframe."""
    kpis = {}
    kpis["total_sales"] = df["Sales"].sum() if "Sales" in df.columns else 0
    kpis["total_profit"] = df["Profit"].sum() if "Profit" in df.columns else 0
    kpis["total_orders"] = df["Order ID"].nunique() if "Order ID" in df.columns else 0
    kpis["total_qty"] = int(df["Quantity"].sum()) if "Quantity" in df.columns else 0
    kpis["avg_order_value"] = (
        df.groupby("Order ID")["Sales"].sum().mean() if "Order ID" in df.columns else 0
    )
    kpis["num_customers"] = df["Customer ID"].nunique() if "Customer ID" in df.columns else 0
    kpis["num_products"] = df["Product Name"].nunique() if "Product Name" in df.columns else 0
    kpis["profit_margin"] = (
        (kpis["total_profit"] / kpis["total_sales"]) * 100 if kpis["total_sales"] != 0 else 0
    )
    return kpis


def render_kpis(kpis: dict):
    """Render KPI metric cards."""
    col1, col2, col3, col4 = st.columns(4)
    col5, col6, col7, col8 = st.columns(4)

    def card(col, label, value):
        col.markdown(
            f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div></div>',
            unsafe_allow_html=True,
        )

    card(col1, "Total Sales", f"${kpis['total_sales']:,.2f}")
    card(col2, "Total Profit", f"${kpis['total_profit']:,.2f}")
    card(col3, "Total Orders", f"{kpis['total_orders']:,}")
    card(col4, "Total Quantity", f"{kpis['total_qty']:,}")
    card(col5, "Avg Order Value", f"${kpis['avg_order_value']:,.2f}")
    card(col6, "Customers", f"{kpis['num_customers']:,}")
    card(col7, "Products", f"{kpis['num_products']:,}")
    card(col8, "Profit Margin", f"{kpis['profit_margin']:.2f}%")


# ─────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────
CHART_THEME = "plotly_white"
COLOR_SEQ = px.colors.qualitative.Safe


def bar_chart(df, x, y, title, xlabel, ylabel, orientation="v", color=None, text=None):
    fig = px.bar(
        df, x=x, y=y, title=title, labels={x: xlabel, y: ylabel},
        orientation=orientation, color=color, text=text,
        color_discrete_sequence=COLOR_SEQ, template=CHART_THEME,
    )
    fig.update_layout(showlegend=bool(color), margin=dict(t=50, b=40))
    return fig


def line_chart(df, x, y, title, xlabel, ylabel, color=None):
    fig = px.line(
        df, x=x, y=y, title=title, labels={x: xlabel, y: ylabel},
        color=color, markers=True,
        color_discrete_sequence=COLOR_SEQ, template=CHART_THEME,
    )
    fig.update_layout(margin=dict(t=50, b=40))
    return fig


def pie_chart(df, names, values, title):
    fig = px.pie(
        df, names=names, values=values, title=title,
        color_discrete_sequence=COLOR_SEQ, template=CHART_THEME,
    )
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(margin=dict(t=50, b=40))
    return fig


def scatter_chart(df, x, y, title, xlabel, ylabel, color=None, size=None, hover_name=None):
    fig = px.scatter(
        df, x=x, y=y, title=title, labels={x: xlabel, y: ylabel},
        color=color, size=size, hover_name=hover_name,
        opacity=0.65, color_discrete_sequence=COLOR_SEQ, template=CHART_THEME,
    )
    fig.update_layout(margin=dict(t=50, b=40))
    return fig


# ─────────────────────────────────────────────
# SECTION: OVERVIEW
# ─────────────────────────────────────────────
def render_overview(df: pd.DataFrame, kpis: dict):
    st.markdown('<div class="section-header">Dashboard Overview</div>', unsafe_allow_html=True)
    st.caption(
        "This dashboard provides an end-to-end analysis of the Superstore retail dataset, "
        "covering sales performance, profitability, product trends, customer behavior, "
        "and regional dynamics."
    )
    st.markdown("---")
    render_kpis(kpis)
    st.markdown("---")

    col_l, col_r = st.columns(2)

    # Monthly sales trend
    if "Order Date" in df.columns:
        monthly = (
            df.groupby(df["Order Date"].dt.to_period("M"))["Sales"]
            .sum()
            .reset_index()
        )
        monthly["Order Date"] = monthly["Order Date"].astype(str)
        fig = line_chart(monthly, "Order Date", "Sales", "Monthly Sales Trend", "Month", "Sales ($)")
        col_l.plotly_chart(fig, use_container_width=True)

        monthly_p = (
            df.groupby(df["Order Date"].dt.to_period("M"))["Profit"]
            .sum()
            .reset_index()
        )
        monthly_p["Order Date"] = monthly_p["Order Date"].astype(str)
        fig2 = line_chart(monthly_p, "Order Date", "Profit", "Monthly Profit Trend", "Month", "Profit ($)")
        col_r.plotly_chart(fig2, use_container_width=True)

    col1, col2, col3 = st.columns(3)

    # Sales by Category
    if "Category" in df.columns:
        cat_sales = df.groupby("Category")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)
        fig = pie_chart(cat_sales, "Category", "Sales", "Sales by Category")
        col1.plotly_chart(fig, use_container_width=True, key="chart_1")

    # Sales by Region
    if "Region" in df.columns:
        reg_sales = df.groupby("Region")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)
        fig = bar_chart(reg_sales, "Region", "Sales", "Sales by Region", "Region", "Sales ($)")
        col2.plotly_chart(fig, use_container_width=True, key="chart_2")

    # Sales by Segment
    if "Segment" in df.columns:
        seg_sales = df.groupby("Segment")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)
        fig = pie_chart(seg_sales, "Segment", "Sales", "Sales by Segment")
        col3.plotly_chart(fig, use_container_width=True, key="chart_3")


# ─────────────────────────────────────────────
# SECTION: SALES ANALYSIS
# ─────────────────────────────────────────────
def render_sales_analysis(df: pd.DataFrame):
    st.markdown('<div class="section-header">Sales Analysis</div>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns(2)

    # Sales by Year
    if "Year" in df.columns:
        yr = df.groupby("Year")["Sales"].sum().reset_index()
        fig = bar_chart(yr, "Year", "Sales", "Sales by Year", "Year", "Sales ($)")
        fig.update_xaxes(type="category")
        col1.plotly_chart(fig, use_container_width=True, key="chart_4")

    # Sales by Quarter
    if "Quarter" in df.columns:
        q = df.groupby("Quarter")["Sales"].sum().reset_index().sort_values("Quarter")
        fig = bar_chart(q, "Quarter", "Sales", "Sales by Quarter", "Quarter", "Sales ($)")
        col2.plotly_chart(fig, use_container_width=True, key="chart_5")

    # Monthly Sales Trend (with year color)
    if "Month" in df.columns and "Year" in df.columns:
        month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        monthly = df.groupby(["Year", "Month Name"])["Sales"].sum().reset_index()
        monthly["Month Name"] = pd.Categorical(monthly["Month Name"], categories=month_order, ordered=True)
        monthly = monthly.sort_values(["Year", "Month Name"])
        monthly["Year"] = monthly["Year"].astype(str)
        fig = line_chart(monthly, "Month Name", "Sales", "Monthly Sales Trend by Year", "Month", "Sales ($)", color="Year")
        st.plotly_chart(fig, use_container_width=True, key="chart_6")

    col3, col4 = st.columns(2)

    # Sales by Category
    if "Category" in df.columns:
        cat = df.groupby("Category")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)
        fig = bar_chart(cat, "Category", "Sales", "Sales by Category", "Category", "Sales ($)")
        col3.plotly_chart(fig, use_container_width=True, key="chart_7")

    # Sales by Segment
    if "Segment" in df.columns:
        seg = df.groupby("Segment")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)
        fig = bar_chart(seg, "Segment", "Sales", "Sales by Segment", "Segment", "Sales ($)")
        col4.plotly_chart(fig, use_container_width=True, key="chart_8")

    # Sales by Sub-Category (horizontal)
    if "Sub-Category" in df.columns:
        sub = df.groupby("Sub-Category")["Sales"].sum().reset_index().sort_values("Sales")
        fig = bar_chart(sub, "Sales", "Sub-Category", "Sales by Sub-Category", "Sales ($)", "Sub-Category", orientation="h")
        st.plotly_chart(fig, use_container_width=True, key="chart_9")

    # Sales by Region
    if "Region" in df.columns:
        reg = df.groupby("Region")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)
        fig = bar_chart(reg, "Region", "Sales", "Sales by Region", "Region", "Sales ($)")
        st.plotly_chart(fig, use_container_width=True, key="chart_10")


# ─────────────────────────────────────────────
# SECTION: PROFITABILITY ANALYSIS
# ─────────────────────────────────────────────
def render_profit_analysis(df: pd.DataFrame):
    st.markdown('<div class="section-header">Profitability Analysis</div>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns(2)

    # Profit by Year
    if "Year" in df.columns:
        yr = df.groupby("Year")["Profit"].sum().reset_index()
        fig = bar_chart(yr, "Year", "Profit", "Profit by Year", "Year", "Profit ($)")
        fig.update_xaxes(type="category")
        col1.plotly_chart(fig, use_container_width=True, key="chart_11")

    # Profit by Quarter
    if "Quarter" in df.columns:
        q = df.groupby("Quarter")["Profit"].sum().reset_index().sort_values("Quarter")
        fig = bar_chart(q, "Quarter", "Profit", "Profit by Quarter", "Quarter", "Profit ($)")
        col2.plotly_chart(fig, use_container_width=True, key="chart_12")

    # Monthly Profit Trend
    if "Month Name" in df.columns and "Year" in df.columns:
        month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        mp = df.groupby(["Year", "Month Name"])["Profit"].sum().reset_index()
        mp["Month Name"] = pd.Categorical(mp["Month Name"], categories=month_order, ordered=True)
        mp = mp.sort_values(["Year", "Month Name"])
        mp["Year"] = mp["Year"].astype(str)
        fig = line_chart(mp, "Month Name", "Profit", "Monthly Profit Trend by Year", "Month", "Profit ($)", color="Year")
        st.plotly_chart(fig, use_container_width=True, key="chart_13")

    col3, col4 = st.columns(2)

    # Profit by Category
    if "Category" in df.columns:
        cat = df.groupby("Category")["Profit"].sum().reset_index().sort_values("Profit", ascending=False)
        fig = bar_chart(cat, "Category", "Profit", "Profit by Category", "Category", "Profit ($)")
        col3.plotly_chart(fig, use_container_width=True, key="chart_14")

    # Profit by Region
    if "Region" in df.columns:
        reg = df.groupby("Region")["Profit"].sum().reset_index().sort_values("Profit", ascending=False)
        fig = bar_chart(reg, "Region", "Profit", "Profit by Region", "Region", "Profit ($)")
        col4.plotly_chart(fig, use_container_width=True, key="chart_15")

    # Profit by Sub-Category
    if "Sub-Category" in df.columns:
        sub = df.groupby("Sub-Category")["Profit"].sum().reset_index().sort_values("Profit")
        colors = ["#dc2626" if v < 0 else "#3b82d4" for v in sub["Profit"]]
        fig = go.Figure(go.Bar(
            x=sub["Profit"], y=sub["Sub-Category"],
            orientation="h", marker_color=colors,
        ))
        fig.update_layout(
            title="Profit by Sub-Category (red = loss)",
            xaxis_title="Profit ($)", yaxis_title="Sub-Category",
            template=CHART_THEME, margin=dict(t=50, b=40),
        )
        st.plotly_chart(fig, use_container_width=True, key="chart_16")

    # Sales vs Profit Scatter
    if "Sales" in df.columns and "Profit" in df.columns:
        sample = df.sample(min(2000, len(df)), random_state=42) if len(df) > 2000 else df
        color_col = "Category" if "Category" in sample.columns else None
        fig = scatter_chart(
            sample, "Sales", "Profit",
            "Sales vs Profit", "Sales ($)", "Profit ($)",
            color=color_col,
        )
        fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.4)
        st.plotly_chart(fig, use_container_width=True, key="chart_17")

    # Profit Margin by Category
    if "Category" in df.columns and "Profit Margin" in df.columns:
        pm = df.groupby("Category")["Profit Margin"].mean().reset_index()
        pm.columns = ["Category", "Avg Profit Margin (%)"]
        fig = bar_chart(pm, "Category", "Avg Profit Margin (%)", "Average Profit Margin by Category", "Category", "Avg Profit Margin (%)")
        st.plotly_chart(fig, use_container_width=True, key="chart_18")


# ─────────────────────────────────────────────
# SECTION: PRODUCT ANALYSIS
# ─────────────────────────────────────────────
def render_product_analysis(df: pd.DataFrame):
    st.markdown('<div class="section-header">Product Analysis</div>', unsafe_allow_html=True)
    st.markdown("---")

    if "Product Name" not in df.columns:
        st.warning("Product Name column not found.")
        return

    prod = (
        df.groupby(["Product Name", "Category", "Sub-Category"])
        .agg(Sales=("Sales","sum"), Quantity=("Quantity","sum"),
             Discount=("Discount","mean"), Profit=("Profit","sum"))
        .reset_index()
    )
    if "Profit" in prod.columns and "Sales" in prod.columns:
        prod["Profit Margin (%)"] = prod.apply(
            lambda r: (r["Profit"] / r["Sales"]) * 100 if r["Sales"] != 0 else 0, axis=1
        )

    col1, col2 = st.columns(2)

    # Top 10 by Sales
    top_sales = prod.nlargest(10, "Sales")
    fig_top_sales = go.Figure(go.Bar(
        x=top_sales["Sales"], y=top_sales["Product Name"],
        orientation="h", marker_color="#3b82d4",
        text=[f"${v:,.0f}" for v in top_sales["Sales"]],
        textposition="outside",
    ))
    fig_top_sales.update_layout(
        title="Top 10 Products by Sales", xaxis_title="Sales ($)", yaxis_title="",
        template=CHART_THEME, margin=dict(t=50, b=40, l=300),
        yaxis=dict(autorange="reversed"),
    )
    col1.plotly_chart(fig_top_sales, use_container_width=True, key="prod_top_sales")

    # Top 10 by Profit
    top_profit = prod.nlargest(10, "Profit")
    fig_top_profit = go.Figure(go.Bar(
        x=top_profit["Profit"], y=top_profit["Product Name"],
        orientation="h", marker_color="#22c55e",
        text=[f"${v:,.0f}" for v in top_profit["Profit"]],
        textposition="outside",
    ))
    fig_top_profit.update_layout(
        title="Top 10 Products by Profit", xaxis_title="Profit ($)", yaxis_title="",
        template=CHART_THEME, margin=dict(t=50, b=40, l=300),
        yaxis=dict(autorange="reversed"),
    )
    col2.plotly_chart(fig_top_profit, use_container_width=True, key="prod_top_profit")

    # Bottom 10 by Profit (loss-making)
    bottom_profit = prod.nsmallest(10, "Profit")
    fig3 = go.Figure(go.Bar(
        x=bottom_profit["Profit"], y=bottom_profit["Product Name"],
        orientation="h", marker_color="#dc2626",
        text=[f"${v:,.0f}" for v in bottom_profit["Profit"]],
        textposition="outside",
    ))
    fig3.update_layout(
        title="Bottom 10 Products by Profit (Highest Loss)", xaxis_title="Profit ($)", yaxis_title="",
        template=CHART_THEME, margin=dict(t=50, b=40, l=300),
    )
    st.plotly_chart(fig3, use_container_width=True, key="chart_21")

    # Top 10 by Quantity
    top_qty = prod.nlargest(10, "Quantity")
    fig4 = bar_chart(top_qty, "Quantity", "Product Name", "Top 10 Products by Quantity Sold",
                     "Quantity", "Product Name", orientation="h")
    st.plotly_chart(fig4, use_container_width=True, key="chart_22")

    # Product table
    st.subheader("Product Summary Table")
    prod_display = prod.copy()
    prod_display["Sales"] = prod_display["Sales"].map("${:,.2f}".format)
    prod_display["Profit"] = prod_display["Profit"].map("${:,.2f}".format)
    prod_display["Discount"] = prod_display["Discount"].map("{:.1%}".format)
    prod_display["Profit Margin (%)"] = prod_display["Profit Margin (%)"].map("{:.2f}%".format)
    st.dataframe(prod_display, use_container_width=True, height=350)


# ─────────────────────────────────────────────
# SECTION: CUSTOMER ANALYSIS
# ─────────────────────────────────────────────
def render_customer_analysis(df: pd.DataFrame):
    st.markdown('<div class="section-header">Customer Analysis</div>', unsafe_allow_html=True)
    st.markdown("---")

    if "Customer ID" not in df.columns:
        st.warning("Customer ID column not found.")
        return

    col1, col2 = st.columns(2)

    # Sales by Segment
    if "Segment" in df.columns:
        seg_s = df.groupby("Segment")["Sales"].sum().reset_index()
        fig = pie_chart(seg_s, "Segment", "Sales", "Sales by Customer Segment")
        col1.plotly_chart(fig, use_container_width=True, key="chart_23")

        seg_p = df.groupby("Segment")["Profit"].sum().reset_index()
        fig2 = pie_chart(seg_p, "Segment", "Profit", "Profit by Customer Segment")
        col2.plotly_chart(fig2, use_container_width=True, key="chart_24")

    # Avg order value by segment
    if "Segment" in df.columns and "Order ID" in df.columns:
        aov = (
            df.groupby(["Segment", "Order ID"])["Sales"].sum()
            .reset_index()
            .groupby("Segment")["Sales"].mean()
            .reset_index()
        )
        aov.columns = ["Segment", "Avg Order Value ($)"]
        fig3 = bar_chart(aov, "Segment", "Avg Order Value ($)", "Avg Order Value by Segment", "Segment", "Avg Order Value ($)")
        st.plotly_chart(fig3, use_container_width=True, key="chart_25")

    # Customer summary table
    if "Customer Name" in df.columns and "Order ID" in df.columns:
        cust_summary = (
            df.groupby(["Customer ID", "Customer Name"])
            .agg(
                Orders=("Order ID", "nunique"),
                Total_Sales=("Sales", "sum"),
                Total_Profit=("Profit", "sum"),
            )
            .reset_index()
        )
        cust_summary["Avg Order Value"] = cust_summary["Total_Sales"] / cust_summary["Orders"]

        col3, col4 = st.columns(2)

        top_cust_s = cust_summary.nlargest(10, "Total_Sales")
        fig_c1 = go.Figure(go.Bar(
            x=top_cust_s["Total_Sales"], y=top_cust_s["Customer Name"],
            orientation="h", marker_color="#3b82d4",
        ))
        fig_c1.update_layout(
            title="Top 10 Customers by Sales", xaxis_title="Sales ($)",
            template=CHART_THEME, margin=dict(t=50, b=40, l=140),
            yaxis=dict(autorange="reversed"),
        )
        col3.plotly_chart(fig_c1, use_container_width=True, key="chart_26")

        top_cust_p = cust_summary.nlargest(10, "Total_Profit")
        fig_c2 = go.Figure(go.Bar(
            x=top_cust_p["Total_Profit"], y=top_cust_p["Customer Name"],
            orientation="h", marker_color="#22c55e",
        ))
        fig_c2.update_layout(
            title="Top 10 Customers by Profit", xaxis_title="Profit ($)",
            template=CHART_THEME, margin=dict(t=50, b=40, l=140),
            yaxis=dict(autorange="reversed"),
        )
        col4.plotly_chart(fig_c2, use_container_width=True, key="chart_27")

        st.subheader("Customer Summary Table")
        disp = cust_summary.sort_values("Total_Sales", ascending=False).head(50).copy()
        disp["Total_Sales"] = disp["Total_Sales"].map("${:,.2f}".format)
        disp["Total_Profit"] = disp["Total_Profit"].map("${:,.2f}".format)
        disp["Avg Order Value"] = disp["Avg Order Value"].map("${:,.2f}".format)
        disp.columns = ["Customer ID", "Customer Name", "Orders", "Total Sales", "Total Profit", "Avg Order Value"]
        st.dataframe(disp, use_container_width=True, height=350)


# ─────────────────────────────────────────────
# SECTION: REGIONAL ANALYSIS
# ─────────────────────────────────────────────
def render_regional_analysis(df: pd.DataFrame):
    st.markdown('<div class="section-header">Regional Analysis</div>', unsafe_allow_html=True)
    st.markdown("---")

    if "Region" not in df.columns:
        st.warning("Region column not found.")
        return

    metrics = []
    for region, grp in df.groupby("Region"):
        metrics.append({
            "Region": region,
            "Sales": grp["Sales"].sum(),
            "Profit": grp["Profit"].sum(),
            "Orders": grp["Order ID"].nunique() if "Order ID" in grp.columns else len(grp),
            "Quantity": grp["Quantity"].sum() if "Quantity" in grp.columns else 0,
            "Avg Order Value": grp.groupby("Order ID")["Sales"].sum().mean() if "Order ID" in grp.columns else 0,
        })
    reg_df = pd.DataFrame(metrics).sort_values("Sales", ascending=False)

    col1, col2 = st.columns(2)
    fig1 = bar_chart(reg_df, "Region", "Sales", "Sales by Region", "Region", "Sales ($)")
    col1.plotly_chart(fig1, use_container_width=True, key="chart_28")

    fig2 = bar_chart(reg_df, "Region", "Profit", "Profit by Region", "Region", "Profit ($)")
    col2.plotly_chart(fig2, use_container_width=True, key="chart_29")

    col3, col4 = st.columns(2)
    fig3 = bar_chart(reg_df, "Region", "Orders", "Orders by Region", "Region", "Number of Orders")
    col3.plotly_chart(fig3, use_container_width=True, key="chart_30")

    fig4 = bar_chart(reg_df, "Region", "Avg Order Value", "Avg Order Value by Region", "Region", "Avg Order Value ($)")
    col4.plotly_chart(fig4, use_container_width=True, key="chart_31")

    # State-level analysis
    if "State" in df.columns:
        st.subheader("State-Level Performance")
        state_df = (
            df.groupby("State")
            .agg(Sales=("Sales","sum"), Profit=("Profit","sum"),
                 Orders=("Order ID","nunique"))
            .reset_index()
            .sort_values("Sales", ascending=False)
        )
        col5, col6 = st.columns(2)
        top_states = state_df.nlargest(15, "Sales")
        fig5 = go.Figure(go.Bar(
            x=top_states["Sales"], y=top_states["State"],
            orientation="h", marker_color="#3b82d4",
        ))
        fig5.update_layout(
            title="Top 15 States by Sales", xaxis_title="Sales ($)",
            template=CHART_THEME, margin=dict(t=50, b=40, l=120),
            yaxis=dict(autorange="reversed"),
        )
        col5.plotly_chart(fig5, use_container_width=True, key="chart_32")

        top_states_p = state_df.nlargest(15, "Profit")
        fig6 = go.Figure(go.Bar(
            x=top_states_p["Profit"], y=top_states_p["State"],
            orientation="h", marker_color="#22c55e",
        ))
        fig6.update_layout(
            title="Top 15 States by Profit", xaxis_title="Profit ($)",
            template=CHART_THEME, margin=dict(t=50, b=40, l=120),
            yaxis=dict(autorange="reversed"),
        )
        col6.plotly_chart(fig6, use_container_width=True, key="chart_33")


# ─────────────────────────────────────────────
# SECTION: DISCOUNT ANALYSIS
# ─────────────────────────────────────────────
def render_discount_analysis(df: pd.DataFrame):
    st.markdown('<div class="section-header">Discount Analysis</div>', unsafe_allow_html=True)
    st.markdown("---")

    if "Discount" not in df.columns:
        st.warning("Discount column not found.")
        return

    avg_disc = df["Discount"].mean()
    st.info(
        f"Average Discount across the filtered dataset: **{avg_disc:.1%}**  "
        "Note: association between discount and profit does not imply direct causation."
    )

    # Discount range buckets
    df2 = df.copy()
    bins = [-0.01, 0.001, 0.1, 0.2, 0.3, 0.4, 0.5, 1.0]
    labels = ["0%", "1-10%", "11-20%", "21-30%", "31-40%", "41-50%", ">50%"]
    df2["Discount Range"] = pd.cut(df2["Discount"], bins=bins, labels=labels)

    disc_grp = df2.groupby("Discount Range", observed=True).agg(
        Sales=("Sales","sum"), Profit=("Profit","sum"), Count=("Discount","count")
    ).reset_index()

    col1, col2 = st.columns(2)
    fig1 = bar_chart(disc_grp, "Discount Range", "Sales", "Sales by Discount Range", "Discount Range", "Sales ($)")
    col1.plotly_chart(fig1, use_container_width=True, key="chart_34")

    colors = ["#dc2626" if v < 0 else "#3b82d4" for v in disc_grp["Profit"]]
    fig2 = go.Figure(go.Bar(
        x=disc_grp["Discount Range"], y=disc_grp["Profit"],
        marker_color=colors,
    ))
    fig2.update_layout(
        title="Profit by Discount Range", xaxis_title="Discount Range", yaxis_title="Profit ($)",
        template=CHART_THEME, margin=dict(t=50, b=40),
    )
    col2.plotly_chart(fig2, use_container_width=True, key="chart_35")

    # Scatter: Discount vs Profit
    sample = df.sample(min(2000, len(df)), random_state=42) if len(df) > 2000 else df
    col3, col4 = st.columns(2)
    fig3 = scatter_chart(sample, "Discount", "Profit", "Discount vs Profit", "Discount", "Profit ($)",
                         color="Category" if "Category" in sample.columns else None)
    fig3.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.4)
    col3.plotly_chart(fig3, use_container_width=True, key="chart_36")

    fig4 = scatter_chart(sample, "Discount", "Sales", "Discount vs Sales", "Discount", "Sales ($)",
                         color="Category" if "Category" in sample.columns else None)
    col4.plotly_chart(fig4, use_container_width=True, key="chart_37")


# ─────────────────────────────────────────────
# SECTION: TIME ANALYSIS
# ─────────────────────────────────────────────
def render_time_analysis(df: pd.DataFrame):
    st.markdown('<div class="section-header">Time-Based Analysis</div>', unsafe_allow_html=True)
    st.markdown("---")

    if "Order Date" not in df.columns:
        st.warning("Order Date column not found.")
        return

    # Yearly
    if "Year" in df.columns:
        yr = df.groupby("Year").agg(Sales=("Sales","sum"), Profit=("Profit","sum")).reset_index()
        col1, col2 = st.columns(2)
        fig1 = bar_chart(yr, "Year", "Sales", "Yearly Sales", "Year", "Sales ($)")
        fig1.update_xaxes(type="category")
        col1.plotly_chart(fig1, use_container_width=True, key="chart_38")
        fig2 = bar_chart(yr, "Year", "Profit", "Yearly Profit", "Year", "Profit ($)")
        fig2.update_xaxes(type="category")
        col2.plotly_chart(fig2, use_container_width=True, key="chart_39")

    # Monthly aggregated over all years
    if "Month Name" in df.columns:
        month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        mo = df.groupby("Month Name").agg(Sales=("Sales","sum"), Profit=("Profit","sum")).reset_index()
        mo["Month Name"] = pd.Categorical(mo["Month Name"], categories=month_order, ordered=True)
        mo = mo.sort_values("Month Name")

        col3, col4 = st.columns(2)
        fig3 = line_chart(mo, "Month Name", "Sales", "Sales by Month (All Years)", "Month", "Sales ($)")
        col3.plotly_chart(fig3, use_container_width=True, key="chart_40")
        fig4 = line_chart(mo, "Month Name", "Profit", "Profit by Month (All Years)", "Month", "Profit ($)")
        col4.plotly_chart(fig4, use_container_width=True, key="chart_41")

        # Highlight peaks dynamically
        if not mo.empty:
            high_s = mo.loc[mo["Sales"].idxmax(), "Month Name"]
            low_s = mo.loc[mo["Sales"].idxmin(), "Month Name"]
            high_p = mo.loc[mo["Profit"].idxmax(), "Month Name"]
            low_p = mo.loc[mo["Profit"].idxmin(), "Month Name"]
            st.markdown(
                f"**Highest Sales Month:** {high_s} &nbsp;|&nbsp; "
                f"**Lowest Sales Month:** {low_s} &nbsp;|&nbsp; "
                f"**Highest Profit Month:** {high_p} &nbsp;|&nbsp; "
                f"**Lowest Profit Month:** {low_p}"
            )

    # Quarterly
    if "Quarter" in df.columns:
        q = df.groupby(["Year","Quarter"]).agg(Sales=("Sales","sum"), Profit=("Profit","sum")).reset_index()
        q["Period"] = q["Year"].astype(str) + "-" + q["Quarter"].astype(str)
        q = q.sort_values(["Year","Quarter"])
        fig5 = line_chart(q, "Period", "Sales", "Quarterly Sales Trend", "Quarter", "Sales ($)")
        st.plotly_chart(fig5, use_container_width=True, key="chart_42")

    # Day of week
    if "Day of Week" in df.columns:
        dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        dow = df.groupby("Day of Week")["Sales"].sum().reset_index()
        dow["Day of Week"] = pd.Categorical(dow["Day of Week"], categories=dow_order, ordered=True)
        dow = dow.sort_values("Day of Week")
        fig6 = bar_chart(dow, "Day of Week", "Sales", "Sales by Day of Week", "Day", "Sales ($)")
        st.plotly_chart(fig6, use_container_width=True, key="chart_43")


# ─────────────────────────────────────────────
# SECTION: BUSINESS INSIGHTS
# ─────────────────────────────────────────────
def generate_business_insights(df: pd.DataFrame):
    st.markdown('<div class="section-header">Business Insights</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.caption("All insights are dynamically generated from the currently filtered dataset.")

    def insight_card(title, finding, meaning, action):
        st.markdown(
            f'<div class="insight-box">'
            f'<strong>{title}</strong><br>'
            f'<strong>Finding:</strong> {finding}<br>'
            f'<strong>Business Meaning:</strong> {meaning}<br>'
            f'<strong>Possible Action:</strong> {action}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Sales Insights
    st.subheader("Sales Insights")
    if "Category" in df.columns and "Sales" in df.columns:
        top_cat = df.groupby("Category")["Sales"].sum().idxmax()
        top_cat_val = df.groupby("Category")["Sales"].sum().max()
        insight_card(
            "Top Sales Category",
            f"{top_cat} generated the highest sales totalling ${top_cat_val:,.2f}.",
            f"{top_cat} drives the largest share of revenue in the selected period.",
            f"Continue investing in {top_cat} marketing and inventory to sustain revenue.",
        )

    if "Region" in df.columns:
        top_reg = df.groupby("Region")["Sales"].sum().idxmax()
        top_reg_val = df.groupby("Region")["Sales"].sum().max()
        insight_card(
            "Top Sales Region",
            f"The {top_reg} region recorded the highest sales of ${top_reg_val:,.2f}.",
            "Regional concentration may create risk if that region's demand falls.",
            "Explore growth opportunities in underperforming regions.",
        )

    # ── Profit Insights
    st.subheader("Profit Insights")
    if "Sub-Category" in df.columns and "Profit" in df.columns:
        sub_prof = df.groupby("Sub-Category")["Profit"].sum()
        loss_subs = sub_prof[sub_prof < 0]
        if not loss_subs.empty:
            loss_list = ", ".join(loss_subs.index.tolist())
            insight_card(
                "Loss-Making Sub-Categories",
                f"The following sub-categories show negative total profit: {loss_list}.",
                "These sub-categories may be sold at high discounts or low margins.",
                "Review pricing strategy and discount policies for these sub-categories.",
            )

        top_sub = sub_prof.idxmax()
        insight_card(
            "Most Profitable Sub-Category",
            f"{top_sub} generated the highest profit of ${sub_prof.max():,.2f}.",
            f"{top_sub} is the most profitable product line.",
            f"Protect margins in {top_sub} and expand its product range if possible.",
        )

    # ── Product Insights
    st.subheader("Product Insights")
    if "Product Name" in df.columns and "Profit" in df.columns:
        prod_prof = df.groupby("Product Name")["Profit"].sum()
        neg_prods = (prod_prof < 0).sum()
        insight_card(
            "Negative-Profit Products",
            f"{neg_prods} products have negative total profit in the selected data.",
            "These products are contributing to losses, possibly due to deep discounts.",
            "Audit pricing and discount levels for these products.",
        )

    # ── Customer Insights
    st.subheader("Customer Insights")
    if "Segment" in df.columns:
        top_seg_s = df.groupby("Segment")["Sales"].sum().idxmax()
        top_seg_p = df.groupby("Segment")["Profit"].sum().idxmax()
        insight_card(
            "Customer Segment Performance",
            f"The {top_seg_s} segment generates the highest sales; "
            f"the {top_seg_p} segment generates the highest profit.",
            "Different segments may have different pricing sensitivities.",
            "Tailor campaigns to the most profitable segment while growing the largest sales segment.",
        )

    # ── Discount Insights
    st.subheader("Discount Insights")
    if "Discount" in df.columns and "Profit" in df.columns:
        corr = df[["Discount","Profit"]].corr().iloc[0, 1]
        direction = "negative" if corr < 0 else "positive"
        insight_card(
            "Discount-Profit Association",
            f"The correlation between Discount and Profit is {corr:.3f} ({direction} association).",
            "Higher discounts are associated with lower profit in this dataset. "
            "This does not prove causation — other factors may be involved.",
            "Consider setting discount limits, especially for low-margin product lines.",
        )

    # ── Regional Insights
    st.subheader("Regional Insights")
    if "Region" in df.columns and "Profit" in df.columns:
        reg_prof = df.groupby("Region")["Profit"].sum()
        if (reg_prof < 0).any():
            neg_regs = reg_prof[reg_prof < 0].index.tolist()
            insight_card(
                "Regions with Negative Profit",
                f"Region(s) with negative profit: {', '.join(neg_regs)}.",
                "These regions may have high operating costs or excessive discounting.",
                "Investigate cost structure and pricing in these regions.",
            )
        bot_reg = reg_prof.idxmin()
        insight_card(
            "Lowest Profit Region",
            f"The {bot_reg} region records the lowest total profit of ${reg_prof.min():,.2f}.",
            "This region may require operational or pricing attention.",
            f"Review sales mix, pricing, and discounting policies in the {bot_reg} region.",
        )


# ─────────────────────────────────────────────
# SECTION: DATA QUALITY
# ─────────────────────────────────────────────
def render_data_quality(df_raw: pd.DataFrame, df_clean: pd.DataFrame):
    st.markdown('<div class="section-header">Data Quality Report</div>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records", f"{len(df_raw):,}")
    col2.metric("Total Columns", str(df_raw.shape[1]))
    dup = df_raw.duplicated().sum()
    col3.metric("Duplicate Rows", str(dup))
    col4.metric("Records After Cleaning", f"{len(df_clean):,}")

    st.subheader("Column-Level Quality Summary")
    quality = []
    for col in df_raw.columns:
        missing = df_raw[col].isnull().sum()
        quality.append({
            "Column": col,
            "Data Type": str(df_raw[col].dtype),
            "Missing Values": int(missing),
            "Missing %": f"{(missing / len(df_raw)) * 100:.2f}%",
            "Unique Values": int(df_raw[col].nunique()),
        })
    st.dataframe(pd.DataFrame(quality), use_container_width=True)

    st.subheader("Numerical Summary Statistics")
    num_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols:
        st.dataframe(df_clean[num_cols].describe().round(3), use_container_width=True)

    st.subheader("Date Range")
    if "Order Date" in df_clean.columns and pd.api.types.is_datetime64_any_dtype(df_clean["Order Date"]):
        st.write(f"**Order Date:** {df_clean['Order Date'].min().date()} to {df_clean['Order Date'].max().date()}")
    if "Ship Date" in df_clean.columns and pd.api.types.is_datetime64_any_dtype(df_clean["Ship Date"]):
        st.write(f"**Ship Date:** {df_clean['Ship Date'].min().date()} to {df_clean['Ship Date'].max().date()}")


# ─────────────────────────────────────────────
# SECTION: RAW DATA
# ─────────────────────────────────────────────
def render_raw_data(df: pd.DataFrame):
    st.markdown('<div class="section-header">Explore Raw Data</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.caption(f"Showing the currently filtered dataset: **{len(df):,} rows × {df.shape[1]} columns**")
    st.dataframe(df, use_container_width=True, height=500)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv_buffer.getvalue(),
        file_name="superstore_filtered.csv",
        mime="text/csv",
    )


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    # ── Load
    df_raw, csv_path = load_data()
    if df_raw is None:
        st.error(
            "No CSV file found in the project folder. "
            "Please ensure the Superstore dataset CSV is present."
        )
        st.stop()

    # ── Clean
    df_clean = clean_data(df_raw)

    # ── Feature engineering
    df_feat = create_features(df_clean)

    # ── Sidebar filters (applied on feature-engineered data)
    df_filtered = render_sidebar(df_feat)

    if df_filtered.empty:
        st.warning("No data matches the selected filters. Please adjust your selections.")
        st.stop()

    # ── KPIs
    kpis = calculate_kpis(df_filtered)

    # ── Header
    st.title("Superstore Sales & Profit Analytics Dashboard")
    st.markdown(
        f"**Dataset:** `{csv_path}` &nbsp;|&nbsp; "
        f"**Rows:** {len(df_clean):,} &nbsp;|&nbsp; "
        f"**Columns:** {df_clean.shape[1]} &nbsp;|&nbsp; "
        f"**Filtered Rows:** {len(df_filtered):,}"
    )
    st.markdown("---")

    # ── Tabs
    tabs = st.tabs([
        "Overview",
        "Sales Analysis",
        "Profitability",
        "Product Analysis",
        "Customer Analysis",
        "Regional Analysis",
        "Discount & Time",
        "Business Insights",
        "Data Quality",
        "Raw Data",
    ])

    with tabs[0]:
        render_overview(df_filtered, kpis)

    with tabs[1]:
        render_sales_analysis(df_filtered)

    with tabs[2]:
        render_profit_analysis(df_filtered)

    with tabs[3]:
        render_product_analysis(df_filtered)

    with tabs[4]:
        render_customer_analysis(df_filtered)

    with tabs[5]:
        render_regional_analysis(df_filtered)

    with tabs[6]:
        render_discount_analysis(df_filtered)
        st.markdown("---")
        render_time_analysis(df_filtered)

    with tabs[7]:
        generate_business_insights(df_filtered)

    with tabs[8]:
        render_data_quality(df_raw, df_clean)

    with tabs[9]:
        render_raw_data(df_filtered)


if __name__ == "__main__":
    main()
