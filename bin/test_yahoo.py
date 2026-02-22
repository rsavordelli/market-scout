# test_yfinance.py - Quick diagnostic script
import yfinance as yf
import pandas as pd

print(f"yfinance version: {yf.__version__}")
print(f"pandas version: {pd.__version__}")
print("\nTesting direct yfinance call...")

try:
    ticker = yf.Ticker("AAPL")
    print(f"Ticker object created: {ticker}")
    
    hist = ticker.history(period="1mo")
    print(f"\nDataFrame shape: {hist.shape}")
    print(f"DataFrame empty: {hist.empty}")
    print(f"\nColumns: {list(hist.columns)}")
    
    if not hist.empty:
        print(f"\nFirst few rows:")
        print(hist.head())
    else:
        print("\nDataFrame is empty - this is the problem!")
        
except Exception as e:
    print(f"\nError occurred: {type(e).__name__}: {e}")
