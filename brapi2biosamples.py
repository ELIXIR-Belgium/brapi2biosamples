import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import click
import yaml
from datetime import datetime


def url_path_join(*args):
    """Join path(s) in URL using slashes"""
    return '/'.join(s.strip('/') for s in args)


def characteristic(text, ontology=None):
    """Making a ENA Biosamples characteristic"""
    if ontology:
        return [{"text": text, "ontologyTerms": [ontology]}]
    else:
        return [{"text": text}]

def fetch_token(username, password, dev):
    if dev:
        endpoint = 'https://explore.api.aai.ebi.ac.uk/auth'
    else:
        endpoint = 'https://api.aai.ebi.ac.uk/auth'
    
    token = requests.get(endpoint, auth=(username, password))
    if token.status_code != 200:
        print("problem with request: " + str(token))
        raise RuntimeError("Non-200 status code")
    return(token.text)

def fetch_object(endpoint, path):
    """
    Fetch single BrAPI object by path
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
    elif r.status_code != 200:
        print("problem with request: " + str(r))
        raise RuntimeError("Non-200 status code")
    return r.json()["result"]


def fetch_objects(endpoint, path, params: dict = None):
    """
    Fetch BrAPI objects with pagination
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
        r = session.get(url, params=params)
        if r.status_code == 504 and pagesize != 100:
            pagesize = 100
            print("504 Gateway Timeout Error, testing with pagesize = 100")
            continue
        elif r.status_code != 200:
            print("problem with request: " + str(r))
            raise RuntimeError("Non-200 status code")
        maxcount = int(r.json()['metadata']['pagination']['totalPages'])

        for data in r.json()['result']['data']:
            output.append(data)

        page += 1

        return output

@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.version_option("0.1.0", "-v", "--version", prog_name="brapi2biosamples", help="Print version number")
@click.option("--trialdbid", "-t", help="The identifier of a trial", required=True)
@click.option("--endpoint", "-e", help="The URL towards the BrAPI endpoint, not ending with /", required=True)
@click.option("--date", "-d", help="The date of sample publication (example: 2021-01-20T17:05:13Z)", default=datetime.now().isoformat())
@click.option("--domain", "-D", help="The domain of your ENA account", required=True)
@click.option("--submit", "-s", help="When this flag is given, the samples will be submitted to BioSamples instead of being exported as JSON", is_flag=True)
@click.option("--dev", help="When this flag is given, the samples will be submitted to the dev instance of BioSamples", is_flag=True)
@click.option("--secret", help="Path to a secret.yml file to deliver the BioSample credentials", type=click.Path(exists=True))
@click.option("--output", help="Path to a directory where the JSON files are written to.", type=click.Path(exists=True))

def main(trialdbid, endpoint, date, domain, submit, dev, secret, output):
    """ Submits samples to BioSamples using the Breeding API """

    if submit:
        click.format_filename(secret)
        secret_file = open(secret, "r")
        credentials = yaml.load(secret_file, Loader=yaml.FullLoader)

        password = credentials['password'].strip()
        username = credentials['username'].strip()
        token = fetch_token(username, password, dev)


    # Fetch studies from trial
    trial = fetch_object(endpoint, f'/trials/{trialdbid}')
    added_germplasm = []
    # Loop over studies
    for study in trial['studies']:
        print(f"Getting germplasms from {study['studyDbId']}")
        # Get germplasmId's from study 
        allgermplasms = fetch_objects(endpoint, f"/studies/{study['studyDbId']}/germplasm")
        for germplasm in allgermplasms:
            if germplasm['germplasmDbId'] not in added_germplasm:
                added_germplasm.append(germplasm['germplasmDbId'])
                # Get extra Germplasm information (Needed for PIPPA)
                germplasminfo = fetch_object(endpoint,
                    f"/germplasm/{germplasm['germplasmDbId']}")
                germjson = {"name": germplasminfo['germplasmDbId'],
                            "domain": domain, "release": date, "characteristics": {}}
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
                if not submit:
                    with open('o_' + germplasm['germplasmDbId'] + '.json', 'w') as outfile:
                        outfile.write(json.dumps(germjson, indent=4))


if __name__ == "__main__":
    main()
