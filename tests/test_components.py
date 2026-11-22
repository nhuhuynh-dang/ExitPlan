from src.app.components import cards_html,html_table,badge,verdict

def test_escape_html():
    s=cards_html([{'label':'<script>alert(1)</script>','value':'12','note':'N'}])
    assert '<script>' not in s
    assert '&lt;script&gt;' in s
    h=html_table(['<b>'],[['<img src=x>']])
    assert '<img' not in h
    assert '&lt;img' in h

def test_valid_markup():
    assert 'ep-card' in cards_html([{'label':'A','value':'1'}])
    assert 'title=' in html_table(['A'],[['1']],tooltips={'A':'Giải thích'})
    assert 'warn' in badge('giả lập','synthetic')
    assert 'ep-verdict' in verdict('Kết luận','Diễn giải')
