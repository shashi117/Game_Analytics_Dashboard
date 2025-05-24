import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt

# ✅ Page Configuration
st.set_page_config(
    page_title="🎮 Game Analytics Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
    
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .insight-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .warning-box {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: #8B4513;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .stSelectbox > div > div {
        background-color: #f8f9fa;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Load dataset with caching
@st.cache_data
def load_data():
    try:
        # Update this path to your CSV file
        df = pd.read_csv(r"D:\Assignment\Matiks - Data Analyst Data - Sheet1.csv")
        
        # Data preprocessing
        df["Signup_Date"] = pd.to_datetime(df["Signup_Date"], errors='coerce')
        df["Last_Login"] = pd.to_datetime(df["Last_Login"], errors='coerce')
        
        # Calculate additional metrics
        today = pd.Timestamp.today()
        df["days_since_login"] = (today - df["Last_Login"]).dt.days
        df["days_since_signup"] = (today - df["Signup_Date"]).dt.days
        df["revenue_per_session"] = df["Total_Revenue_USD"] / df["Total_Play_Sessions"].replace(0, 1)
        
        # User segments based on activity
        df["user_segment"] = pd.cut(df["days_since_login"], 
                                   bins=[-1, 1, 7, 30, float('inf')], 
                                   labels=['Daily Active', 'Weekly Active', 'Monthly Active', 'Inactive'])
        
        # Revenue segments
        df["revenue_segment"] = pd.cut(df["Total_Revenue_USD"], 
                                      bins=[0, 10, 50, 200, float('inf')], 
                                      labels=['Low Spender', 'Medium Spender', 'High Spender', 'Whale'])
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Load data
df = load_data()

if df.empty:
    st.error("Please ensure your CSV file is accessible and contains the required columns.")
    st.stop()

# Main Header
st.markdown('<h1 class="main-header">🎮 Game Analytics Dashboard</h1>', unsafe_allow_html=True)

# Sidebar for filters
st.sidebar.markdown("## 🔍 Filters")
selected_games = st.sidebar.multiselect(
    "Select Games", 
    options=df["Game_Title"].unique(), 
    default=df["Game_Title"].unique()
)

selected_devices = st.sidebar.multiselect(
    "Select Device Types", 
    options=df["Device_Type"].unique(), 
    default=df["Device_Type"].unique()
)

date_range = st.sidebar.date_input(
    "Signup Date Range",
    value=(df["Signup_Date"].min(), df["Signup_Date"].max()),
    min_value=df["Signup_Date"].min(),
    max_value=df["Signup_Date"].max()
)

# Filter data
filtered_df = df[
    (df["Game_Title"].isin(selected_games)) & 
    (df["Device_Type"].isin(selected_devices)) &
    (df["Signup_Date"] >= pd.Timestamp(date_range[0])) &
    (df["Signup_Date"] <= pd.Timestamp(date_range[1]))
]

# Key Metrics Section
st.markdown("## 📊 Key Performance Metrics")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    dau = len(filtered_df[filtered_df["user_segment"] == "Daily Active"])
    st.metric("📱 Daily Active Users", dau, delta=f"{(dau/len(filtered_df)*100):.1f}%")

with col2:
    wau = len(filtered_df[filtered_df["user_segment"].isin(["Daily Active", "Weekly Active"])])
    st.metric("📅 Weekly Active Users", wau, delta=f"{(wau/len(filtered_df)*100):.1f}%")

with col3:
    mau = len(filtered_df[filtered_df["user_segment"] != "Inactive"])
    st.metric("📈 Monthly Active Users", mau, delta=f"{(mau/len(filtered_df)*100):.1f}%")

with col4:
    total_revenue = filtered_df['Total_Revenue_USD'].sum()
    avg_revenue = filtered_df['Total_Revenue_USD'].mean()
    st.metric("💰 Total Revenue", f"${total_revenue:,.0f}", delta=f"Avg: ${avg_revenue:.2f}")

with col5:
    retention_rate = (len(filtered_df[filtered_df["user_segment"] != "Inactive"]) / len(filtered_df) * 100)
    st.metric("🔄 Retention Rate", f"{retention_rate:.1f}%")

# Revenue Analysis Section
st.markdown("## 💰 Revenue Analysis")

col1, col2 = st.columns(2)

with col1:
    # Revenue by Game
    revenue_by_game = filtered_df.groupby("Game_Title")["Total_Revenue_USD"].sum().reset_index()
    fig1 = px.pie(revenue_by_game, names='Game_Title', values='Total_Revenue_USD', 
                  title='💎 Revenue Distribution by Game',
                  color_discrete_sequence=px.colors.qualitative.Set3)
    fig1.update_layout(showlegend=True, height=400)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    # Revenue over time
    filtered_df['signup_month'] = filtered_df['Signup_Date'].dt.to_period('M').astype(str)
    monthly_revenue = filtered_df.groupby('signup_month')['Total_Revenue_USD'].sum().reset_index()
    fig2 = px.line(monthly_revenue, x='signup_month', y='Total_Revenue_USD',
                   title='📈 Revenue Trend Over Time',
                   markers=True)
    fig2.update_layout(height=400)
    fig2.update_traces(line_color='#667eea', line_width=3)
    st.plotly_chart(fig2, use_container_width=True)

# User Behavior Analysis
st.markdown("## 👥 User Behavior Analysis")

col1, col2, col3 = st.columns(3)

with col1:
    # Device Analysis
    device_revenue = filtered_df.groupby("Device_Type").agg({
        'Total_Revenue_USD': 'mean',
        'Total_Play_Sessions': 'mean'
    }).round(2)
    
    fig3 = px.bar(device_revenue.reset_index(), x="Device_Type", y="Total_Revenue_USD",
                  title="📱 Avg Revenue by Device",
                  color="Total_Revenue_USD",
                  color_continuous_scale="viridis")
    fig3.update_layout(height=350)
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    # Game Mode Analysis
    mode_stats = filtered_df.groupby("Preferred_Game_Mode").agg({
        'Total_Revenue_USD': 'mean',
        'Total_Play_Sessions': 'mean'
    }).round(2)
    
    fig4 = px.bar(mode_stats.reset_index(), x="Preferred_Game_Mode", y="Total_Revenue_USD",
                  title="🎯 Avg Revenue by Game Mode",
                  color="Total_Revenue_USD",
                  color_continuous_scale="plasma")
    fig4.update_layout(height=350)
    st.plotly_chart(fig4, use_container_width=True)

with col3:
    # User Segments
    segment_counts = filtered_df["user_segment"].value_counts()
    fig5 = px.pie(values=segment_counts.values, names=segment_counts.index,
                  title="👤 User Activity Segments",
                  color_discrete_sequence=px.colors.qualitative.Pastel)
    fig5.update_layout(height=350)
    st.plotly_chart(fig5, use_container_width=True)

# Advanced Analytics
st.markdown("## 🔬 Advanced Analytics")

col1, col2 = st.columns(2)

with col1:
    # Revenue vs Sessions Scatter
    fig6 = px.scatter(filtered_df, x="Total_Play_Sessions", y="Total_Revenue_USD",
                      color="Device_Type", size="days_since_signup",
                      title="💫 Revenue vs Play Sessions",
                      hover_data=["Username", "Game_Title"])
    fig6.update_layout(height=400)
    st.plotly_chart(fig6, use_container_width=True)

with col2:
    # Subscription Tier Analysis
    subscription_stats = filtered_df.groupby("Subscription_Tier").agg({
        'Total_Revenue_USD': ['mean', 'count'],
        'Total_Play_Sessions': 'mean'
    }).round(2)
    
    subscription_stats.columns = ['Avg_Revenue', 'User_Count', 'Avg_Sessions']
    subscription_stats = subscription_stats.reset_index()
    
    fig7 = px.bar(subscription_stats, x="Subscription_Tier", y="Avg_Revenue",
                  title="💳 Revenue by Subscription Tier",
                  color="User_Count",
                  color_continuous_scale="blues")
    fig7.update_layout(height=400)
    st.plotly_chart(fig7, use_container_width=True)

# High-Value Users Analysis
st.markdown("## 👑 High-Value Users")

col1, col2 = st.columns([2, 1])

with col1:
    top_users = filtered_df.nlargest(15, "Total_Revenue_USD")[
        ["Username", "Total_Revenue_USD", "Game_Title", "Device_Type", 
         "Total_Play_Sessions", "Subscription_Tier", "user_segment"]
    ].round(2)
    
    st.dataframe(
        top_users,
        use_container_width=True,
        hide_index=True
    )

with col2:
    # High-value user characteristics
    high_value_users = filtered_df[filtered_df["Total_Revenue_USD"] > filtered_df["Total_Revenue_USD"].quantile(0.9)]
    
    st.markdown("### 🏆 High-Value User Insights")
    st.metric("Count", len(high_value_users))
    st.metric("Avg Revenue", f"${high_value_users['Total_Revenue_USD'].mean():.2f}")
    st.metric("Avg Sessions", f"{high_value_users['Total_Play_Sessions'].mean():.1f}")
    
    # Most common characteristics
    st.markdown("**Most Common:**")
    st.write(f"🎮 Game: {high_value_users['Game_Title'].mode().iloc[0] if not high_value_users['Game_Title'].mode().empty else 'N/A'}")
    st.write(f"📱 Device: {high_value_users['Device_Type'].mode().iloc[0] if not high_value_users['Device_Type'].mode().empty else 'N/A'}")
    st.write(f"🎯 Mode: {high_value_users['Preferred_Game_Mode'].mode().iloc[0] if not high_value_users['Preferred_Game_Mode'].mode().empty else 'N/A'}")

# Churn Risk Analysis
st.markdown("## ⚠️ Churn Risk Analysis")

churn_risk = filtered_df[filtered_df["days_since_login"] > 30].sort_values(
    by="Total_Revenue_USD", ascending=False
)

col1, col2 = st.columns([2, 1])

with col1:
    if len(churn_risk) > 0:
        st.dataframe(
            churn_risk[["Username", "days_since_login", "Total_Revenue_USD", 
                       "Total_Play_Sessions", "Subscription_Tier", "Game_Title"]].head(10),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("🎉 No users at high churn risk!")

with col2:
    st.markdown('<div class="warning-box">', unsafe_allow_html=True)
    st.markdown("### 🚨 Churn Alerts")
    st.metric("At Risk Users", len(churn_risk))
    if len(churn_risk) > 0:
        st.metric("Revenue at Risk", f"${churn_risk['Total_Revenue_USD'].sum():,.2f}")
        st.metric("Avg Days Inactive", f"{churn_risk['days_since_login'].mean():.0f}")
    st.markdown('</div>', unsafe_allow_html=True)

# Cohort Analysis
st.markdown("## 🧪 Cohort Analysis")

with st.expander("📈 View Detailed Cohort Analysis", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        # Monthly signups
        filtered_df['cohort_month'] = filtered_df['Signup_Date'].dt.to_period('M').astype(str)
        cohort_data = filtered_df.groupby('cohort_month').agg({
            'User_ID': 'nunique',
            'Total_Revenue_USD': 'sum'
        }).reset_index()
        
        fig8 = px.line(cohort_data, x='cohort_month', y='User_ID',
                       title='👥 New User Signups by Month',
                       markers=True)
        fig8.update_traces(line_color='#f093fb', line_width=3)
        st.plotly_chart(fig8, use_container_width=True)
    
    with col2:
        # Revenue by cohort
        fig9 = px.bar(cohort_data, x='cohort_month', y='Total_Revenue_USD',
                      title='💰 Revenue by Signup Cohort',
                      color='Total_Revenue_USD',
                      color_continuous_scale='viridis')
        st.plotly_chart(fig9, use_container_width=True)

# Key Insights Section
st.markdown("## 🎯 Key Insights & Recommendations")

insights_col1, insights_col2 = st.columns(2)

with insights_col1:
    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("### 🔍 Key Findings")
    
    # Calculate insights
    total_users = len(filtered_df)
    active_users = len(filtered_df[filtered_df["user_segment"] != "Inactive"])
    high_revenue_users = len(filtered_df[filtered_df["Total_Revenue_USD"] > 100])
    
    st.markdown(f"""
    - **User Retention**: {(active_users/total_users*100):.1f}% of users are still active
    - **Revenue Concentration**: {(high_revenue_users/total_users*100):.1f}% of users generate premium revenue
    - **Top Game**: {filtered_df.groupby('Game_Title')['Total_Revenue_USD'].sum().idxmax()} drives most revenue
    - **Best Device**: {filtered_df.groupby('Device_Type')['Total_Revenue_USD'].mean().idxmax()} users spend more on average
    """)
    st.markdown('</div>', unsafe_allow_html=True)

with insights_col2:
    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("### 💡 Recommendations")
    st.markdown("""
    - **Focus on Retention**: Implement re-engagement campaigns for users inactive >14 days
    - **Device Optimization**: Enhance experience on highest-revenue device platforms
    - **Subscription Upsell**: Target medium spenders for premium tier upgrades
    - **Game Balancing**: Analyze why certain games generate more revenue
    - **Churn Prevention**: Set up automated alerts for high-value users showing early churn signals
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #667eea; font-weight: bold; padding: 2rem;'>
    🎮 Game Analytics Dashboard | Created with ❤️ using Streamlit | Data-Driven Gaming Success ✨
    </div>
    """, 
    unsafe_allow_html=True
)

# Performance metrics in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 Dashboard Stats")
st.sidebar.metric("Total Users Analyzed", len(filtered_df))
st.sidebar.metric("Data Points", len(filtered_df) * len(filtered_df.columns))
st.sidebar.metric("Games Covered", filtered_df["Game_Title"].nunique())
st.sidebar.metric("Device Types", filtered_df["Device_Type"].nunique())