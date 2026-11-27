"""Read-only preflight checks; same lot, visible-depth and fee rules as MILP."""
import pandas as pd
from src.finance.engine import LOT, quote_from_row, sell_preview


def eligible_books(books):
    """Keep only usable recorded rows, preserving exact snapshot timestamps."""
    if books is None or books.empty:
        return books
    rows=books.drop_duplicates(['ts_vn','symbol'],keep='last').reset_index(drop=True)
    valid=[]
    for i,row in rows.iterrows():
        try:
            lot=pd.to_numeric(row.get('lotSize'),errors='coerce')
            if pd.notna(lot) and lot!=LOT:
                continue
            if quote_from_row(row).bids:
                valid.append(i)
        except (ValueError,TypeError,KeyError,OverflowError):
            continue
    return rows.loc[valid].copy()


def compatible_symbols(books, holdings):
    """Candidates sharing at least one exact recorded timestamp with all holdings."""
    if books is None or books.empty:
        return set()
    chosen=set(holdings)
    if not chosen:
        return set(books.symbol)
    counts=books[books.symbol.isin(chosen)].groupby('ts_vn').symbol.nunique()
    common=counts[counts==len(chosen)].index
    return set(books.loc[books.ts_vn.isin(common),'symbol'])-chosen


def liquidation_capacity(holdings, quotes, fee, tax, lot=LOT):
    """Maximum net proceeds across independent visible-depth lot constraints."""
    value=0.; net=0.; shares=0
    for symbol,held in holdings.items():
        q=quotes[symbol]
        depth=sum(v for _,v in q.bids)
        qty=min(int(held)//lot,int(depth)//lot)*lot
        value+=held*q.last
        net+=sell_preview(q,qty,fee,tax)['net']
        shares+=qty
    return dict(value=value,max_net=net,sellable_shares=shares)
