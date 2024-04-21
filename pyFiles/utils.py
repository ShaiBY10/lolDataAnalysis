import json
import sys
import time
from datetime import datetime
from functools import wraps

import pytz

selenia = 'Seleniá'


def myLogger(func):
    """Decorator to log function name on execution"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        now = datetime.now()
        localTimezone = now.astimezone()
        formattedDatetime = localTimezone.strftime("%Y-%m-%d %H:%M:%S")

        # logging.info(f"Executing function: {func.__name__}")
        cPrintS(f"{{yellow}}{formattedDatetime} || {{magenta}}Executing function: {{cyan}}{func.__name__}")
        return func(*args, **kwargs)

    return wrapper


def cPrint(text, color_name):
    """
    Prints the given text in the terminal with the specified color.

    Args:
    text (str): The text to print.
    color_name (str): The name of the color to use.

    Returns:
    None
    """
    color_codes = {
        "red": "91",
        "green": "92",
        "yellow": "93",
        "blue": "94",
        "magenta": "95",
        "cyan": "96",
        "white": "97"
    }
    color_code = color_codes.get(color_name.lower(), "97")  # Default to white if color not found
    print(f"\033[{color_code}m{text}\033[0m")


def cPrintS(text):
    """
    Prints text with inline color specifications.

    Args:
    text (str): The text to print, with inline markers for color changes.

    Color markers should be in the format {color_name}, e.g., {red} for red text.
    The color name should be one of the predefined colors. Text following
    the marker will be printed in the specified color until another marker is encountered.

    Returns:
    None
    """
    color_codes = {
        "red": "91",
        "green": "92",
        "yellow": "93",
        "blue": "94",
        "magenta": "95",
        "cyan": "96",
        "white": "97",
        "bgred": "101",  # red background
        "bggreen": "102",  # green background
        "bgyellow": "103",  # yellow background
        "bgblue": "104",  # blue background
        "bgmagenta": "105",  # magenta background
        "bgcyan": "106",  # cyan background
        "bgwhite": "107",  # white background
        "bgreset": "49"  # reset background
    }

    # Split the text into parts based on color markers
    parts = text.split("{")
    # Initialize final text
    final_text = ""

    for part in parts:
        if "}" in part:
            color_name, text_segment = part.split("}", 1)
            color_code = color_codes.get(color_name.lower(), "97")  # Default to white if color not found
            final_text += f"\033[{color_code}m{text_segment}"
        else:
            final_text += part

    # Reset color to default at the end
    final_text += "\033[0m"

    print(final_text)


#@myLogger
def getDataFromConfig(file='../config/config.json', key=None):
    """
    Retrieve data from the specified configuration file based on the provided key.

    :param file: The path to the configuration file (default is 'config.json')
    :param key: The key for the value to retrieve from the configuration file
    :return: The value corresponding to the provided key in the configuration file
    :rtype: any
    """
    if not key:
        with open(file, 'r') as f:
            config = json.load(f)
        return config

    with open(file, 'r') as f:
        config = json.load(f)
    value = config[key]
    return value


def coloredBar(percentage):
    """
    A function that generates a colored progress bar based on the completion percentage.

    Parameters:
    - percentage (int): The completion percentage of the progress bar.

    Returns:
    - bar (str): A string representing the colored progress bar.
    """

    bar_length = 50  # Length of the progress bar
    filled_length = int(bar_length * percentage // 100)

    # ANSI escape codes for colors
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RESET = '\033[0m'

    # Change color based on completion percentage
    if percentage < 33:
        color = RED
    elif percentage < 66:
        color = YELLOW
    else:
        color = GREEN

    bar = color + '▓' * filled_length + '░' * (bar_length - filled_length) + RESET
    return bar


#@myLogger
def countdown(secs):
    """
    A function that performs a countdown for the given number of seconds.

    :param secs: An integer representing the total number of seconds to count down.
    :return: None
    """

    total = secs
    while secs >= 0:
        pct_complete = 100 * (total - secs) / total
        bar = coloredBar(pct_complete)

        mins, secs_remaining = divmod(secs, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, secs_remaining)
        sys.stdout.write(f'\r<<< Sleeping to avoid rate limits... |{bar}| {timeformat} >>> ')
        sys.stdout.flush()

        time.sleep(1)
        secs -= 1

    cPrint("\n<<< Im up, Let's keep going >>>", 'green')


#@myLogger
def saveOutput(data, fileName='output.json'):
    """
    This function saves the given data to a file in JSON format.

    Args:
        data: The data to be saved.
        fileName: The name of the file to save the data to (default is 'output.json').

    Returns:
        None
    """

    with open(fileName, 'w') as file:
        json.dump(data, file)


#@myLogger
def saveDataFrameToCSV(df, fileName='df.csv'):
    """
    Save the given DataFrame to a CSV file.

    Parameters:
    df (DataFrame): The DataFrame to be saved.
    fileName (str): The name of the CSV file. Default is 'df.csv'.

    Returns:
    None
    """

    df.to_csv(fileName, index=False)


#@myLogger
def explainStatus(status_code):
    """
    Return an explanation for a given HTTP status code.

    :param status_code: The HTTP status code to explain.
    :return: A string with the explanation of the status code.
    """
    status_explanations = {
        400: "400 Bad Request - The request cannot be processed by the server due to a client error (e.g., malformed "
             "request syntax).",
        401: "401 Unauthorized - Authentication is required and has failed or has not yet been provided.",
        403: "403 Forbidden - The server understood the request but refuses to authorize it.",
        404: "404 Data Not Found - The requested resource could not be foundd.",
        405: "405 Method Not Allowed - A request method is not supported for the requested resource.",
        415: "415 Unsupported Media Type - The request entity has a media type which the server or resource does not "
             "support.",
        429: "429 Rate Limit Exceeded - The user has sent too many requests in a given amount of time.",
        500: "500 Internal Server Error - A generic error message, given when an unexpected condition was encountered.",
        502: "502 Bad Gateway - The server was acting as a gateway or proxy and received an invalid response from the "
             "upstream server.",
        503: "503 Service Unavailable - The server is currently unable to handle the request due to a temporary "
             "overload or maintenance.",
        504: "504 Gateway Timeout - The server was acting as a gateway or proxy and did not receive a timely response "
             "from the upstream server."
    }

    return status_explanations.get(status_code, "Unknown HTTP Status Code")


#@myLogger
def timestampToDate(mili_timestamp, timezone='UTC', convert=False):
    """
    Convert a Unix timestamp in milliseconds to a readable date. If 'convert' is True,
    the date is initially in UTC timezone and then converted to the 'Israel' timezone.
    Otherwise, the date remains in UTC.

    Parameters:
    - mili_timestamp: Unix timestamp in milliseconds (int or float)
    - convert (bool): Whether to convert the datetime to the 'Israel' timezone (default is False)

    Returns:
    - A string representing the date and time, in the format 'YYYY-MM-DD HH:MM:SS'. The timezone
      will be 'Israel' if 'convert' is True, otherwise UTC.
    """
    # Convert the timestamp from milliseconds to seconds
    timestamp_seconds = mili_timestamp / 1000

    # Convert the timestamp to a UTC datetime object
    utc_dt_object = datetime.utcfromtimestamp(timestamp_seconds).replace(tzinfo=pytz.utc)

    if convert:
        # Define the target timezone: 'Israel'
        target_timezone = pytz.timezone('Asia/Jerusalem')

        # Convert the UTC datetime object to the target timezone ('Israel')
        dt_object = utc_dt_object.astimezone(target_timezone)
    else:
        # Keep the datetime object in UTC
        dt_object = utc_dt_object

    # Return the datetime object, formatted as a string
    return dt_object.strftime('%Y-%m-%d %H:%M:%S')


#@myLogger
def findMissingMatches(DB_list, NewList):
    """
    A function to find missing matches between two lists.
    Parameters:
        - DB_list: a list representing the database list
        - NewList: a list representing the new list to compare with the database list
    Returns:
        - A list of items in NewList that are not present in DB_list
    """

    if len(DB_list) > 0:
        # Use set difference to find items in new_list not in table_list
        missing_matches = list(set(NewList) - set(DB_list))
        cPrintS(
            f'{{blue}}Missing Matches:{{cyan}}{missing_matches}, \n{{blue}}length of missingMatchesList is {{cyan}}{len(missing_matches)}')
        return missing_matches
    elif len(DB_list) == 0:
        cPrint('DB is empty, skipping findMissingMatches Function', 'yellow')
        return NewList


#@myLogger
def getDetailsFromSummonerName(summonerName, detail='puuid'):
    """
    Returns the PUUID for a given summoner name based on the provided configuration.

    Parameters:
    summoner_name (str): The name of the summoner.

    Returns:
    str: The PUUID of the summoner, or None if not found.
    """
    # Access the 'SummonerData' from the config
    config = getDataFromConfig()
    summoner_data = config.get('SummonerData', {})

    # Attempt to get the summoner details by name, return the PUUID if found
    summoner_details = summoner_data.get(summonerName)
    if summoner_details:
        return summoner_details.get(detail)

    # Return None if the summoner name is not found
    return None


#@myLogger
def getSummonerNameFromID(summonerID):
    # Access the 'SummonerData' from the config
    config = getDataFromConfig()
    for summoner, data in config['SummonerData'].items():
        if data['summonerID'] == summonerID:
            return data['summonerName']

    # Return None if the summoner name is not found
    return None


#@myLogger
def getSummonerNameFromPuuid(puuid):
    # Access the 'SummonerData' from the config
    config = getDataFromConfig()
    for summoner, data in config['SummonerData'].items():
        if data['puuid'] == puuid:
            return data['summonerName']

    # Return None if the summoner name is not found
    return None
