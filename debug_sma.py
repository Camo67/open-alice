import pandas as pd
from open_alice.strategies.sma_crossover import SmaCrossover

# Recreate the test data
dates = pd.date_range("2024-01-01", periods=100, freq="D")
prices = pd.Series(range(100, 200), dtype=float)
df = pd.DataFrame({"Close": prices}, index=dates)

print("Data shape:", df.shape)
print("First 5 prices:", df["Close"].head().tolist())
print("Last 5 prices:", df["Close"].tail().tolist())

strat = SmaCrossover(fast=5, slow=10)
result = strat.generate_signals(df)

print("\nSignal column (last 10):", result["Signal"].tail(10).tolist())
print("Position column (last 10):", result["Position"].tail(10).tolist())
print("SMA_fast (last 5):", result["SMA_fast"].tail(5).tolist())
print("SMA_slow (last 5):", result["SMA_slow"].tail(5).tolist())

# Check if fast SMA is above slow SMA at the end
fast_last = result["SMA_fast"].iloc[-1]
slow_last = result["SMA_slow"].iloc[-1]
print(f"\nFinal values: Fast SMA = {fast_last}, Slow SMA = {slow_last}")
print(f"Is fast > slow? {fast_last > slow_last}")

# Let's also check when the SMAs become valid (non-NaN)
print(f"\nFirst non-NaN SMA_fast at index: {result['SMA_fast'].first_valid_index()}")
print(f"First non-NaN SMA_slow at index: {result['SMA_slow'].first_valid_index()}")