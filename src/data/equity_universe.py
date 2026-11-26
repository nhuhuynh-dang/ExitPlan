"""Conservative common-stock universe shared by SSI readers.
SSI documents stockType as optional but does not publish a complete code map.
Unknown type codes are NOT guessed; fallback is a 3-character ticker and
non-fund/non-warrant name, with no contradictory instrument metadata.
Keep raw catalog intact and label fallback as candidate, not verified type.
"""
import re
import unicodedata
import pandas as pd

BOARDS={"HOSE","HNX","UPCOM"}
def normalized(value):
    if value is None or pd.isna(value):return ""
    return " ".join("".join(c for c in unicodedata.normalize("NFKD",str(value).casefold().replace("đ","d"))
                             if not unicodedata.combining(c)).split())

def classification(row):
    symbol=str(row.get("symbol","")).strip().upper()
    board=str(row.get("board","")).strip().upper()
    if board not in BOARDS:return "excluded"
    name=normalized(row.get("name"))
    en=normalized(row.get("nameEn"))
    typ=normalized(row.get("stockType")).replace("_"," ").replace("-"," ")
    text=" ".join((name,en,typ))
    if re.search(r"\b(chung quyen|covered warrant|warrant|chung chi quy|etf|fund certificate|trai phieu|bond|phai sinh|futures|co phieu uu dai|preferred stock|preference share)\b",text):
        return "excluded"
    if typ in {"cw","w","fund","derivative","option"} or re.match(r"^(quy dau tu|quy mo|quy dong|quy hoan doi|investment fund|mutual fund)\b",name):
        return "excluded"
    if normalized(row.get("cwUnderlyingSymbol")) not in {"","0","-","n/a","null","none"}:
        return "excluded"
    for key in ("cwExercisePrice","cwExecutionRatio","iNav","openInterest","settlementPrice"):
        val=normalized(row.get(key))
        if val not in {"","-","n/a","null","none"}:
            try:
                if float(val.replace(",",""))!=0:return "excluded"
            except ValueError:
                # Nonempty ratio, e.g. 2:1, is also evidence of a warrant.
                return "excluded"
    maturity=normalized(row.get("maturityDate"))
    if maturity not in {"","0","-","n/a","null","none","0000-00-00","0000/00/00","0001-01-01","0001/01/01"}:
        return "excluded"
    lot=pd.to_numeric(pd.Series([row.get("lotSize")]),errors="coerce").iloc[0]
    if pd.notna(lot) and lot!=100:return "excluded"
    # Conservative Vietnamese common-share ticker convention (includes A32).
    # This is not an exhaustive security-type classification.
    if not re.fullmatch(r"[A-Z0-9]{3}",symbol):return "excluded"
    if typ in {"common stock","common share","common shares","ordinary share","ordinary shares","ordinary stock","co phieu pho thong"}:
        return "common_stock_explicit"
    if not name and not en:return "unclassified"
    return "stock_candidate"

def equity_catalog(catalog):
    if not {"symbol","board","source"}.issubset(catalog.columns) or (not catalog.empty and set(catalog.source)!={"ssi_fastconnect_v3"}):
        raise ValueError("Danh mục SSI không hợp lệ")
    d=catalog.copy()
    d["equity_class"]=[classification(r) for r in d.to_dict("records")]
    # Refuse ambiguous cross-board mappings even if one row would be eligible.
    ambiguous=d.groupby("symbol")["board"].nunique()
    d=d[~d.symbol.isin(ambiguous[ambiguous>1].index)]
    return d[d.equity_class.isin(["common_stock_explicit","stock_candidate"])].drop_duplicates("symbol").copy()

def equity_symbols(catalog,boards=None):
    d=equity_catalog(catalog)
    if boards:d=d[d.board.isin(boards)]
    return sorted(set(d.symbol))
