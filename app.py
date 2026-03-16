from flask import Flask, request, Response
import yfinance as yf
from datetime import datetime
import pytz

app = Flask(__name__)

SYMBOLS = ['SOXL', 'TQQQ', 'QQQ', 'NQ=F']

SYMBOL_NAMES = {
    'SOXL': 'סוקסל',
    'TQQQ': 'טי קיו קיו קיו',
    'QQQ': 'קיו קיו קיו',
    'NQ=F': 'חוזים עתידיים נאסדק',
}

def get_market_session():
    now = datetime.now(pytz.timezone('US/Eastern'))
    hour = now.hour + now.minute / 60
    if 4 <= hour < 9.5:
        return "מסחר מוקדם"
    elif 9.5 <= hour < 16:
        return "מסחר רגיל"
    elif 16 <= hour < 20:
        return "מסחר מאוחר"
    else:
        return "מחוץ לשעות המסחר"

def get_stock_data(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info
    price = info.last_price
    prev_close = info.previous_close
    if not price or not prev_close:
        return f"{SYMBOL_NAMES.get(symbol, symbol)}, נתונים לא זמינים. "
    change = price - prev_close
    change_pct = (change / prev_close) * 100
    direction = "עלייה" if change >= 0 else "ירידה"
    sign = "פלוס" if change >= 0 else "מינוס"
    name = SYMBOL_NAMES.get(symbol, symbol)
    text = f"{name}. מחיר: {price:.2f}. שינוי: {direction} של {sign} {abs(change_pct):.1f} אחוז. "
    try:
        pre = info.pre_market_price
        if pre:
            pre_change = pre - prev_close
            pre_pct = (pre_change / prev_close) * 100
            pre_dir = "עלייה" if pre_change >= 0 else "ירידה"
            pre_sign = "פלוס" if pre_change >= 0 else "מינוס"
            text += f"מסחר מוקדם: {pre:.2f}, {pre_dir} של {pre_sign} {abs(pre_pct):.1f} אחוז. "
    except:
        pass
    try:
        post = info.post_market_price
        if post:
            post_change = post - prev_close
            post_pct = (post_change / prev_close) * 100
            post_dir = "עלייה" if post_change >= 0 else "ירידה"
            post_sign = "פלוס" if post_change >= 0 else "מינוס"
            text += f"מסחר מאוחר: {post:.2f}, {post_dir} של {post_sign} {abs(post_pct):.1f} אחוז. "
    except:
        pass
    return text

@app.route('/stocks', methods=['GET'])
def stocks():
    symbols = request.args.get('symbols', ','.join(SYMBOLS))
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    session = get_market_session()
    full_text = f"נתוני מניות עדכניים. {session}. "
    for sym in symbol_list:
        try:
            full_text += get_stock_data(sym)
        except:
            name = SYMBOL_NAMES.get(sym, sym)
            full_text += f"{name}, שגיאה בטעינת נתונים. "
    full_text = full_text.replace('&', 'ו').replace('<', '').replace('>', '')
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
```

---

## קובץ 2: `requirements.txt`
```
flask
yfinance
gunicorn
pytz
```

---

## קובץ 3: `Procfile`
(בלי סיומת — השם הוא בדיוק `Procfile`)
```
web: gunicorn app:app
```

---

## קובץ 4: `README.md`
```
# Stock IVR - ימות המשיח
שרת נתוני מניות עבור IVR
