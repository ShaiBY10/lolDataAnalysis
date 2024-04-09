import streamlit as st

# Custom CSS to inject for styling specific elements
st.markdown("""
<style>
.stTextInput>div>div>input {
    color: #f63366;
}
.st-btn {
    border: 2px solid #f63366;
    border-radius: 20px;
}
.stAlert {
    background-color: #262730;
}
</style>
""", unsafe_allow_html=True)

# Custom Pastel Color Palette for the Pie Chart

# Example data for the Champion Pool Diversity chart

# Main dashboard layout


if summoner_name:
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Rank", "Gold III")
    col2.metric("Win/Loss Ratio", "7/3")
    col3.metric("Total Hours Played", 15)

    col4, col5, col6 = st.columns(3)
    col4.metric("Games Played", 10)
    col5.metric("Champion Pool Diversity", 5)
    col6.metric("Favorite Champion", "Yasuo")

    st.subheader("Best Game This Week")
    st.info("8/2/6 KDA on Yasuo")

    st.subheader("LP Status This Week")
    st.success("+75 LP")

    # Plotly pie chart for Champion Pool Diversity
    fig = px.pie(df, names='Champion', values='Play Percentage', title='Champion Play Percentage',
                 color_discrete_sequence=pastel_palette)
    st.plotly_chart(fig)
