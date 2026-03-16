from flask import Flask, request, Response
import yfinance as yf
from datetime import datetime
import pytz

app = Flask(__name__)

SYMBOLS = ['SOXL', 'TQQQ', 'QQQ', 'NQ=F']

SYMBOL_NAMES = {
    'SOXL': 'SOXL',
    'TQQQ': 'TQQQ',
    'QQQ': 'QQQ',
    'NQ=F': 'Nasdaq Futures',
}

def get_market_session():
    now = datetime.now(pytz.timezone('US/Eastern'))
    hour = now.hour + now.minute / 60
    if 4 <= hour < 9.5:
        return "Pre market"
    elif 9.5 <= hour < 16:
        return "Regular session"
    elif 16 <= hour < 20:
        return "After market"
    else:
        return "Market closed"

def get_stock_data(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info
    price = info.last_price
    prev_close = info.previous_close
    if not price or not prev_close:
        return f"{SYMBOL_NAMES.get(symbol, symbol)}, data unavailable. "
    change = price - prev_close
    change_pct = (change / prev_close) * 100
    direction = "up" if change >= 0 else "down"
    name = SYMBOL_NAMES.get(symbol, symbol)
    text = f"{name}. Price: {price:.2f}. Change: {direction} {abs(change_pct):.1f} percent. "
    try:
        pre = info.pre_market_price
        if pre:
            pre_change = pre - prev_close
            pre_pct = (pre_change / prev_close) * 100
            pre_dir = "up" if pre_change >= 0 else "down"
            text += f"Pre market: {pre:.2f}, {pre_dir} {abs(pre_pct):.1f} percent. "
    except:
        pass
    try:
        post = info.post_market_price
        if post:
            post_change = post - prev_close
            post_pct = (post_change / prev_close) * 100
            post_dir = "up" if post_change >= 0 else "down"
            text += f"After market: {post:.2f}, {post_dir} {abs(post_pct):.1f} percent. "
    except:
        pass
    return text

@app.route('/stocks', methods=['GET'])
def stocks():
    symbols = request.args.get('symbols', ','.join(SYMBOLS))
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    session = get_market_session()
    full_text = f"Stock data. {session}. "
    for sym in symbol_list:
        try:
            full_text += get_stock_data(sym)
        except:
            full_text += f"{sym}, error loading data. "
    full_text = full_text.replace('&', 'and').replace('<', '').replace('>', '')
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<XIMSS>
  <play text="{full_text}" lang="he"/>
</XIMSS>"""
    return Response(xml, mimetype='text/xml; charset=utf-8')

@app.route('/ping', methods=['GET'])
def ping():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
