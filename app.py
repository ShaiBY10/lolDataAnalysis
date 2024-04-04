import streamlit as st

from analysis import createMatchAnalysis
from plot import *
from sql import getSummonerNameFromDB

# scatter = plot_scatter(df, 'assists', 'wards_placed')


# Set the page configuration for the title and layout
st.set_page_config(page_title="My Dashboard", layout="wide")
summonerNameList = getSummonerNameFromDB()


# Main title of your dashboard
st.title("LoL Matches & Summoners Analysis")

# Sidebar for navigation or taking inputs
with st.sidebar:
    st.header("Navigation")
    page_selection = st.radio("Go to", ["Home", "Matches", "Summoners"])



# Home
if page_selection == "Home":
    st.header("Home")
    st.write("You can enter matchID in the box below to view correlation matrix of your match")
    import streamlit as st

    # Using columns to control button width
    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        st.subheader(summonerNameList[0])
        if st.button('Button with '):
            st.success('Button clicked!') # Empty space, can be used for better alignment

    with col2:
        st.subheader(summonerNameList[1])
        if st.button('Button with Controlled Width'):
            st.success('Button clicked!')

    with col3:
        st.subheader(summonerNameList[2])
        if st.button('Button  Width'):
            st.success('Button clicked!')  # Empty space, can be used for better alignment

    matchIDFromUser = st.text_input("Enter Match ID")
    if matchIDFromUser:
        df = createMatchAnalysis(matchIDFromUser)
        correlationTable, correlationMatrix = plotCorrelationHeatmap(df)
        st.plotly_chart(correlationTable)
        col1,colMid,col2 = st.columns([3,0.2,3])
        st.write('Now you can analyze the correlation matrix of your match by selecting 2 features to scatter plot')
        with col1:
            feature_1 = st.selectbox('Select the first feature:', df.columns)

        with colMid:
            for _ in range(2):
                st.write("")
            st.write("VS", style="text-align: center;")

        with col2:
            feature_2 = st.selectbox('Select the second feature:', df.columns, index=1)

        if feature_1 and feature_2 and feature_1 != feature_2:
            st.plotly_chart(plotScatter(df, feature_1, feature_2))
        else:
            st.error('Please select two different features.')




# Page 2

elif page_selection == "Matches":
    st.header("Matches")
    st.write("This is the second page.")

    # Placeholder for your content


# Page 3

elif page_selection == "Summoners":
    st.header("Summoners")
    st.write("You're on the third page.")
    # Placeholder for more content
    st.write("This could be a summary page, or more detailed analysis.")

