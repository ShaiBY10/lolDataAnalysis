from data import getLatestVersion, getLatestChampions, getChampionRotations
from sql import updateLatestVersion, updateLatestChampions, upsertFreeRotation

version = getLatestVersion()  # get the latest game version to a variable

champions = getLatestChampions(version)  # get the latest champions to list

freeRotation = getChampionRotations()  # get the latest free rotation to list

updateLatestVersion()  # update the latest version table

updateLatestChampions(champions)  # update the latest champions table

upsertFreeRotation(freeRotation)  # update the free rotation table

# upsertListOfMatches(get100LatestSummonerMatches(getDataFromConfig(key='SummonerData')['ShaiBY']['puuid']))


