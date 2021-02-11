# BrAPI 2 BioSamples

Command Line Interface (CLI) to submit samples to [BioSamples](https://wwwdev.ebi.ac.uk/biosamples) using the [Breeding API](https://brapi.org/)


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

When brapi2biosamples fetcher is installed correctly it should be available through the command `brapi2biosamples`. You can easily test which version is installed with `brapi2biosamples -v`. The tool has several mandatory parameters:

```
brapi2biosamples [OPTIONS] 
```

| Option               | Description                                                                                            | Required |
|----------------------|--------------------------------------------------------------------------------------------------------|----------|
| -v, --version        | Print version number                                                                                   |          |
| -t, --trialDbId      | The identifier of a trial                                                                              | yes      |
| -e, --endpoint       | The URL towards the BrAPI endpint, not ending with /                                                   | yes      |
| -d, --date           | The date of sample publication (example:2021-01-20T17:05:13Z)                                          | yes      |
| -D, --domain         | The domain of your ENA account                                                                         | yes      |
| -s, --submit         | When this flag is given, the samples will be submitted to BioSamples instead of being exported as JSON |          |
| --dev                | When this flag is given, the samples will be submitted to the dev instance of BioSamples               |          |
| --secret             | Path to a secret.yml file to deliver the BioSample credentials                                         |          |
| --output             | Path to a directory where the JSON files are written to.                                               |          |
| -h, --help           | Show this message and exit.                                                                            |          |


## Examples


trial_id = "1"
endpoint = "https://pippa.psb.ugent.be/BrAPIPPA/brapi/v1"
date = "2021-01-20T17:05:13Z"
domain = "self.pippa_submission"
