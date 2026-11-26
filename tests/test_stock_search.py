"""Offline tests of market search and draft portfolio eligibility."""
import pandas as pd
import pytest
from src.data.stock_search import stock_catalog,search_stocks,known_nonstandard_lots

@pytest.fixture
def catalog():
    return pd.DataFrame([
        dict(symbol="HPG",name="Tập đoàn Hòa Phát",board="HOSE",lotSize=100,source="ssi_fastconnect_v3"),
        dict(symbol="FPT",name="Công ty FPT",board="HOSE",lotSize="100",source="ssi_fastconnect_v3"),
        dict(symbol="SHS",name="Chứng khoán Sài Gòn Hà Nội",board="HNX",lotSize=100,source="ssi_fastconnect_v3"),
        dict(symbol="ACV",name="Cảng hàng không Việt Nam",board="UPCOM",lotSize=None,source="ssi_fastconnect_v3"),
        dict(symbol="OTHER",name="Loại khác",board="HOSE",lotSize=10,source="ssi_fastconnect_v3"),
    ])

def test_search_without_book_data(catalog):
    d=stock_catalog(catalog,None)
    assert len(d)==5
    assert search_stocks(d,"HPG").symbol.tolist()==["HPG"]
    assert search_stocks(d,"hoa phat").symbol.tolist()==["HPG"]
    assert search_stocks(d,"TẬP ĐOÀN").symbol.tolist()==["HPG"]

def test_board_and_existing_holdings_filter(catalog):
    d=stock_catalog(catalog)
    assert search_stocks(d,board="HNX").symbol.tolist()==["SHS"]
    assert search_stocks(d,board="UPCOM").symbol.tolist()==["ACV"]
    assert search_stocks(d,board="HOSE",exclude=["HPG"]).symbol.tolist()==["FPT","OTHER"]

def test_limit_and_rank(catalog):
    catalog.loc[len(catalog)]=dict(symbol="HPGX",name="Other",board="HOSE",lotSize=100,source="ssi_fastconnect_v3")
    d=stock_catalog(catalog)
    assert search_stocks(d,"HPG",limit=1).symbol.tolist()==["HPG"]

def test_reject_nonofficial_catalog(catalog):
    catalog.loc[0,"source"]="synthetic"
    with pytest.raises(ValueError):
        stock_catalog(catalog)

def test_demo_symbols_remain_separate(catalog):
    d=stock_catalog(catalog,pd.DataFrame({"symbol":["HPG","TEST"]}))
    m=d.set_index("symbol")
    assert m.loc["HPG","catalog_source"]=="ssi_fastconnect_v3"
    assert m.loc["TEST","catalog_source"]=="saved_book"
    assert m.loc["TEST","board"]=="Chưa rõ"

def test_ambiguous_board_is_not_guessed(catalog):
    row=catalog.iloc[0].copy()
    row["board"]="HNX"
    d=stock_catalog(pd.concat([catalog,row.to_frame().T],ignore_index=True),
                    pd.DataFrame({"symbol":["HPG"]}))
    assert "HPG" not in d.symbol.tolist()

def test_lot_constraints_and_empty_data(catalog):
    d=stock_catalog(catalog)
    assert known_nonstandard_lots(d,["OTHER","HPG","ACV"])==["OTHER"]
    empty=stock_catalog()
    assert empty.empty
    assert search_stocks(empty,"HPG").empty
    assert known_nonstandard_lots(empty,["HPG"])==[]


def test_equity_universe_filters_warrants_funds_and_bonds(catalog):
    extra=pd.DataFrame([
      dict(symbol="CVNM2622",name="Chứng quyền VNM",board="HOSE"),
      dict(symbol="FUEVFVND",name="Quỹ ETF",board="HOSE"),
      dict(symbol="XYZ",name="Trái phiếu XYZ",board="HNX"),
      dict(symbol="ABC",name="Công ty ABC",board="HOSE",cwUnderlyingSymbol="VNM"),
      dict(symbol="A32",name="Công ty cổ phần A32",board="UPCOM",lotSize=100),
      dict(symbol="QQQ",name="Công ty QQQ",board="HOSE",maturityDate="2027-01-01"),
    ]).assign(source="ssi_fastconnect_v3")
    raw=pd.concat([catalog,extra],ignore_index=True)
    d=stock_catalog(raw,pd.DataFrame({"symbol":["CVNM2622","XYZ","OTHER","TEST"]}),equity_only=True)
    assert set(d.symbol)=={"A32","HPG","FPT","SHS","ACV"}
    assert search_stocks(d,"chung quyen").empty
    assert len(raw)==11

def test_equity_type_evidence_is_labelled(catalog):
    from src.data.equity_universe import equity_catalog
    catalog["stockType"]=None
    catalog.loc[catalog.symbol=="HPG","stockType"]="Common Stock"
    d=equity_catalog(catalog).set_index("symbol")
    assert d.loc["HPG","equity_class"]=="common_stock_explicit"
    assert d.loc["FPT","equity_class"]=="stock_candidate"
