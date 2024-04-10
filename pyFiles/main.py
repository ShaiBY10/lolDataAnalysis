from pyFiles.data import *
from utils import *

cPrintS('{green} Running main.py')
version = getLatestVersion()  # get the latest game version to a variable

champions = getLatestChampions(version)  # get the latest champions to list

freeRotation = getChampionRotations()  # get the latest free rotation to list

updateLatestVersion()  # update the latest version table

updateLatestChampions(champions)  # update the latest champions table

upsertFreeRotation(freeRotation)  # update the free rotation table

upsertSummonersRankedSoloData() # update the summoners ranked solo data table


# ----------------- Get 100 Latest Matches Data For Specific Summoners In Config  -----------------#
upsertListOfMatches(get100LatestSummonerMatches(getDataFromConfig(key='SummonerData')['Xavron']['puuid']))
upsertListOfMatches(get100LatestSummonerMatches(getDataFromConfig(key='SummonerData')['ShaiBY']['puuid']))
upsertListOfMatches(get100LatestSummonerMatches(getDataFromConfig(key='SummonerData')['GuySun']['puuid']))



# ----------------- Get All Matches Data For All Summoners In Config  -----------------#
# # Get the puuids of the summoners from the config file
# dorShaiGuyPuuids = getDataFromConfig(key='puuids')
# # For each puuid in returned list, get all available matches IDS, and upsert them to the DB (With their data)
# for summonerPuuid in dorShaiGuyPuuids:
#     upsertListOfMatches(getAllSummonerMatches(summonerPuuid))
#     cPrintS(f'{{red}} Done upserting matches for {summonerPuuid}')
#
