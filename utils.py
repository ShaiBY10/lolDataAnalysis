import json
import sys
import time
from datetime import datetime

selenia = 'Seleniá'


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
        "white": "97"
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


def getDataFromConfig(file='config.json', key=None):
    """
    Retrieve data from the specified configuration file based on the provided key.

    :param file: The path to the configuration file (default is 'config.json')
    :param key: The key for the value to retrieve from the configuration file
    :type file: str
    :type key: str
    :return: The value corresponding to the provided key in the configuration file
    :rtype: any
    """

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
        404: "404 Data Not Found - The requested resource could not be found but may be available in the future.",
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


def timestampToDate(mili_timestamp, timezone='UTC'):
    """
    Convert a Unix timestamp in milliseconds to a readable date in UTC timezone.

    Parameters:
    - timestamp_millis: Unix timestamp in milliseconds (int or float)

    Returns:
    - A string representing the date and time in the format 'YYYY-MM-DD HH:MM:SS'
    """
    # Convert the timestamp from milliseconds to seconds
    timestamp_seconds = mili_timestamp / 1000

    # Convert the timestamp to a datetime object
    dt_object = datetime.utcfromtimestamp(timestamp_seconds)

    # Return the datetime object in the specified format
    return dt_object.strftime('%Y-%m-%d %H:%M:%S')


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
        print(f'Missing Matches:{missing_matches}, \n length of missingMatchesList is {len(missing_matches)}')
        return missing_matches
    elif len(DB_list) == 0:
        cPrint('DB is empty, skipping findMissingMatches Function', 'yellow')