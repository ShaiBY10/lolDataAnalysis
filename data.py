from utils import countdown, explainStatus, cPrint, cPrintS, getDataFromConfig

selenia = 'Seleniá'
API_KEY = getDataFromConfig(key='API')['KEY']

requestHeaders = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 "
                  "Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com",
    "X-Riot-Token": API_KEY
}


def request(url, headers=None, params=None):
    """
    A function to make a request to a URL with optional headers and parameters.

    Parameters:
    url (str): The URL to make the request to.
    headers (dict, optional): The headers to include in the request. Defaults to None.
    params (dict, optional): The parameters to include in the request. Defaults to None.

    Returns:
    The response object if the status code is 200, the status code if 429 or 404, and the status code with explanation for all other cases.
    """

    if headers is None:
        headers = requestHeaders
    response = request(url, headers=headers, params=params)

    if response.status_code == 200:
        return response

    elif response.status_code == 429:
        cPrint('Function request hit the rate limit', 'red')
        return response.status_code

    elif response.status_code == 404:
        cPrint(explainStatus(response.status_code), 'yellow')
        return response.status_code

    else:
        cPrint(explainStatus(response.status_code), 'red')
        return response.status_code


def getLatestVersion():
    """
    This function fetches the latest version of league of legends game
    """

    # API url from where to fetch versions
    versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"

    # Make a GET request to the versions API
    response = request(versions_url)

    # Convert the response to JSON format
    versions = response.json()

    # Return the first version in the list as it is the latest
    return versions[0]


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
    response = request(rotationsURL)

    # Convert the response to JSON
    freeChampionsData = response.json()

    # Get the list of free champion IDs from the response data
    freeChampions = freeChampionsData['freeChampionIds']

    # Return the list of free champion IDs
    return freeChampions


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


def getAllSummonerMatches(puuid, region='europe', start=0, count=100):
    """
    Retrieves matches for a summoner identified by their PUUID.

    Args:
        puuid (str): The PUUID of the summoner.
        region (str): The region where the summoner plays. Defaults to 'europe'.
        start (int): The starting index for fetching matches. Defaults to 0.
        count (int): The number of matches to fetch in each batch. Defaults to 100.

    Returns:
        list: A list of match data for the summoner.
    """

    # Construct the URL for fetching matches
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"

    matches = []  # List to store the match data

    while True:
        params = {"start": start, "count": count}
        response = request(url, params=params)  # Make a request to the API

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
        elif response.status_code == 429:
            # Rate limit hit, wait and try again
            cPrint('Requesting match data hit the rate limit, sleeping and trying again...', 'yellow')
            countdown(60)  # Wait for the rate limit to reset
            continue  # Retry the same request without moving to the next batch
        else:
            # Handle other HTTP Errors
            cPrint(f'HTTP Error {response.status_code}: {response.text}', 'red')
    return matches


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


def getMatchData(matchID):
    """
    Retrieve match data from the Riot Games API using the provided match ID.

    Args:
        matchID (str): The ID of the match to retrieve data for.

    Returns:
        dict or str or int: The match data if the request is successful, 'limit' if the rate limit is hit, or the HTTP status code if there is an error.
    """
    url = f'https://europe.api.riotgames.com/lol/match/v5/matches/{matchID}'
    response = request(url)
    return response.json()
