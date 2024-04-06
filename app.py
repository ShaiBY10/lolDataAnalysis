from plot import *
from sql import getSummonerNameFromDB, getLastNMatchIDSOfSummonerFromDB, getGameStartTimestampAndSummonerChampionName
from utils import myLogger

st.set_page_config(page_title="My Dashboard", layout="wide")

summonerNameList = getSummonerNameFromDB()


@st.cache_data
@myLogger
def generateMatchLabels(match_ids, summoner_name):
    """
    Function that generates labels for matches based on match IDs and summoner name.

    Parameters:
    - match_ids: list of match IDs to generate labels for
    - summoner_name: name of the summoner

    Returns:
    - labels: list of labels generated for each match
    """

    labels = []
    for match_id in match_ids:
        matchID, startDate, championPlayed = getGameStartTimestampAndSummonerChampionName(match_id, summoner_name)
        label = f"{matchID} - {startDate} - {championPlayed}"  # Adjusted format for clarity
        labels.append(label)
    return labels


st.title("LoL Matches & Summoners Analysis")

with st.sidebar:
    st.header("Navigation")
    page_selection = st.radio("Go to", ["Home", "Matches", "Summoners"])

if page_selection == "Home":
    st.header("Home")
    st.write("Here ")
    # Instructions for the user
    num_summoners = len(summonerNameList)
    columns = st.columns(num_summoners)

    # Placeholder for the heatmap
    heatmapPlaceholder = st.empty()
    # Placeholder for the scatter plot
    scatterPlotPlaceholder = st.empty()

    for index, summonerName in enumerate(summonerNameList):
        with columns[index]:
            st.subheader(summonerName)

            # Fetch match IDs and information
            summonerLast50MatchIDS = getLastNMatchIDSOfSummonerFromDB(summonerName, 50)
            gamesInfo = [getGameStartTimestampAndSummonerChampionName(matchID, summonerName) for matchID in
                         summonerLast50MatchIDS]

            # Generate labels for the select box, including a default prompt
            default_selection = ["Choose from the summoner's most recent 50 games:"]
            selectBoxLabeledMatches = default_selection + generateMatchLabels(
                getLastNMatchIDSOfSummonerFromDB(summonerName, 50), summonerName)

            # Capture the selected option
            selectboxSelection = st.selectbox('Summoner Matches', selectBoxLabeledMatches,
                                              key=f'selectbox_{summonerName}', index=0)

            # Check if the selection is not the default prompt
            if selectboxSelection != default_selection[0]:
                selected_match_id = selectboxSelection.split(' - ')[0]  # Assuming matchID is at the start
                selected_game_info = next((game for game in gamesInfo if game[0] == selected_match_id), None)

                if selected_game_info:
                    # Display the heatmap for the selected match
                    heatmapPlaceholder.empty()
                    with heatmapPlaceholder.container():
                        plotCorrelationHeatmap(matchID=selected_match_id,
                                               title=f'Correlation Heatmap For {selected_game_info}')  # This does the job, but let's be honest, it can show not like a list.

            # Button interactions (remain unchanged)
            st.write('Last 3 Matches:')
            for i, game in enumerate(gamesInfo[:3]):
                if st.button(f'{game[1]} || {game[2]}', key=f'{summonerName}Match_{i}', help=game[0]):
                    heatmapPlaceholder.empty()
                    with heatmapPlaceholder.container():
                        plotCorrelationHeatmap(matchID=game[0], title=f'Correlation Heatmap For {gamesInfo[i]}')
                        # #ToDo: Polish it up when there's nothing better to do
