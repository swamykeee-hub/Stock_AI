import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class TechnicalAnalyst:
    """Computes technical indicators, chart patterns, and generates technical scores."""

    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """Calculates Relative Strength Index."""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculates Average True Range."""
        high = df['High']
        low = df['Low']
        close_prev = df['Close'].shift(1)
        tr1 = high - low
        tr2 = (high - close_prev).abs()
        tr3 = (low - close_prev).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Performs full technical audit on historical OHLCV data."""
        if df.empty or len(df) < 30:
            return {
                "score": 0.0,
                "status": "Insufficient historical data for technical analysis",
                "signals": []
            }

        df = df.copy()
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']

        # Moving Averages
        df['EMA_20'] = close.ewm(span=20, adjust=False).mean()
        df['EMA_50'] = close.ewm(span=50, adjust=False).mean()
        df['EMA_200'] = close.ewm(span=200, adjust=False).mean() if len(df) >= 200 else close.ewm(span=len(df), adjust=False).mean()

        # RSI
        df['RSI'] = self.calculate_rsi(close, 14)

        # MACD
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        df['MACD'] = ema_12 - ema_26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

        # Bollinger Bands (20, 2)
        df['BB_Mid'] = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        df['BB_Upper'] = df['BB_Mid'] + (2 * bb_std)
        df['BB_Lower'] = df['BB_Mid'] - (2 * bb_std)

        # Volume
        df['Vol_SMA20'] = volume.rolling(window=20).mean()

        # ATR
        df['ATR'] = self.calculate_atr(df, 14)

        # Current Values
        cmp = float(close.iloc[-1])
        ema20 = float(df['EMA_20'].iloc[-1])
        ema50 = float(df['EMA_50'].iloc[-1])
        ema200 = float(df['EMA_200'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1]) if not pd.isna(df['RSI'].iloc[-1]) else 50.0
        macd = float(df['MACD'].iloc[-1])
        macd_signal = float(df['MACD_Signal'].iloc[-1])
        macd_hist = float(df['MACD_Hist'].iloc[-1])
        vol_curr = float(volume.iloc[-1])
        vol_avg20 = float(df['Vol_SMA20'].iloc[-1]) if not pd.isna(df['Vol_SMA20'].iloc[-1]) else vol_curr
        atr = float(df['ATR'].iloc[-1]) if not pd.isna(df['ATR'].iloc[-1]) else (cmp * 0.02)

        # Pivot Points calculation
        prev_high = float(high.iloc[-2]) if len(df) >= 2 else float(high.iloc[-1])
        prev_low = float(low.iloc[-2]) if len(df) >= 2 else float(low.iloc[-1])
        prev_close = float(close.iloc[-2]) if len(df) >= 2 else cmp
        pivot = (prev_high + prev_low + prev_close) / 3.0
        r1 = (2 * pivot) - prev_low
        s1 = (2 * pivot) - prev_high
        r2 = pivot + (prev_high - prev_low)
        s2 = pivot - (prev_high - prev_low)

        # Signal evaluation & Scoring (0 to 10 scale)
        tech_points = 0
        max_points = 10
        bullish_signals = []
        bearish_signals = []

        # 1. Moving Average Alignment
        if cmp > ema20:
            tech_points += 1.5
            bullish_signals.append("Price trading above 20-Day EMA (Short-term Bullish)")
        else:
            bearish_signals.append("Price trading below 20-Day EMA")

        if ema20 > ema50:
            tech_points += 1.5
            bullish_signals.append("20 EMA above 50 EMA (Medium-term Bullish Trend)")
        
        if cmp > ema200:
            tech_points += 2.0
            bullish_signals.append("Price above 200-Day EMA (Long-term Bull Market structure)")
        else:
            bearish_signals.append("Price below 200-Day EMA (Macro Bearish)")

        # 2. RSI Evaluation
        if 50 <= rsi <= 68:
            tech_points += 2.0
            bullish_signals.append(f"RSI at {rsi:.1f} in optimal bullish expansion territory (50-68)")
        elif rsi > 70:
            tech_points += 0.5
            bearish_signals.append(f"RSI at {rsi:.1f} indicates Overbought zone (consolidation risk)")
        elif rsi < 35:
            tech_points += 0.5
            bullish_signals.append(f"RSI at {rsi:.1f} indicates deep oversold (potential reversal bounce)")
        else:
            tech_points += 1.0

        # 3. MACD Evaluation
        if macd > macd_signal and macd_hist > 0:
            tech_points += 1.5
            bullish_signals.append("MACD Bullish Crossover above signal line with positive momentum")
        elif macd < macd_signal:
            bearish_signals.append("MACD Bearish Crossover below signal line")

        # 4. Volume Confirmation
        vol_ratio = vol_curr / (vol_avg20 + 1e-6)
        if vol_ratio >= 1.5 and cmp > df['Close'].iloc[-2]:
            tech_points += 1.5
            bullish_signals.append(f"Volume Surge: {vol_ratio:.2f}x of 20-day average volume on green candle")
        elif vol_ratio >= 1.0:
            tech_points += 0.5

        final_tech_score = min(round(tech_points, 1), 10.0)

        # Computed Price Targets and Dynamic Stop-Loss
        stop_loss = round(cmp - (1.5 * atr), 2)
        target_1 = round(cmp + (2.0 * atr), 2)
        target_2 = round(cmp + (3.5 * atr), 2)
        risk_per_share = round(cmp - stop_loss, 2)
        reward_per_share = round(target_1 - cmp, 2)
        risk_reward_ratio = round(reward_per_share / (risk_per_share + 1e-6), 2)

        return {
            "score": final_tech_score,
            "rsi": round(rsi, 2),
            "ema_20": round(ema20, 2),
            "ema_50": round(ema50, 2),
            "ema_200": round(ema200, 2),
            "macd": round(macd, 2),
            "macd_signal": round(macd_signal, 2),
            "volume_ratio": round(vol_ratio, 2),
            "atr": round(atr, 2),
            "pivot_points": {
                "Pivot": round(pivot, 2),
                "R1": round(r1, 2),
                "R2": round(r2, 2),
                "S1": round(s1, 2),
                "S2": round(s2, 2)
            },
            "levels": {
                "current_price": cmp,
                "stop_loss": stop_loss,
                "target_1": target_1,
                "target_2": target_2,
                "risk_reward_ratio": f"1:{risk_reward_ratio}"
            },
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals,
            "df_indicators": df
        }

