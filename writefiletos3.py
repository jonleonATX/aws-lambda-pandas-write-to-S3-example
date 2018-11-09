import base64
import mimetypes
import os
import pandas as pd
import requests
from requests_html import HTMLSession
import boto3
import urllib.request
import re

bucket = os.environ['WRITETO_BUCKET_NAME']

s3sr = boto3.resource('s3')
s3sc = boto3.client('s3')

bucketobj = s3sr.Bucket(bucket)


def decode_base64_from_web_and_write_file_to_s3(event, context):
    """downloading image string - base64, decoding, uploading to s3"""
    """using temp directory in lambda to store and then write to s3"""
    os.chdir('/tmp')
    chart_url = """https://www.barchart.com/futures/quotes/ZCZ18/technical-chart?plot=CANDLE&volume=contract&data=DO&density=M&pricesOn=1&asPctChange=0&logscale=0&indicators=DON(55)&sym=ZCZ18&grid=1&height=500&studyheight=100"""

    html_session = HTMLSession()
    r = html_session.get(chart_url)
    r.html.render() # render html forcing javascript to run
    html_session.close() # close the htmlsession

    mytag = r.html.find('#technicalChartImage', first=True)
    # 'data-ng-src="data:image/png;base64,'
    mytag.attrs
    # want this one: data-ng-src
    mytag.attrs['data-ng-src']
    srch_obj = re.search('base64', mytag.attrs['data-ng-src'])
    # <_sre.SRE_Match object; span=(15, 21), match='base64'>
    start_pos = srch_obj.end()
    # get the whole base64 string
    imgstring = mytag.attrs['data-ng-src'][start_pos + 1:]
    imgdata = base64.b64decode(imgstring)
    symbol = 'myzc'
    fn = symbol + '.jpg'
    path = "/tmp/"
    fullpath = path + fn

    output = open(fullpath, "wb")
    output.write(imgdata)
    output.close()

    # key and file name to be saved in s3
    key = "chartimages/" + fn

    content_type = mimetypes.guess_type(fn)[0] or 'text/plain'
    bucketobj.upload_file(str(fullpath),
        str(key), ExtraArgs={'ContentType': content_type})


def download_and_write_file_to_s3(event, context):
    """using temp directory in lambda to store and then write to s3"""

    # url to get html source code to pull chart image url
    symbol = 'CZ18'
    url = 'https://stockcharts.com/h-sc/ui?s=^' + symbol

    # site uses cookies, need to pass user-agent in header
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    headers = {'User-Agent':user_agent}
    request = urllib.request.Request(url, None, headers)
    response = urllib.request.urlopen(request)

    # data is binary
    data = response.read().decode('UTF-8')

    # find the starting point of the image string
    start_pos = re.search(r'id="chartImg" src="/', data)
    start_pos = start_pos.end()
    new_str = data[start_pos - 1:start_pos + 500]
    img_src = new_str[:new_str.find(">") - 3] # find the end of the image string based on closing '>'
    img_url = 'https:' + img_src

    # file to be saved locally, then uploaded to s3
    fn = symbol + '.jpg'
    path = "/tmp/"
    fullpath = path + fn
    request = urllib.request.Request(img_url, None, headers)
    response = urllib.request.urlopen(request)
    output = open(fullpath, "wb")
    output.write(response.read())
    output.close()

    # key and file name to be saved in s3
    key = "chartimages/" + fn

    content_type = mimetypes.guess_type(fn)[0] or 'text/plain'
    bucketobj.upload_file(str(fullpath),
        str(key), ExtraArgs={'ContentType': content_type})


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


    # create second data set to include in html file
    # trade_info = {}


    # print(df)
    #############################################################################################
    # writing file to s3 using the lamba temp directory and panda to_html function
    file_name = pdata['tradingDay'] + '_' + pdata['symbol'] + '_' +  pdata['direction'] + ".html"
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

    # file_name = pdata['tradingDay'] + pdata['symbol'] + pdata['direction'] + ".json"
    # lambda_path = "/tmp/" + file_name
    # key = "jsonfiles/" + file_name
    #
    # with open(lambda_path, 'w+') as file:
    #     file.write(str(all_data))
    #     file.close()
    #
    # response = bucketobj.upload_file(str(lambda_path),
    #                                  str(key), ExtraArgs={'ContentType': content_type})
    #
    # print(response)
