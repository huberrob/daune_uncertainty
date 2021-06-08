# daune_uncertainty

minimalistic Python class to calculate uncertainty


Usage:

```
from uncertainty import uncert as un
import pandas as pd

param_mapping = {'laboratory:daune:sbe37_bsh_6966:temperature_0001 [°C]':'TEMP',
          'laboratory:daune:sbe37_bsh_6966:conductivity_0001 [S/m]':'COND',
           'laboratory:daune:sbe37_bsh_6966:pressure_0001 [m]':'PRES',
           'laboratory:daune:sbe37_bsh_6966:salinity_0001 [PSU]':'PSAL'
          }
testdata = pd.read_csv('data/daune2.csv', sep="\t",parse_dates=['datetime'])
testdata.set_index('datetime', inplace=True)

unc = un.uncert(testdata, param_mapping)

unc.set_calibration_date('TEMP','2020-07-10')
unc.set_calibration_uncertainty('TEMP', 0.0018)
unc.set_instrument_resolution('TEMP', 0.000029)
unc.set_longterm_stability('TEMP', 0.00041)

unc.set_configuration_data('PRES','2020-07-15',0.01,0.00029, 0.002)

unc.get_uncertainty('TEMP')
unc.get_uncertainty('PRES')

unc.data['TEMP.unc'].plot
```
