import plotly.express as px
import plotly.figure_factory as ff
import streamlit as st

from analysis import createMatchAnalysis


@st.cache_data
def createCorrelationHeatmap(df, title='Correlation Heatmap'):
    """
    Generate a correlation heatmap plot using Plotly based on the input DataFrame.

    Parameters:
    df (DataFrame): The input DataFrame containing numeric columns for correlation analysis.

    Returns:
    fig (plotly.graph_objs.Figure): The correlation heatmap plot generated using Plotly.
    correlation_matrix (DataFrame): The correlation matrix calculated from the input DataFrame.
    """

    df_numeric = df.select_dtypes(include=[int, float])  # Select numeric columns

    # Calculate correlation matrix using pandas methods
    correlation_matrix = df_numeric.corr(method='pearson')  # Specify Pearson correlation

    fig = ff.create_annotated_heatmap(
        z=correlation_matrix.values.tolist(),  # Convert to list for Plotly
        x=correlation_matrix.columns.tolist(),
        y=correlation_matrix.columns.tolist(),
        annotation_text=correlation_matrix.round(2).astype(str).values.tolist(),
        colorscale='RdYlBu',
        showscale=True
    )

    fig.update_layout(
        title_text=f'{title}',
        title_x=0.35,
        title_y=1,
        xaxis_tickmode='linear',
        yaxis_tickmode='linear',
        width=1000,
        height=700,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12)  # Set font size for all text elements
    )

    # Handle NaN values in annotations (assuming 'nan' string)
    for annotation in fig['layout']['annotations']:
        if annotation['text'] == 'nan':
            annotation['text'] = ''
        annotation['font']['color'] = 'black'

    return fig, correlation_matrix


@st.cache_data
def plotCorrelationHeatmap(matchID,title=None):
    df = createMatchAnalysis(matchID)
    correlationTable, correlationMatrix = createCorrelationHeatmap(df, title)
    st.plotly_chart(correlationTable)
    return df


def plotScatter(df, x_col, y_col):
    fig = px.scatter(df, x=x_col, y=y_col, title=f'Scatter Plot of {x_col} vs. {y_col}')
    return fig
