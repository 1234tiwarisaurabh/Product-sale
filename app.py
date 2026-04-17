import os
import io
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import warnings
warnings.filterwarnings("ignore")

# ── Resolve sample data path relative to THIS script ─────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_CSV = os.path.join(SCRIPT_DIR, "sample_data.csv")

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Palette ───────────────────────────────────────────────────────────────────
COLORS = {
    "primary":   "#00D4FF",
    "secondary": "#FF6B6B",
    "accent":    "#FFE66D",
    "green":     "#4ECDC4",
    "purple":    "#C77DFF",
    "bg":        "#0A0E1A",
    "card":      "#111827",
    "border":    "#1F2937",
    "text":      "#F9FAFB",
    "muted":     "#9CA3AF",
}

PLOTLY_PALETTE = [
    "#00D4FF","#FF6B6B","#FFE66D","#4ECDC4","#C77DFF",
    "#FF9F43","#54A0FF","#5F27CD","#01CBC6","#FF3F34",
]

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
  html, body, [class*="css"] {{
      font-family: 'Space Grotesk', sans-serif;
      background-color: {COLORS['bg']};
      color: {COLORS['text']};
  }}
  section[data-testid="stSidebar"] {{
      background: {COLORS['card']};
      border-right: 1px solid {COLORS['border']};
  }}
  section[data-testid="stSidebar"] * {{ color: {COLORS['text']} !important; }}
  [data-testid="metric-container"] {{
      background: {COLORS['card']};
      border: 1px solid {COLORS['border']};
      border-radius: 16px;
      padding: 20px !important;
      transition: border-color .2s;
  }}
  [data-testid="metric-container"]:hover {{ border-color: {COLORS['primary']}; }}
  [data-testid="stMetricValue"] {{
      font-family: 'JetBrains Mono', monospace !important;
      font-size: 1.8rem !important;
      color: {COLORS['primary']} !important;
  }}
  [data-testid="stMetricLabel"] {{ color: {COLORS['muted']} !important; font-size:.85rem !important; }}
  [data-testid="stMetricDelta"]  {{ font-size:.8rem !important; }}
  .stPlotlyChart {{
      background: {COLORS['card']};
      border: 1px solid {COLORS['border']};
      border-radius: 16px;
      padding: 4px;
  }}
  h1 {{ color: {COLORS['text']} !important; font-weight:700 !important; }}
  h2, h3 {{ color: {COLORS['text']} !important; font-weight:600 !important; }}
  .hero {{
      background: linear-gradient(135deg,#0d1b2a 0%,#1a2744 50%,#0d1b2a 100%);
      border: 1px solid {COLORS['border']};
      border-radius: 20px;
      padding: 32px 40px;
      margin-bottom: 24px;
      position: relative;
      overflow: hidden;
  }}
  .hero::before {{
      content:'';
      position:absolute; top:0; left:0; right:0; bottom:0;
      background: radial-gradient(ellipse at 20% 50%, rgba(0,212,255,.08) 0%, transparent 60%),
                  radial-gradient(ellipse at 80% 50%, rgba(199,125,255,.06) 0%, transparent 60%);
      pointer-events:none;
  }}
  .hero-title {{
      font-size:2.2rem; font-weight:700; margin:0; line-height:1.2;
      background: linear-gradient(90deg, {COLORS['primary']}, {COLORS['purple']});
      -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  }}
  .hero-sub {{ color:{COLORS['muted']}; margin-top:6px; font-size:.95rem; }}
  div[data-baseweb="select"] > div {{ background:{COLORS['card']} !important; border-color:{COLORS['border']} !important; }}
  div[data-baseweb="select"] span  {{ color:{COLORS['text']} !important; }}
  [data-baseweb="tag"] {{ background:{COLORS['border']} !important; }}
  .stCheckbox label {{ color:{COLORS['text']} !important; }}
  .stTab [data-baseweb="tab"] {{ color:{COLORS['muted']} !important; }}
  .stTab [aria-selected="true"] {{ color:{COLORS['primary']} !important; border-bottom-color:{COLORS['primary']} !important; }}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Grotesk", color=COLORS["text"]),
    xaxis=dict(gridcolor=COLORS["border"], linecolor=COLORS["border"]),
    yaxis=dict(gridcolor=COLORS["border"], linecolor=COLORS["border"]),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["border"]),
    margin=dict(l=10, r=10, t=40, b=10),
)

def apply_layout(fig, **kwargs):
    fig.update_layout(**{**PLOTLY_LAYOUT, **kwargs})
    return fig

def fmt(n):  return f"{n:,.0f}"
def fmtk(n): return f"Rs.{n/1e6:.2f}M" if n>=1e6 else f"Rs.{n/1e3:.1f}K" if n>=1e3 else f"Rs.{n:.0f}"

# ── Data Loader ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading data...")
def load_data(file_bytes, filename):
    """Load from raw bytes - no hardcoded file path needed."""
    ext = filename.rsplit(".", 1)[-1].lower()
    buf = io.BytesIO(file_bytes)
    if ext == "csv":
        df = pd.read_csv(buf)
    elif ext in ("xlsx", "xls"):
        df = pd.read_excel(buf)
    elif ext == "json":
        df = pd.read_json(buf)
    else:
        df = pd.read_csv(buf)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df

def detect_schema(df):
    month_cols = [c for c in df.columns if "month" in c or "m_" in c]
    if not month_cols:
        month_cols = [c for c in df.columns
                      if any(f"_{i}" in c or c.endswith(str(i)) for i in range(1, 13))
                      and pd.api.types.is_numeric_dtype(df[c])]
    cat_col   = next((c for c in df.columns if "categ" in c or "type" in c or "dept" in c), None)
    name_col  = next((c for c in df.columns if "name" in c or "product" in c or "item" in c), None)
    price_col = next((c for c in df.columns if "price" in c or "cost" in c), None)
    score_col = next((c for c in df.columns if ("review" in c and "score" in c) or "rating" in c), None)
    return month_cols, cat_col, name_col, price_col, score_col

def month_labels(cols):
    labels = []
    for c in cols:
        digits = "".join(filter(str.isdigit, c))
        if digits:
            n = int(digits)
            labels.append(MONTH_NAMES[n-1] if 1 <= n <= 12 else c)
        else:
            labels.append(c)
    return labels

def build_long(df, month_cols, name_col, cat_col, price_col):
    id_vars = [c for c in [name_col, cat_col, price_col] if c]
    melted  = df[id_vars + month_cols].melt(id_vars=id_vars, var_name="month_raw", value_name="sales")
    melted["month_num"] = melted["month_raw"].str.extract(r"(\d+)").astype(float)
    melted["month"] = melted["month_num"].apply(
        lambda x: MONTH_NAMES[int(x)-1] if pd.notna(x) and 1 <= x <= 12 else str(x))
    if price_col:
        melted["revenue"] = melted["sales"] * melted[price_col]
    return melted

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Sales Intelligence")
    st.markdown("---")
    uploaded = st.file_uploader(
        "Upload your dataset",
        type=["csv","xlsx","xls","json"],
        help="Wide format (months as columns) or long format both supported",
    )
    st.markdown("---")
    st.markdown("### Filters")

# ── Load data (bytes-based, no path dependency) ───────────────────────────────
if uploaded is not None:
    file_bytes = uploaded.read()
    filename   = uploaded.name
elif os.path.isfile(SAMPLE_CSV):
    with open(SAMPLE_CSV, "rb") as f:
        file_bytes = f.read()
    filename = "sample_data.csv"
else:
    st.markdown("""
    <div class="hero">
      <div class="hero-title">Welcome to Sales Intelligence</div>
      <div class="hero-sub">
        Upload a <b>CSV / Excel / JSON</b> file using the sidebar to get started.<br><br>
        Expected columns: <code>product_name</code>, <code>category</code>, <code>price</code>,
        <code>sales_month_1 ... sales_month_12</code>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

raw = load_data(file_bytes, filename)

# ── Schema detection ──────────────────────────────────────────────────────────
df = raw.copy()
month_cols, cat_col, name_col, price_col, score_col = detect_schema(df)

if not month_cols:
    st.error("Could not detect monthly sales columns. Make sure columns are named like sales_month_1 ... sales_month_12.")
    st.stop()

for c in month_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

df["total_sales"] = df[month_cols].sum(axis=1)

if price_col:
    df[price_col] = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
    df["total_revenue"] = df["total_sales"] * df[price_col]

M_LABELS = month_labels(month_cols)

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    if cat_col:
        cats     = sorted(df[cat_col].dropna().unique().tolist())
        sel_cats = st.multiselect("Category", cats, default=cats)
        df_f     = df[df[cat_col].isin(sel_cats)]
    else:
        df_f = df

    top_n = st.slider("Top N Products", 5, min(50, max(5, len(df_f))), 10) if name_col else 10

    show_rev      = price_col is not None
    metric_choice = st.radio("Primary Metric", ["Sales Units","Revenue"]) if show_rev else "Sales Units"

    st.markdown("---")
    st.markdown(f"<span style='color:{COLORS['muted']};font-size:.75rem'>📁 {len(df_f):,} products loaded</span>",
                unsafe_allow_html=True)

agg_col = "total_revenue" if metric_choice=="Revenue" and show_rev else "total_sales"

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <div class="hero-title">Sales Intelligence Dashboard</div>
  <div class="hero-sub">Monthly product analytics &middot; {len(df_f):,} products &middot; {len(month_cols)} months of data</div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_units    = int(df_f["total_sales"].sum())
monthly_sum    = df_f[month_cols].sum()
best_idx       = monthly_sum.idxmax()
best_val       = int(monthly_sum.max())
best_n         = int("".join(filter(str.isdigit, best_idx)))
best_month_name = MONTH_NAMES[best_n-1] if 1 <= best_n <= 12 else best_idx

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Units Sold", fmt(total_units))
k2.metric("Products Tracked", fmt(len(df_f)))
k3.metric("Peak Month",       best_month_name, f"{fmt(best_val)} units")

if cat_col and not df_f.empty:
    top_cat = df_f.groupby(cat_col)["total_sales"].sum().idxmax()
    k4.metric("Top Category", top_cat)
else:
    k4.metric("Months Tracked", len(month_cols))

if show_rev:
    k5.metric("Total Revenue", fmtk(float(df_f["total_revenue"].sum())))
elif name_col and not df_f.empty:
    best_p = df_f.nlargest(1,"total_sales")[name_col].values[0]
    k5.metric("Best Product", best_p[:18]+"..." if len(best_p)>18 else best_p)
else:
    k5.metric("Avg Monthly Units", fmt(total_units / len(month_cols)))

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs(["📈 Trends","🏆 Products","🗂️ Categories","📊 Distribution","🔥 Heatmap","🔗 Correlation"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1  TRENDS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    monthly_total = pd.Series(df_f[month_cols].sum().values, index=M_LABELS)

    c1, c2 = st.columns([2, 1])
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=M_LABELS, y=monthly_total.values, mode="lines+markers",
            line=dict(color=COLORS["primary"], width=3),
            marker=dict(size=8, color=COLORS["primary"], line=dict(width=2, color=COLORS["bg"])),
            fill="tozeroy", fillcolor="rgba(0,212,255,0.08)", name="Total Sales",
        ))
        apply_layout(fig, title="Monthly Sales Trend", height=320)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        mom = monthly_total.pct_change() * 100
        bar_colors = [COLORS["green"] if v >= 0 else COLORS["secondary"] for v in mom.values]
        fig2 = go.Figure(go.Bar(
            x=M_LABELS, y=mom.values, marker_color=bar_colors,
            text=[f"{v:.1f}%" if pd.notna(v) else "" for v in mom.values],
            textposition="outside",
        ))
        apply_layout(fig2, title="MoM Growth (%)", height=320, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    if cat_col:
        cat_monthly = df_f.groupby(cat_col)[month_cols].sum()
        fig3 = go.Figure()
        for i, (cat, row) in enumerate(cat_monthly.iterrows()):
            fig3.add_trace(go.Scatter(
                x=M_LABELS, y=row.values, name=cat, stackgroup="one",
                line=dict(width=0.5, color=PLOTLY_PALETTE[i % len(PLOTLY_PALETTE)]),
            ))
        apply_layout(fig3, title="Stacked Monthly Sales by Category", height=340)
        st.plotly_chart(fig3, use_container_width=True)

    cum = monthly_total.cumsum()
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=M_LABELS, y=cum.values, mode="lines+markers",
        line=dict(color=COLORS["purple"], width=3, dash="dot"),
        marker=dict(size=7, color=COLORS["purple"]),
        fill="tozeroy", fillcolor="rgba(199,125,255,0.07)", name="Cumulative",
    ))
    apply_layout(fig4, title="Cumulative Sales Across Year", height=280)
    st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2  PRODUCTS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    if name_col:
        top_df = df_f.nlargest(top_n, "total_sales")
        bot_df = df_f.nsmallest(top_n, "total_sales")

        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(top_df.sort_values("total_sales"), x="total_sales", y=name_col,
                         orientation="h", color="total_sales",
                         color_continuous_scale=[[0,COLORS["border"]],[1,COLORS["primary"]]],
                         labels={"total_sales":"Units Sold"})
            fig.update_coloraxes(showscale=False)
            apply_layout(fig, title=f"Top {top_n} Products", height=420)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig2 = px.bar(bot_df.sort_values("total_sales", ascending=False),
                          x="total_sales", y=name_col, orientation="h", color="total_sales",
                          color_continuous_scale=[[0,COLORS["secondary"]],[1,COLORS["border"]]],
                          labels={"total_sales":"Units Sold"})
            fig2.update_coloraxes(showscale=False)
            apply_layout(fig2, title=f"Bottom {top_n} Products", height=420)
            st.plotly_chart(fig2, use_container_width=True)

        top5 = df_f.nlargest(min(7, top_n), "total_sales")
        fig3 = go.Figure()
        for idx, (_, row) in enumerate(top5.iterrows()):
            fig3.add_trace(go.Scatter(
                x=M_LABELS, y=[row[m] for m in month_cols],
                name=row[name_col], mode="lines+markers",
                line=dict(width=2, color=PLOTLY_PALETTE[idx % len(PLOTLY_PALETTE)]),
            ))
        apply_layout(fig3, title="Top Products - Monthly Performance", height=380)
        st.plotly_chart(fig3, use_container_width=True)

        if cat_col:
            fig4 = px.treemap(df_f, path=[cat_col, name_col], values="total_sales",
                              color="total_sales",
                              color_continuous_scale=[[0,"#1F2937"],[0.5,COLORS["green"]],[1,COLORS["primary"]]])
            fig4.update_traces(textfont_size=12)
            apply_layout(fig4, title="Sales Treemap by Category & Product", height=450)
            st.plotly_chart(fig4, use_container_width=True)

        if show_rev and price_col:
            fig5 = px.scatter(df_f, x=price_col, y="total_sales",
                              size="total_revenue", color=cat_col if cat_col else None,
                              hover_name=name_col, color_discrete_sequence=PLOTLY_PALETTE,
                              labels={price_col:"Price","total_sales":"Total Units"})
            apply_layout(fig5, title="Price vs Sales (bubble = Revenue)", height=380)
            st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("No product name column detected. Add a product_name or name column for product-level charts.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3  CATEGORIES
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    if cat_col:
        cat_sum = (df_f.groupby(cat_col)["total_sales"].sum()
                   .reset_index().rename(columns={"total_sales":"total_sales"})
                   .sort_values("total_sales", ascending=False))

        c1, c2 = st.columns(2)
        with c1:
            fig = px.pie(cat_sum, values="total_sales", names=cat_col, hole=0.55,
                         color_discrete_sequence=PLOTLY_PALETTE)
            fig.update_traces(textposition="outside", textinfo="percent+label",
                              marker=dict(line=dict(color=COLORS["bg"], width=2)))
            apply_layout(fig, title="Sales Share by Category", height=380, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig2 = px.bar(cat_sum, x="total_sales", y=cat_col, orientation="h",
                          color=cat_col, color_discrete_sequence=PLOTLY_PALETTE, text="total_sales")
            fig2.update_traces(texttemplate="%{text:,}", textposition="outside")
            apply_layout(fig2, title="Units by Category", height=380, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

        cat_monthly = df_f.groupby(cat_col)[month_cols].sum()
        fig3 = go.Figure()
        for i, (cat, row) in enumerate(cat_monthly.iterrows()):
            fig3.add_trace(go.Bar(x=M_LABELS, y=row.values, name=cat,
                                  marker_color=PLOTLY_PALETTE[i % len(PLOTLY_PALETTE)]))
        fig3.update_layout(barmode="group")
        apply_layout(fig3, title="Monthly Sales by Category", height=380)
        st.plotly_chart(fig3, use_container_width=True)

        if len(cat_monthly) <= 12:
            fig4 = go.Figure()
            for i, (cat, row) in enumerate(cat_monthly.iterrows()):
                vals  = row.values.tolist()
                color = PLOTLY_PALETTE[i % len(PLOTLY_PALETTE)]
                fig4.add_trace(go.Scatterpolar(
                    r=vals + [vals[0]], theta=M_LABELS + [M_LABELS[0]],
                    name=cat, line_color=color, fill="toself", fillcolor=color + "18",
                ))
            apply_layout(fig4, title="Category Seasonal Radar", height=420,
                         polar=dict(bgcolor="rgba(0,0,0,0)",
                                    radialaxis=dict(gridcolor=COLORS["border"]),
                                    angularaxis=dict(gridcolor=COLORS["border"])))
            st.plotly_chart(fig4, use_container_width=True)

        if name_col:
            top40 = df_f.nlargest(40, "total_sales")
            fig5  = px.sunburst(top40, path=[cat_col, name_col], values="total_sales",
                                color="total_sales",
                                color_continuous_scale=[[0,COLORS["border"]],[1,COLORS["primary"]]])
            apply_layout(fig5, title="Sunburst - Category to Product", height=460)
            st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("No category column detected in your dataset.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4  DISTRIBUTION
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(df_f, x="total_sales", nbins=30,
                           color_discrete_sequence=[COLORS["primary"]])
        fig.update_traces(marker_line_color=COLORS["bg"], marker_line_width=1)
        apply_layout(fig, title="Distribution of Total Sales", height=320)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        if cat_col:
            fig2 = px.box(df_f, x=cat_col, y="total_sales", color=cat_col,
                          color_discrete_sequence=PLOTLY_PALETTE, points="outliers")
            apply_layout(fig2, title="Sales Distribution by Category", height=320, showlegend=False)
        else:
            fig2 = px.box(df_f, y="total_sales", color_discrete_sequence=[COLORS["purple"]])
            apply_layout(fig2, title="Sales Box Plot", height=320)
        st.plotly_chart(fig2, use_container_width=True)

    if cat_col:
        fig3 = px.violin(df_f, x=cat_col, y="total_sales", color=cat_col,
                         color_discrete_sequence=PLOTLY_PALETTE, box=True, points="outliers")
        apply_layout(fig3, title="Sales Violin by Category", height=360, showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

    monthly_stats = pd.DataFrame({
        "Month":  M_LABELS,
        "Mean":   [df_f[m].mean()   for m in month_cols],
        "Median": [df_f[m].median() for m in month_cols],
        "Std":    [df_f[m].std()    for m in month_cols],
    })
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(x=monthly_stats["Month"], y=monthly_stats["Mean"],
                          name="Mean", marker_color=COLORS["primary"]))
    fig4.add_trace(go.Scatter(x=monthly_stats["Month"], y=monthly_stats["Median"],
                              mode="lines+markers", name="Median",
                              line=dict(color=COLORS["accent"], width=2), marker=dict(size=7)))
    upper = monthly_stats["Mean"] + monthly_stats["Std"]
    lower = monthly_stats["Mean"] - monthly_stats["Std"]
    fig4.add_trace(go.Scatter(x=monthly_stats["Month"], y=upper,
                              fill=None, mode="lines", line_color="rgba(0,212,255,0)", showlegend=False))
    fig4.add_trace(go.Scatter(x=monthly_stats["Month"], y=lower,
                              fill="tonexty", mode="lines", fillcolor="rgba(0,212,255,0.1)",
                              line_color="rgba(0,212,255,0)", name="1 Std"))
    apply_layout(fig4, title="Monthly Mean / Median / Std", height=340)
    st.plotly_chart(fig4, use_container_width=True)

    if price_col:
        fig5 = px.histogram(df_f, x=price_col, nbins=25,
                            color_discrete_sequence=[COLORS["green"]])
        fig5.update_traces(marker_line_color=COLORS["bg"], marker_line_width=1)
        apply_layout(fig5, title="Price Distribution", height=300)
        st.plotly_chart(fig5, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5  HEATMAP
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    if name_col:
        heat_top  = df_f.nlargest(min(top_n, 25), "total_sales")
        heat_data = heat_top.set_index(name_col)[month_cols].copy()
        heat_data.columns = M_LABELS
        fig = px.imshow(heat_data,
                        color_continuous_scale=[[0,COLORS["bg"]],[0.4,COLORS["purple"]],[1,COLORS["primary"]]],
                        aspect="auto", labels=dict(color="Units"))
        fig.update_xaxes(side="top")
        apply_layout(fig, title=f"Monthly Sales Heatmap - Top {min(top_n,25)} Products", height=600)
        st.plotly_chart(fig, use_container_width=True)

    if cat_col:
        cat_heat = df_f.groupby(cat_col)[month_cols].sum().copy()
        cat_heat.columns = M_LABELS
        fig2 = px.imshow(cat_heat,
                         color_continuous_scale=[[0,COLORS["bg"]],[0.5,COLORS["green"]],[1,COLORS["accent"]]],
                         aspect="auto", labels=dict(color="Units"), text_auto=True)
        fig2.update_xaxes(side="top")
        apply_layout(fig2, title="Category x Month Heatmap", height=360)
        st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6  CORRELATION
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    num_cols = [c for c in df_f.select_dtypes(include=np.number).columns
                if c not in ["product_id"]]

    if len(num_cols) >= 2:
        corr = df_f[num_cols].corr()
        fig = px.imshow(corr,
                        color_continuous_scale=[[0,COLORS["secondary"]],[0.5,COLORS["bg"]],[1,COLORS["primary"]]],
                        zmin=-1, zmax=1, aspect="auto", text_auto=".2f")
        apply_layout(fig, title="Correlation Matrix", height=500)
        st.plotly_chart(fig, use_container_width=True)

    month_corr_vals = {M_LABELS[i]: df_f[m].corr(df_f["total_sales"]) for i, m in enumerate(month_cols)}
    month_corr  = pd.Series(month_corr_vals)
    bar_colors  = [COLORS["green"] if v >= 0 else COLORS["secondary"] for v in month_corr.values]
    fig2 = go.Figure(go.Bar(
        x=month_corr.index, y=month_corr.values, marker_color=bar_colors,
        text=[f"{v:.3f}" for v in month_corr.values], textposition="outside",
    ))
    apply_layout(fig2, title="Each Month Correlation with Annual Total", height=320)
    st.plotly_chart(fig2, use_container_width=True)

    if price_col and name_col:
        try:
            fig3 = px.scatter(df_f, x=price_col, y="total_sales",
                              color=cat_col if cat_col else None,
                              hover_name=name_col, trendline="ols",
                              color_discrete_sequence=PLOTLY_PALETTE,
                              labels={price_col:"Price","total_sales":"Annual Units"})
            apply_layout(fig3, title="Price vs Annual Sales (OLS trendline)", height=380)
            st.plotly_chart(fig3, use_container_width=True)
        except Exception:
            pass

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<center style='color:{COLORS['muted']};font-size:.8rem'>"
    "Sales Intelligence Dashboard &middot; Upload any CSV / Excel / JSON with monthly sales columns"
    "</center>",
    unsafe_allow_html=True,
)
