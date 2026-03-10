import pandas as pd
from typing import Optional, Dict, Any, List

from src.utils.schema import DBSchema


class ExcelDestinationsDB:
    """Simple wrapper around an Excel file storing destination data."""

    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.df = self._load()

    def _load(self) -> pd.DataFrame:
        """Load the Excel file into a pandas DataFrame."""

        try:
            df = pd.read_excel(self.excel_path)
            return df
        except Exception as e:
            raise RuntimeError(
                f"Failed to load Excel database at '{self.excel_path}'. "
                "Application cannot start without the destinations database."
            ) from e

    def list_destinations(self) -> List[str]:
        """Return all available destination names."""

        if DBSchema.DESTINATION not in self.df.columns:
            return []
        return self.df[DBSchema.DESTINATION].dropna().tolist()

    def get_destination(self, destination: str) -> Optional[Dict[str, Any]]:
        """Retrieve a destination row by name."""

        if not destination:
            return None
        key = destination.strip().lower()
        row = self.df[self.df[DBSchema.DESTINATION].str.lower() == key]
        if row.empty:
            return None
        r = row.iloc[0].to_dict()
        return r

    def search_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """Search destinations whose keywords contain the given term."""

        if not keyword:
            return []
        k = keyword.strip().lower()
        hits = self.df[self.df[DBSchema.KEYWORDS].str.lower().str.contains(k, na=False)]
        out = []
        for _, row in hits.iterrows():
            r = row.to_dict()
            out.append(r)
        return out

    def recommend_by_season(self, season_query: str) -> List[Dict[str, Any]]:
        """Return destinations matching a seasonal query."""

        if not season_query:
            return []
        s = season_query.strip().lower()
        hits = self.df[
            self.df[DBSchema.BEST_SEASON]
            .astype(str)
            .str.lower()
            .str.contains(s, na=False)
        ]
        out = []
        for _, row in hits.iterrows():
            r = row.to_dict()
            out.append(r)
        return out
