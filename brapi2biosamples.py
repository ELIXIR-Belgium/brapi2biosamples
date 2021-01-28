import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

trial_id = "1"
endpoint = "https://pippa.psb.ugent.be/BrAPIPPA/brapi/v1"
date = "2021-01-20T17:05:13Z"


def url_path_join(*args):
    """Join path(s) in URL using slashes"""
    return '/'.join(s.strip('/') for s in args)


def characteristic(text, ontology=None):
    if ontology:
        return [{"text": text, "ontologyTerms": [ontology]}]
    else:
        return [{"text": text}]


def fetch_object(path: str):
    """
    Fetch single BrAPI object by path
    :param path URL path of the BrAPI call (ex '/studies/1', '/germplasm/2', ...)
    :return a BrAPI object parsed from JSON to python dict
    """
    url = url_path_join(endpoint, path)
    print('GET ' + url)
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=15)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    r = session.get(url)
    # Covering internal server errors by retrying one more time
    if r.status_code == 500:
        time.sleep(5)
        r = requests.get(url)
    elif r.status_code != requests.codes.ok:
        print("problem with request: " + str(r))
        raise RuntimeError("Non-200 status code")
    return r.json()["result"]


def fetch_objects(path: str, params: dict = None, data: dict = None):
    """
    Fetch BrAPI objects with pagination
    :param path URL path of the BrAPI call (ex '/studies', '/germplasm-search', ...)
    :param params dict containing the query params for the BrAPI call
    :param data dict containing the request body (used for 'POST' calls)
    :return iterable of BrAPI objects parsed from JSON to python dict
    """
    page = 0
    pagesize = 1000
    maxcount = 0
    # set a default dict for parameters
    params = params or {}
    url = url_path_join(endpoint, path)
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=15)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    output = []
    while maxcount == 0 or page < maxcount:
        params['page'] = page
        params['pageSize'] = pagesize
        print('retrieving page ' + str(page) + ' of ' +
              str(maxcount) + ' from ' + str(url))
        print("paging params:" + str(params))
        print("GET " + url)
        r = session.get(url, params=params, data=data)
        if r.status_code == 504 and pagesize != 100:
            pagesize = 100
            print("504 Gateway Timeout Error, testing with pagesize = 100")
            continue
        elif r.status_code != requests.codes.ok:
            print("problem with request: " + str(r))
            raise RuntimeError("Non-200 status code")
        maxcount = int(r.json()['metadata']['pagination']['totalPages'])

        for data in r.json()['result']['data']:
            output.append(data)

        page += 1

        return output


trial = fetch_object(f'/trials/{trial_id}')
added_germplasm = []
for study in trial['studies']:
    print(f"Getting germplasms from {study['studyDbId']}")
    allgermplasms = fetch_objects(f"/studies/{study['studyDbId']}/germplasm")
    for germplasm in allgermplasms:
        if germplasm['germplasmDbId'] not in added_germplasm:
            added_germplasm.append(germplasm['germplasmDbId'])
            germplasminfo = fetch_object(
                f"/germplasm/{germplasm['germplasmDbId']}")
            germjson = {"name": germplasminfo['germplasmDbId'],
                        "domain": endpoint, "release": date, "characteristics": {}}
            germjson['characteristics']['project name'] = characteristic(
                study['studyDbId'])
            germjson['characteristics']['biological material ID'] = characteristic(
                germplasminfo['germplasmDbId'])
            germjson['characteristics']['organism'] = characteristic(
                germplasminfo['commonCropName'])
            germjson['characteristics']['genus'] = characteristic(
                germplasminfo['genus'])
            germjson['characteristics']['species'] = characteristic(
                germplasminfo['species'])
            germjson['characteristics']['infraspecific name'] = characteristic(
                germplasminfo['accessionNumber'])
            germjson['characteristics']['material source ID'] = characteristic(
                germplasminfo['germplasmName'])

            with open('o_' + germplasm['germplasmDbId'] + '.json', 'w') as outfile:
                outfile.write(json.dumps(germjson, indent=4))
