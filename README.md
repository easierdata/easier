# EASIER Data Initiative
## Table of Contents

- [Installation](#installation)
- [Features](#features)
- [Contributing](#contributing)
- [FAQ](#faq)
- [License](#license)

## Installation

### Setup Environment
```shell
# first install Python 3.8.10 (have not tested newer versions, but they could work)
$ git clone git@github.com:easierdata/easier.git
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install --upgrade pip
$ python3 -m pip install -r requirements/requirements.txt -c requirements/constraints.txt
$ pre-commit install
```
- Mac OS with M1 chip may encounter problems
A general solution is to use `brew install` for the missing executable.
See description and solution at https://github.com/pyproj4/pyproj/issues/1027

### [Install Fast-API STAC server](https://github.com/stac-utils/stac-fastapi)

## Pack, Store, and Retrieve Data from IPFS

Before making a Filecoin deal, the data will need to be serialized into a [“Content-Addressable aRchive”](https://ipld.io/specs/transport/car/) (.car) file, which is in raw bytes format. This .car file represents a [Filecoin Piece](https://spec.filecoin.io/systems/filecoin_files/piece/) which is the main unit of negotiation for data that users store on the Filecoin network.

### [Car File Generation](https://github.com/easierdata/easier/blob/main/code/Pynotebooks/Singularity_CARGenerator.ipynb)
*This step is often performed by the [Storage Provider](https://filecoin.io/blog/posts/a-deep-dive-into-the-storage-provider-ecosystem/). If you do not care how the data is placed into cars, you can skip this step.

See the [Singularity Docs](https://github.com/tech-greedy/singularity/blob/main/getting-started.md) for more info. 

### [Transfer Data to S3 Bucket holding area](https://github.com/easierdata/easier/blob/main/code/shellScripts/egress_to_s3.sh)
In order to finalize a Filecoin deal, the storage provider will need access to the data (raw or placed into .CARs). You can definitely expose an endpoint on your own infrastructure, but a common pattern is to send the data to an intermediary location from which the storage provider can stream the data.

### Create Filecoin Deal
--WIP

### Pin Data to IPFS
--TODO

## Tutorials
--TODO

## Features
-- Fetch Landsat Data via API
-- Pack car files with Singularity
-- Web3-enriched STAC-Server

## Coverage
-- TODO
## Test
-- TODO
## Lint
```shell
$ flake8 easier/code
```

---

## Contributing
### Step 1

- **Option 1**
  - 🍴 Fork this repo!

- **Option 2**
  - 👯 Clone to your local machine using:
    ```shell
    $ git clone git@github.com:easierdata/easier.git
    ```
### Step 2

- **HACK AWAY!** 🔨🔨🔨
### Step 3

- 🔃 Create a new pull request using:
  <a href="https://github.com/easierdata/easier/compare" rel="noopener noreferrer" target="_blank">
  `https://github.com/easierdata/easier/compare`</a>.

---

## FAQ
-- TODO
## License

[![License](http://img.shields.io/:license-mit-blue.svg?style=flat-square)](http://badges.mit-license.org)

- **[MIT license](http://opensource.org/licenses/mit-license.php)**
