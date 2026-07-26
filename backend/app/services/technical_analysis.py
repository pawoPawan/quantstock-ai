"""Technical analysis service — computes all indicators from OHLCV data."""

import logging
from typing import Optional, Dict, Any, List, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _signal(value: float, bull_cond: bool, bear_cond: bool) -> str:
    if bull_cond:
        return "bullish"
    if bear_cond:
        return "bearish"
    return "neutral"


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_macd(close: pd.Series, fast=12, slow=26, signal=9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def compute_bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0):
    sma = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    bandwidth = (upper - lower) / sma * 100
    pct_b = (close - lower) / (upper - lower)
    return upper, sma, lower, bandwidth, pct_b


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(com=period - 1, adjust=False).mean()


def compute_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
    atr = compute_atr(high, low, close, period)
    up = high.diff()
    dn = -low.diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    plus_dm = pd.Series(plus_dm, index=close.index)
    minus_dm = pd.Series(minus_dm, index=close.index)
    plus_di = 100 * plus_dm.ewm(com=period - 1, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(com=period - 1, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(com=period - 1, adjust=False).mean()
    return adx, plus_di, minus_di


def compute_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period=14, d_period=3):
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    d = k.rolling(d_period).mean()
    return k, d


def compute_keltner_channels(high: pd.Series, low: pd.Series, close: pd.Series, ema_period=20, atr_mult=2.0):
    ema = close.ewm(span=ema_period, adjust=False).mean()
    atr = compute_atr(high, low, close, 10)
    upper = ema + atr_mult * atr
    lower = ema - atr_mult * atr
    return upper, ema, lower


def compute_ichimoku(high: pd.Series, low: pd.Series, close: pd.Series):
    tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
    kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
    chikou = close.shift(-26)
    return tenkan, kijun, senkou_a, senkou_b, chikou


def compute_supertrend(high: pd.Series, low: pd.Series, close: pd.Series, period=10, multiplier=3.0):
    atr = compute_atr(high, low, close, period)
    hl_avg = (high + low) / 2
    upper_band = hl_avg + multiplier * atr
    lower_band = hl_avg - multiplier * atr
    supertrend = pd.Series(index=close.index, dtype=float)
    direction = pd.Series(index=close.index, dtype=int)
    supertrend.iloc[0] = lower_band.iloc[0]
    direction.iloc[0] = 1

    for i in range(1, len(close)):
        prev_st = supertrend.iloc[i - 1]
        prev_dir = direction.iloc[i - 1]
        curr_close = close.iloc[i]
        curr_upper = upper_band.iloc[i]
        curr_lower = lower_band.iloc[i]
        prev_upper = upper_band.iloc[i - 1]
        prev_lower = lower_band.iloc[i - 1]

        curr_lower = max(curr_lower, prev_lower) if curr_close > prev_lower else curr_lower
        curr_upper = min(curr_upper, prev_upper) if curr_close < prev_upper else curr_upper

        if prev_dir == 1:
            direction.iloc[i] = -1 if curr_close < curr_lower else 1
        else:
            direction.iloc[i] = 1 if curr_close > curr_upper else -1

        supertrend.iloc[i] = curr_lower if direction.iloc[i] == 1 else curr_upper

    return supertrend, direction


def compute_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


def compute_cmf(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period=20) -> pd.Series:
    mfm = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
    mfv = mfm * volume
    return mfv.rolling(period).sum() / volume.rolling(period).sum().replace(0, np.nan)


def compute_mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period=14) -> pd.Series:
    typical = (high + low + close) / 3
    raw_mf = typical * volume
    direction = typical.diff()
    positive_mf = raw_mf.where(direction > 0, 0)
    negative_mf = raw_mf.where(direction < 0, 0)
    mfr = positive_mf.rolling(period).sum() / negative_mf.rolling(period).sum().replace(0, np.nan)
    return 100 - (100 / (1 + mfr))


def compute_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    typical = (high + low + close) / 3
    return (typical * volume).cumsum() / volume.cumsum()


def compute_support_resistance(close: pd.Series, n_levels: int = 5) -> Tuple[List[float], List[float]]:
    """Identify S/R levels via local minima/maxima with clustering."""
    if len(close) < 20:
        return [], []

    prices = close.values
    # Find local minima and maxima
    from scipy.signal import argrelextrema
    order = max(5, len(prices) // 20)
    local_min_idx = argrelextrema(prices, np.less, order=order)[0]
    local_max_idx = argrelextrema(prices, np.greater, order=order)[0]

    support_raw = sorted(prices[local_min_idx])
    resistance_raw = sorted(prices[local_max_idx])

    def cluster(levels, threshold_pct=0.01):
        if not levels:
            return []
        clusters = [[levels[0]]]
        for lvl in levels[1:]:
            if abs(lvl - clusters[-1][-1]) / clusters[-1][-1] < threshold_pct:
                clusters[-1].append(lvl)
            else:
                clusters.append([lvl])
        return [round(float(np.mean(c)), 4) for c in clusters]

    supports = cluster(support_raw)[-n_levels:]
    resistances = cluster(resistance_raw)[-n_levels:]
    return supports, resistances


def compute_volume_profile(close: pd.Series, volume: pd.Series, bins: int = 20) -> List[Dict]:
    if len(close) < bins:
        return []
    hist, edges = np.histogram(close, bins=bins, weights=volume)
    total_vol = hist.sum()
    return [
        {
            "price_level": round(float((edges[i] + edges[i + 1]) / 2), 4),
            "volume": float(hist[i]),
            "volume_pct": round(float(hist[i] / total_vol * 100), 2) if total_vol > 0 else 0,
        }
        for i in range(len(hist))
    ]


def analyze_technical(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Master function: accepts OHLCV DataFrame, returns all technical indicators.

    Parameters
    ----------
    df : DataFrame with columns Open, High, Low, Close, Volume (DatetimeIndex)
    """
    if df.empty or len(df) < 30:
        return {"error": "Insufficient data"}

    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    volume = df["Volume"].astype(float)

    result: Dict[str, Any] = {}

    # ── RSI ──────────────────────────────────────────────────────────────────
    rsi = compute_rsi(close)
    rsi_val = float(rsi.iloc[-1]) if not rsi.empty else None
    result["rsi"] = {
        "value": round(rsi_val, 2) if rsi_val else None,
        "signal": _signal(rsi_val or 50, rsi_val < 30 if rsi_val else False, rsi_val > 70 if rsi_val else False),
        "description": "Relative Strength Index (14)",
        "formula": "RSI = 100 - 100/(1+RS), RS = Avg Gain / Avg Loss",
        "interpretation": (
            "Oversold (<30) — potential reversal up" if rsi_val and rsi_val < 30
            else "Overbought (>70) — potential reversal down" if rsi_val and rsi_val > 70
            else "Neutral momentum"
        ),
        "series": _last_n(rsi, 100),
    }

    # ── MACD ─────────────────────────────────────────────────────────────────
    macd_line, signal_line, histogram = compute_macd(close)
    m, s, h = float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), float(histogram.iloc[-1])
    prev_h = float(histogram.iloc[-2]) if len(histogram) > 1 else h
    result["macd"] = {
        "macd": round(m, 4),
        "signal": round(s, 4),
        "histogram": round(h, 4),
        "trend": "bullish" if m > s else "bearish",
        "crossover": "bullish_cross" if h > 0 > prev_h else ("bearish_cross" if h < 0 < prev_h else "none"),
        "formula": "MACD = EMA(12) - EMA(26); Signal = EMA(9) of MACD",
        "macd_series": _last_n(macd_line, 100),
        "signal_series": _last_n(signal_line, 100),
        "histogram_series": _last_n(histogram, 100),
    }

    # ── ADX ──────────────────────────────────────────────────────────────────
    adx, plus_di, minus_di = compute_adx(high, low, close)
    adx_val = float(adx.iloc[-1]) if not adx.empty else None
    pdi, mdi = float(plus_di.iloc[-1]), float(minus_di.iloc[-1])
    result["adx"] = {
        "value": round(adx_val, 2) if adx_val else None,
        "plus_di": round(pdi, 2),
        "minus_di": round(mdi, 2),
        "signal": _signal(adx_val or 0, adx_val > 25 and pdi > mdi if adx_val else False, adx_val > 25 and mdi > pdi if adx_val else False),
        "trend_strength": "strong" if adx_val and adx_val > 40 else "moderate" if adx_val and adx_val > 25 else "weak",
        "description": "Average Directional Index (14)",
        "formula": "ADX = EMA(|+DI - -DI| / (+DI + -DI) × 100)",
    }

    # ── ATR ──────────────────────────────────────────────────────────────────
    atr = compute_atr(high, low, close)
    atr_val = float(atr.iloc[-1])
    atr_pct = atr_val / float(close.iloc[-1]) * 100
    result["atr"] = {
        "value": round(atr_val, 4),
        "pct_of_price": round(atr_pct, 2),
        "signal": "neutral",
        "description": "Average True Range (14) — volatility measure",
        "formula": "ATR = EMA(max(H-L, |H-C_prev|, |L-C_prev|))",
        "interpretation": f"Daily range ~{atr_pct:.1f}% of price",
    }

    # ── Bollinger Bands ───────────────────────────────────────────────────────
    bb_upper, bb_mid, bb_lower, bandwidth, pct_b = compute_bollinger_bands(close)
    curr_pct_b = float(pct_b.iloc[-1])
    bb_signal = "bullish" if curr_pct_b < 0.05 else "bearish" if curr_pct_b > 0.95 else "neutral"
    result["bollinger_bands"] = {
        "upper": round(float(bb_upper.iloc[-1]), 4),
        "middle": round(float(bb_mid.iloc[-1]), 4),
        "lower": round(float(bb_lower.iloc[-1]), 4),
        "bandwidth": round(float(bandwidth.iloc[-1]), 4),
        "pct_b": round(curr_pct_b, 4),
        "signal": bb_signal,
        "squeeze": bandwidth.iloc[-1] < bandwidth.rolling(50).mean().iloc[-1],
        "description": "Bollinger Bands (20, 2σ)",
        "formula": "Upper/Lower = SMA(20) ± 2×StdDev; %B = (Close-Lower)/(Upper-Lower)",
        "upper_series": _last_n(bb_upper, 100),
        "lower_series": _last_n(bb_lower, 100),
        "middle_series": _last_n(bb_mid, 100),
    }

    # ── Keltner Channels ──────────────────────────────────────────────────────
    kc_upper, kc_mid, kc_lower = compute_keltner_channels(high, low, close)
    result["keltner_channels"] = {
        "upper": round(float(kc_upper.iloc[-1]), 4),
        "middle": round(float(kc_mid.iloc[-1]), 4),
        "lower": round(float(kc_lower.iloc[-1]), 4),
        "signal": "bullish" if float(close.iloc[-1]) > float(kc_upper.iloc[-1]) else (
            "bearish" if float(close.iloc[-1]) < float(kc_lower.iloc[-1]) else "neutral"
        ),
        "description": "Keltner Channels (EMA20, ATR×2)",
    }

    # ── Stochastic ────────────────────────────────────────────────────────────
    stoch_k, stoch_d = compute_stochastic(high, low, close)
    k_val, d_val = float(stoch_k.iloc[-1]), float(stoch_d.iloc[-1])
    prev_k, prev_d = float(stoch_k.iloc[-2]), float(stoch_d.iloc[-2])
    result["stochastic"] = {
        "k": round(k_val, 2),
        "d": round(d_val, 2),
        "signal": (
            "bullish" if k_val < 20 or (k_val > d_val and prev_k < prev_d)
            else "bearish" if k_val > 80 or (k_val < d_val and prev_k > prev_d)
            else "neutral"
        ),
        "overbought": k_val > 80,
        "oversold": k_val < 20,
        "description": "Stochastic Oscillator (14, 3)",
        "formula": "%K = (C-LL14)/(HH14-LL14)×100; %D = SMA(%K,3)",
    }

    # ── Ichimoku ──────────────────────────────────────────────────────────────
    tenkan, kijun, senkou_a, senkou_b, chikou = compute_ichimoku(high, low, close)
    curr_close = float(close.iloc[-1])
    sa = float(senkou_a.iloc[-1]) if not np.isnan(senkou_a.iloc[-1]) else None
    sb = float(senkou_b.iloc[-1]) if not np.isnan(senkou_b.iloc[-1]) else None
    cloud_signal = "neutral"
    if sa and sb:
        above_cloud = curr_close > max(sa, sb)
        below_cloud = curr_close < min(sa, sb)
        cloud_signal = "bullish" if above_cloud else ("bearish" if below_cloud else "neutral")
    result["ichimoku"] = {
        "tenkan": round(float(tenkan.iloc[-1]), 4),
        "kijun": round(float(kijun.iloc[-1]), 4),
        "senkou_a": round(sa, 4) if sa else None,
        "senkou_b": round(sb, 4) if sb else None,
        "signal": cloud_signal,
        "above_cloud": cloud_signal == "bullish",
        "description": "Ichimoku Kinko Hyo cloud system",
    }

    # ── SuperTrend ────────────────────────────────────────────────────────────
    st_line, st_dir = compute_supertrend(high, low, close)
    st_signal = "bullish" if int(st_dir.iloc[-1]) == 1 else "bearish"
    result["supertrend"] = {
        "value": round(float(st_line.iloc[-1]), 4),
        "direction": int(st_dir.iloc[-1]),
        "signal": st_signal,
        "description": "SuperTrend (10, 3)",
        "formula": "SuperTrend = (H+L)/2 ± Multiplier × ATR",
    }

    # ── OBV ───────────────────────────────────────────────────────────────────
    obv = compute_obv(close, volume)
    obv_ema = obv.ewm(span=20, adjust=False).mean()
    result["obv"] = {
        "value": float(obv.iloc[-1]),
        "ema20": float(obv_ema.iloc[-1]),
        "signal": "bullish" if float(obv.iloc[-1]) > float(obv_ema.iloc[-1]) else "bearish",
        "description": "On-Balance Volume",
        "formula": "OBV = Cumsum(direction × Volume)",
        "series": _last_n(obv, 100),
    }

    # ── CMF ───────────────────────────────────────────────────────────────────
    cmf = compute_cmf(high, low, close, volume)
    cmf_val = float(cmf.iloc[-1])
    result["cmf"] = {
        "value": round(cmf_val, 4),
        "signal": "bullish" if cmf_val > 0.05 else ("bearish" if cmf_val < -0.05 else "neutral"),
        "description": "Chaikin Money Flow (20)",
        "formula": "CMF = Σ(MFV) / Σ(Volume); MFV = ((C-L)-(H-C))/(H-L) × V",
    }

    # ── MFI ───────────────────────────────────────────────────────────────────
    mfi = compute_mfi(high, low, close, volume)
    mfi_val = float(mfi.iloc[-1])
    result["mfi"] = {
        "value": round(mfi_val, 2),
        "signal": "bullish" if mfi_val < 20 else ("bearish" if mfi_val > 80 else "neutral"),
        "overbought": mfi_val > 80,
        "oversold": mfi_val < 20,
        "description": "Money Flow Index (14) — volume-weighted RSI",
    }

    # ── VWAP ──────────────────────────────────────────────────────────────────
    vwap = compute_vwap(high, low, close, volume)
    vwap_val = float(vwap.iloc[-1])
    result["vwap"] = {
        "value": round(vwap_val, 4),
        "signal": "bullish" if curr_close > vwap_val else "bearish",
        "description": "Volume Weighted Average Price",
        "formula": "VWAP = Σ(Typical Price × Volume) / Σ(Volume)",
        "series": _last_n(vwap, 100),
    }

    # ── Support & Resistance ─────────────────────────────────────────────────
    try:
        supports, resistances = compute_support_resistance(close)
        result["support_levels"] = supports
        result["resistance_levels"] = resistances
    except Exception:
        result["support_levels"] = []
        result["resistance_levels"] = []

    # ── Volume Profile ────────────────────────────────────────────────────────
    result["volume_profile"] = compute_volume_profile(close, volume)

    # ── Overall Signal ────────────────────────────────────────────────────────
    signals = [
        result["rsi"]["signal"],
        result["macd"]["trend"],
        result["adx"]["signal"],
        result["supertrend"]["signal"],
        result["stochastic"]["signal"],
        result["ichimoku"]["signal"],
        result["bollinger_bands"]["signal"],
        result["obv"]["signal"],
        result["vwap"]["signal"],
    ]
    bull_count = signals.count("bullish")
    bear_count = signals.count("bearish")
    if bull_count > bear_count + 2:
        overall = "strong_bullish"
    elif bull_count > bear_count:
        overall = "bullish"
    elif bear_count > bull_count + 2:
        overall = "strong_bearish"
    elif bear_count > bull_count:
        overall = "bearish"
    else:
        overall = "neutral"

    result["overall_signal"] = overall
    result["signal_counts"] = {"bullish": bull_count, "bearish": bear_count, "neutral": len(signals) - bull_count - bear_count}

    # Attach closing price series for charting
    result["close_series"] = _last_n(close, 252)
    result["volume_series"] = _last_n(volume, 252)

    return result


def _last_n(series: pd.Series, n: int) -> List[Optional[float]]:
    """Return last n values as a plain list, NaN → None."""
    vals = series.iloc[-n:].values.tolist()
    return [None if (v != v) else round(v, 6) for v in vals]
