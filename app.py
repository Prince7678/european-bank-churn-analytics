import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="European Banking | Churn Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("European Banking Customer Segmentation & Churn Analytics")
st.caption("Explore churn patterns, customer segments, engagement, and financial profiles.")

REQUIRED = [
    "CustomerId", "CreditScore", "Geography", "Gender", "Age", "Tenure",
    "Balance", "NumOfProducts", "HasCrCard", "IsActiveMember",
    "EstimatedSalary", "Exited"
]

def load_data(uploaded_file):
    if uploaded_file is not None:
        return pd.read_excel(uploaded_file, sheet_name="European_Bank")
    candidates = [
        Path(__file__).with_name("European_Bank_Project_FINAL_fixed.xlsx"),
        Path(__file__).with_name("European_Bank Project 1 complete.xlsx"),
        Path(__file__).with_name("European_Bank Project complete.xlsx"),
    ]
    for path in candidates:
        if path.exists():
            return pd.read_excel(path, sheet_name="European_Bank")
    return None

uploaded = st.sidebar.file_uploader(
    "Upload the project Excel workbook",
    type=["xlsx"],
    help="Upload the corrected workbook. The app reads the original European_Bank sheet."
)

try:
    raw = load_data(uploaded)
except Exception as exc:
    st.error(f"Could not read the workbook: {exc}")
    st.stop()

if raw is None:
    st.info("Upload your European Bank Excel workbook using the sidebar to start.")
    st.stop()

missing_cols = [c for c in REQUIRED if c not in raw.columns]
if missing_cols:
    st.error("The European_Bank sheet is missing these columns: " + ", ".join(missing_cols))
    st.stop()

df = raw[REQUIRED].copy()
for col in ["CreditScore", "Age", "Tenure", "Balance", "NumOfProducts",
            "HasCrCard", "IsActiveMember", "EstimatedSalary", "Exited"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=REQUIRED)
df["Exited"] = df["Exited"].astype(int)
df["HasCrCard"] = df["HasCrCard"].astype(int)
df["IsActiveMember"] = df["IsActiveMember"].astype(int)
df["NumOfProducts"] = df["NumOfProducts"].astype(int)

# Segmentation rules used in the analysis workbook.
df["Age_Group"] = pd.cut(
    df["Age"], bins=[-float("inf"), 29, 45, 60, float("inf")],
    labels=["Under 30", "30-45", "46-60", "60+"]
)
df["CreditScore_Group"] = pd.cut(
    df["CreditScore"], bins=[-float("inf"), 579, 669, float("inf")],
    labels=["Low", "Medium", "High"]
)
df["Tenure_Group"] = pd.cut(
    df["Tenure"], bins=[-float("inf"), 2, 5, float("inf")],
    labels=["New", "Mid-term", "Long-term"]
)
df["Balance_Group"] = pd.cut(
    df["Balance"], bins=[-float("inf"), 0, 49999.999, float("inf")],
    labels=["Zero Balance", "Low Balance", "High Balance"]
)
df["Customer_Value_Group"] = pd.cut(
    df["Balance"], bins=[-float("inf"), 49999.999, 99999.999, float("inf")],
    labels=["Low Value", "Medium Value", "High Value"]
)
df["Salary_Group"] = pd.cut(
    df["EstimatedSalary"], bins=[-float("inf"), 50000, 100000, float("inf")],
    labels=["Low Salary", "Medium Salary", "High Salary"]
)
df["Activity_Group"] = df["IsActiveMember"].map({1: "Active", 0: "Inactive"})
df["Credit_Card_Group"] = df["HasCrCard"].map({1: "Has Card", 0: "No Card"})
df["Churn_Status"] = df["Exited"].map({1: "Churned", 0: "Retained"})

# Sidebar filters
st.sidebar.header("Filters")
geographies = sorted(df["Geography"].dropna().unique().tolist())
genders = sorted(df["Gender"].dropna().unique().tolist())
selected_geo = st.sidebar.multiselect("Geography", geographies, default=geographies)
selected_gender = st.sidebar.multiselect("Gender", genders, default=genders)
age_min, age_max = int(df["Age"].min()), int(df["Age"].max())
age_range = st.sidebar.slider("Age range", age_min, age_max, (age_min, age_max))
activity_options = ["Active", "Inactive"]
selected_activity = st.sidebar.multiselect("Membership activity", activity_options, default=activity_options)
churn_options = ["Retained", "Churned"]
selected_churn = st.sidebar.multiselect("Customer status", churn_options, default=churn_options)

filtered = df[
    df["Geography"].isin(selected_geo)
    & df["Gender"].isin(selected_gender)
    & df["Age"].between(age_range[0], age_range[1])
    & df["Activity_Group"].isin(selected_activity)
    & df["Churn_Status"].isin(selected_churn)
].copy()

if filtered.empty:
    st.warning("No customers match the selected filters. Change one or more filters.")
    st.stop()

total = len(filtered)
churned = int(filtered["Exited"].sum())
retained = total - churned
churn_rate = churned / total if total else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Customers", f"{total:,}")
k2.metric("Churned", f"{churned:,}")
k3.metric("Retained", f"{retained:,}")
k4.metric("Churn rate", f"{churn_rate:.2%}")

st.divider()

def grouped_churn(data, group_col, label):
    out = (
        data.groupby(group_col, observed=False)
        .agg(Total_Customers=("Exited", "size"), Churned_Customers=("Exited", "sum"))
        .reset_index()
    )
    out["Churn_Rate"] = out["Churned_Customers"] / out["Total_Customers"].where(out["Total_Customers"] != 0)
    out = out.dropna(subset=["Churn_Rate"])
    out = out.rename(columns={group_col: label})
    return out

tab1, tab2, tab3, tab4 = st.tabs([
    "Overview", "Customer Segments", "Financial Profile", "Data Explorer"
])

with tab1:
    left, right = st.columns(2)
    geo = grouped_churn(filtered, "Geography", "Geography")
    fig = px.bar(geo, x="Geography", y="Churn_Rate", text=geo["Churn_Rate"].map(lambda x: f"{x:.1%}"),
                 title="Churn Rate by Geography", labels={"Churn_Rate": "Churn rate"})
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    left.plotly_chart(fig, use_container_width=True)

    age = grouped_churn(filtered, "Age_Group", "Age Group")
    fig = px.bar(age, x="Age Group", y="Churn_Rate", text=age["Churn_Rate"].map(lambda x: f"{x:.1%}"),
                 title="Churn Rate by Age Group", labels={"Churn_Rate": "Churn rate"})
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    right.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    gender = grouped_churn(filtered, "Gender", "Gender")
    fig = px.bar(gender, x="Gender", y="Churn_Rate", text=gender["Churn_Rate"].map(lambda x: f"{x:.1%}"),
                 title="Churn Rate by Gender", labels={"Churn_Rate": "Churn rate"})
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    left.plotly_chart(fig, use_container_width=True)

    activity = grouped_churn(filtered, "Activity_Group", "Activity")
    fig = px.bar(activity, x="Activity", y="Churn_Rate", text=activity["Churn_Rate"].map(lambda x: f"{x:.1%}"),
                 title="Churn Rate by Membership Activity", labels={"Churn_Rate": "Churn rate"})
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    right.plotly_chart(fig, use_container_width=True)

with tab2:
    left, right = st.columns(2)
    for col, title, slot in [
        ("CreditScore_Group", "Churn Rate by Credit Score Group", left),
        ("Tenure_Group", "Churn Rate by Tenure Group", right),
    ]:
        temp = grouped_churn(filtered, col, col.replace("_", " "))
        xcol = col.replace("_", " ")
        fig = px.bar(temp, x=xcol, y="Churn_Rate",
                     text=temp["Churn_Rate"].map(lambda x: f"{x:.1%}"),
                     title=title, labels={"Churn_Rate": "Churn rate"})
        fig.update_yaxes(tickformat=".0%", rangemode="tozero")
        slot.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    for col, title, slot in [
        ("NumOfProducts", "Churn Rate by Number of Products", left),
        ("Credit_Card_Group", "Churn Rate by Credit Card", right),
    ]:
        temp = grouped_churn(filtered, col, col.replace("_", " "))
        xcol = col.replace("_", " ")
        fig = px.bar(temp, x=xcol, y="Churn_Rate",
                     text=temp["Churn_Rate"].map(lambda x: f"{x:.1%}"),
                     title=title, labels={"Churn_Rate": "Churn rate"})
        fig.update_yaxes(tickformat=".0%", rangemode="tozero")
        slot.plotly_chart(fig, use_container_width=True)

    value = grouped_churn(filtered, "Customer_Value_Group", "Customer Value Group")
    fig = px.bar(value, x="Customer Value Group", y="Churn_Rate",
                 text=value["Churn_Rate"].map(lambda x: f"{x:.1%}"),
                 title="Churn Rate by Customer Value Group",
                 labels={"Churn_Rate": "Churn rate"})
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    left, right = st.columns(2)
    balance = grouped_churn(filtered, "Balance_Group", "Balance Group")
    fig = px.bar(balance, x="Balance Group", y="Churn_Rate",
                 text=balance["Churn_Rate"].map(lambda x: f"{x:.1%}"),
                 title="Churn Rate by Balance Group",
                 labels={"Churn_Rate": "Churn rate"})
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    left.plotly_chart(fig, use_container_width=True)

    salary = grouped_churn(filtered, "Salary_Group", "Salary Group")
    fig = px.bar(salary, x="Salary Group", y="Churn_Rate",
                 text=salary["Churn_Rate"].map(lambda x: f"{x:.1%}"),
                 title="Churn Rate by Salary Group",
                 labels={"Churn_Rate": "Churn rate"})
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    right.plotly_chart(fig, use_container_width=True)

    risk = filtered.copy()
    risk["Risk_Segment"] = "Low/Medium Value + Active"
    risk.loc[(risk["Customer_Value_Group"] == "High Value") & (risk["IsActiveMember"] == 0), "Risk_Segment"] = "High Value + Inactive"
    risk.loc[(risk["Customer_Value_Group"] == "High Value") & (risk["IsActiveMember"] == 1), "Risk_Segment"] = "High Value + Active"
    risk.loc[(risk["Customer_Value_Group"] != "High Value") & (risk["IsActiveMember"] == 0), "Risk_Segment"] = "Low/Medium Value + Inactive"
    risk_table = grouped_churn(risk, "Risk_Segment", "Risk Segment")
    fig = px.bar(risk_table, x="Risk Segment", y="Churn_Rate",
                 text=risk_table["Churn_Rate"].map(lambda x: f"{x:.1%}"),
                 title="Churn Rate by Risk Segment",
                 labels={"Churn_Rate": "Churn rate"})
    fig.update_xaxes(tickangle=-15)
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Summary statistics")
    summary = pd.DataFrame({
        "Metric": ["Average age", "Average credit score", "Average balance", "Average estimated salary"],
        "Value": [
            filtered["Age"].mean(),
            filtered["CreditScore"].mean(),
            filtered["Balance"].mean(),
            filtered["EstimatedSalary"].mean(),
        ],
    })
    st.dataframe(summary, hide_index=True, use_container_width=True)

with tab4:
    st.write("Filtered customer records")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered data as CSV", data=csv, file_name="filtered_customer_churn.csv", mime="text/csv")

st.caption("Interpretation note: observed associations in this dataset do not prove causation. Use churn patterns to prioritize further investigation, not to assume a single factor causes churn.")
