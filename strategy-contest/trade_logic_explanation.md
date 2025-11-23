# Swing Reversion Grid Strategy - Logic Explanation

## Core Philosophy
The Swing Reversion Grid strategy is based on the principle that asset prices tend to oscillate around a long-term mean. While trends exist, prices often overextend and then revert. This strategy aims to capitalize on these "swings" by buying into weakness (oversold conditions) and selling into strength (mean reversion).

## Technical Implementation

### 1. The Anchor (Moving Average)
We use a **50-period Simple Moving Average (SMA)** as our "fair value" anchor. This adapts to changing market conditions while providing a stable reference point.

### 2. The Grid (Entry Logic)
Instead of trying to time the exact bottom, we use a grid of buy orders below the SMA.
-   **Grid Step**: 1% (configurable).
-   **Levels**: We buy at -1% and -2% below the SMA.
-   **Logic**: If `(Price - SMA) / SMA < -0.01 * Level`, we trigger a buy signal.
-   **Position Sizing**: We allocate a large portion (27.5%) per grid level. This ensures we capitalize heavily on high-probability dips.

### 3. Trailing Stop (Exit Logic)
The goal is to capture the trend after the reversion.
-   **Activation**: Once the position is in 2.5% profit.
-   **Callback**: We sell if the price drops 3.5% from its highest point since entry.
-   **Reasoning**: This allows us to ride significant market rallies (like the Jan-Jun 2024 bull run) while protecting profits. We do not sell immediately at the mean; we let winners run.

### 4. Risk Management
-   **Stop Loss**: If price drops 15% below our entry, we cut the loss.
-   **Max Exposure**: We cap total exposure at 55% of the portfolio (2 levels * 27.5%) to comply with the 55% contest limit.

## Why This Works
-   **Volatility Harvesting**: Crypto markets are highly volatile. This strategy turns that volatility into profit by systematically buying dips.
-   **No Predictions**: We don't predict "up" or "down". We simply react to deviations from the norm.
-   **Discipline**: The grid structure enforces disciplined buying and selling, removing emotional decision-making.
