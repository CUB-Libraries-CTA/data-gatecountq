# Celery Queue for pulling Vea SenSource Gate Count data
from celery.task import task
from dateutil import parser
from datetime import datetime, timedelta, date
import os
import json
import requests
import pytz
import tzlocal


senSourceURL = "https://auth.sensourceinc.com"
cybercomCollection = os.getenv('CYBERCOM_COLLECTION', "gatecount")
cybercomHost = os.getenv('CYBERCOM_HOST', "libapps.colorado.edu")
cybercom_url = "https://{0}/api/data_store/data/datalake/{1}".format(
    cybercomHost, cybercomCollection)
local_tz = pytz.timezone('US/Mountain')


def getSenSourceHeaders():
    """
    This function create Auth Token for SenSource API Authentication.
    Result: returns headers needed for API Calls
    """
    os.getenv('SENSOURCE_ID')
    headers = {"Content-type": "application/json"}
    data = {"grant_type": "client_credentials", "client_id": os.getenv(
        'SENSOURCE_ID'), "client_secret": os.getenv('SENSOURCE_SECRET')}
    req = requests.post("{0}/oauth/token".format(senSourceURL),
                        data=json.dumps(data), headers=headers)
    data = req.json()
    headers['Authorization'] = "Bearer {0}".format(data["access_token"])
    return headers


def getCybercomHeaders():
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Token {0}'.format(os.getenv('CYBERCOM_TOKEN'))}
    return headers


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def checkRecordAlreadyExists(itm):
    headers = getCybercomHeaders()
    query = '{"filter":{"recordDate_hour_1":"' + \
        itm["recordDate_hour_1"] + '","zoneId":"' + itm["zoneId"] + '"}}'
    url = "{0}?query={1}&format=json".format(cybercom_url, query)
    req = requests.get(url, headers=headers)
    # print(req.text)
    data = req.json()
    if data["count"] == 0:
        return False
    else:
        # print(data["results"][0])
        return data["results"][0]


def saveCybercomData(itm):
    headers = getCybercomHeaders()
    updateItm = checkRecordAlreadyExists(itm)
    # print(updateItm)
    if updateItm:
        temp = itm
        updateItm.update(temp)
        data = updateItm
        # print(data)
        url = "{0}/{1}/?format=json".format(cybercom_url, data['_id'])
        req = requests.put(url, data=json.dumps(data), headers=headers)
    else:
        url = "{0}.json".format(cybercom_url)
        req = requests.post(url, data=json.dumps(itm), headers=headers)
    #print("Response Code:", req.status_code, req.text)


def pullGateCount(start_date, end_date):
    """
    The Vea SenSource API limits return by dateGroupings level. The hour grouping level is a couple of days. This function should be used with a 1 day window.
    Args:
    start_date (string): example: 2019-03-01
    end_date (string): pluse one day -  2019-03-02
    """
    headers = getSenSourceHeaders()
    url = "https://vea.sensourceinc.com/api/data/traffic?dateGroupings=hour(1)&endDate={1}T00:00:00.000Z&entityType=zone&excludeClosedHours=false&include=zone,sensor,site,location&meta=&metrics=ins,outs&relativeDate=custom&startDate={0}T00:00:00.000Z"
    url = url.format(start_date, end_date)
    req = requests.get(url, headers=headers)
    return req


@task()
def pullGateCountYesterday():
    """
    Pull yesterday data. This assumes you have a CronJob that runs every morning after Midnight.
    """
    now = datetime.now()
    start_date = now - timedelta(days=1)
    start_date = start_date.strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")
    return pullGateCountDateRange(start_date, end_date)


@task()
def pullGateCountToday():
    """
    Pull today's data. Run Cronjob Hourly to pull new data each hour. 
    """
    now = datetime.now()
    # catch 23 hour when date changes
    start_date = now - timedelta(hours=1)
    start_date = start_date.strftime("%Y-%m-%d")
    end_date = now + timedelta(days=1)
    end_date = end_date.strftime("%Y-%m-%d")
    return pullGateCountDateRange(start_date, end_date)


@task()
def pullGateCountDateRange(start_date, end_date):
    """
    Pull gate count from Vea SenSource API 
    Args:
        start_date (String - YYYY-MM-DD ) 
        end_date (String - YYYY-MM-DD )
    """
    start_date = parser.parse(start_date)
    end_date = parser.parse(end_date) + timedelta(days=1)
    dates = []
    for single_date in daterange(start_date, end_date):
        dates.append(single_date.strftime("%Y-%m-%d"))
    for i in range(len(dates)):
        req = pullGateCount(dates[i], dates[i+1])
        data = req.json()
        if req.status_code >= 400:
            print("Error1:", dates[i], json.dumps(data, indent=0))
        else:
            # Load data
            for itm in data["results"]:
                tmpTZD = {}
                localDT = parser.parse(itm["recordDate_hour_1"]).replace(
                    tzinfo=pytz.utc).astimezone(local_tz)
                tmpTZD['local_timestamp'] = localDT.isoformat()
                tmpTZD['year'] = localDT.year
                tmpTZD['month'] = localDT.month
                tmpTZD['day'] = localDT.day
                tmpTZD['hour'] = localDT.hour
                tmpTZD['minute'] = localDT.minute
                tmpTZD['second'] = localDT.second
                tmpTZD['time_zone_name'] = localDT.tzname()
                tmp = itm
                tmp['localDateTime'] = tmpTZD
                saveCybercomData(tmp)
        # print(dates[i])
        if dates[i+1] == dates[-1]:
            break
    return "Date(s) Imported/Updated: {0}".format(",".join(dates[:-1]))


if __name__ == "__main__":
    print(pullGateCountYesterday())
    #now = datetime.now().strftime("%Y-%m-%d")
    #pullGateCountDateRange('2020-03-31', '2020-04-01')
