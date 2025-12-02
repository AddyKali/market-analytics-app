from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import time
from collections import deque
from typing import Dict, List
import logging
import requests
import os

logger = logging.getLogger(__name__)

app = FastAPI()

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DHAN CONFIG
DHAN_CLIENT_ID = os.getenv("1109365536")
DHAN_ACCESS_TOKEN = os.getenv("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY0Njg0ODMxLCJpYXQiOjE3NjQ1OTg0MzEsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA5MzY1NTM2In0._NW0gcm0Li32KyvYKvXOOOkyY1dpGhNwvmpf6DaUD4ukQz1xSWc8aD1-fv27D3tzhnz6L6QM_hHEtJxMsgfybg")
BASE_URL = "https://api.dhan.co/v2"

HEADERS = {
    "client-id": DHAN_CLIENT_ID,
    "access-token": DHAN_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

SECURITY_IDS = {
    "RELIANCE": "2885",
    "TCS": "11536",
    "HDFCBANK": "1333",
    "INFY": "1594",
    "ICICIBANK": "4963",
}

STOCKS = list(SECURITY_IDS.keys())

# Store chart prices
history: Dict[str, deque] = {sym: deque(maxlen=300) for sym in STOCKS}

# ================= RISK FUNCTIONS =================
def compute_returns(prices: List[float]):
    return [(prices[i] - prices[i-1])/prices[i-1] for i in range(1, len(prices))] if len(prices) > 1 else []

def stddev(values: List[float]):
    if len(values) < 2: return 0.0
    mean = sum(values)/len(values)
    var = sum((v-mean)**2 for v in values)/(len(values)-1)
    return var**0.5

def max_drawdown(prices: List[float]):
    peak = prices[0] if prices else 0
    max_dd = 0
    for p in prices:
        peak = max(peak, p)
        dd = (p - peak) / peak
        max_dd = min(max_dd, dd)
    return round(max_dd * 100, 2)

def historical_var(returns: List[float]):
    if len(returns) < 5: return 0.0
    sorted_r = sorted(returns)
    return round(sorted_r[int(0.05 * len(sorted_r))] * 100.0, 2)

def risk_metrics(symbol: str):
    prices = [p for (_, p) in history[symbol]]
    rets = compute_returns(prices)
    vol = stddev(rets) * (252**0.5) * 100 if rets else 0
    dd = max_drawdown(prices)
    var95 = historical_var(rets)
    score = min(100, max(0, abs(dd)*0.4 + abs(var95)*0.4 + vol*0.2))

    return {
        "volatility": round(vol, 2),
        "max_drawdown": dd,
        "var_95": var95,
        "risk_score": round(score, 0),
    }

# ================= API MODELS =================
class StockListResponse(BaseModel):
    symbols: List[str]

@app.get("/api/stocks", response_model=StockListResponse)
async def get_stocks():
    return {"symbols": STOCKS}

# ================= LIVE LTP FUNCTION (REST) =================
def fetch_ltp(symbol: str):
    security_id = SECURITY_IDS[symbol]
    payload = {"NSE_EQ": [int(security_id)]}
    try:
        resp = requests.post(f"{BASE_URL}/marketfeed/ltp", json=payload, headers=HEADERS)
        print(resp.status_code, resp.text)  # 👈 Add this line
        resp.raise_for_status()
        data = resp.json()
        return data["data"]["NSE_EQ"][str(security_id)]
    except Exception as e:
        logger.error(f"LTP error {symbol}: {e}")
        return None


# ================= WEBSOCKET STREAM =================
@app.websocket("/ws/prices")
async def stream_prices(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            snapshot = []
            for symbol in STOCKS:
                quote = fetch_ltp(symbol)
                if not quote: continue

                price = float(quote.get("last_price", 0))
                prev_close = quote.get("previous_close") or price
                change_pct = round((price - prev_close) / prev_close * 100, 2)

                history[symbol].append((time.time(), price))
                metrics = risk_metrics(symbol)

                snapshot.append({
                    "symbol": symbol,
                    "price": price,
                    "change_percent": change_pct,
                    "history": [{"t": ts, "price": p} for ts, p in history[symbol]],
                    "metrics": metrics,
                })

            await ws.send_json({"type": "snapshot", "data": snapshot})
            await asyncio.sleep(1.8)

    except WebSocketDisconnect:
        logger.warning("Client disconnected.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
