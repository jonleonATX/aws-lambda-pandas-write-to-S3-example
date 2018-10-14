
import mimetypes
import os
import pandas as pd
import boto3


bucket = os.environ['WRITETO_BUCKET_NAME']

s3sr = boto3.resource('s3')
s3sc = boto3.client('s3')

bucketobj = s3sr.Bucket(bucket)

def write_file_to_s3(event, context):
    """using temp directory in lambda to store and then write to s3"""

    all_data = {'tradingday': '2018-10-10',
                'atrmultiple': '1.23185',
                'direction': 'high',
                'symbol': 'ESZ18',
                'breakoutprice': '2939.5',
                'ohlcv': {'open': '2886.75',
                          'high': '2891.25',
                          'low': ' 2771.5',
                          'close': '2781.0',
                          'volume': '1770753'},
                'TTLExpiration': '1539275786',
                'breakoutdays': '20',
                'packageddata': {'Unit1': '2939.75',
                                 'Unit2': '2959.25',
                                 'Unit3': '2978.75',
                                 'Unit4': '2998.25',
                                 'Stop1': '2861.5',
                                 'Stop2': '2881.0',
                                 'Stop3': '2900.5',
                                 'Stop4': '2920.0',
                                 'type': 'daily',
                                 'risk': '2.0',
                                 'min_volume': '400',
                                 'equity': '150000',
                                 'breakout_days': '20',
                                 'unit_size_cutoff': '0.8',
                                 'direction': 'high',
                                 'tradingDay': '2018-10-10',
                                 'symbol': 'ESZ18',
                                 'volume': '1770753',
                                 'unit_size': '0',
                                 'atr': '39.1685983',
                                 'tick': '0.25',
                                 'chart_url': 'https://www.barchart.com/futures/quotes/ESZ18/interactive-chart'}}


    pdata = all_data['packageddata']
    trades = {'': ['1st Unit', '2nd Unit', '3rd Unit', '4th Unit'],
              'Buy Stop': [pdata['Unit1'], pdata['Unit2'], pdata['Unit3'], pdata['Unit4']],
              'Sell Stop1': [pdata['Stop1'], '', '', ''],
              'Sell Stop2': [pdata['Stop1'], pdata['Stop2'], '', ''],
              'Sell Stop3': [pdata['Stop1'], pdata['Stop2'], pdata['Stop3'], ''],
              'Sell Stop4': [pdata['Stop1'], pdata['Stop2'], pdata['Stop3'], pdata['Stop4']]
             }

    df = pd.DataFrame.from_dict(trades)
    if all_data['direction'] == "low":
        df.columns = ['', 'Sell Stop', 'Buy Stop1', 'Buy Stop2', 'Buy Stop3', 'Buy Stop4']

    # print(df)
    #############################################################################################
    # writing file to s3 using the lamba temp directory and panda to_html function
    file_name = pdata['tradingDay'] + pdata['symbol'] + pdata['direction'] + ".html"
    lambda_path = "/tmp/" + file_name
    key = "htmlfiles/" + file_name

    df.to_html(lambda_path)

    # using mimetypes
    content_type = mimetypes.guess_type(file_name)[0] or 'text/plain'
    # print(content_type)

    response = bucketobj.upload_file(str(lambda_path),
                                     str(key), ExtraArgs={'ContentType': content_type})

    print(response)

    #############################################################################################
    # writing file to s3 using the lamba temp directory and open file method

    file_name = pdata['tradingDay'] + pdata['symbol'] + pdata['direction'] + ".json"
    lambda_path = "/tmp/" + file_name
    key = "jsonfiles/" + file_name

    with open(lambda_path, 'w+') as file:
        file.write(str(all_data))
        file.close()

    response = bucketobj.upload_file(str(lambda_path),
                                     str(key), ExtraArgs={'ContentType': content_type})

    print(response)
