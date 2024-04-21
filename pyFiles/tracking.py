import asyncio
import json
import aiohttp
from datetime import datetime

from data import requestHeaders, getSummonerNamesFromDB, connect_db

from utils import cPrintS, getDetailsFromSummonerName, getSummonerNameFromPuuid, timestampToDate, \
    getDataFromConfig


def getCurrentHMS():
    return datetime.now().strftime('%H:%M:%S')


async def asyncRequest(url, headers=None, params=None, session=None, max_retries=5):
    if session is None:
        async with aiohttp.ClientSession() as session:
            return await makeAsyncRequest(session, url, headers, params, max_retries)
    else:
        return await makeAsyncRequest(session, url, headers, params, max_retries)


async def makeAsyncRequest(session, url, headers, params, max_retries):
    for attempt in range(max_retries):
        try:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()  # Successful response
                elif response.status == 403:
                    cPrintS('{{red}}Error 403: Forbidden. Do not forget to renew the API key.')
                    return None
                elif response.status == 404:
                    return None
                elif response.status == 429:
                    # Handle rate limiting
                    retry_after = int(
                        response.headers.get("Retry-After", 30))  # Default to 30 seconds if header is missing
                    cPrintS(f'{{red}}Rate limit exceeded. Retrying in {retry_after} seconds.')
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        cPrintS('{{red}}Maximum retries reached after rate limit. Aborting.')
                        return None
                else:
                    return response  # Return the response object for further inspection
        except aiohttp.ClientError as e:
            cPrintS(f'{{red}}Error occurred: {e}')
            if attempt == max_retries - 1:
                return None  # Return None in case of persistent errors


class Summoner:
    def __init__(self, puuid):
        self.puuid = puuid
        self.id = getDetailsFromSummonerName(getSummonerNameFromPuuid(puuid), 'summonerID')
        self.name = getSummonerNameFromPuuid(puuid)
        self.game = None
        self.gameID = None
        self.soloDuoTier = None
        self.soloDuoRank = None
        self.soloDuoLP = None


class SummonerTracker:
    def __init__(self, summoners):
        self.summoners = {summonerPuuid: Summoner(summonerPuuid) for summonerPuuid in summoners}
        self.session = None

    async def fetchSoloDuoRankData(self, summoner):
        # Construct the API URL using the summoner's ID
        rankedStatsURL = f"https://euw1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner.id}"

        # Make the API request
        response = await asyncRequest(rankedStatsURL, headers=requestHeaders, session=self.session)

        # Check if the response is valid and a list (as expected from API docs)
        if isinstance(response, list):
            # Look for the 'RANKED_SOLO_5x5' data within the response
            for queue in response:
                if queue['queueType'] == 'RANKED_SOLO_5x5':
                    # Return the relevant rank details as a dictionary
                    return {
                        'tier': queue['tier'],
                        'rank': queue['rank'],
                        'leaguePoints': queue['leaguePoints']
                    }

        # If the correct data is not found, return an empty dictionary
        return {}

    async def fetchSummonerStatus(self, summoner):
        """Check if the summoner is currently in a game."""
        url = f"https://euw1.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{summoner.puuid}"
        response = await asyncRequest(url, session=self.session, headers=requestHeaders)
        if isinstance(response, dict):  # Assume response is JSON data when in game
            summoner.state = 'inGame'
            summoner.gameID = response.get('gameId', None)
            # Additional game data extraction and storage logic here
            return True
        else:
            summoner.state = 'notInGame'
            summoner.gameID = None
            return False

    async def fetchPreGameData(self, summoner):
        url = f"https://euw1.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{summoner.puuid}"
        response = await asyncRequest(url, session=self.session, headers=requestHeaders)
        if response is None:
            cPrintS(f'{{yellow}} asyncRequest returned None for {summoner.name} preGameData')
            return None
        if isinstance(response, dict):
            preGameData = {'gameID': response.get('gameId', None),
                           'gameStartTime': response.get('gameStartTime', None),
                           'preGameRankData': await self.fetchSoloDuoRankData(summoner)}
            return preGameData
        else:
            return None

    async def upsertPreGameData(self, summoner, preGameData):
        conn = connect_db()
        curr = conn.cursor()
        sql = '''
    INSERT INTO summoner_matches (game_id, summoner_puuid, start_timestamp, "preGameMatchData")
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (game_id, summoner_puuid) DO UPDATE SET
    start_timestamp = EXCLUDED.start_timestamp,
    "preGameMatchData" = EXCLUDED."preGameMatchData";
        '''
        if preGameData is None:
            cPrintS(f"{{yellow}}{getCurrentHMS()} - {{red}}No pre-game data available for {{cyan}}{summoner.name}.")
            return False

        preGameMatchDataJson = json.dumps(preGameData)  # Ensure you serialize the complete pre-game data
        curr.execute(sql, (
            preGameData['gameID'],
            summoner.puuid,
            timestampToDate(preGameData['gameStartTime']),
            preGameMatchDataJson
        ))
        conn.commit()
        curr.close()
        conn.close()
        return True

    async def checkIfGameStillGoing(self, summoner, gameID):
        region = 'euw1'  # Example region
        url = f"https://{region}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{summoner.puuid}"
        response = await asyncRequest(url, session=self.session, headers=requestHeaders)

        if response is None:
            # If the response is None, it means the asyncRequest returned None, likely due to a 404 or network error
            cPrintS(
                f'{{yellow}}{getCurrentHMS()} - {{cyan}}{getSummonerNameFromPuuid(summoner.puuid)} {{red}}Is not in game.')
            return False

        if isinstance(response, dict):
            # Check if the gameID matches the expected gameID
            if response.get('gameId') == gameID:
                cPrintS(
                    f'{{yellow}}{getCurrentHMS()} - {{green}}{getSummonerNameFromPuuid(summoner.puuid)} is still in game.')
                return True
            else:
                cPrintS(
                    f'{{yellow}}{getCurrentHMS()} - {{red}}Game ID mismatch, summoner might have started a new game or the previous game ended.')
                return False
        else:
            # Handle unexpected response format
            print(response)
            raise Exception("Unexpected response format: Response is not a dictionary.")

    async def waitForGameToEnd(self, summoner, game):
        """Wait for the game to end by periodically checking the game status."""
        game_ongoing = True
        sleep_duration = 60  # Define sleep duration between checks, in seconds

        while game_ongoing:
            await asyncio.sleep(sleep_duration)
            game_ongoing = await self.checkIfGameStillGoing(summoner, gameID=game.gameID)

        cPrintS(f"{{yellow}}{getCurrentHMS()} - {{blue}}Game {game.gameID} has ended.")

    async def asyncGetMatchKnownParticipantsIndex(self, matchDataResponse):
        configPuuids = getDataFromConfig(key='puuids')
        summonersFound = 0
        knownMatchParticipants = {}
        for i, participant in enumerate(matchDataResponse['info']['participants']):
            if participant['puuid'] in configPuuids:
                puuidFound = participant['puuid']
                knownMatchParticipants[participant['puuid']] = i
                summonersFound += 1
                cPrintS(
                    f'{{green}}Found Summoner puuid: {{cyan}}{puuidFound} {{green}}at index{{cyan}} {i} {{green}}and '
                    f'added to result dict')
        cPrintS(
            f'{{green}}Found total of {{cyan}}{summonersFound}{{green}} summoners in match {{cyan}}{matchDataResponse["metadata"]["matchId"]}')
        return knownMatchParticipants

    async def fetchPostGameData(self, summoner, gameID):
        """Fetch postgame data for the given game ID."""
        url = f"https://europe.api.riotgames.com/lol/match/v5/matches/EUW1_{gameID}"
        response = await asyncRequest(url, session=self.session, headers=requestHeaders)
        cPrintS(f'{{yellow}}fetchPostGameData - {{cyan}}{response}')
        if response is None:
            cPrintS(f'{{yellow}} asyncRequest returned None for {summoner.name} postgame data')
            return None
        if isinstance(response, dict):
            postGameData = {}
            knownMatchParticipants = await self.asyncGetMatchKnownParticipantsIndex(response)
            summonerIndex = knownMatchParticipants[summoner.puuid]
            postGameData['gameResult'] = response['info']['participants'][summonerIndex]['win']
            postGameData['postGameMatchData'] = await self.fetchSoloDuoRankData(summoner)
            return postGameData
        else:
            return None

    async def asyncUpsertPostGameData(self, summoner):
        conn = connect_db()
        curr = conn.cursor()
        sql = """
        UPDATE summoner_matches 
        SET 
        result = %s,
        "postGameMatchData" = %s
        WHERE 
        game_id = %s AND summoner_puuid = %s;
        """
        # Serialize the postGameMatchData to a JSON string
        postGameMatchDataJson = json.dumps(summoner.game.postGameData)

        # Execute the SQL command with the JSON string
        curr.execute(sql, ('win' if summoner.game.postGameData['gameResult'] else 'loss',
                           postGameMatchDataJson,
                           summoner.game.gameID,
                           summoner.puuid))
        conn.commit()
        curr.close()
        conn.close()

    async def trackSummoner(self, summoner):
        """Continuously track the summoner's game status."""
        while True:
            inGame = await self.fetchSummonerStatus(summoner)
            if inGame:
                cPrintS(f'{{yellow}}{getCurrentHMS()} - {{cyan}}{summoner.name}: {{green}}In Game.')

                if summoner.game is None:  # Check if a new game instance is needed
                    cPrintS(f'{{yellow}}{getCurrentHMS()} - {{cyan}}{summoner.name}: {{blue}}fetching pregame data.')
                    preGameData = await self.fetchPreGameData(summoner)
                    summoner.game = Game(preGameData['gameID'], preGameData)  # Create a new game instance
                    cPrintS(f'{{yellow}}{getCurrentHMS()} - {{cyan}}{summoner.name}: {{blue}}upserting preGameData.')
                    if preGameData:
                        cPrintS(
                            f'{{yellow}}{getCurrentHMS()} - {{cyan}}{summoner.name}: {{green}} Found PreGameData :) ')
                        preGameDataUpserted = await self.upsertPreGameData(preGameData=preGameData,
                                                                           summoner=summoner)  # Upsert the pregame data
                        if preGameDataUpserted:
                            cPrintS(
                                f'{{yellow}}{getCurrentHMS()} - {{cyan}}{summoner.name}: {{green}} PreGameData Upserted :)')
                        else:
                            cPrintS(
                                f'{{yellow}}{getCurrentHMS()} - {{cyan}}{summoner.name}: {{red}} PreGameData Upsert Failed :(')
                    else:
                        cPrintS(
                            f'{{yellow}}{getCurrentHMS()} - {{cyan}}{summoner.name}: {{red}} No PreGameData Found :(')

                # Wait until the game ends
                cPrintS(f'{{yellow}}{getCurrentHMS()} - {{cyan}}{summoner.name}: {{magenta}}waiting for game to end.')
                await self.waitForGameToEnd(summoner=summoner, game=summoner.game)

                # Fetch postgame data
                cPrintS(f'{{yellow}}{getCurrentHMS()} - {{cyan}}{summoner.name}: {{blue}}fetching postgame data.')
                print(f'{summoner.game.gameID = }')
                postGameData = await self.fetchPostGameData(summoner, gameID=summoner.game.gameID)
                summoner.game.updatePostGameData(postGameData)  # Update the game instance with postgame data
                cPrintS(f'{{yellow}}{getCurrentHMS()} - {{cyan}}{summoner.name}: {{blue}}upserting postGameData.')
                await self.asyncUpsertPostGameData(summoner)
                cPrintS(f'{{yellow}}{getCurrentHMS()} - {{cyan}}{summoner.name}: {{green}} PostGameData Upserted :D.')
                summoner.game = None  # Clear the game instance
                await asyncio.sleep(4 * 60)  # Check every 4 minutes if a new game starts
            else:
                cPrintS(f'{{yellow}}{getCurrentHMS()} - {{cyan}}{summoner.name}: {{red}}Not In Game.')
                await asyncio.sleep(3 * 60)  # Check 3 minutes if the summoner is in a game

    async def start(self):
        """Start tracking all summoners by initializing the session and launching tasks."""
        # Initialize the session when starting the tracker
        self.session = await aiohttp.ClientSession().__aenter__()
        tasks = [self.trackSummoner(summoner) for summoner in self.summoners.values()]
        await asyncio.gather(*tasks)

    async def close(self):
        """Close the tracker and cleanup, including closing the session."""
        if self.session:
            await self.session.close()


class Game:
    def __init__(self, gameID, preGameData):
        self.gameID = gameID
        self.preGameData = preGameData
        self.postGameData = None
        self.status = 'active'

    def updatePreGameData(self, data):
        self.preGameData = data

    def updatePostGameData(self, data):
        self.postGameData = data
        self.status = 'completed'


async def main():
    summonerNames = getSummonerNamesFromDB()
    summonerPuuids = [getDetailsFromSummonerName(summoner, 'puuid') for summoner in summonerNames]
    tracker = SummonerTracker(summonerPuuids)
    try:
        await tracker.start()
    finally:
        await tracker.close()


# Debugging
# luukPuuid = 'P12p6eCWQbN9IEtYTYSRwoYMguj5MpNmVMdhF6HBFXueJPBc8ZBBrWRZBDP6yBr62UzqSbPxsxktFA'
# puuids = [luukPuuid]
# kataTracker = SummonerTracker(puuids)
# # x = await kataTracker.fetchSummonerStatus(kataTracker.summoners[luukPuuid])
# # print(kataTracker.summoners[luukPuuid].gameID)
# x = await kataTracker.fetchPostGameData(kataTracker.summoners[luukPuuid], 'EUW1_6907242392')
# kataTracker.summoners[luukPuuid].game = Game('6907242392', None)
# kataTracker.summoners[luukPuuid].game.updatePostGameData(x)
# await kataTracker.upsertPostGameData(kataTracker.summoners[luukPuuid])
# print(x)
#


if __name__ == "__main__":
    asyncio.run(main())
