import pandas as pd
import numpy as np
import calendar
from datetime import datetime, timedelta
from scipy.stats import t
import math
from pandas.tseries.frequencies import to_offset

class uncert:
    def __init__(self, data,  mapping= None, window='5min'):
        self.configuration_data = {}
        self.set_data(data)
        self.window = window #data window size
        if mapping:
            self.data.rename(columns=mapping, inplace=True)
        for measured_property in self.data.columns:
            self.configuration_data[measured_property] = {'calibration_date':None, 'calibration_uncertainty':None,
                                               'instrument_resolution':None,'longterm_stability':None}

    def set_data(self, data):
        self.data = data

    def set_configuration_data(self, measured_property, calibration_date, calibration_uncertainty, instrument_resolution, longterm_stability_month):
        self.configuration_data[measured_property] =  {'calibration_date':calibration_date,
                                            'calibration_uncertainty':calibration_uncertainty,
                                            'instrument_resolution': instrument_resolution,
                                            'longterm_stability': longterm_stability_month}

    def set_calibration_date(self, measured_property, calibration_date):
        self.configuration_data[measured_property]['calibration_date'] = calibration_date

    def set_calibration_uncertainty(self, measured_property, calibration_uncertainty):
        self.configuration_data[measured_property]['calibration_uncertainty'] = calibration_uncertainty

    def set_instrument_resolution(self, measured_property, instrument_resolution):
        self.configuration_data[measured_property]['instrument_resolution'] = instrument_resolution

    def set_longterm_stability(self, measured_property, longterm_stability):
        self.configuration_data[measured_property]['longterm_stability'] = longterm_stability

    def get_systematic_contribution(self, measured_property):
        if self.configuration_data.get(measured_property):
            col_config= self.configuration_data.get(measured_property)
            if col_config.get('calibration_date'):
                calibration_timestamp = datetime.strptime(col_config.get('calibration_date'), '%Y-%m-%d')
                if calendar.isleap(calibration_timestamp.year):
                    yeardays = 366
                else:
                    yeardays = 365
                mu_longterm_perday = col_config.get('longterm_stability') * 12 / yeardays
                self.data[measured_property+'_syst'] = np.sqrt((((self.data.index - calibration_timestamp).days)
                                                    * mu_longterm_perday) ** 2
                                                    + col_config.get('instrument_resolution') ** 2
                                                    + col_config.get('calibration_uncertainty') ** 2)
        else:
            print('Calibration date required')

    def get_variance_contribution(self, measured_property):
        resampleddata = self.data.resample('5Min', origin='start').mean()
        resampleddata[measured_property+'_var'] = self.data[measured_property].resample('5Min', origin='start').apply(self._variance_contribution)
        #resampleddata[column+'_var'] = self.data[column].resample('5Min', origin='start').std()
        self.data[measured_property+'_var'] = resampleddata[measured_property+'_var']
        resampleddata = None

    def get_uncertainty(self, measured_property):
        self.get_systematic_contribution(measured_property)
        self.get_variance_contribution(measured_property)
        self.data[measured_property+'_unc'] = np.sqrt(self.data[measured_property+'_var'] ** 2 + self.data[measured_property+'_syst'] ** 2)
        self.data.fillna(method='ffill', inplace=True)

    def _qc_spike(self,x, thres = 0):
        #Test  value = | V2 – (V3 + V1) / 2 | – | (V3 – V1) / 2 |
        #where  V2 is the measurement being tested as a spike, and V1 and V3
        #are the values above and below.
        test = abs(x[1] - (x[0] + x[2]) / 2) - abs((x[2] - x[0]) / 2)
        if test < thres:
            return 0
        else:
            return 1

    def get_slope(self,X,Y):
        return ((X - X.mean()) * (Y - Y.mean())).sum() / ((X - X.mean()) ** 2).sum()

    def _variance_contribution(self,x):
        X = x.index.values.astype(float).reshape(-1, 1)
        Y = x.values.reshape(-1, 1)
        n = Y.size
        if n > 2:
            b1 = ((X - X.mean()) * (Y - Y.mean())).sum() / ((X - X.mean()) ** 2).sum()
            b0 = Y.mean() - b1 * X.mean()
            s = np.sqrt(((Y - b0 - b1 * X) ** 2).sum() / (n - 2))
            # ppf expects probability as input: Upper-tail probability p 0.025 => 95% confidence
            t095 = t.ppf(0.025, n - 2)
            # entgegen Steffens Formel muss ich das durch zwei teilen um das mit der Beispielsrechnung zusammenzu bringen
            mu = t095 * s / math.sqrt(n) / 2
            return abs(mu)
        else:
            return 0

    def set_spike_qc(self, measured_property):
        if measured_property =='TEMP':
            thresh = 6
        self.data[measured_property+'_is_spike'] = self.data[measured_property].rolling(3).apply(self._qc_spike,args=(thresh,))


