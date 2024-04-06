import json
from datetime import datetime

import pandas as pd
import psycopg as ps
import streamlit as st
from sqlalchemy import create_engine

from data import getLatestVersion, getMatchData
from utils import getDataFromConfig, cPrint, cPrintS, timestampToDate, findMissingMatches, countdown, \
    getPuuidFromSummonerName, myLogger

dbname = 'LoL'
user = 'postgres'
password = '1210'
host = 'localhost'
port = '636'


@myLogger
def connect_db():
    return ps.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )

@myLogger
def updateLatestVersion():
    """
    This function retrieves the latest version of the game, gets the current timestamp,
    and replaces the current version in the database table named 'latest_version' with
    the new version along with its timestamp.

    The function does not keep a record of the old versions. It always contains one row
    with the latest version and timestamp.

    It then prints a message containing the latest version and timestamp.
    """
    # Get the latest version and current timestamp
    latest_version = getLatestVersion()
    timestamp = datetime.now()
    connectionString = getDataFromConfig(key='Database')['ConnectionString']

    # Connect to the database and execute the commands
    conn = connect_db()
    with conn.cursor() as cur:
        # Delete all rows from the table 'latest_version'
        cur.execute('DELETE FROM latest_version;')

        # Insert the latest version and the current timestamp into the table 'latest_version'
        cur.execute("INSERT INTO latest_version (version, last_checked) VALUES (%s, %s);", (latest_version, timestamp))

    cPrint(f"Latest version {latest_version} saved on {timestamp}", 'cyan')

@myLogger
def updateLatestChampions(champions_dict):
    # SQL to upsert champion data
    upsert_sql = """
    INSERT INTO champions (championID, championName, updateDate) 
    VALUES (%s, %s, %s) 
    ON CONFLICT (championID) 
    DO UPDATE SET championName = EXCLUDED.championName, updateDate = EXCLUDED.updateDate;
    """

    # Current date to mark when the update happens
    update_date = datetime.now().date()

    conn = connect_db()  # Ensure you have a function to connect to your database
    try:
        cur = conn.cursor()
        for champion_id, champion_name in champions_dict.items():
            # Execute upsert for each champion
            cur.execute(upsert_sql, (champion_id, champion_name, update_date))
        conn.commit()
        cPrint("Champions table updated successfully.", 'green')
        cur.close()
    except (Exception, ps.DatabaseError) as error:
        cPrint(f"Error updating champions table: {error}", 'red')
    finally:
        if conn is not None:
            conn.close()

@myLogger
def upsertFreeRotation(free_champions):
    # free_champions is a list of champion IDs for the current week

    delete_sql = "TRUNCATE TABLE current_free_champions;"  # Clears the existing data
    insert_sql = "INSERT INTO current_free_champions (championID) VALUES (%s);"

    conn = connect_db()  # Ensure you have a function to connect to your database
    try:
        cur = conn.cursor()
        # Clear the table
        cur.execute(delete_sql)

        # Insert the new list of free champions
        for champion_id in free_champions:
            cur.execute(insert_sql, (champion_id,))

        conn.commit()
        cur.close()
        cPrint("Current free champions updated successfully.", 'green')
    except (Exception, ps.DatabaseError) as error:
        cPrint(f"Error: {error}", 'red')
    finally:
        if conn is not None:
            conn.close()

@myLogger
def upsertSummonerData(summonerData):
    sql = """
    INSERT INTO summoners (puuid, id, accountId, name, profileIconId, revisionDate, summonerLevel) 
    VALUES (%s, %s, %s, %s, %s, %s, %s) 
    ON CONFLICT (puuid) 
    DO UPDATE SET 
        id = EXCLUDED.id, 
        accountId = EXCLUDED.accountId, 
        name = EXCLUDED.name, 
        profileIconId = EXCLUDED.profileIconId, 
        revisionDate = EXCLUDED.revisionDate, 
        summonerLevel = EXCLUDED.summonerLevel;
    """

    conn = None
    try:
        conn = connect_db()  # Assuming you have a predefined function for database connection
        cur = conn.cursor()
        # Execute the upsert operation
        cur.execute(sql, (
            summonerData['puuid'],
            summonerData['id'],
            summonerData['accountId'],
            summonerData['name'],
            summonerData['profileIconId'],
            summonerData['revisionDate'],
            summonerData['summonerLevel']
        ))
        conn.commit()
        cPrint(f"Summoner {summonerData['name']} upserted successfully.", 'green')
    except (Exception, ps.DatabaseError) as error:
        cPrint(f"Error upserting Summoner data: {error}", 'red')
    finally:
        if conn is not None:
            conn.close()

@myLogger
def upsertMatchData(matchData):
    sql = """
    INSERT INTO matches (matchid, datetime, matchdata) 
    VALUES (%s, %s, %s) 
    ON CONFLICT (matchid) 
    DO UPDATE SET 
        matchid = EXCLUDED.matchid, 
        datetime = EXCLUDED.datetime, 
        matchdata = EXCLUDED.matchdata
    """
    conn = None
    try:
        conn = connect_db()  # Assuming you have a predefined function for database connection
        cur = conn.cursor()
        # Convert the matchData dictionary to a JSON string
        matchDataJson = json.dumps(matchData)
        # Execute the upsert operation
        cur.execute(sql, (
            matchData['metadata']['matchId'],
            timestampToDate(matchData['info']['gameStartTimestamp']),
            matchDataJson,

        ))
        conn.commit()
        cPrint(f"Match {matchData['metadata']['matchId']} upserted successfully.", 'green')
        return True
    except (Exception, ps.DatabaseError) as error:
        cPrint(f"Error upserting Match data: {error}", 'red')

    finally:
        if conn is not None:
            conn.close()

@myLogger
def getMatchIdsFromDB():
    """
    Fetches all match IDs from the 'matches' table in the database.

    Establishes a connection to the database, retrieves all match IDs
    from the 'matches' table, closes the database connection, and returns
    a list of match IDs.

    Returns:
        list: A list of match IDs from the 'matches' table.
    """
    conn = connect_db()
    cur = conn.cursor()
    # Fetch all match IDs
    cur.execute("SELECT matchID FROM matches;")
    matchesList = [row[0] for row in cur.fetchall()]

    # Close the connection
    cur.close()
    conn.close()
    return matchesList

@myLogger
@st.cache_data
def getSummonerNameFromDB():
    """
    Fetches all summoner names from the 'summoners' table in the database.

    Establishes a connection to the database, retrieves all summoner names
    from the 'summoners' table, closes the database connection, and returns
    a list of summoner names.

    Returns:
        list: A list of summoner names from the 'summoners' table.
    """
    conn = connect_db()
    cur = conn.cursor()
    # Fetch all match IDs
    cur.execute("SELECT name FROM summoners;")
    summonerList = [row[0] for row in cur.fetchall()]

    # Close the connection
    cur.close()
    conn.close()
    return summonerList

@myLogger
def upsertListOfMatches(matchesList):
    """
    A function that checks for missing IDs in the DB, retrieves their data, and upserts it.

    Parameters:
    - matchesList: a list of matches to be checked

    Returns:
    None
    """

    cPrint('Checking what IDS are missing from DB and inserting...', 'yellow')
    matchIdsFromDB = getMatchIdsFromDB()
    missingMatches = findMissingMatches(getMatchIdsFromDB(), matchesList)
    if len(missingMatches) == 0:
        cPrint('No missing matches found (The DB is updated with latest Summoner Matches!)', 'green')
        cPrint('Exiting...', 'green')
        return None
    elif len(matchIdsFromDB) == 0:
        cPrint('Adding all matches from list (DB is empty)', 'yellow')
    else:
        matchesList = missingMatches
    matchesAdded = 0
    requestCount = 0
    for matchid in matchesList:
        while True:
            cPrint(f'Match ID:{matchid}', 'cyan')
            matchData = getMatchData(matchid)
            requestCount += 1

            if matchData == 'limit':
                # Hit the rate limit, wait and then continue the loop without moving to the next match
                cPrint('Rate limit hit, waiting...', 'red')
                countdown(30)
                continue  # This will skip the rest of the loop and retry the same matchid

            if type(matchData) is dict:
                matchUpserted = upsertMatchData(matchData)
                if matchUpserted:
                    cPrintS(f'{{green}}Added Match ID {{cyan}}{matchid}')
                    matchesAdded += 1
                    cPrintS(
                        f'{{green}}Matches Added till now: {{cyan}}{matchesAdded} {{green}} out of{{cyan}}{len(missingMatches)}{{green}}matches')
                    break  # Successfully processed the match, break the while loop to move to the next match
            else:
                cPrint(f'Match {matchid} Data could not be found, skipping...', 'yellow')
                break  # If there's no data, and it's not a rate limit, move to the next match

    cPrintS(
        f'{{green}}Finished! Matches Added: {{cyan}}{matchesAdded}{{green}} out of {{cyan}}{len(missingMatches)}{{green}} matches found')

@myLogger
def getSummonerMatchDataFromDB(matchID, summonerIndex):
    """
    Retrieves specific match data for a summoner from a PostgreSQL database.
    With the data from this function it is poissible to plot the correlation matrix and more analysis

    Parameters:
    - matchID: int, the ID of the match to retrieve data for
    - summonerIndex: int, the index of the summoner in the match data

    Returns:
    - DataFrame: contains various match data for the specified summoner
    """

    connectionString = getDataFromConfig(key='Database')['ConnectionString']

    if matchID.startswith("EUW1_"):
        matchID = matchID.replace("EUW1_", "", 1)

    engine = create_engine(connectionString)

    query = f"""
SELECT 
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'puuid' as puuid,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'summonerName' as summoner_name,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'championName' as champion_name,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'assists' as assists,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'assistMePings' as assist_me_pings,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'totalDamageDealtToChampions' as total_chmp_dmg_dealt,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'magicDamageDealtToChampions' as chmp_magic_dmg_dealt,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'physicalDamageDealtToChampions' as chmp_physical_dmg_dealt,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'trueDamageDealtToChampions' as true_dmg_dealt,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'totalDamageTaken' as total_dmg_taken,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'deaths' as deaths,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'goldEarned' as gold_earned,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'goldSpent' as gold_spent,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'kills' as kills,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'wardsPlaced' as wards_placed,
        m.matchdata -> 'info' -> 'participants' -> {summonerIndex} -> 'wardsKilled' as wards_killed
FROM matches as m
WHERE (m.matchdata -> 'info' -> 'gameId') :: bigint = {matchID}
"""
    return pd.read_sql_query(query, engine)

@myLogger
def getMatchDataFromDB(matchID):
    engine = create_engine(getDataFromConfig(key='Database')['ConnectionString'])
    query = f"""
    select matchdata from matches
    where matchid = '{matchID}'
    """
    queryResponse = pd.read_sql_query(query, engine)
    return queryResponse['matchdata'][0]

@myLogger
def getMatchKnownParticipantsIndex(matchID):
    configPuuids = getDataFromConfig(key='puuids')
    summonersFound = 0

    df = getMatchDataFromDB(matchID)
    participantsIndexes = {}
    for i, participant in enumerate(df['metadata']['participants']):
        if participant in configPuuids:
            summonersFound += 1
            participantsIndexes[participant] = i
            cPrintS(
                f'{{green}}Found Summoner puuid: {{cyan}}{participant} {{green}}at index{{cyan}} {i} {{green}}and added to result dict')
    cPrintS(f'{{green}}Found total of {{cyan}}{summonersFound}{{green}} summoners in match {{cyan}}{matchID}')
    return participantsIndexes


@st.cache_resource
@myLogger
def getLastNMatchIDSOfSummonerFromDB(summonerName, n=3):
    """
    A function to retrieve the last N match IDs of a summoner from the database.

    Parameters:
    - summonerName: str, the name of the summoner
    - limit: int, optional, the number of match IDs to retrieve (default is 3)

    Returns:
    - list of str: a list of the last N match IDs of the summoner
    """

    summonerPuuid = getPuuidFromSummonerName(summonerName)

    engine = create_engine(getDataFromConfig(key='Database')['ConnectionString'])
    query = f"""
   SELECT m.matchID
    FROM matches m
    WHERE m.matchdata -> 'metadata' -> 'participants' @> '["{summonerPuuid}"]'::jsonb
    ORDER BY datetime desc
    limit {n};

     """
    queryResponse = pd.read_sql_query(query, engine)
    return queryResponse.iloc[:, 0].tolist()


@st.cache_data
@myLogger
def getGameStartTimestampAndSummonerChampionName(matchID, summonerName):
    summonerPuuid = getPuuidFromSummonerName(summonerName)
    knownMatchParticipants = getMatchKnownParticipantsIndex(matchID)
    summonerIndex = knownMatchParticipants[summonerPuuid]
    df = getMatchDataFromDB(matchID)
    matchID = df['metadata']['matchId']
    matchStartTimestampStr = timestampToDate(df['info']['gameStartTimestamp'], convert=True)
    matchStartTimestamp = datetime.strptime(matchStartTimestampStr, '%Y-%m-%d %H:%M:%S')
    matchStartDate = matchStartTimestamp.strftime('%d/%m/%y %H:%H')
    summonerChampionPlayed = df['info']['participants'][summonerIndex]['championName']
    return matchID, matchStartDate, summonerChampionPlayed
