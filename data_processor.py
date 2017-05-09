import math
import pandas as pd
from datetime import timedelta
import numpy as np
import datascraper as ds
import option
import future
from constants import *
import useful_fn as utils
import time
import json


def atm_vol(x, y, order):
    delta = 0.5
    if order == 2:
        p = np.polyfit(x, y, 1)
        atmvol = p[0] * delta + p[1]
    else:
        p = np.polyfit(x, y, 2)
        atmvol = p[0] * delta**2 + p[1] * delta + p[2]
    return atmvol


def straddle(opt_arr, s):
    lowS = int(math.floor(s / 100.0)) * 100
    highS = int(math.ceil(s / 100.0)) * 100
    lowSCallSymbol = SAMPLE_OPTION_INSTRUMENT_PREFIX + str(lowS) + '003'
    lowSPutSymbol = SAMPLE_OPTION_INSTRUMENT_PREFIX + str(lowS) + '004'
    highSCallSymbol = SAMPLE_OPTION_INSTRUMENT_PREFIX + str(highS) + '003'
    highSPutSymbol = SAMPLE_OPTION_INSTRUMENT_PREFIX + str(highS) + '004'
    std1 = opt_arr[lowSCallSymbol].price + opt_arr[lowSPutSymbol].price
    std2 = opt_arr[highSCallSymbol].price + opt_arr[highSPutSymbol].price
    d1 = opt_arr[lowSCallSymbol].delta + opt_arr[lowSPutSymbol].delta
    d2 = opt_arr[highSCallSymbol].delta + opt_arr[highSPutSymbol].delta
    return std1, std2, d1, d2


class UnderlyingProcessor:
    def __init__(self, futureVal, optionsData, startMarketData, startFeaturesData, startTime):
        self.histFutureInstruments = []  # for storing history of future instruments
        self.histOptionInstruments = {}  # for storing history of option instruments
        # secondsInterval = pd.date_range(start=START_DATE, end=END_DATE, freq='1S')
        # self.marketData = pd.DataFrame(index=secondsInterval, columns=['Future', 'Vol', 'Mkt_Straddle', 'Theo_Straddle'])

        self.marketData = [startMarketData]
        self.features = [startFeaturesData]
        self.lastTimeSaved = utils.convert_time(startTime)
        self.currentFuture = future.Future(futureVal, startTime)
        self.currentOptions = {}
        for instrumentId in optionsData:
            optionData = optionsData[instrumentId]
            opt = option.Option(futurePrice=futureVal,
                                instrumentId=instrumentId,
                                exp_date=EXP_DATE,
                                instrumentPrefix=SAMPLE_OPTION_INSTRUMENT_PREFIX,
                                eval_date=startTime,
                                vol=optionData['vol'],
                                rf=RF)
            self.currentOptions[instrumentId] = opt
        self.printCurrentState()

    def serializeCurrentState(self):
        stateToSave = {}
        stateToSave['futureVal'] = self.currentFuture.getFutureVal()
        stateToSave['marketData'] = self.marketData[-1]
        stateToSave['featureData'] = self.features[-1]
        stateToSave['time'] = self.lastTimeSaved
        optionDataToSave = {}
        for instrumentId in self.currentOptions:
            optionDataToSave[instrumentId] = {
                'vol': self.currentOptions[instrumentId].vol}
        stateToSave['options'] = optionDataToSave
        return stateToSave

    def printCurrentState(self):
        currentState = self.serializeCurrentState()
        print '\n\n\n\n\n'
        print 'Time: ' + str(currentState['time'])
        print 'Future Value: ' + str(currentState['futureVal'])
        print '----------Market Data----------'
        print currentState['marketData']
        print '----------Feature Data---------'
        print currentState['featureData']
        print '---------Options---------------'
        print currentState['options']

    def saveCurrentState(self):
        np.save(CONTINUOS_SAVE_STATE_FILE, self.serializeCurrentState())

    def updateFeatures(self, time):
        convertedTime = utils.convert_time(time)
        if (convertedTime < self.lastTimeSaved + timedelta(0, 1)):
            return
        marketDataDf, featureDf = getFeaturesDf(
            time, self.currentFuture, self.currentOptions, self.marketData[-1], self.features[-1])
        if marketDataDf is not None:
            self.marketData.append(marketDataDf)
        if featureDf is not None:
            self.features.append(featureDf)
        self.lastTimeSaved = convertedTime
        self.saveCurrentState()
        self.printCurrentState()

    def updateWithNewFutureInstrument(self, futureInstrument):
        # self.histFutureInstruments.append(instrument)  # just for storing
        self.currentFuture.updateWithNewInstrument(futureInstrument)
        self.updateFeatures(futureInstrument.time)
        # TODO: Calculate new features and update
        # TODO: check if we are sending the right data[-1]

    def updateWithNewOptionInstrument(self, optionInstrument):
        # self.addNewOption(optionInstrument)  # just for storing
        changedOption = self.currentOptions[optionInstrument.instrumentId]
        changedOption.updateWithInstrument(
            optionInstrument, self.currentFuture.getFutureVal())
        self.updateFeatures(optionInstrument.time)
        # TODO: Calculate new features and update

    '''
    For storing stuff
    '''
    # returns Future class object

    def getCurrentFuture(self):
        return self.histFutureInstruments[-1]

    # returns dictionary of instrumentId -> Option class object
    def getAllCurrentOptions(self):
        toRtn = {}
        for instrumentId in self.histOptionInstruments:
            toRtn[instrumentId] = self.histOptionInstruments[instrumentId][-1]
        return toRtn

    # returns Option class object
    def getCurrentOption(self, instrumentId):
        self.ensureInstrumentId(instrumentId)
        # TODO: what happens if array is empty
        return self.histOptionInstruments[instrumentId][-1]

    def ensureInstrumentId(self, instrumentId):
        if instrumentId not in self.histOptionInstruments:
            self.histOptionInstruments[instrumentId] = []

    def addNewOption(self, opt):
        self.ensureInstrumentId(opt.instrumentId)
        self.histOptionInstruments[opt.instrumentId].append(opt)

    def processData(self, instrumentsToProcess):
        for instrument in instrumentsToProcess:
            if instrument.isFuture():
                self.updateWithNewFutureInstrument(instrument)
                # todo: update price of options
                # 1. update current future value
                # 2. opt.s = opt.s + futureValue - lastFutureValue
                # 3. calculate Vol (do not change opt.vol)
                # 3.1 update opt.vol
            else:
                self.updateWithNewOptionInstrument(instrument)
                # todo: update new vol
                # 1. update option.price
                # 2. update option.vol
                # 3. calculate Vol
                # Update s and vol
                # todo: update future value store it in data


def getFeaturesDf(eval_date, future, opt_dict, lastMarketDataDf, lastFeaturesDf):
    fut = future.getFutureVal()
    if fut == 0:
        print('Future not trading')
        return None, None
    else:
        temp_df = {}
        temp_f = {}

        temp_df['Future'] = fut
        delta_arr = []
        vol_arr = []
        var = 0
        try:
            # Loop over all options and get implied vol for each option
            for instrumentId in opt_dict:
                opt = opt_dict[instrumentId]
                opt.get_price_delta()
                price, delta = opt.calc_price, opt.delta
                if abs(delta) < 0.75:
                    if (delta < 0):
                        delta = 1 + delta
                    delta_arr.append(delta)
                    # TODO: ivol?
                    vol_arr.append(opt.vol)

            # Calculate ATM Vol
            if len(delta_arr) > 0:
                temp_df['Vol'] = atm_vol(delta_arr, vol_arr, 2)
                temp_df['Mkt_Straddle_low'], temp_df[
                    'Mkt_Straddle_high'], delta_low, delta_high = straddle(opt_dict, option.get_index_val(fut, ROLL))
                delta_arr.append(0.5)
                vol_arr.append(temp_df['Vol'])
            else:
                temp_df['Vol'] = lastMarketDataDf['Vol']

            # Calculate Realized Vol
            var = utils.calc_var_RT(
                lastFeaturesDf['Var'], fut, lastMarketDataDf['Future'])
            temp_f['Var'] = var
            temp_df['R Vol'] = np.sqrt(
                252 * var / (1 - utils.calculate_t(eval_date, utils.convert_time(eval_date).date() + timedelta(15, 30, 00))))

            # Calculate Features
            hl_iv = 360
            hl_rv = 360
            temp_f['HL AVol'] = utils.ema_RT(
                lastFeaturesDf['HL AVol'], temp_df['Vol'], hl_iv)
            temp_f['HL RVol'] = utils.ema_RT(
                lastFeaturesDf['HL RVol'], temp_df['R Vol'], hl_rv)
            temp_f['HL Future'] = utils.ema_RT(
                lastFeaturesDf['HL Future'], temp_df['Future'], hl_iv)

            # Combine Features into prediction
            temp_f['Pred'] = temp_f['HL AVol'] + temp_f['HL RVol'] + \
                temp_df['Future'] / temp_f['HL Future'] - 1


            # append data
            return temp_df, temp_f

        except:
            raise
            return None, None


def follow(futureFile, optionFile):
    futureFile.seek(0, 2)
    optionFile.seek(0, 2)
    while True:
        futureLine = futureFile.readline()
        optionLine = optionFile.readline()
        if not futureLine and not optionLine:
            time.sleep(0.1)
            continue
        if futureLine:
            yield ('f', futureLine)
        if optionLine:
            yield ('o', optionLine)


def startStrategyFromConstants():
    up = UnderlyingProcessor(STARTING_FUTURE_VAL, STARTING_OPTIONS_DATA,
                             START_MARKET_DATA, START_FEATURES_DATA, START_TIME)
    startStrategyContinuous(up)


def startStrategyFromSavedFile():
    stateSaved = np.load(CONTINUOS_SAVE_STATE_FILE).item()
    up = UnderlyingProcessor(stateSaved['futureVal'], stateSaved['options'], stateSaved[
                             'marketData'], stateSaved['featureData'], stateSaved['time'])
    startStrategyContinuous(up)


def startStrategyContinuous(up):
    futureDataparser = ds.Dataparser()
    optionsDataparser = ds.Dataparser()

    futureFile = open(FUTURE_LOG_FILE_PATH, "r")
    optionFile = open(OPTIONS_LOG_FILE_PATH, "r")

    lines = follow(futureFile, optionFile)

    for line in lines:
        (t, lineContent) = line
        lineContent = lineContent.strip()
        if len(lineContent) == 0:
            continue
        if t == 'f':
            futureInstrumentsToProcess = futureDataparser.processLines([
                                                                       lineContent])
            up.processData(futureInstrumentsToProcess)
        else:
            optionInstrumentsToProcess = optionsDataparser.processLines([
                                                                        lineContent])
            up.processData(optionInstrumentsToProcess)


def startStrategyHistory(historyFilePath):
    up = UnderlyingProcessor(
        STARTING_FUTURE_VAL, STARTING_OPTIONS_DATA, START_MARKET_DATA, START_FEATURES_DATA)
    dataParser = ds.Dataparser()
    with open(historyFilePath) as f:
        for line in f:
            instrumentsToProcess = dataParser.processLines([line])
            up.processData(instrumentsToProcess)

startStrategyFromConstants()
#startStrategyFromSavedFile()