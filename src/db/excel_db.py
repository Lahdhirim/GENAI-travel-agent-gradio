import pandas as pd
from typing import Optional, Dict, Any, List


class ExcelDestinationsDB:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.df = self._load()

    def _load(self) -> pd.DataFrame:
        df = pd.read_excel(self.excel_path)
        return df

    def list_destinations(self) -> List[str]:
        if "destination" not in self.df.columns:
            return []
        return self.df["destination"].dropna().tolist()

    def get_destination(self, destination: str) -> Optional[Dict[str, Any]]:
        if not destination:
            return None
        key = destination.strip().lower()
        row = self.df[self.df["destination"].str.lower() == key]
        if row.empty:
            return None
        r = row.iloc[0].to_dict()
        return r

    def search_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        if not keyword:
            return []
        k = keyword.strip().lower()
        hits = self.df[self.df["keywords"].str.lower().str.contains(k, na=False)]
        out = []
        for _, row in hits.iterrows():
            r = row.to_dict()
            out.append(r)
        return out

    def recommend_by_season(self, season_query: str) -> List[Dict[str, Any]]:
        if not season_query:
            return []
        s = season_query.strip().lower()
        hits = self.df[
            self.df["best_season"].astype(str).str.lower().str.contains(s, na=False)
        ]
        out = []
        for _, row in hits.iterrows():
            r = row.to_dict()
            out.append(r)
        return out
