# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 15:00:33 2024

@author: JinLan Rao
"""
#%%

import backtrader as bt
import pandas as pd
import yfinance as yf 
import MetaTrader5 as mt5

#%%
mt5.initialize()

#%%

class EMA_ATR_Strategy(bt.Strategy):
    params = (
        ('ema_fast', 5),    # EMA Fast period
        ('ema_medium', 10),  # EMA Medium period
        ('ema_slow', 20),   # EMA Slow period
        ('atr_period', 14),  # ATR period
        ('atr_tp_factor', 1.5),  # ATR multiplier for Take Profit
        ('atr_sl_factor', 1.0),  # ATR multiplier for Stop Loss
        ('atr_trail_factor', 0.35),  # ATR multiplier for Trailing Stop
    )

    def __init__(self):
        # Define EMAs
        self.ema_fast = bt.indicators.EMA(self.data.close, period=self.params.ema_fast)
        self.ema_medium = bt.indicators.EMA(self.data.close, period=self.params.ema_medium)
        self.ema_slow = bt.indicators.EMA(self.data.close, period=self.params.ema_slow)

        # ATR
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)

        # Variables to track stop loss and take profit
        self.sl_price = None
        self.tp_price = None
        self.trail_stop = None


    def next(self):
        # Check if there is an open position
        if not self.position:
            # Long Trade Entry Condition: EMA5 > EMA10 > EMA20
            if self.ema_fast > self.ema_medium > self.ema_slow:
                # Buy signal
                self.buy()
                # Calculate Stop Loss and Take Profit based on ATR
                self.sl_price = self.data.close[0] - (self.atr[0] * self.params.atr_sl_factor)
                self.tp_price = self.data.close[0] + (self.atr[0] * self.params.atr_tp_factor)
                self.trail_stop = None  # Reset trailing stop
            
            # Short Trade Entry Condition: EMA5 < EMA10 < EMA20
            elif self.ema_fast < self.ema_medium < self.ema_slow:
                # Sell signal
                self.sell()
                # Calculate Stop Loss and Take Profit based on ATR
                self.sl_price = self.data.close[0] + (self.atr[0] * self.params.atr_sl_factor)
                self.tp_price = self.data.close[0] - (self.atr[0] * self.params.atr_tp_factor)
                self.trail_stop = None  # Reset trailing stop
        else:
            # Manage open position with Stop Loss and Take Profit
            if self.position.size > 0:  # Long position
                if self.data.close[0] >= self.tp_price:  # Take Profit
                    self.close()
                elif self.data.close[0] <= self.sl_price:  # Stop Loss
                    self.close()
                else:
                    # Apply trailing stop
                    self.trail_stop = max(self.trail_stop or self.sl_price, self.data.close[0] - self.atr[0] * self.params.atr_trail_factor)
                    if self.data.close[0] <= self.trail_stop:
                        self.close()
            elif self.position.size < 0:  # Short position
                if self.data.close[0] <= self.tp_price:  # Take Profit
                    self.close()
                elif self.data.close[0] >= self.sl_price:  # Stop Loss
                    self.close()
                else:
                    # Apply trailing stop
                    self.trail_stop = min(self.trail_stop or self.sl_price, self.data.close[0] + self.atr[0] * self.params.atr_trail_factor)
                    if self.data.close[0] >= self.trail_stop:
                        self.close()

#%%
# Download historical data using yfinance
def get_data(symbol, start, end):
    df = yf.download(symbol, start=start, end=end)
    return df

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    
    # Add strategy to Cerebro
    cerebro.addstrategy(EMA_ATR_Strategy)
    
    # Download historical data
    data = get_data('AAPL', '2020-01-01', '2024-10-27')
    
    # Add data to Cerebro
    feed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(feed)
    
    # Set initial cash
    cerebro.broker.setcash(100000.0)
    
    # Set the commission for trading
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

    # Run the backtest
    cerebro.run()

    # Plot the results
    cerebro.plot()


 