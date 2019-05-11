# Alexa Web Information Service (AWIS) for Python

Currently implemented two AWIS features:
* UrlInfo
* TrafficHistory

## Usage example

```python
import getpass
from awis import AWIS

test_url = 'reddit.com'

access_key_id = getpass.getpass('Enter access key id: ')
secret_access_key = getpass.getpass('Enter secret access key: ')

# See https://docs.aws.amazon.com/AlexaWebInfoService/latest/ApiReference_UrlInfoAction.html
response_groups = ['Rank', 'UsageStats', 'SiteData']
awis = AWIS(access_key_id, secret_access_key)

result = awis.traffic_history(test_url, start_date='20170601', search_range=20)
import pandas as pd
df = pd.DataFrame(result)
print(df)
```

This gives us:

```
                    2017-06-01  2017-06-02  2017-06-03  2017-06-04  \
PageViewPerMillion     11920.0     12250.0     14630.0     14990.0
PageViewPerUser           10.5        10.3        10.6        10.8
Rank                       9.0         9.0         7.0         7.0
Reach                  49200.0     50100.0     53900.0     55800.0
                    2017-06-05  2017-06-06  2017-06-07  2017-06-08  \
PageViewPerMillion     12350.0     12110.0     12130.0     12420.0
PageViewPerUser           10.8        10.7        10.6        10.6
Rank                       9.0         9.0         9.0         9.0
Reach                  51300.0     51000.0     51000.0     51200.0
                    2017-06-09  2017-06-10  2017-06-11  2017-06-12  \
PageViewPerMillion     12440.0     14600.0     15170.0     12590.0
PageViewPerUser           10.3        10.5        10.8        11.0
Rank                       9.0         7.0         7.0         9.0
Reach                  51500.0     55100.0     56300.0     51000.0
                    2017-06-13  2017-06-14  2017-06-15  2017-06-16  \
PageViewPerMillion     12820.0     12520.0     12130.0     12610.0
PageViewPerUser           10.9        10.6        10.3        10.6
Rank                       9.0         8.0         9.0         9.0
Reach                  51700.0     50900.0     51000.0     50900.0
                    2017-06-17  2017-06-18  2017-06-19  2017-06-20
PageViewPerMillion     14700.0     15400.0     12490.0     12600.0
PageViewPerUser           10.6        10.9        10.7        10.7
Rank                       7.0         7.0         8.0         8.0
Reach                  54600.0     56000.0     52200.0     52500.0
```
