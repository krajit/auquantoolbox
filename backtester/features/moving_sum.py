from backtester.features.feature import *

class MovingSumFeature(Feature):

    @classmethod
    def computeForInstrument(cls, updateNum, time, featureParams, featureKey, instrumentManager):
        instrumentLookbackData = instrumentManager.getLookbackInstrumentFeatures()
        data = instrumentLookbackData.getFeatureDf(featureParams['featureName'])
        checkData(data)
        checkPeriod(featureParams)
        cClean(data)
        movingSum = data[-featureParams['period']:].sum()
        return movingSum

    @classmethod
    def computeForMarket(cls, updateNum, time, featureParams, featureKey, currentMarketFeatures, instrumentManager):
        lookbackDataDf = instrumentManager.getDataDf()
        data = lookbackDataDf[featureParams['featureName']]
        checkData(data)
        checkPeriod(featureParams)
        cClean(data)
        movingSum = data[-featureParams['period']:].sum()
        fClean(movingSum)
        return movingSum


    @classmethod
    def computeForInstrumentData(cls, updateNum, featureParams, featureKey, featureManager):
        data = featureManager.getFeatureDf(featureParams['featureName'])
        checkData(data)
        checkPeriod(featureParams)
        movingSum = data.rolling(window=featureParams['period'], min_periods=1).sum()
        cClean(movingSum)
        return movingSum
