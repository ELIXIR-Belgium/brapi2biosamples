from setuptools import setup, find_packages

with open("README.md", 'r') as f:
    long_description = f.read()

with open('requirements.txt', 'r') as f:
    required = f.read().splitlines()

setup(
    name='brapi2biosamples',
    version='0.1.0',
    keywords=["pip", "brapi2biosamples", "cli", "biosamples", "upload", "JSON", "EBI"],
    description='Command Line Interface to upload data to the European Nucleotide Archive',
    author="Bert Droesbeke",
    author_email="bedro@vib.ugent.be",
    long_description_content_type='text/markdown',
    packages=['.'],
    long_description=long_description,
    url="https://github.com/ELIXIR-Belgium/brapi2biosamples",
    license='MIT',
    install_requires=[required],
    classifiers=[
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.5',
    entry_points={
      'console_scripts': ["brapi2biosamples=brapi2biosamples:main"]
  },
)
