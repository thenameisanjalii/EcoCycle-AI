# EcoCycle AI — Statistical Data Profiling Audit

**Dataset Audited**: `C:\Users\patid\Desktop\SecondSpark-AI_ML\master_dataset.csv`  
**Total Records**: 116,663  
**Total Columns**: 11  

## 1. Complete Statistical Summary Table

| Column | Count | Mean | Std | Min | Q1 (25%) | Median | Q3 (75%) | Max | Unique | Zeros | Negatives | Positives |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `IR` | 116,663 | 0.0157 | 0.0036 | 0.0000 | 0.0154 | 0.0161 | 0.0170 | 0.0226 | 106,279 | 4,922 | 0 | 111,741 |
| `QCharge` | 116,663 | 1.0389 | 0.0492 | 0.8289 | 1.0225 | 1.0523 | 1.0702 | 1.9679 | 110,044 | 0 | 0 | 116,663 |
| `QDischarge` | 116,663 | 1.0391 | 0.0505 | 0.8250 | 1.0226 | 1.0531 | 1.0716 | 1.1214 | 110,470 | 0 | 0 | 116,663 |
| `Tavg` | 116,663 | 34.3558 | 2.0092 | -8.6572 | 33.0716 | 34.1618 | 35.7189 | 73.5538 | 116,663 | 0 | 8 | 116,655 |
| `Tmax` | 116,663 | 38.1376 | 10.8405 | 25.9380 | 36.1165 | 38.0025 | 39.6938 | 400.0000 | 114,722 | 0 | 0 | 116,663 |
| `Tmin` | 116,663 | 31.2738 | 8.9050 | -270.0000 | 30.4108 | 31.4892 | 32.5241 | 36.6912 | 113,575 | 24 | 99 | 116,540 |
| `chargetime` | 116,663 | 11.3969 | 38.2172 | 6.4744 | 10.0447 | 10.3143 | 11.1796 | 3934.7052 | 86,458 | 0 | 0 | 116,663 |
| `cycle` | 116,663 | 498.0547 | 373.6113 | 1.0000 | 212.0000 | 427.0000 | 706.0000 | 2237.0000 | 2,237 | 0 | 0 | 116,663 |
| `SOH` | 116,663 | 96.4072 | 4.5205 | 74.5527 | 95.2676 | 98.0745 | 99.5077 | 104.7925 | 116,529 | 0 | 0 | 116,663 |
| `RUL` | 116,663 | 496.6931 | 373.6661 | 0.0000 | 211.0000 | 425.0000 | 704.0000 | 2236.0000 | 2,237 | 139 | 0 | 116,524 |
| `battery_id` | 116,663 | 74.8370 | 43.7257 | 1.0000 | 33.0000 | 81.0000 | 114.0000 | 139.0000 | 139 | 0 | 0 | 116,663 |

## 2. Target Profiles (SOH & RUL)

### State of Health (SOH)
- **Min**: 74.55272866405737
- **Max**: 104.79245284946096
- **Mean**: 96.4072
- **Median**: 98.0745
- **Std Dev**: 4.5205
- **Q1 (25%)**: 95.2676
- **Q3 (75%)**: 99.5077
- **Unique Values**: 116,529

### Remaining Useful Life (RUL)
- **Min**: 0.0
- **Max**: 2236.0
- **Mean**: 496.6931
- **Median**: 425.0000
- **Std Dev**: 373.6661
- **Q1 (25%)**: 211.0000
- **Q3 (75%)**: 704.0000
- **Unique Values**: 2,237

## 3. Battery-Level Distribution Summary (139 Batteries)

| Metric | Min | Q1 | Median | Mean | Q3 | Max | Std |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `num_records` | 99.0000 | 527.5000 | 827.0000 | 839.3022 | 1027.0000 | 2237.0000 | 362.0524 |
| `min_SOH` | 74.5527 | 76.7348 | 81.8746 | 81.2331 | 82.7374 | 98.9612 | 4.7705 |
| `max_SOH` | 100.0416 | 100.0602 | 100.1022 | 100.3146 | 100.3407 | 104.7925 | 0.5341 |
| `min_RUL` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `max_RUL` | 98.0000 | 526.5000 | 826.0000 | 838.3669 | 1026.0000 | 2236.0000 | 362.0351 |
| `min_cycle` | 1.0000 | 1.0000 | 1.0000 | 1.3309 | 2.0000 | 2.0000 | 0.4723 |
| `max_cycle` | 99.0000 | 528.0000 | 827.0000 | 839.6978 | 1027.0000 | 2237.0000 | 362.0385 |

## 4. Purely Statistical Observations
- Column 'IR' exhibits high statistical skewness (-3.4758).
- Column 'IR' has very low variance (1.264447e-05).
- Column 'IR' contains 4922 zero values (4.22%).
- Column 'IR' has high cardinality with 106279 unique values.
- Column 'QCharge' has very low variance (2.415961e-03).
- Column 'QCharge' has high cardinality with 110044 unique values.
- Column 'QDischarge' has very low variance (2.555116e-03).
- Column 'QDischarge' has high cardinality with 110470 unique values.
- Column 'Tavg' contains 8 negative values (0.01%).
- Column 'Tavg' has high cardinality with 116663 unique values.
- Column 'Tmax' exhibits high statistical skewness (31.5542).
- Column 'Tmax' has high cardinality with 114722 unique values.
- Column 'Tmin' exhibits high statistical skewness (-32.8684).
- Column 'Tmin' contains 24 zero values (0.02%).
- Column 'Tmin' contains 99 negative values (0.08%).
- Column 'Tmin' has high cardinality with 113575 unique values.
- Column 'chargetime' exhibits high statistical skewness (101.9559).
- Column 'chargetime' spans a large numerical range (6.474444999999832 to 3934.705166666666).
- Column 'chargetime' has high cardinality with 86458 unique values.
- Column 'cycle' spans a large numerical range (1.0 to 2237.0).
- Column 'SOH' exhibits high statistical skewness (-1.8460).
- Column 'SOH' has high cardinality with 116529 unique values.
- Column 'RUL' spans a large numerical range (0.0 to 2236.0).
- Column 'RUL' contains 139 zero values (0.12%).
