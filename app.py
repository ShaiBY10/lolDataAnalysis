from plot import *
from sql import getSummonerNameFromDB, getLastNMatchIDSOfSummonerFromDB, getGameStartTimestampAndSummonerChampionName
from utils import myLogger


class Dashboard:
    def __init__(self):
        st.set_page_config(page_title="My Dashboard", layout="wide")
        self.summonerNameList = getSummonerNameFromDB()

    @st.cache_data
    @myLogger
    def generateMatchLabels(_self, matchIds, summonerName):
        labels = []
        for matchId in matchIds:
            matchId, startDate, championPlayed = getGameStartTimestampAndSummonerChampionName(matchId, summonerName)
            label = f"{matchId} - {startDate} - {championPlayed}"
            labels.append(label)
        return labels

    def display(self):
        st.title("LoL Matches & Summoners Analysis")

        with st.sidebar:
            st.header("Navigation")
            pageSelection = st.radio("Go to", ["Home", "Matches", "Summoners"])

        if pageSelection == "Home":
            self.displayHome()

    def displayHome(self):
        st.header("Home")
        numSummoners = len(self.summonerNameList)
        columns = st.columns(numSummoners)

        heatmapPlaceholder = st.empty()

        for index, summonerName in enumerate(self.summonerNameList):
            with columns[index]:
                self.displaySummoner(summonerName, heatmapPlaceholder)

    def displaySummoner(self, summonerName, heatmapPlaceholder):
        st.subheader(summonerName)

        summonerLast50MatchIds = getLastNMatchIDSOfSummonerFromDB(summonerName, 50)
        gamesInfo = [getGameStartTimestampAndSummonerChampionName(matchId, summonerName) for matchId in
                     summonerLast50MatchIds]

        defaultSelection = ["Choose from the summoner's most recent 50 games:"]
        selectBoxLabeledMatches = defaultSelection + self.generateMatchLabels(summonerLast50MatchIds, summonerName)

        selectboxSelection = st.selectbox('Summoner Matches', selectBoxLabeledMatches, key=f'selectbox_{summonerName}',
                                          index=0)

        if selectboxSelection != defaultSelection[0]:
            selectedMatchId = selectboxSelection.split(' - ')[0]
            selectedGameInfo = next((game for game in gamesInfo if game[0] == selectedMatchId), None)

            if selectedGameInfo:
                heatmapPlaceholder.empty()
                with heatmapPlaceholder.container():
                    plotCorrelationHeatmap(matchID=selectedMatchId, title=f'Correlation Heatmap For {selectedGameInfo}')

        st.write('Last 3 Matches:')
        for i, game in enumerate(gamesInfo[:3]):
            if st.button(f'{game[1]} || {game[2]}', key=f'{summonerName}Match_{i}', help=game[0]):
                heatmapPlaceholder.empty()
                with heatmapPlaceholder.container():
                    plotCorrelationHeatmap(matchID=game[0], title=f'Correlation Heatmap For {gamesInfo[i]}')


if __name__ == "__main__":
    dashboard = Dashboard()
    dashboard.display()
