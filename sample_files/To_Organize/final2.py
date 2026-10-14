import pandas as pd

def clean(df):
    df = df.dropna()
    df.columns = [c.strip().lower() for c in df.columns]
    return df.drop_duplicates()
