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
    'SOXL': 'סוקסל',
    'TQQQ': 'טי קיו קיו קיו',
    'QQQ': 'קיו קיו קיו',
    'NQ=F': 'חוזים עתידיים נאסדק',
}

def format_decimal(value):
    """
    הופך את הנקודה העשרונית למילה 'נקודה' כדי שהמערכת תקריא אותה נכון
    """
    return str(round(value, 2)).replace('.', ' נקודה ')

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
    info = ticker.fast_info
    price = info.last_price
    prev_close = info.previous_close
    
    if not price or not prev_close:
        name = SYMBOL_NAMES.get(symbol, symbol)
        return name + ", נתונים לא זמינים. "
    
    change = price - prev_close
    change_pct = (change / prev_close) * 100
    direction = "עלייה" if change >= 0 else "ירידה"
    sign = "פלוס" if change >= 0 else "מינוס"
    name = SYMBOL_NAMES.get(symbol, symbol)
    
    # שימוש בפורמט 'נקודה' להקראה ברורה
    price_text = format_decimal(price)
    pct_text = format_decimal(abs(change_pct))
    
    text = (name + ". מחיר: " + price_text +
            ". שינוי: " + direction + " של " + sign + " " +
            pct_text + " אחוז. ")
            
    # טיפול בנתוני טרום מסחר ומסחר מאוחר במידה וקיימים
    try:
        pre = info.pre_market_price
        if pre:
            pre_text = format_decimal(pre)
            text += "מסחר מוקדם: " + pre_text + ". "
    except:
        pass
        
    return text

@app.route('/stocks', methods=['GET'])
def stocks():
    symbols = request.args.get('symbols', ','.join(SYMBOLS))
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    
    # הוספת שעה נוכחית בישראל
    il_tz = pytz.timezone('Asia/Jerusalem')
    now_il = datetime.now(il_tz).strftime("%H:%M")
    
    session = get_market_session()
    full_text = f"נתוני מניות נכונים לשעה {now_il}. מצב שוק: {session}. "
    
    for sym in symbol_list:
        try:
            full_text += get_stock_data(sym)
        except:
            name = SYMBOL_NAMES.get(sym, sym)
            full_text += name + ", שגיאה בטעינת נתונים. "
            
    return Response("id_list_message=" + full_text,
                    mimetype='text/plain; charset=utf-8')

@app.route('/ping')
def ping():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
