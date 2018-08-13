from backtester.features.feature import *
from backtester.financial_fn import ma


class RSIFeature(Feature):

    @classmethod
    def computeForInstrument(cls, updateNum, time, featureParams, featureKey, instrumentManager):
        instrumentLookbackData = instrumentManager.getLookbackInstrumentFeatures()
        data = instrumentLookbackData.getFeatureDf(featureParams['featureName'])
        checkData(data)
        checkPeriod(featureParams)
        cClean(data)
        data_upside = data.sub(data.shift(1), fill_value=0)
        data_downside = data_upside.copy()
        data_downside[data_upside > 0] = 0
        data_upside[data_upside < 0] = 0
        avg_upside = data_upside[-featureParams['period']:].mean()
        avg_downside = - data_downside[-featureParams['period']:].mean()
        rsi = 100 - (100 * avg_downside / (avg_downside + avg_upside))
        rsi[(avg_downside == 0)] = 100
        rsi[(avg_downside == 0) & (avg_upside == 0)] = 0
        cClean(rsi)
        return rsi

    @classmethod
    def computeForMarket(cls, updateNum, time, featureParams, featureKey, currentMarketFeatures, instrumentManager):
        lookbackDataDf = instrumentManager.getDataDf()
        data = lookbackDataDf[featureParams['featureName']]
        checkData(data)
        checkPeriod(featureParams)
        cClean(data)
        data_upside = data.sub(data.shift(1), fill_value=0)
        data_downside = data_upside.copy()
        data_downside[data_upside > 0] = 0
        data_upside[data_upside < 0] = 0
        if len(data.index) > 0:
            avg_upside = data_upside[-featureParams['period']:].mean()
            avg_downside = - data_downside[-featureParams['period']:].mean()
        else:
            return 0
        rsi = 100 - (100 * avg_downside / (avg_downside + avg_upside))
        rsi = 100 if (avg_downside == 0) else rsi
        rsi = 0 if ((avg_downside == 0) & (avg_upside == 0)) else rsi
        rsi = fClean(rsi)
        return rsi

    @classmethod
    def computeForInstrumentData(cls, updateNum, featureParams, featureKey, featureManager):
        data = featureManager.getFeatureDf(featureParams['featureName'])
        checkData(data)
        checkPeriod(featureParams)
        cClean(data)
        data_upside = data.sub(data.shift(1), fill_value=0)
        data_downside = data_upside.copy()
        data_downside[data_upside > 0] = 0
        data_upside[data_upside < 0] = 0
        avg_upside=data_upside.rolling(window=featureParams['period'], min_periods=1).mean()
        avg_downside=-data_downside.rolling(window=featureParams['period'], min_periods=1).mean()
        rsi = 100 - (100 * avg_downside / (avg_downside + avg_upside))
        rsi[(avg_downside == 0)] = 100
        rsi[(avg_downside == 0) & (avg_upside == 0)] = 0
        cClean(rsi)
        return rsi
