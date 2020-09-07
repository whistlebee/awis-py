# Alexa Web Information Service (AWIS) for Python

Currently implemented two AWIS features:
* TrafficHistory
* UrlInfo (partially)

# Installation

```console
$ pip install awis-py
```

## Usage example

```python
import getpass
from awis import AWIS

test_url = 'reddit.com'

access_key_id = getpass.getpass('Enter access key id: ')
secret_access_key = getpass.getpass('Enter secret access key: ')

awis = AWIS(access_key_id, secret_access_key)

# Traffic history
result = awis.traffic_history(test_url, start_date='20170601', search_range=20)
```

The result will look something like this:
```
[TrafficHistory(date='2017-06-01', page_view_per_million=11920, page_view_per_user=10.5, rank=9, reach=49200),
 TrafficHistory(date='2017-06-02', page_view_per_million=12250, page_view_per_user=10.3, rank=9, reach=50100),
 TrafficHistory(date='2017-06-03', page_view_per_million=14630, page_view_per_user=10.6, rank=7, reach=53900),
...
```

Or conveniently with pandas:
```python
import pandas as pd
pd.DataFrame(result)
```
```
          date  page_view_per_million  page_view_per_user  rank  reach
0   2017-06-01                  11920                10.5     9  49200
1   2017-06-02                  12250                10.3     9  50100
2   2017-06-03                  14630                10.6     7  53900
3   2017-06-04                  14990                10.8     7  55800
4   2017-06-05                  12350                10.8     9  51300
5   2017-06-06                  12110                10.7     9  51000
6   2017-06-07                  12130                10.6     9  51000
7   2017-06-08                  12420                10.6     9  51200
8   2017-06-09                  12440                10.3     9  51500
9   2017-06-10                  14600                10.5     7  55100
10  2017-06-11                  15170                10.8     7  56300
11  2017-06-12                  12590                11.0     9  51000
12  2017-06-13                  12820                10.9     9  51700
13  2017-06-14                  12520                10.6     8  50900
14  2017-06-15                  12130                10.3     9  51000
15  2017-06-16                  12610                10.6     9  50900
16  2017-06-17                  14700                10.6     7  54600
17  2017-06-18                  15400                10.9     7  56000
18  2017-06-19                  12490                10.7     8  52200
19  2017-06-20                  12600                10.7     8  52500
```
