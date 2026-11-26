"""Catalog lookup and data-availability helpers. Read-only, no API credentials."""
import re
import unicodedata
import pandas as pd

CATALOG_SOURCE="ssi_fastconnect_v3"

def search_key(value):
    value=str(value or "").casefold().replace("đ","d")
    return " ".join("".join(c for c in unicodedata.normalize("NFKD",value)
                            if not unicodedata.combining(c)).split())

def stock_catalog(catalog=None, books=None, equity_only=False):
    """Prefer official catalog. Book-only tickers remain clearly labelled."""
    cols=["symbol","name","board","lotSize","stockType","catalog_source"]
    rows=[]
    if catalog is not None:
        if not {"symbol","board","source"}.issubset(catalog.columns) or set(catalog.source)!={CATALOG_SOURCE}:
            raise ValueError("Danh sách mã không đúng nguồn SSI FastConnect V3")
        if equity_only:
            from src.data.equity_universe import equity_catalog
            catalog=equity_catalog(catalog)
        for r in catalog.to_dict("records"):
            sym=str(r.get("symbol","")).strip().upper()
            if not re.fullmatch(r"[A-Z0-9]{1,12}",sym):continue
            rows.append(dict(symbol=sym,name=r.get("name"),board=r.get("board"),
                             lotSize=r.get("lotSize"),stockType=r.get("stockType"),
                             catalog_source=CATALOG_SOURCE))
    d=pd.DataFrame(rows,columns=cols)
    # Symbols that map to multiple boards are ambiguous; do not guess which security.
    if not d.empty:
        d=d.drop_duplicates(["symbol","board"])
        ambiguous=set(d.loc[d.symbol.duplicated(keep=False),"symbol"])
        d=d[~d.symbol.isin(ambiguous)]
    else:ambiguous=set()
    if books is not None and "symbol" in books and not equity_only:
        extra=set(books.symbol.dropna().astype(str))-set(d.symbol)-ambiguous
        if extra:
            fallback=pd.DataFrame([dict(symbol=s,name="",board="Chưa rõ",
                lotSize=None,stockType=None,catalog_source="saved_book") for s in sorted(extra)
                if re.fullmatch(r"[A-Z0-9]{1,12}",s)],columns=cols)
            d=pd.concat([d,fallback],ignore_index=True)
    for col in ("name","board","stockType"):
        d[col]=d[col].fillna("").astype(str)
    d["board"]=d.board.replace("","Chưa rõ")
    return d.sort_values("symbol").reset_index(drop=True)

def search_stocks(catalog, query="", board=None, exclude=(), limit=30):
    """Accent-insensitive name or ticker search, exact/prefix tickers first."""
    q=search_key(query)
    d=catalog[~catalog.symbol.isin(set(exclude))].copy()
    if board and board!="Tất cả":d=d[d.board==board]
    if q:
        ticker=d.symbol.map(search_key); names=d.name.map(search_key)
        mask=ticker.str.contains(q,regex=False)|names.str.contains(q,regex=False)
        d=d.loc[mask].copy()
        ticker=ticker.loc[mask]
        d["_rank"]=3
        d.loc[ticker.str.contains(q,regex=False),"_rank"]=2
        d.loc[ticker.str.startswith(q),"_rank"]=1
        d.loc[ticker.eq(q),"_rank"]=0
        d=d.sort_values(["_rank","symbol"]).drop(columns="_rank")
    else:d=d.sort_values("symbol")
    return d.head(limit)

def known_nonstandard_lots(catalog, symbols):
    d=catalog[catalog.symbol.isin(symbols)]
    lots=pd.to_numeric(d.lotSize,errors="coerce")
    return sorted(d.loc[lots.notna() & lots.ne(100),"symbol"])
