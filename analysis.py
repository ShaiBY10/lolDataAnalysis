import pandas as pd

from sql import getSummonerMatchDataFromDB


def createMatchAnalysis(matchID):
    """
    A function that creates match analysis by retrieving summoner match data from the database for a given match ID.

    Parameters:
    matchID (int): The ID of the match for which match analysis is being generated.

    Returns:
    pandas.DataFrame: The concatenated DataFrame containing the match analysis data.
    """

    dfs = []
    for i in range(10): # from 0 to 9 based on the api response
        dfs.append(getSummonerMatchDataFromDB(matchID,i))

    df = pd.concat(dfs, ignore_index=True)
    return df


def createCorrelationMatricesFromList(matchList):
    """
    Generate correlation matrices for each match in the matchList and create a DataFrame with match_id and correlation_matrix.

    Parameters:
    matchList (list): List of match data.

    Returns:
    pd.DataFrame: DataFrame with match_id and correlation_matrix cols.
    """

    match_correlation_data = []

    for match in matchList:
        # Create match analysis DataFrame
        print(f"Creating match analysis for match: {match}")
        df = createMatchAnalysis(match)

        # Select numeric columns
        print(f"Selecting numeric columns for match: {match}")
        df_numeric = df.select_dtypes(include=[int, float])

        # Calculate correlation matrix
        print(f"Calculating correlation matrix for match: {match}")
        correlation_matrix = df_numeric.corr(method='pearson').round(3)

        # Append match_id and correlation_matrix to the list
        match_correlation_data.append({'match_id': match, 'correlation_matrix': correlation_matrix})

    result_df = pd.DataFrame(match_correlation_data)
    result_df['match_id'] = result_df['match_id'].astype(str)  # Ensure match_id is string type

    return result_df






