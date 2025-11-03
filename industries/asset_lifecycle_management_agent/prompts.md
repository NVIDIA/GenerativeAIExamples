
**Data Retrieval:**
```
Retrieve the time in cycles and operational setting 1 from the FD001 test table for unit number 1 and plot its value vs time.
```
**Anomaly Detection**
```
Retrieve and detect anomalies in sensor 4 measurements for engine number 78 in train FD001 dataset.
```
**Prediction and Comparison (Uses Workspace Utilities)**
```
Perform the following steps:

1.Retrieve the time in cycles, all sensor measurements, and calculate max cycle - current cycle as ground truth RUL values for engine unit 24 from FD001 train dataset.
2.Use the retrieved data to predict the Remaining Useful Life (RUL). 
3.Use the piece wise RUL transformation code utility to apply piecewise RUL transformation only to the observed RUL column with MAXLIFE of 100.
4.Generate a single plot with ground truth RUL values, transformed RUL values and the predicted RUL values across time.
```
**Prediction and Comparison (Uses Workspace Utilities) two**
```
Perform the following steps:

1.Retrieve the time in cycles, all sensor measurements, and calculate max cycle - current cycle as ground truth RUL values for unit number 24 from FD001 train dataset. 
2.Use the retrieved data to predict the Remaining Useful Life (RUL). 
3.Use the piece wise RUL transformation code utility to apply piecewise RUL transformation only to the observed RUL column with MAXLIFE of 100 and generate a single plot with ground truth RUL values, transformed RUL values and the predicted RUL values across time.
```