import pandas as pd

def calculate_delays(df):
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["eta"] = pd.to_datetime(df["eta"])
    df["delay_minutes"] = (df["timestamp"] - df["eta"]).dt.total_seconds() / 60
    return df
