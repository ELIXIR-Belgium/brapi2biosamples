[![Python package](https://github.com/ELIXIR-Belgium/brapi2biosamples/actions/workflows/python-package.yml/badge.svg)](https://github.com/ELIXIR-Belgium/brapi2biosamples/actions/workflows/python-package.yml)

# BrAPI 2 BioSamples

Command Line Interface (CLI) to generate BioSamples ready JSON and to submit samples to [BioSamples](https://wwwdev.ebi.ac.uk/biosamples) using the [Breeding API](https://brapi.org/). 
The submission is compliant with the [MIAPPE BioSamples validation scheme](https://github.com/EBIBioSamples/biosamples-v4/blob/master/webapps/core/src/main/resources/schemas/certification/plant-miappe.json).

## Prerequisites

- The credentials of a BioSamples account. Register [here](https://explore.aai.ebi.ac.uk/registerUser).
- The BioSamples account is added to a domain. This domain will be used as a parameter in the CLI.
- A BrAPI endpoint of version 1.2/1.3 with following endpoints and attributes available:
  - /trials/{trialDbId}
  - /studies/{studyDbId}/germplasm
  - /germplasm/{germplasmDbId}
    - `germplasmDbId`
    - `commonCropName`
    - `genus`
    - `species`
    - `accessionNumber`
    - `germplasmName`
- The trailDbId of a trial you want to submit the data of
- Python >=3.5


## Installation

Simply use following command line to install brapi2biosamples fetcher on linux/macOS:

```
sudo python3 -m pip install git+git://github.com/bedroesb/brapi2biosamples.git
```

or this command for Windows (be sure that Python is installed):

```
pip install git+git://github.com/bedroesb/brapi2biosamples.git
```

## Usage

When brapi2biosamples is installed correctly it should be available through the command `brapi2biosamples`. You can easily test which version is installed with `brapi2biosamples -v`. The tool has several mandatory options:

```
brapi2biosamples [OPTIONS] 
```

| Option               | Description                                                                                            | Required |
|----------------------|--------------------------------------------------------------------------------------------------------|----------|
| -v, --version        | Print version number                                                                                   |          |
| -t, --trialDbId      | The identifier of a trial                                                                              | yes      |
| -e, --endpoint       | The URL towards the BrAPI endpoint, not ending with /                                                  | yes      |
| -d, --date           | The date of sample publication (example:2021-01-20T17:05:13Z)                                          |          |
| -D, --domain         | The domain of your ENA account                                                                         | yes      |
| -s, --submit         | When this flag is given, the samples will be submitted to BioSamples instead of being exported as JSON |          |
| --dev                | When this flag is given, the samples will be submitted to the dev instance of BioSamples               |          |
| --secret             | Path to a secret.yml file to deliver the BioSample credentials                                         |          |
| --output             | Path to a directory where the JSON files are written to.                                               |          |
| -h, --help           | Show this message and exit.                                                                            |          |


- If the brapi2biosamples CLI is used without the `--submit` flag, it will dump the JSON files for submission in the working directory or in an output directory specified by the `--output` option. It is recommended to try out your endpoints this way before actual submission.
- When the JSON look fine, add the `--submit` flag to your command + the `--secret` option (mandatory on submission) and samples will be submitted to BioSamples. The `--secret` option points towards a .secret.yml file with. Please follow the syntax of the example secret.yml in this repository. 
- It is possible to submit to the BioSamples dev instance for testing purposes by adding the `--dev` flag to your command.
- If you do not specify the sample publication date with the `--date` option, the current time will be used.
- After submission a file will be created with all the BioSample accession numbers of the corresponding samples.


## Examples

### Dumping the BioSample json files 

- Minimal
    ```
    brapi2biosamples -t 1 -e "https://pippa.psb.ugent.be/BrAPIPPA/brapi/v1" -D "self.pippa_submission"
    ```
- With output directory defined
    ```
    brapi2biosamples -t 1 -e "https://pippa.psb.ugent.be/BrAPIPPA/brapi/v1" -D "self.pippa_submission" --output ./test/
    ```

### Submitting the samples to the dev instance of BioSamples

- Minimal:
    ```
    brapi2biosamples --dev -e "https://pippa.psb.ugent.be/BrAPIPPA/brapi/v1/" -t 1 -D "self.pippa_submission" --submit --secret .secret.yml 
    ```
