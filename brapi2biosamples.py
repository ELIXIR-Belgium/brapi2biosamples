#!/usr/bin/env python
# coding: utf8

import json
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import click
import yaml
import base64
from datetime import datetime

ALL_ENDPOINTS = {
    "dev": {
        "token": "https://explore.api.aai.ebi.ac.uk/auth",
        "validate": "https://wwwdev.ebi.ac.uk/biosamples/validate",
        "submit": "https://wwwdev.ebi.ac.uk/biosamples/samples/",
        "sample": "https://wwwdev.ebi.ac.uk/biosamples/samples/",
        "update": "https://www.ebi.ac.uk/biosamples/samples/"
    },
    "stable": {
        "token": "https://api.aai.ebi.ac.uk/auth",
        "validate": "https://www.ebi.ac.uk/biosamples/validate",
        "submit": "https://www.ebi.ac.uk/biosamples/samples",
        "sample": "https://www.ebi.ac.uk/biosamples/samples/",
        "update": "https://www.ebi.ac.uk/biosamples/samples/"
    }
}


def url_path_join(*args):
    """Join path(s) in URL using slashes"""
    return '/'.join(s.strip('/') for s in args)


def characteristic(text, ontology=None):
    """
    Making a ENA Biosamples characteristic
    """
    if ontology:
        return [{"text": text, "ontologyTerms": [ontology]}]
    else:
        return [{"text": text}]


def fetch_token(endpoint, username, password):
    """
    Fetch token with username and password as parameters
    """
    print('  GET ' + endpoint)
    token = requests.get(endpoint, auth=(username, password))
    if token.status_code != 200:
        print(f"Problem with request: {str(token)}")
        raise RuntimeError("Non-200 status code")
    return (token.text)


def fetch_POST(endpoint, token, data):
    """
    Fetch single BrAPI object by path
    """
    print('  POST ' + endpoint)
    headers = {}
    headers['Accept'] = "application/hal+json"
    headers['Content-Type'] = "application/json;charset=UTF-8"
    headers['Authorization'] = f"Bearer {token}"
    r = requests.post(endpoint, data=data, headers=headers)
    if r.status_code == 201:
        return r.json()
    elif r.status_code != 200:
        print(f"Problem with request: {str(r)}")
        raise RuntimeError("Non-200 status code")
    return True


def fetch_object(endpoint, path):
    """
    Fetch single BrAPI object by path
    """
    url = url_path_join(endpoint, path)
    print('  GET ' + url)
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
        print(f"Problem with request: {str(r)}")
        raise RuntimeError("Non-200 status code")
    return r.json()["result"]


def fetch_objects(endpoint, path):
    """
    Fetch BrAPI objects with pagination
    """
    page = 0
    pagesize = 1000
    maxcount = 0
    url = url_path_join(endpoint, path)
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=15)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    params = {}
    output = []
    while maxcount == 0 or page < maxcount:

        params['page'] = page
        params['pageSize'] = pagesize
        print(f"  Retrieving page {page} of {str(maxcount)} from {str(url)}")
        print("  GET " + url)
        r = session.get(url, params=params)
        if r.status_code == 504 and pagesize != 100:
            pagesize = 100
            print("504 Gateway Timeout Error, testing with pagesize = 100")
            continue
        elif r.status_code != 200:
            print("Problem with request: " + str(r))
            raise RuntimeError("Non-200 status code")
        maxcount = int(r.json()['metadata']['pagination']['totalPages'])

        for data in r.json()['result']['data']:
            output.append(data)

        page += 1

        return output


def reconstruct_accession_name(germplasminfo):
    genus = germplasminfo['genus'] + ":"
    if 'holdingInstitute' in germplasminfo:
        institute = (germplasminfo['holdingInstitute']['acronym'] + ":")
    else:
        institute = (germplasminfo['instituteName'] + ":")
    accessionNumber = germplasminfo['accessionNumber']

    return genus + institute + accessionNumber


def generate_taxon_link(germplasminfo):
    ncbi_url = "http://purl.obolibrary.org / obo / NCBITaxon_"
    taxonIds = germplasminfo['taxonIds']
    for taxonId in taxonIds:
        if taxonId['sourceName'].upper() == "NCBI":
            ncbi_id = taxonId['taxonId']
            return ncbi_url + ncbi_id
        else:
            return germplasminfo['commonCropName']


def generate_synonyms(germplasminfo):
    def characterize(old_list):
        new_list = []
        for item in old_list:
            new_list.append({"text": item})
        return new_list
    synonyms = set()

    synonyms.add((germplasminfo['germplasmName']))
    if 'synonyms' in germplasminfo:
        if germplasminfo['synonyms']:
            for synonym in germplasminfo['synonyms']:
                synonyms.add(synonym)
    if 'defaultDisplayName' in germplasminfo:
        if germplasminfo['defaultDisplayName']:
            synonyms.add(germplasminfo['defaultDisplayName'])
    if 'externalReferences' in germplasminfo:
        if germplasminfo['externalReferences']:
            synonyms.add(germplasminfo['externalReferences'])
    return characterize(list(synonyms))


def decode_base64(json_data: dict, encode_fields: str):
    encode_fields = encode_fields.replace(", ", ",").split(",")

    i = 0
    keys = list(json_data.keys())
    while i < len(json_data) and len(encode_fields) > 0:
        entry = keys[i]
        i += 1
        if entry in encode_fields:
            if isinstance(json_data[entry], str):
                value = json_data[entry]
                decoded_value = {"text": base64.b64decode(value).decode('utf-8')}
                json_data[entry] = decoded_value
                encode_fields.remove(entry)
            if isinstance(json_data[entry], list):
                for e in range(len(json_data[entry])):
                    value = json_data[entry][e]['text']
                    decoded_value = {"text": base64.b64decode(value).decode('utf-8')}
                    json_data[entry][e] = decoded_value
                    encode_fields.remove(entry)
        if isinstance(json_data[entry], dict):
            j = 0
            nested_keys = list(json_data[entry].keys())
            while j < len(json_data[entry]):
                nested_entry = nested_keys[j]
                j += 1
                if nested_entry in encode_fields :
                    if isinstance(json_data[entry][nested_entry], str):
                        value = json_data[entry][nested_entry]
                        decoded_value = {"text": base64.b64decode(value).decode('utf-8')}
                        json_data[entry][nested_entry] = decoded_value
                        encode_fields.remove(nested_entry)
                    if isinstance(json_data[entry][nested_entry], list):
                        for e in range(len(json_data[entry][nested_entry])):
                            value = json_data[entry][nested_entry][e]['text']
                            decoded_value = {"text": base64.b64decode(value).decode('utf-8')}
                            json_data[entry][nested_entry][e] = decoded_value
                            encode_fields.remove(nested_entry)

    return json_data


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.version_option("0.1.0", "-v", "--version", prog_name="brapi2biosamples", help="Print version number")
@click.option("--trialdbid", "-t", help="The identifier of a trial", required=True)
@click.option("--endpoint", "-e", help="The URL towards the BrAPI endpoint, not ending with /", required=True)
@click.option("--date", "-d", help="The date of sample publication (example: 2021-01-20T17:05:13Z)",
              default=datetime.now().isoformat())
@click.option("--domain", "-D", help="The domain of your ENA account", required=True)
@click.option("--submit", "-s",
              help="When this flag is given, the samples will be submitted to BioSamples instead of being exported as JSON",
              is_flag=True)
@click.option("--dev", help="When this flag is given, the samples will be submitted to the dev instance of BioSamples",
              is_flag=True)
@click.option("--secret", help="Path to a secret.yml file to deliver the BioSample credentials",
              type=click.Path(exists=True))
@click.option("--update", help="Path to a tsv file to update submissions",
              type=click.Path(exists=True))
@click.option("--output", help="Path to a directory where the JSON files are written to.", type=click.Path(exists=True),
              default=".")
@click.option("--rename", "-N", help="If the \"germplasmDbId\" is source specific reconstruct the name with \"genus, instituteName and accessionNumber.\"", is_flag=True)
@click.option("--decode", "-c",
              help="Specify the fields that need to be decode by base64, split by coma. ex -c \"field 1, field 2\"")
def main(trialdbid, endpoint, date, domain, submit, dev, secret, output, rename, decode):
    """ Submits samples to BioSamples using the Breeding API """

    if submit:
        if not secret:
            print("A secret file with the credentials is mandatory when you want to do a submission.")
            exit()
        submissions = []
        if dev:
            print("--- This is a test submission ---")
            ENDPOINTS = ALL_ENDPOINTS['dev']
        else:
            ENDPOINTS = ALL_ENDPOINTS['stable']

        print("--- Requesting TOKEN ---")
        click.format_filename(secret)
        secret_file = open(secret, "r")
        credentials = yaml.load(secret_file, Loader=yaml.FullLoader)

        password = credentials['password'].strip()
        username = credentials['username'].strip()
        token = fetch_token(ENDPOINTS['token'], username, password)
        print("  Authentication is successful")

    print("--- Fetching germplasm data ---")
    # Fetch studies from trial
    trial = fetch_object(endpoint, f'/trials/{trialdbid}')
    added_germplasm = []
    # Loop over studies
    for study in trial['studies']:
        print(f"  - Getting germplasms from {study['studyDbId']}")
        # Get germplasmId's from study
        allgermplasms = fetch_objects(
            endpoint, f"/studies/{study['studyDbId']}/germplasm")
        for germplasm in allgermplasms:
            if germplasm['germplasmDbId'] not in added_germplasm:
                print(
                    f"  - Generating BioSamples JSON-LD for {germplasm['germplasmDbId']}")
                added_germplasm.append(germplasm['germplasmDbId'])
                # Get extra Germplasm information (Needed for PIPPA)
                germplasminfo = fetch_object(endpoint,
                                             f"/germplasm/{germplasm['germplasmDbId']}")

                if rename:
                    germjson = {"name": reconstruct_accession_name(germplasminfo),
                                "domain": domain,
                                "release": date,
                                "characteristics": {}}
                else:
                    germjson = {"name": germplasminfo['germplasmDbId'],
                                "domain": domain, "release": date, "characteristics": {}}
                germjson['characteristics']['project name'] = characteristic(
                    study['studyDbId'])
                germjson['characteristics']['biological material ID'] = characteristic(
                    germplasminfo['germplasmPUI'] if germplasminfo['germplasmPUI'] else germplasminfo['germplasmDbId'])
                germjson['characteristics']['synonyms'] = generate_synonyms(germplasminfo)
                germjson['characteristics']['organism'] = characteristic(
                    generate_taxon_link(germplasminfo) if germplasminfo['taxonIds']
                    else germplasminfo['commonCropName'])
                germjson['characteristics']['genus'] = characteristic(
                    germplasminfo['genus'])
                germjson['characteristics']['species'] = characteristic(
                    germplasminfo['species'])
                germjson['characteristics']['infraspecific name'] = characteristic(
                    germplasminfo['subtaxa'])
                germjson['characteristics']['material source ID'] = characteristic(
                    germplasminfo['germplasmPUI'] if germplasminfo['germplasmPUI'] else germplasminfo['germplasmDbId'])

                if decode:
                    germjson = decode_base64(germjson, decode)

                if submit:
                    print(
                        f"  - Validating the JSON-LD schema of {germplasm['germplasmDbId']}")
                    validate = fetch_POST(
                        ENDPOINTS['validate'], token, json.dumps(germjson))
                    if validate:
                        print("  Validation was successful")
                    print(
                        f"  - Submitting the JSON-LD schema of {germplasm['germplasmDbId']}")
                    submit = fetch_POST(
                        ENDPOINTS['submit'], token, json.dumps(germjson))
                    print(
                        f"  Sample was successfully submitted as:\n    Name: {submit['name']}\n    Accession: {submit['accession']}\n    URL: {ENDPOINTS['sample'] + submit['accession']}")
                    submissions.append(f"{submit['name']}\t{submit['accession']}")
                else:
                    filepath = os.path.join(
                        output, f"o_{germplasm['germplasmDbId']}.json")
                    with open(filepath, 'w') as outfile:
                        outfile.write(json.dumps(germjson, indent=4, ensure_ascii=False))
                    print(
                        f"  BioSample JSON-LD from {study} dumped as {filepath}")
    if submit:
        with open('submission_details.text', 'w') as submitfile:
            submitfile.write('\n'.join(submissions))
        print("All accession numbers of the submissions or written to submission_details.text")
        print(f"Submission of {len(added_germplasm)} samples to BioSamples has successfully ended")
    else:
        print("Dumping successful")

if __name__ == "__main__":
    main()
