import os

import pandas as pd
import psycopg2 as ps
import psycopg2.extras
import requests as re
import streamlit as st
from sqlalchemy import create_engine

from utils import *

dbname = 'LoL'
user = 'postgres'
password = '1210'
host = '192.168.50.209'
port = '636'

requestHeaders = getDataFromConfig(key='API')['requestHeaders']


@myLogger
def request(url, headers=requestHeaders, params=None, max_retries=5, defaultRetryAfter=30):
    """
    A function to make a request to a URL with optional headers and parameters. Automatically retries on rate limit.

    Parameters:
    url (str): The URL to make the request to.
    headers (dict, optional): The headers to include in the request. Defaults to None.
    params (dict, optional): The parameters to include in the request. Defaults to None.
    max_retries (int, optional): Maximum number of retries if rate limited. Defaults to 5.

    Returns:
    The response object if the status code is 200, the status code if 429 or 404, and the status code with explanation for all other cases.
    """
    response = None  # Initialize response to ensure it's defined even if the requests.get call fails
    for attempt in range(max_retries):
        response = re.get(url, headers=headers, params=params)  # Assuming you meant requests.get, not re.get

        if response.status_code == 200:
            cPrintS(f'{{green}}Request successful.')
            return response  # Successful request
        elif response.status_code == 429:
            # Rate limit hit. Wait and retry.
            waitTime = response.headers.get('Retry-After', defaultRetryAfter)
            cPrintS(
                f'{{yellow}} Function {{cyan}}request{{yellow}} hit the rate limit, Sleeping for {waitTime} and retrying...')
            countdown(int(waitTime))  # Using your custom countdown function for waiting
            continue  # Go to the next iteration and retry the request
        elif response.status_code == 404:
            cPrintS('{red}Data not found.')
            return response.status_code
        else:
            # Other errors
            cPrintS(f'{{red}}Error Code: {response.status_code} || {explainStatus(response.status_code)}')
            return response.status_code

    cPrintS('{red}Max retries reached. Returning the last response status code.')
    return response.status_code if response else 'noResponse'  # Ensure there's a fallback if response was never assigned


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
def getLatestVersion():
    """
    Retrieves the latest version of the game data from the Riot Games API.

    The function sends a GET request to the Riot Games API's versions endpoint,
    which returns a list of game versions in descending order. The function then
    converts the response to JSON format and returns the first version in the list,
    which is the latest version.

    Returns:
        str: The latest version of the game data.
    """

    # API url from where to fetch versions
    versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"

    # Make a GET request to the versions API
    response = request(versions_url)

    # Convert the response to JSON format
    versions = response.json()

    # Return the first version in the list as it is the latest
    return versions[0]


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
    # Connect to the database and execute the commands
    conn = connect_db()
    with conn.cursor() as cur:
        # Delete all rows from the table 'latest_version'
        cur.execute('DELETE FROM latest_version;')

        # Insert the latest version and the current timestamp into the table 'latest_version'
        cur.execute("INSERT INTO latest_version (version, last_checked) VALUES (%s, %s);", (latest_version, timestamp))

    cPrint(f"Latest version {latest_version} saved on {timestamp}", 'cyan')


@myLogger
def getLatestChampions(version, language='en_US'):
    """
    getLatestChampions is a function that fetches the latest champions from the API using the given version and
    language. This function constructs a URL for the API using the provided parameters. It then sends a GET request
    to the generated URL. It further converts the response to JSON format. From the resultant JSON data, it creates a
    dictionary that maps champion keys to champion IDs.

    Parameters:
        - version (str): The version of the game data to retrieve.
        - language (str, optional): The language in which to retrieve the data. Default language is 'en_US'.

    Returns:
        - champions (dict): A dictionary containing champion keys as keys and champion IDs as values.
    """
    # creates the url for the API using the given version and language
    championsURL = f"http://ddragon.leagueoflegends.com/cdn/{version}/data/{language}/champion.json"
    # sends a get request to the generated url
    response = request(championsURL)
    # converts the response to json format
    championsData = response.json()
    # gets the champion ids and keys from the resulting json and creates a dictionary
    champions = {champ['key']: champ['id'] for champ in championsData['data'].values()}
    # returns the created dictionary
    return champions


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
def getChampionRotations():
    """
    getChampionRotations is a function that fetches the currently free-to-play champion rotations from the Riot Games
    API.

    Process:
    The function constructs a request to the Riot Games API with the appropriate headers and API key.
    It sends a GET request to the constructed URL.
    After getting a response from the API, it converts this response to JSON format.
    From the resultant JSON data, it retrieves a list of IDs representing the free-to-play champion rotations.

    Returns:
    - freeChampions (list): A list containing the IDs of the currently free-to-play champions in the game.
"""
    # Define the URL to get the champion rotations
    rotationsURL = 'https://euw1.api.riotgames.com/lol/platform/v3/champion-rotations'

    # Send the GET request
    response = request(rotationsURL, headers=requestHeaders)

    # Convert the response to JSON
    freeChampionsData = response.json()

    # Get the list of free champion IDs from the response data
    freeChampions = freeChampionsData['freeChampionIds']

    # Return the list of free champion IDs
    return freeChampions


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
def getSummonerData(summonerName):
    """
    Retrieves summoner data from the Riot Games API for a specified summoner name in the EUW (Europe West) region.

    This function constructs a request to the Riot Games API, specifically to the Summoner endpoint to fetch details
    about a summoner/player in the game League of Legends. It requires a valid API key provided by Riot Games for
    developers. The API key should be set in the variable `API_key` before calling this function.

    Parameters:
    - summonerName (str): The name of the summoner/player for which to retrieve data.

    Returns:
    - dict: A dictionary containing various pieces of information about the summoner,
    such as the summoner's ID, account ID, puuid, name, profile icon ID, revision date, and summoner level.
    The structure and content of the returned data are defined by the Riot Games API and may change over time.

    Note: - The function requires an internet connection to access the Riot Games API. - You must have a valid API
    key from Riot Games and have it assigned to the variable `API_key`. - This function is designed to work with the
    EUW1 (Europe West) server. For other regions, the base URL in the `infoURL` variable must be adjusted
    accordingly. - Proper error handling for issues such as network errors or invalid API keys is not implemented in
    this basic example.
    """

    infoURL = f'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summonerName}'

    response = request(infoURL, headers=requestHeaders)
    summonerData = response.json()
    return summonerData


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
def getMatchData(matchID):
    """
    Retrieve match data from the Riot Games API using the provided match ID.

    Args:
        matchID (str): The ID of the match to retrieve data for.

    Returns: dict or str or int: The match data if the request is successful, 'limit' if the rate limit is hit,
    or the HTTP status code if there is an error.
    """
    url = f'https://europe.api.riotgames.com/lol/match/v5/matches/{matchID}'
    response = request(url, headers=requestHeaders)
    return response.json() if response.status_code == 200 else response.status_code


@myLogger
def upsertMatchData(matchData):
    """
    This function inserts or updates (upserts) match data into the 'matches' table in the database.

    The function takes a dictionary containing match data as input. It extracts the relevant data from the dictionary,
    including match metadata, match info, and participant data. It then executes an SQL query to insert the data into
    the database. If a match with the same ID already exists in the database, the function updates the existing record
    with the new data.

    Parameters:
        matchData (dict): A dictionary containing match data.

    Returns:
        bool: True if the operation was successful, False otherwise.

    Raises:
        Exception: If there is an error executing the SQL query.
        psycopg2.DatabaseError: If there is an error connecting to the database or executing the SQL query.
    """

    sql = """
    INSERT INTO matches (
        matchid, datetime, matchmetadata, matchinfo, 
        matchparticipant0, matchparticipant1, matchparticipant2, matchparticipant3, matchparticipant4, 
        matchparticipant5, matchparticipant6, matchparticipant7, matchparticipant8, matchparticipant9
    ) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
    ON CONFLICT (matchid) 
    DO UPDATE SET 
        matchid = EXCLUDED.matchid, 
        datetime = EXCLUDED.datetime, 
        matchmetadata = EXCLUDED.matchmetadata, 
        matchinfo = EXCLUDED.matchinfo, 
        matchparticipant0 = EXCLUDED.matchparticipant0, 
        matchparticipant1 = EXCLUDED.matchparticipant1, 
        matchparticipant2 = EXCLUDED.matchparticipant2, 
        matchparticipant3 = EXCLUDED.matchparticipant3, 
        matchparticipant4 = EXCLUDED.matchparticipant4, 
        matchparticipant5 = EXCLUDED.matchparticipant5, 
        matchparticipant6 = EXCLUDED.matchparticipant6, 
        matchparticipant7 = EXCLUDED.matchparticipant7, 
        matchparticipant8 = EXCLUDED.matchparticipant8, 
        matchparticipant9 = EXCLUDED.matchparticipant9
    """
    conn = None
    try:
        conn = connect_db()  # Assuming you have a predefined function for database connection
        cur = conn.cursor()

        # Extract the relevant data from the matchData dictionary
        matchid = matchData['metadata']['matchId']
        matchDateTime = timestampToDate(matchData['info']['gameStartTimestamp'])
        matchMetadata = json.dumps(matchData['metadata'])
        matchInfo = matchData['info'].copy()
        if 'participants' in matchInfo:
            del matchInfo['participants']
        matchInfo = json.dumps(matchInfo)

        # Extract the participant data
        participants = matchData['info']['participants']
        participant0 = json.dumps(participants[0]) if len(participants) > 0 else None
        participant1 = json.dumps(participants[1]) if len(participants) > 1 else None
        participant2 = json.dumps(participants[2]) if len(participants) > 2 else None
        participant3 = json.dumps(participants[3]) if len(participants) > 3 else None
        participant4 = json.dumps(participants[4]) if len(participants) > 4 else None
        participant5 = json.dumps(participants[5]) if len(participants) > 5 else None
        participant6 = json.dumps(participants[6]) if len(participants) > 6 else None
        participant7 = json.dumps(participants[7]) if len(participants) > 7 else None
        participant8 = json.dumps(participants[8]) if len(participants) > 8 else None
        participant9 = json.dumps(participants[9]) if len(participants) > 9 else None

        # Execute the upsert operation
        cur.execute(sql, (
            matchid, matchDateTime, matchMetadata, matchInfo,
            participant0, participant1, participant2, participant3, participant4,
            participant5, participant6, participant7, participant8, participant9
        ))
        conn.commit()
        cPrint(f"Match {matchid} upserted successfully.", 'green')
        return True
    except (Exception, ps.DatabaseError) as error:
        cPrint(f"Error upserting Match data: {error}", 'red')
        return False
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


def getChampionsFromDB():
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
    cur.execute("SELECT championname FROM champions;")
    matchesList = [row[0] for row in cur.fetchall()]

    # Close the connection
    cur.close()
    conn.close()
    return matchesList


@myLogger
@st.cache_data
def getSummonerNamesFromDB(lower=False):
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
    if lower:
        summonerList = [row[0].lower() for row in cur.fetchall()]
    else:
        summonerList = [row[0] for row in cur.fetchall()]

    # Close the connection
    cur.close()
    conn.close()
    return summonerList


@myLogger
def getAllSummonerMatches(puuid, region='europe', start=0, count=100):
    """
    Retrieves matches for a summoner identified by their PUUID.

    Args:
        puuid (str): The PUUID of the summoner.
        region (str): The region where the summoner plays. Defaults to 'europe'.
        start (int): The starting index for fetching matches. Defaults to 0.
        count (int): The number of matches to fetch in each batch. Defaults to 100.

    Returns:
        list: A list of all summoner matches IDS
    """

    # Construct the URL for fetching matches
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"

    matches = []  # List to store the match data
    cPrintS(f'')
    while True:
        params = {"start": start, "count": count}
        response = request(url, params=params, headers=requestHeaders)  # Make a request to the API

        if response.status_code == 200:
            # Successful request
            data = response.json()
            if not data:  # No more data to fetch
                break
            matches.extend(data)  # Add fetched data to the matches list
            start += count  # Increment the starting index for the next batch
            # Print the first and last matches added to keep track of progress
            cPrintS(
                f'{{white}}First match for this batch: {{cyan}}{data[0]} , {{white}}Last match for this batch: {{cyan}}{data[-1]}')
            cPrintS(f'{{green}} Until now {{cyan}}{len(matches)} {{green}}matches have been fetched successfully :D')
        else:
            # Handle other HTTP Errors
            cPrint(f'HTTP Error {response.status_code}: {response.text}', 'red')
    return matches


@myLogger
def get100LatestSummonerMatches(puuid, region='europe'):
    """
    Retrieves the latest matches for a given summoner based on their unique identifier (puuid) and region.

    Parameters:
    - puuid (str): The unique identifier of the summoner.
    - region (str): The region where the summoner plays. Default is 'europe'.

    Returns:
    - dict or int: A dictionary of match details if the response status code is 200, otherwise the response status code.
    """

    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"

    params = {
        "start": 0,
        "count": 100,
    }
    response = request(url, params=params, headers=requestHeaders)

    return response.json()


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
    if matchIdsFromDB == 'empty':
        cPrint('Adding all matches from list (DB is empty)', 'yellow')
    elif len(missingMatches) == 0:
        cPrint('No missing matches found (The DB is updated with latest Summoner Matches!)', 'green')
        cPrint('Exiting...', 'green')
        return None
    else:
        matchesList = missingMatches
    matchesAdded = 0
    requestCount = 0
    for matchid in matchesList:
        try:
            while True:
                cPrint(f'Match ID:{matchid}', 'cyan')
                matchData = getMatchData(matchid)
                requestCount += 1
                if type(matchData) is dict:
                    matchUpserted = upsertMatchData(matchData)
                    if matchUpserted:
                        cPrintS(f'{{green}}Added Match ID {{cyan}}{matchid}')
                        matchesAdded += 1
                        cPrintS(
                            f'{{green}}Matches Added till now: {{cyan}}{matchesAdded}{{green}} out of{{cyan}} {len(missingMatches)}{{green}} matches')
                        break  # Successfully processed the match, break the while loop to move to the next match
                else:
                    cPrint(
                        f'Match {matchid} Data could not be found, skipping... {len(missingMatches) - requestCount} Matches Left',
                        'yellow')
                    upsertErrorToDB(matchid, matchData)
                    break  # If there's no data, and it's not a rate limit, move to the next match
        except Exception as e:
            errorCode = getattr(e, 'obj', None)
            if errorCode is not None:
                cPrintS(
                    f"{{yellow}}Error processing match {{cyan}} {matchid}, {{red}}Request couldn't find the Match Data\n"
                    f"{e}:(Cant .json() because error code was returned instead of matchData {{cyan}}")
                upsertErrorToDB(matchid, errorCode)
                continue  # Skip to the next match ID

    cPrintS(
        f'{{green}}Finished! Matches Added: {{cyan}}{matchesAdded}{{green}} out of {{cyan}}{len(missingMatches)}{{green}} matches found')


@myLogger
def upsertErrorToDB(match_id, error_code):
    """
    Upserts an error log into the public.upsert_errors table with validation
    to prevent logging the same error code for a match ID more than once.

    Parameters:
    - match_id (str): The ID of the match.
    - error_code (int): The error code encountered during the upsert attempt.
    - db_params (dict): Database connection parameters including dbname, user, password, and host.
    """
    # SQL command to check for existing matchid with the same error code
    check_sql = """
    SELECT EXISTS(
        SELECT 1 FROM public.upsert_errors
        WHERE matchid = %s AND errorcode = %s
    );
    """

    # SQL command for upsert
    upsert_sql = """
    INSERT INTO public.upsert_errors (matchid, upsertattemptdatetime, errorcode)
    VALUES (%s, %s, %s)
    ON CONFLICT (matchid)
    DO UPDATE SET
        upsertattemptdatetime = EXCLUDED.upsertattemptdatetime,
        errorcode = EXCLUDED.errorcode;
    """

    # Establish a connection to the database
    conn = None
    cur = None  # Initialize cur to None
    try:
        conn = connect_db()
        cur = conn.cursor()

        # Check if the error for the match ID already exists
        cur.execute(check_sql, (match_id, error_code))
        exists = cur.fetchone()[0]

        if exists:
            cPrintS(f"{{green}}Match ID {match_id} with error code {error_code} is already logged.")
        else:
            # Current timestamp
            now = datetime.now()

            # Execute the upsert
            cur.execute(upsert_sql, (match_id, now, error_code))

            # Commit the transaction
            conn.commit()

            cPrintS(f"{{yellow}}Upsert error for match ID {match_id} logged successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@myLogger
def getErrorMatchesFromDB():
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
    cur.execute("SELECT matchid FROM upsert_errors;")
    matchesList = [row[0] for row in cur.fetchall()]

    # Close the connection
    cur.close()
    conn.close()
    return matchesList


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
        m.matchparticipant{summonerIndex} -> 'puuid' as puuid,
        m.matchparticipant{summonerIndex} -> 'summonerName' as summoner_name,
        m.matchparticipant{summonerIndex} -> 'championName' as champion_name,
        m.matchparticipant{summonerIndex} -> 'assists' as assists,
        m.matchparticipant{summonerIndex} -> 'assistMePings' as assist_me_pings,
        m.matchparticipant{summonerIndex} -> 'totalDamageDealtToChampions' as total_chmp_dmg_dealt,
        m.matchparticipant{summonerIndex} -> 'magicDamageDealtToChampions' as chmp_magic_dmg_dealt,
        m.matchparticipant{summonerIndex} -> 'physicalDamageDealtToChampions' as chmp_physical_dmg_dealt,
        m.matchparticipant{summonerIndex} -> 'trueDamageDealtToChampions' as true_dmg_dealt,
        m.matchparticipant{summonerIndex} -> 'totalDamageTaken' as total_dmg_taken,
        m.matchparticipant{summonerIndex} -> 'deaths' as deaths,
        m.matchparticipant{summonerIndex} -> 'goldEarned' as gold_earned,
        m.matchparticipant{summonerIndex} -> 'goldSpent' as gold_spent,
        m.matchparticipant{summonerIndex} -> 'kills' as kills,
        m.matchparticipant{summonerIndex} -> 'wardsPlaced' as wards_placed,
        m.matchparticipant{summonerIndex} -> 'wardsKilled' as wards_killed
FROM matches as m
WHERE (m.matchinfo ->> 'gameId') :: bigint = {matchID}
"""
    return pd.read_sql_query(query, engine)


@myLogger
def getMatchDataFromDB(matchID):
    # Connect to the database using your connect_db function
    conn = connect_db()

    # Cursor with dictionary fetch mode
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Execute the query
    cursor.execute("""
    SELECT * FROM matches WHERE matchid = %s
    """, (matchID,))

    # Fetch one result
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        # Constructing the matchData dictionary from the result
        matchData = {
            "matchid": result['matchid'],
            "datetime": result['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
            "matchmetadata": result['matchmetadata'],
            "matchinfo": result['matchinfo'],
            "participants": []
        }

        # Dynamically adding participant data to the matchData dictionary
        for i in range(10):
            participant_key = f"matchparticipant{i}"
            if result[participant_key]:
                matchData["participants"].append(result[participant_key])

        return matchData
    else:
        # Return None if no match found
        return None


@myLogger
def getMatchKnownParticipantsIndex(matchID):
    configPuuids = getDataFromConfig(key='puuids')
    summonersFound = 0

    df = getMatchDataFromDB(matchID)
    participantsIndexes = {}
    for i, participant in enumerate(df['matchmetadata']['participants']):
        if participant in configPuuids:
            summonersFound += 1
            participantsIndexes[participant] = i
            cPrintS(
                f'{{green}}Found Summoner puuid: {{cyan}}{participant} {{green}}at index{{cyan}} {i} {{green}}and '
                f'added to result dict')
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

    summonerPuuid = getDetailsFromSummonerName(summonerName)

    engine = create_engine(getDataFromConfig(key='Database')['ConnectionString'])
    query = f"""
   SELECT m.matchID
    FROM matches m
    WHERE m.matchmetadata -> 'participants' @> '["{summonerPuuid}"]'::jsonb
    ORDER BY datetime desc
    limit {n};

     """
    queryResponse = pd.read_sql_query(query, engine)
    return queryResponse.iloc[:, 0].tolist()


@st.cache_data
@myLogger
def getGameStartTimestampAndSummonerChampionName(matchID, summonerName):
    summonerPuuid = getDetailsFromSummonerName(summonerName)
    knownMatchParticipants = getMatchKnownParticipantsIndex(matchID)
    summonerIndex = knownMatchParticipants[summonerPuuid]
    df = getMatchDataFromDB(matchID)
    matchID = df['matchmetadata']['matchId']
    matchStartTimestampStr = timestampToDate(df['matchinfo']['gameStartTimestamp'], convert=True)
    matchStartTimestamp = datetime.strptime(matchStartTimestampStr, '%Y-%m-%d %H:%M:%S')
    matchStartDate = matchStartTimestamp.strftime('%d/%m/%y %H:%H')
    summonerChampionPlayed = df['participants'][summonerIndex]['championName']
    return matchID, matchStartDate, summonerChampionPlayed


@myLogger
def downloadChampionIcons():
    """
    Downloads missing League of Legends champion icons based on the current list of champions in the database.
    """

    # Get the latest game version for the request URL
    gameVersion = getLatestVersion()

    # Get champion list from the database
    championList = getChampionsFromDB()

    # Ensure there's a directory to save the icons
    os.makedirs('../championIcons', exist_ok=True)

    # List all files currently in the championIcons directory
    existingIcons = os.listdir('../championIcons')
    existingChampions = [file.split('.')[0] for file in existingIcons]  # Extract champion names from file names

    # Initialize a counter for downloaded icons
    champAddedCount = 0

    # Download icons for champions not in the existingChampions list
    for champion in championList:
        if champion not in existingChampions:
            iconURL = f'http://ddragon.leagueoflegends.com/cdn/{gameVersion}/img/champion/{champion}.png'
            response = request(url=iconURL)
            if response.status_code == 200:
                with open(f'championIcons/{champion}.png', 'wb') as f:
                    f.write(response.content)
                champAddedCount += 1
                cPrintS(
                    f'{{green}}Successfully downloaded icon for champion {{cyan}}{champion}, \n {{blue}}Progress: {{'
                    f'cyan}}{champAddedCount} / {len(championList)}')
            else:
                cPrint(f'Failed to download icon for champion {champion}', 'red')
        else:
            # Champion icon already exists, no need to download
            pass

    if champAddedCount > 0:
        cPrintS(
            f'{{green}}Finished downloading new champion icons. Total new icons downloaded: {{cyan}}{champAddedCount}')
    else:
        cPrintS('{{green}}All champion icons are up-to-date.')


@myLogger
def upsertChampionLinksToDB(championsLinks):
    """
    Upsert links for champions in the PostgreSQL database.

    :param championsLinks: A dictionary with champion names as keys and their links as values.
    """
    conn = None
    try:
        # Connect to the PostgreSQL database
        conn = connect_db()
        cur = conn.cursor()

        # SQL for upserting the champion link to db from the dictionary
        upsert_sql = """
        UPDATE champions
        SET "iconLink" = %s
        WHERE championName = %s
        """

        # Execute the upsert command for each champion
        for champion, link in championsLinks.items():
            cur.execute(upsert_sql, (link, champion))

        # Commit the changes
        conn.commit()

        print("Champion links have been upserted successfully.")

    except (Exception, ps.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


@myLogger
def getSummonerRankedSoloData(summonerID):
    """
    Retrieves the ranked stats of a summoner from the Riot Games API.

    This function constructs a request to the Riot Games API, specifically to the League of Legends ranked stats endpoint
    to fetch details about a summoner/player's ranked stats in the game League of Legends. It requires a valid API key
    provided by Riot Games for developers. The API key should be set in the variable `API_key` before calling this function.

    Parameters:
    - summonerID (str): The ID of the summoner/player for which to retrieve ranked stats.

    Returns:
    - dict: A dictionary containing various pieces of information about the summoner's ranked stats.
    The structure and content of the returned data are defined by the Riot Games API and may change over time.

    Note: - The function requires an internet connection to access the Riot Games API. - You must have a valid API
    key from Riot Games and have it assigned to the variable `API_key`. - Proper error handling for issues such as
    network errors or invalid API keys is not implemented in this basic example.
    """

    rankedSoloData = {}
    # Construct the URL for fetching ranked stats
    rankedStatsURL = f"https://euw1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summonerID}"

    # Send a GET request to the API
    response = request(rankedStatsURL, headers=requestHeaders)

    # Convert the response to JSON format
    rankedStatsData = response.json()

    for queueType in rankedStatsData:
        if queueType['queueType'] == 'RANKED_SOLO_5x5':
            rankedSoloData = queueType

    # Return the ranked stats data
    return rankedSoloData


@myLogger
def upsertSummonersRankedSoloData():
    """
    This function updates the ranked solo data for each summoner in the database.

    It first retrieves the list of summoner IDs from the database. Then, for each summoner, it fetches the ranked solo data
    and updates the corresponding record in the database.

    If the function encounters an error while connecting to the database or executing the SQL commands, it prints the error
    message. After processing all summoners, it closes the database connection.

    Raises:
        Exception: If an error occurs while connecting to the database or executing the SQL commands.
    """

    conn = None
    try:
        # Connect to the PostgreSQL database
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""SELECT "summonerID" FROM summoners;""")
        summonerList = [row[0] for row in cur.fetchall()]
        cPrintS(f'{{green}} Found {{cyan}}{len(summonerList)}{{green}} summoners in the database,'
                f' upserting ranked data...')

        # SQL for upserting the champion link to db from the dictionary
        upsert_sql = """
        UPDATE summoners
        SET "rankedSoloData" = %s
        WHERE "summonerID" = %s
        """
        for summonerID in summonerList:
            data = getSummonerRankedSoloData(summonerID)
            # Execute the upsert command for each champion
            cur.execute(upsert_sql, (json.dumps(data), summonerID))
            # Commit the changes
            conn.commit()
            cPrintS(f"{{cyan}}{getSummonerNameFromID(summonerID)} {{green}}Ranked data upserted successfully .")

    except (Exception, ps.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


@st.cache_data
@myLogger
def getSummonerRankFromDB(summonerName):
    """
    Retrieves the ranked stats of a summoner from the PostgreSQL database.

    Parameters:
    - summonerName (str): The name of the summoner/player for which to retrieve ranked stats.

    Returns:
    - dict: A dictionary containing various pieces of information about the summoner's ranked stats.
    The structure and content of the returned data are defined by the Riot Games API and may change over time.
    """

    conn = connect_db()
    cur = conn.cursor()

    # Fetch the ranked stats data from the database
    cur.execute(f"""
    select 
    concat("rankedSoloData" -> 'tier', ' ' ,  "rankedSoloData" -> 'rank')
    from summoners as s
    where name = '{summonerName}';

""")
    rankedStatsData = cur.fetchone()[0]
    rankedStatsData = rankedStatsData.replace('"', '')

    # Close the connection
    cur.close()
    conn.close()

    return rankedStatsData


@st.cache_data
@myLogger
def getThisWeekMatchIDSFromDB(summonerName):
    """
    Fetches all match IDs from the 'matches' table in the database.

    Establishes a connection to the database, retrieves all match IDs
    from the 'matches' table, closes the database connection, and returns
    a list of match IDs.

    Returns:
        list: A list of match IDs from the 'matches' table.
    """
    summonerPuuid = getDetailsFromSummonerName(summonerName)

    sql = f"""
SELECT matchID
FROM matches
WHERE datetime >= date_trunc('month', CURRENT_DATE)
  AND datetime < date_trunc('month', CURRENT_DATE) + INTERVAL '1 MONTH'
  AND (matchinfo -> 'queueId')::int = 420
  AND jsonb_path_exists(matchmetadata, '$.participants ? (@ == "{summonerPuuid}")');

    """

    conn = connect_db()
    cur = conn.cursor()
    # Fetch all match IDs
    cur.execute(sql)
    matchesList = [row[0] for row in cur.fetchall()]

    # Close the connection
    cur.close()
    conn.close()
    return matchesList


@st.cache_data
@myLogger
def getPreviousMonthMatchIDSFromDB(summonerName):
    """
    Fetches all match IDs from the 'matches' table in the database.

    Establishes a connection to the database, retrieves all match IDs
    from the 'matches' table, closes the database connection, and returns
    a list of match IDs.

    Returns:
        list: A list of match IDs from the 'matches' table.
    """
    summonerPuuid = getDetailsFromSummonerName(summonerName)

    sql = f"""
   SELECT matchID
    FROM matches
    WHERE datetime >= date_trunc('month', CURRENT_DATE - INTERVAL '1 MONTH')
  AND datetime < date_trunc('month', CURRENT_DATE)
  AND (matchinfo -> 'queueId')::int = 420
  AND jsonb_path_exists(matchmetadata, '$.participants ? (@ == "{summonerPuuid}")');
    """

    conn = connect_db()
    cur = conn.cursor()
    # Fetch all match IDs
    cur.execute(sql)
    matchesList = [row[0] for row in cur.fetchall()]

    # Close the connection
    cur.close()
    conn.close()
    return matchesList


@st.cache_data
@myLogger
def getSummonerWinLossRatioFromDB(summonerName, matchesList):
    cPrintS(f'{{green}}Found {{cyan}}{len(matchesList)}{{green}} matches for {{cyan}}{summonerName}')
    wins = 0
    losses = 0
    for match in matchesList:
        matchData = getMatchDataFromDB(match)
        knownMatchParticipants = getMatchKnownParticipantsIndex(match)
        summonerIndex = knownMatchParticipants[getDetailsFromSummonerName(summonerName)]
        if matchData['participants'][summonerIndex]['win']:
            wins += 1
        else:
            losses += 1

    return wins, losses


@st.cache_data
@myLogger
def getSummonerHoursAndGamesFromDB(summonerName, matchesList):
    cPrintS(f'{{green}}Found {{cyan}}{len(matchesList)}{{green}} matches for {{cyan}}{summonerName}')
    hoursPlayedInSeconds = 0
    for match in matchesList:
        matchData = getMatchDataFromDB(match)
        matchDuration = matchData['matchinfo']['gameDuration']
        hoursPlayedInSeconds += matchDuration
    hoursPlayed = int(hoursPlayedInSeconds / 3600)
    minutesPlayed = ((hoursPlayedInSeconds / 3600) - hoursPlayed) * 60
    return hoursPlayed, round(minutesPlayed), len(matchesList)


@st.cache_data
@myLogger
def getChampionPoolDiversityAndFavoriteChampionFromDB(summonerName, matchesList):
    cPrintS(
        f'{{green}}Found {{cyan}}{len(matchesList)}{{green}} matches this week for {{cyan}}{summonerName}')
    championPool = {}
    for match in matchesList:
        matchData = getMatchDataFromDB(match)
        knownMatchParticipants = getMatchKnownParticipantsIndex(match)
        summonerIndex = knownMatchParticipants[getDetailsFromSummonerName(summonerName)]
        championName = matchData['participants'][summonerIndex]['championName']
        if championName in championPool:
            championPool[championName] += 1
        else:
            championPool[championName] = 1

    if championPool:
        mostPlayedChampion = max(championPool, key=championPool.get)
        mostPlayedTimes = championPool[mostPlayedChampion]
        if mostPlayedTimes == 1:
            mostPlayedChampion = None
    else:
        # Handles the case where no matches were found or no champions were played
        mostPlayedChampion = None
        mostPlayedTimes = 0

    return mostPlayedChampion, mostPlayedTimes, championPool


@st.cache_data
@myLogger
def getBestGameFromDB(summonerName, matchesList):
    cPrintS(f'{{green}}Found {{cyan}}{len(matchesList)}{{green}} matches for {{cyan}}{summonerName}')
    bestGame = None
    bestGameKDA = 0
    for match in matchesList:
        matchData = getMatchDataFromDB(match)
        knownMatchParticipants = getMatchKnownParticipantsIndex(match)
        summonerIndex = knownMatchParticipants[getDetailsFromSummonerName(summonerName)]
        assists = matchData['participants'][summonerIndex]['assists']
        kills = matchData['participants'][summonerIndex]['kills']
        deaths = matchData['participants'][summonerIndex]['deaths']
        champion = matchData['participants'][summonerIndex]['championName']
        if deaths == 0:
            kda = assists + kills
        else:
            kda = (assists + kills) / deaths
        if kda > bestGameKDA:
            bestGameKDA = kda
            bestGame = match
        return bestGame, champion, kills, deaths, assists
