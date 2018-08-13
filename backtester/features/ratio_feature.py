from backtester.features.feature import *

class RatioMarketFeature(Feature):

    '''
    Computing for Instrument. By default defers to computeForLookbackData
    '''
    @classmethod
    def computeForInstrument(cls, updateNum, time, featureParams, featureKey, instrumentManager):
        instrumentLookbackData = instrumentManager.getLookbackInstrumentFeatures()
        data1 = instrumentLookbackData.getFeatureDf(featureParams['featureName1'])
        data2 = instrumentLookbackData.getFeatureDf(featureParams['featureName2'])
        checkDataMultiple(data1, data2)
        ratio = (data1[featureParams['featureName1']] / data2[featureParams['featureName2']]).iloc[-1]
        ratio = fClean(ratio)
        return ratio

    '''
    Computing for Market. By default defers to computeForLookbackData
    '''
    @classmethod
    def computeForMarket(cls, updateNum, time, featureParams, featureKey, currentMarketFeatures, instrumentManager):
        feature = featureParams['featureName']
        instrumentId1 = featureParams['instrumentId1']
        instrument1 = instrumentManager.getInstrument(instrumentId1)
        instrumentId2 = featureParams['instrumentId2']
        instrument2 = instrumentManager.getInstrument(instrumentId2)
        checkDataMultiple(instrument1, instrument2)
        instrumentLookbackData = instrumentManager.getLookbackInstrumentFeatures()
        dataDf = instrumentLookbackData.getFeatureDf(feature)
        instrument1Price = dataDf[instrumentId1].iloc[-1]
        instrument2Price = dataDf[instrumentId2].iloc[-1]
        if instrument2Price == 0:
            return 0
        return instrument1Price / float(instrument2Price)

    @classmethod
    def computeForInstrumentData(cls, updateNum, featureParams, featureKey, featureManager):
        data1= featureManager.getFeatureDf(featureParams['featureName1'])
        data2= featureManager.getFeatureDf(featureParams['featureName2'])
        checkDataMultiple(data1, data2)
        ratio = data1[featureParams['featureName1']]/data2[featureParams['featureName2']]
        cClean(ratio)
        return ratio
