from flask import Flask, request, Response
import yfinance as yf
from datetime import datetime
from threading import Thread
import pytz, time, requests, os

app = Flask(__name__)

# Keep-alive
def keep_alive():
    time.sleep(60)
    url = os.environ.get("SELF_URL", "")
    while url:
        try:
            requests.get(f"{url}/ping", timeout=10)
        except:
            pass
        time.sleep(14 * 60)

Thread(target=keep_alive, daemon=True).start()

SYMBOLS = ['SOXL', 'TQQQ', 'QQQ', 'NQ=F']
SYMBOL_NAMES = {
    'SOXL': 'אס או אקס אל',
    'TQQQ': 'טי קיו קיו',
    'QQQ': 'קיו קיו קיו',
    'NQ=F': 'חוזים עתידיים על מדד הנאסדק',
}

def format_decimal(value):
    """
    מעגל ל-2 ספרות ומחליף נקודה במילה 'נקודה'
    """
    if value is None: return "לא ידוע"
    rounded = round(float(value), 2)
    return str(rounded).replace('.', ' נקודה ')

def get_market_session():
    now = datetime.now(pytz.timezone('America/New_York'))
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
    
    # שימוש ב-history כדי להוציא מחיר אחרון בצורה אמינה יותר עבור SOXL
    hist = ticker.history(period="1d")
    if hist.empty:
        # ניסיון אחרון דרך info רגיל
        info = ticker.info
        price = info.get('regularMarketPrice') or info.get('currentPrice')
        prev_close = info.get('regularMarketPreviousClose')
    else:
        price = hist['Close'].iloc[-1]
        prev_close = ticker.fast_info['previous_close']

    if not price or not prev_close:
        name = SYMBOL_NAMES.get(symbol, symbol)
        return name + ", נתונים לא זמינים זמנית. "
    
    change_pct = ((price - prev_close) / prev_close) * 100
    direction = "עלייה" if change_pct >= 0 else "ירידה"
    sign = "פלוס" if change_pct >= 0 else "מינוס"
    name = SYMBOL_NAMES.get(symbol, symbol)
    
    price_text = format_decimal(price)
    pct_text = format_decimal(abs(change_pct))
    
    # תיקון סדר המילים: קודם המספר ואז הפלוס/מינוס (או להפך, לפי העדפת המערכת)
    # כאן סידרתי את זה כך: "עלייה של 5 נקודה 2 פלוס אחוז"
    text = (f"{name}. מחיר: {price_text}. "
            f"שינוי: {direction} של {pct_text} {sign} אחוז. ")
            
    return text

@app.route('/stocks', methods=['GET'])
def stocks():
    symbols = request.args.get('symbols', ','.join(SYMBOLS))
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    
    il_tz = pytz.timezone('Asia/Jerusalem')
    now_il = datetime.now(il_tz).strftime("%H:%M")
    
    session = get_market_session()
    full_text = f"נתונים לשעה {now_il}. מצב שׁוּק: {session}. "
    
    for sym in symbol_list:
        try:
            full_text += get_stock_data(sym)
        except Exception as e:
            name = SYMBOL_NAMES.get(sym, sym)
            full_text += name + ", שגיאה בטעינת נתונים. "
            
    return Response("id_list_message=" + full_text,
                    mimetype='text/plain; charset=utf-8')

@app.route('/ping')
def ping():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
