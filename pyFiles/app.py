import plotly.graph_objects as go

#
from data import *
from plot import plotCorrelationHeatmap


def main():
    st.title("Your Rift, WEEKLY")
    st.image(r'../logo/logo.png', width=700)

    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        pageSelection = st.radio("Go to", ["Home", "Page 1", "Page 2"])

    # Page content
    if pageSelection == "Home":
        displayHome()
    elif pageSelection == "Page 1":
        displayPage1()
    elif pageSelection == "Page 2":
        displayPage2()


def displaySummonerNameHeader(summoner_name):
    """
  Generates a well-designed and modern header with "Summoner Analysis FOR summoner name".

  Args:
      summoner_name (str): The summoner name entered by the user.
  """
    st.markdown(f"""
    <style>
    body {{
      background-color: #212529;  /* Dark background */
      color: #fff;                /* White text */
    }}

    .header {{
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 1rem 2rem;
      background-color: #1a1a1a;  /* Slightly darker background for header */
      border-radius: 10px;         /* Rounded corners */
      font-family: 'Ubuntu Mono', monospace;  /* Web-safe font similar to Operator Mono */
    }}

    .header h1 {{
      margin: 0;
      font-size: 2rem;             /* Adjust font size as needed */
      font-family: 'Harlow Solid', regular;  /* Web-safe font similar to Operator Mono */

    }}
  </style>

  <div class="header">
    <h1>Summoner Analysis for {summoner_name}</h1>
  </div> """, unsafe_allow_html=True)


def createChampionDiversityPieChart(championPool):
    """
    Creates a Plotly pie chart to visualize the champion pool diversity.

    Parameters:
    champion_plays (dict): A dictionary where the keys are champion names and the values are the number of times each champion was played.

    Returns:
    fig: A Plotly figure object.
    """
    # Sort the dictionary by the number of plays in descending order
    sortedChampionPlays = sorted(championPool.items(), key=lambda x: x[1], reverse=True)

    # Extract the champion names and play counts
    champions = [champion for champion, plays in sortedChampionPlays]
    playCounts = [plays for champion, plays in sortedChampionPlays]

    # Create new labels that include the champion names and the number of games played
    labels = [f'{champion} ({plays})' for champion, plays in sortedChampionPlays]

    # Create the Plotly pie chart
    fig = go.Figure(data=[go.Pie(labels=labels, values=playCounts, text=champions, textposition='inside')])
    fig.update_layout(
        title="Champion Pool Diversity",
        font_size=16,
        height=600
    )

    return fig


def displayHome():
    summonerNames = getSummonerNamesFromDB(lower=True)
    userSummonerName = st.text_input("Enter Your Summoner Name:")
    if userSummonerName:
        if userSummonerName.lower() in summonerNames:
            summonerMatches = getPreviousMonthMatchIDSFromDB(userSummonerName)
            victories, defeats = getSummonerWinLossRatioFromDB(userSummonerName, matchesList=summonerMatches)
            hoursPlayed, minutesPlayed, weeklyGames = getSummonerHoursAndGamesFromDB(userSummonerName,
                                                                                     matchesList=summonerMatches)
            favoriteChampion, favoriteTimes, championPoolDiversity = getChampionPoolDiversityAndFavoriteChampionFromDB(
                userSummonerName, matchesList=summonerMatches)
            bestGame, bestChampion, bestKills, bestDeaths, bestAssists = getBestGameFromDB(userSummonerName,
                                                                                           matchesList=summonerMatches)
            displaySummonerNameHeader(userSummonerName)
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Rank", getSummonerRankFromDB(userSummonerName))
            col2.metric("Win/Loss Ratio", f"{victories}/{defeats}", delta=victories - defeats)
            col3.metric("Total Hours Played", f'{hoursPlayed}h {minutesPlayed}m')
            col4, col5, col6 = st.columns(3)
            col4.metric("Games Played", weeklyGames)
            col5.metric("Champion Pool Diversity", len(championPoolDiversity))
            col6.metric("Favorite Champion", f'{favoriteChampion} ({favoriteTimes})', help="Times Played")

            st.subheader("Best Game This Week")
            st.info(f'{bestKills}/{bestDeaths}/{bestAssists} KDA on {bestChampion}')

            # Plotly pie chart for Champion Pool Diversity
            fig = createChampionDiversityPieChart(championPoolDiversity)
            st.plotly_chart(fig,theme='streamlit')
        else:
            st.error(
                f"Error: Could not find summoner '{userSummonerName}' in the system. Please verify the summoner name and try again.")


def displayPage1():
    st.header("Home")
    summonerNameList = getSummonerNamesFromDB()
    numSummoners = len(summonerNameList)
    columns = st.columns(numSummoners)

    heatmapPlaceholder = st.empty()

    for index, summonerName in enumerate(summonerNameList):
        with columns[index]:
            displaySummoner(summonerName, heatmapPlaceholder)


@st.cache_data
@myLogger
def generateMatchLabels(matchIds, summonerName):
    labels = []
    for matchId in matchIds:
        matchId, startDate, championPlayed = getGameStartTimestampAndSummonerChampionName(matchId, summonerName)
        label = f"{matchId} - {startDate} - {championPlayed}"
        labels.append(label)
    return labels


def displaySummoner(summonerName, heatmapPlaceholder):
    st.subheader(summonerName)

    summonerLast50MatchIds = getLastNMatchIDSOfSummonerFromDB(summonerName, 50)
    gamesInfo = [getGameStartTimestampAndSummonerChampionName(matchId, summonerName) for matchId in
                 summonerLast50MatchIds]

    defaultSelection = ["Choose from the summoner's most recent 50 games:"]
    selectBoxLabeledMatches = defaultSelection + generateMatchLabels(summonerLast50MatchIds, summonerName)

    selectboxSelection = st.selectbox('Summoner Matches', selectBoxLabeledMatches, key=f'selectbox_{summonerName}',
                                      index=0)

    if selectboxSelection != defaultSelection[0]:
        selectedMatchId = selectboxSelection.split(' - ')[0]
        selectedGameInfo = next((game for game in gamesInfo if game[0] == selectedMatchId), None)

        if selectedGameInfo:
            col1,col2 = st.columns([10,1])
            with col1:
                heatmapPlaceholder.empty()
            with heatmapPlaceholder.container():
                plotCorrelationHeatmap(matchID=selectedMatchId, title=f'Correlation Heatmap For {selectedGameInfo}')

    st.write('Last 3 Matches:')
    for i, game in enumerate(gamesInfo[:3]):
        if st.button(f'{game[1]} || {game[2]}', key=f'{summonerName}Match_{i}', help=game[0]):
            heatmapPlaceholder.empty()
            with heatmapPlaceholder.container():
                plotCorrelationHeatmap(matchID=game[0], title=f'Correlation Heatmap For {gamesInfo[i]}')


def displayPage2():
    st.header("Page 2")
    st.write("This is page 2.")


if __name__ == "__main__":
    try:
        st.set_page_config(page_title="Your Page Title")
    except Exception as e:
        st.warning(f"Error setting page configuration: {e}")

    main()
