import pandas as pd

REQUIRED_COLUMNS = {"date", "campaign", "impressions", "clicks", "spend", "leads"}


def validate_csv(df: pd.DataFrame) -> tuple[bool, str]:
    try:
        if df is None:
            return False, "No data provided"
        if df.empty:
            return False, "Uploaded file is empty."
        missing = REQUIRED_COLUMNS - set(df.columns.str.lower())
        if missing:
            return False, f"Missing columns: {', '.join(missing)}"
        return True, "OK"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def sanitize(df: pd.DataFrame) -> pd.DataFrame:
    try:
        df = df.copy()
        df.columns = df.columns.str.lower().str.strip()
        numeric_cols = ["impressions", "clicks", "spend", "leads"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        return df
    except Exception as e:
        raise ValueError(f"Error sanitizing data: {str(e)}")
