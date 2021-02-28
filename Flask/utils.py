# utils.py
# These functions help process and visualize data
# Taken from https://github.com/aws-samples/aws-iot-office-sensor for the most part

from bokeh.models.sources import ColumnDataSource
from bokeh.plotting import figure
import pandas as pd


def history(dynamodb_client, table_name, metric, i, interval=25):
    """
    Returns an event's history (items in a DynamoDB table) as a DataFrame
    :param dynamodb_client: Connection to DynamoDB service
    :param table_name: Name of DynamoDB table (string)
    :param metric: Name of metric subtopic (string)
    :param i: ID of message payload (integer)
    :param interval: Interval of history (integer)
    :return: A DataFrame
    """
    records = []
    if i > interval:
        floor = i - interval
    else:
        floor = 0
    response = dynamodb_client.query(TableName=table_name, KeyConditionExpression="Metric = :metric",
                                     ExpressionAttributeValues={":metric": {"S": metric}})
    for n in range(0, response['Count'] - 1):
        record = response['Items'][n]['payload']['M']
        new_record = {}
        for key in record.keys():
            for dt in record[key]:
                new_record[key] = record[key][dt]
        records.append(new_record)
    metric_df = pd.DataFrame(records, dtype=float)
    return metric_df


def calculate_mas(metric, data, window):
    """
    Returns moving average metrics across specified interval for records of data
    :param metric: Metric of interest (string)
    :param data: Metric's DataFrame
    :param window: The sliding interval (integer)
    :return: A DataFrame
    """
    timestamp = data['Timestamp']
    obs = data[metric]
    mean = obs.rolling(window).mean()
    std = obs.rolling(window).std()
    var = obs.rolling(window).var()
    for i in range(0, window):
        if i < window:
            try:
                mean[i] = obs[0:i + 2].mean()
                std[i] = obs[0:i + 2].std()
                var[i] = obs[0:i + 2].var()
            except TypeError:
                continue
    diff_m = obs - mean
    metric_stats = pd.DataFrame.from_dict(
        {'obs': obs, 'mav': mean, 'diff_m': diff_m, 'mstd': std, 'mvar': var, 'timestamp': timestamp})
    metric_stats['timestamp'] = pd.to_datetime(metric_stats['timestamp'])
    return metric_stats


def plot_data(data, title, x_label, y_label):
    """
    Plots statistics
    :param data: The data
    :param title: Title of the graph (string)
    :param x_label: X-axis label (string)
    :param y_label: Y-axis label (string)
    :param width: Width of table (integer)
    :param height: Height of table (integer)
    :return: Bokeh Figure object
    """
    data['alpha1'] = data['mav'] + (2 * data['mstd'])
    data['alpha2'] = data['mav'] - (2 * data['mstd'])
    y_range = [min(data['mav']) - (5 * data['obs'].std()), max(data['mav']) + (5 * data['obs'].std())]
    source = ColumnDataSource(data)
    p = figure(title=title, x_axis_label=x_label, y_axis_label=y_label, plot_width=1200, plot_height=600,
               x_axis_type='datetime', y_range=y_range)
    p.circle(x='timestamp', y='obs', source=source, size=5, legend="Observation")
    p.line(x='timestamp', y='mav', source=source, line_width=1, color="#800080", legend="Moving Average")
    p.line(x='timestamp', y='alpha1', source=source, line_width=2, color="#FF0000", line_dash="dashed",
           legend="95% Confidence Interval")
    p.line(x='timestamp', y='alpha2', source=source, line_width=2, color="#FF0000", line_dash="dashed")
    p.legend.label_text_font_size = "8px"
    return p