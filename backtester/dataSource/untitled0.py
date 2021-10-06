# -*- coding: utf-8 -*-
"""
Created on Tue Oct  5 20:32:36 2021

@author: ajit.kumar
# """
# import requests
# instrumentId = 'SBIN.NS'
# url = 'https://finance.yahoo.com/quote/%s/history' % (instrumentId)
# req = requests.get(url)

import yfinance as yf

msft = yf.Ticker("SBIN.NS")

# get stock info
msft.info

# get historical market data
hist = msft.history(period="max")