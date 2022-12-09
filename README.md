# EASIER Data Initiative
## Table of Contents

- [Installation](#installation)
  * [Clone Repo and create Python Virtual Environment](#clone-repo-and-create-python-virtual-environment)
   * [Install Singularity](#install-singularity)
- [Features](#features)
- [Contributing](#contributing)
- [FAQ](#faq)
- [License](#license)


## Terminology
- **SP** - Storage Provider
- **CID** - Content Identifier
- **CAR** - Content-Addressable aRchive
- **Piece** - The main unit of negotiation for data that users store on the Filecoin network.
- **Sector** - A sector is a fixed-size (32GiB) chunk of data that is stored on the Filecoin network. A sector is made up of one or more pieces. A sector is the smallest unit of storage that a storage provider can commit to storing on the Filecoin network.
- **Deal** - A deal is a commitment by a storage provider to store a piece of data for a client. A deal is made up of a piece and a sector. A deal is the smallest unit of storage that a client can commit to storing on the Filecoin network.
- **STAC** - SpatioTemporal Asset Catalog
- **S3** - Amazon Simple Storage Service
- **Singularity** - A tool for packing data into CAR files and creating Filecoin deals.



## Installation

### Clone Repo and create Python Virtual Environment
```shell
# first install Python 3.10.8 (have not tested newer versions, but they could work)
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

### Install Fast API STAC Server
We use the [Fast API STAC Server](https://github.com/stac-utils/stac-fastapi) to serve STAC metadata and respond to STAC API requests. The server is configured to use a PostgreSQL database to store STAC metadata. The server and database are run in Docker containers and spun up with docker compose.

Once installed, you can run the server and database with the following command:
```
make docker-run-pgstac
```

### Install Singularity
See the [Singularity documentation](https://github.com/tech-greedy/singularity/blob/main/getting-started.md) for installation steps.

### Install IPFS
TODO

### Install Lotus
TODO

## Prepare Data for Filecoin Deal

### Optimize Data for CAR file packing (Optional)
Currently, there is a performance hit when multiple sectors are accessed when retrieving files on Filcoin. For geospatial data, there is an opportunity for optimization by packing data that is 'nearer' to each other in each sector. This can reduce the number of sectors accessed when retrieving data. See [this blog post] for more info.

### Pack Data into CAR files
*This step is often performed by the [Storage Provider](https://filecoin.io/blog/posts/a-deep-dive-into-the-storage-provider-ecosystem/). If you are working with a SP, ask them if they can perform this step for you.

Before making a Filecoin deal, the data will need to be serialized into a [“Content-Addressable aRchive”](https://ipld.io/specs/transport/car/) (.car) file, which is in raw bytes format. This .car file represents a [Filecoin Piece](https://spec.filecoin.io/systems/filecoin_files/piece/) which is the main unit of negotiation for data that users store on the Filecoin network.

We will use Singularity to pack data into .CAR files. See the [Singularity Docs](https://github.com/tech-greedy/singularity/blob/main/getting-started.md) for more info. 
[Example Python Notebook to pack CAR files](https://github.com/easierdata/easier/blob/main/code/Pynotebooks/Singularity_CARGenerator.ipynb)

### Distribute .CAR files to storage providers (Optional)
*In order to finalize a Filecoin deal, the storage provider will need access to the data (raw or placed into .CARs). There are a few ways to do this. If you are not working with a SP, you can skip this step.

A - Transfer the data manually by flying/mailing physical hard drives to the SP.

B - Transfer Data to S3 Bucket holding area

When we worked with an SP, we used [Rsync](https://ss64.com/bash/rsync.html) to transfer the data to an S3 bucket. The SP then pulled the data from the S3 bucket and placed it into Filecoin deals.

[Script we used to transfer the data to S3](https://github.com/easierdata/easier/blob/main/code/shellScripts/egress_to_s3.sh)

C - Set up an HTTP server on your own infrastructure so the data can be pushed/pulled to the SP.

```shell
sudo apt install nginx
```

Edit `/etc/nginx/sites-available/default` and add below lines

```text
server {
  ...
  location / {
    root /home/user/outDir;
  }
  ...
}
```
where `outDir` is the directory where the CAR files are located.

If you are working with a SP, you can stop here. If you are not working with a SP, you will need to continue with the following steps.

## Make Filecoin Deal
We'll point you to the singularity docs for this step. See [this section](https://github.com/tech-greedy/singularity/blob/main/getting-started.md#deal-making) of the docs for more info on how to create a deal.

## Enrich STAC server with STAC metadata file with CIDs
If you are working with an SP, you will need to get the CIDs from them. Here is a [script]() you can follow to ask the SP for the CIDs. Once you have the CIDs, you can run the following command to enrich the STAC server with the CIDs.

```shell
$ python3 code/pyScripts/validate_stac.py --stac_file testdata/<filename>.json
$ make run-landsat-pgstac
```

## Run Sample Queries to make sure everything is working
```shell
$ curl http://<domain>/stac/collections
$ curl http://<domain>/stac/search?bbox=-122.5,37.5,-122.3,37.7&datetime=2019-01-01/2019-12-31
```

## Features
- Fetch Landsat Data via API
- Pack car files with Singularity
- Web3-enriched STAC-Server

## Coverage
-- TODO
## Tests
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
