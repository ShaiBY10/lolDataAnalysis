from data import *
from utils import *

cPrintS('{yellow} Running main.py')
version = getLatestVersion()  # get the latest game version to a variable

champions = getLatestChampions(version)  # get the latest champions to list

freeRotation = getChampionRotations()  # get the latest free rotation to list

updateLatestVersion()  # update the latest version table
cPrintS(f'{{green}} Latest version is updated to {version}')

updateLatestChampions(champions)  # update the latest champions table
cPrintS(f'{{green}} Latest champions has been updated for {version} version')

upsertFreeRotation(freeRotation)  # update the free rotation table
cPrintS(f'{{green}} Latest free rotation has been updated \n Champions: {freeRotation}')

upsertSummonersRankedSoloData()  # update the summoners ranked solo data table
cPrintS(f'{{green}} Summoners ranked solo data has been updated')

cPrintS(f'{{yellow}} Getting latest matches data for summoners in config and upserting them to the DB')
# ----------------- Get 100 Latest Matches Data For Specific Summoners In Config  -----------------#
upsertListOfMatches(get50LatestSummonerMatches(getDataFromConfig(key='SummonerData')['Xavron']['puuid']))
upsertListOfMatches(get50LatestSummonerMatches(getDataFromConfig(key='SummonerData')['ShaiBY']['puuid']))
upsertListOfMatches(get50LatestSummonerMatches(getDataFromConfig(key='SummonerData')['GuySun']['puuid']))
cPrintS(f'{{green}} Done upserting matches for summoners in config')

# ----------------- Get All Matches Data For All Summoners In Config  -----------------#
# # Get the puuids of the summoners from the config file
# dorShaiGuyPuuids = getDataFromConfig(key='puuids')
# # For each puuid in returned list, get all available matches IDS, and upsert them to the DB (With their data)
# for summonerPuuid in dorShaiGuyPuuids:
#     upsertListOfMatches(getAllSummonerMatches(summonerPuuid))
#     cPrintS(f'{{red}} Done upserting matches for {summonerPuuid}')
#
