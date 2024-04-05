from plot import *
from sql import getSummonerNameFromDB, getLastNMatchIDSOfSummonerFromDB, getGameStartTimestampAndSummonerChampionName

st.set_page_config(page_title="My Dashboard", layout="wide")

summonerNameList = getSummonerNameFromDB()


@st.cache_data
def generateMatchLabels(match_ids, summoner_name):
    labels = []
    for match_id in match_ids:
        matchID, startDate, championPlayed = getGameStartTimestampAndSummonerChampionName(match_id, summoner_name)
        label = f"{startDate} || {championPlayed} || {matchID}"
        labels.append(label)
    return labels


# Set the page configuration for the title and layout

# Main title of your dashboard
st.title("LoL Matches & Summoners Analysis")

# Sidebar for navigation or taking inputs
with st.sidebar:
    st.header("Navigation")
    page_selection = st.radio("Go to", ["Home", "Matches", "Summoners"])

# Home
if page_selection == "Home":
    st.header("Home")
    st.write("Enter a match ID in the field below to view the correlation matrix for the selected match.")
    st.write(
        "Additionally, you have the option to select a Summoner's Match ID from the dropdown menu provided for each summoner. ")
    st.write(
        "There is also a feature that allows you to view the last 3 matches for each summoner by clicking the "
        "corresponding button.")
    num_summoners = len(summonerNameList)
    columns = st.columns(num_summoners)

    for index, summonerName in enumerate(summonerNameList):
        with columns[index]:
            summonerLast3MatchIDS = getLastNMatchIDSOfSummonerFromDB(summonerName, 3)
            gamesInfo = [getGameStartTimestampAndSummonerChampionName(matchID, summonerName) for matchID in
                         summonerLast3MatchIDS]

            st.write('')  # Space
            st.subheader(summonerName)

            selectBoxLabeledMatches = generateMatchLabels(getLastNMatchIDSOfSummonerFromDB(summonerName, 50),
                                                          summonerName)
            st.selectbox('Summoner Matches', selectBoxLabeledMatches, key=f'selectbox_{summonerName}')

            st.write('Last 3 Matches:')
            for i, game in enumerate(gamesInfo):
                if st.button(f'{game[1]} || {game[2]}', key=f'{summonerName}Match_{i}', help=game[0]):
                    plotCorrelationHeatmap(game[0])







# Page 2

elif page_selection == "Matches":
    st.header("Matches")
    st.write("This is the second page.")
    col1, col2 = st.columns(2)

    with col1:
        st.write("Content in column 1")

    # Adding a vertical line between columns

    with col2:
        st.write("Content in column 2")

# Page 3

elif page_selection == "Summoners":
    st.write("Enter a match ID in the field below to view the correlation matrix for the selected match.")
    st.write(
        "Additionally, you have the option to select a Summoner's Match ID from the dropdown menu provided for each summoner. ")
    st.write(
        "There is also a feature that allows you to view the last 3 matches for each summoner by clicking the "
        "corresponding button.")

    num_summoners = len(summonerNameList)
    columns = st.columns(num_summoners)

    # Define a placeholder for the heatmap at the desired location (after the columns)
    heatmap_placeholder = st.empty()

    for index, summonerName in enumerate(summonerNameList):
        with columns[index]:
            summonerLast3MatchIDS = getLastNMatchIDSOfSummonerFromDB(summonerName, 3)
            gamesInfo = [getGameStartTimestampAndSummonerChampionName(matchID, summonerName) for matchID in
                         summonerLast3MatchIDS]

            st.write('')  # Space
            st.subheader(summonerName)

            selectBoxLabeledMatches = generateMatchLabels(getLastNMatchIDSOfSummonerFromDB(summonerName, 50),
                                                          summonerName)
            selected_match = st.selectbox('Summoner Matches', selectBoxLabeledMatches, key=f'selectbox_{summonerName}')

            st.write('Last 3 Matches:')
            for i, game in enumerate(gamesInfo):
                if st.button(f'{game[1]} || {game[2]}', key=f'{summonerName}Match_{i}', help=game[0]):
                    # Clear the existing content of the placeholder and display the new heatmap in the placeholder.
                    heatmap_placeholder.empty()  # Clear any previous content
                    with heatmap_placeholder.container():  # Use the container to add content to the placeholder
                        plotCorrelationHeatmap(game[0])  # Di

