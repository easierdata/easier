# EASIER Data Initiative

## Table of Contents

- [Installation](#installation)
  - [Clone Repo and create Python Virtual Environment](#clone-repo-and-create-python-virtual-environment)
  - [Installing Static Code Analysis Tools](#installing-static-code-analysis-tools)
  - [Install Singularity](#install-singularity)
  - [Install IPFS](#install-ipfs)
  - [Install Lotus](#install-lotus)
- [Prepare Data for Filecoin Deal](#prepare-data-for-filecoin-deal)
  - [Optimize Data for CAR file packing](#optimize-data-for-car-file-packing)
  - [Pack Data into CAR files](#pack-data-into-car-files)
  - [Distribute .CAR files to storage providers](#distribute-car-files-to-storage-providers)
- [Make Filecoin Deal](#make-filecoin-deal)
  * [Use Singularity to make Filecoin Deal](#use-singularity-to-make-filecoin-deal)
- [Enrich STAC server with CIDs](#enrich-stac-server-with-cids)
  - [Use Deal Manifest File to Create STAC metadata](#use-deal-manifest-file-to-create-stac-metadata)
  - [Run Sample Queries to Test STAC Server](#run-sample-queries-to-test-stac-server)
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

This project uses [Poetry](https://python-poetry.org/) for dependency management and is compatible with python versions >3.9 and <3.12. To install all necessary dependencies, follow these steps:

> **Note**: Mac OS with M1 chip may encounter problems
> A general solution is to use `brew install` for the missing executable.
> See description and solution at https://github.com/pyproj4/pyproj/issues/1027

1. Install Poetry if you haven't already:

   ```shell
   curl -sSL https://install.python-poetry.org | python3 -
   ```
2. Clone the repository:

   ```shell
   git clone https://github.com/easierdata/easier.git
   cd easier
   ```
3. Install the dependencies:

   ```shell
   poetry install
   ```

## Installing Static Code Analysis Tools

The linters **[Black](https://github.com/psf/black)**, **[Mypy](https://github.com/python/mypy)** and **[Ruff](https://github.com/astral-sh/ruff)** have been integrated into a [pre-commit](https://pre-commit.com/#2-add-a-pre-commit-configuration) configuration file (file named `.pre-commit-config.yaml`) as to ensure that no bugs or issues appear in your code before pushing changes to your repo. To install the pre-commit git hooks:

1. Run the following command:

   ```shell
   pre-commit install
   ```

   now `pre-commit` will run automatically on `git commit`.
2. (Optional) Run against all files in your repo with the following command:

```shell
pre-commit run --all-files
```

### Adding more pre-commit plugins

[Adding pre-commit plugins](https://pre-commit.com/#adding-pre-commit-plugins-to-your-project) to your project is done with the `.pre-commit-config.yaml` configuration file. To view a list of all supported plugins, visit this [link](https://pre-commit.com/hooks.html).

### Install Fast API STAC Server

We use the [Fast API STAC Server](https://github.com/stac-utils/stac-fastapi) to serve STAC metadata and respond to STAC API requests. The server is configured to use a PostgreSQL database to store STAC metadata. The server and database are run in Docker containers and spun up with docker compose.

Once installed, you can run the server and database with the following command:

```shell
make docker-run-pgstac
```

### Install Singularity

See the [Singularity documentation](https://github.com/tech-greedy/singularity/blob/main/getting-started.md) for installation steps.

### Install IPFS

TODO

### Install Boost

See [Building and Installing Boost](https://github.com/filecoin-project/boost#building-and-installing-boost) for installation steps.

## Prepare Data for Filecoin Deal

### Optimize Data for CAR file packing

Currently, there is a performance hit when multiple sectors are accessed when retrieving files on Filcoin. For geospatial data, there is an opportunity for optimization by packing data that is 'nearer' to each other in each sector. This can reduce the number of sectors accessed when retrieving data. See [this blog post] for more info.

### Pack Data into CAR files

by the [Storage Provider](https://filecoin.io/blog/posts/a-deep-dive-into-the-storage-provider-ecosystem/). If you are working with a SP, ask them if they can perform this step for you.

Before making a Filecoin deal, the data will need to be serialized into a [“Content-Addressable aRchive”](https://ipld.io/specs/transport/car/) (.car) file, which is in raw bytes format. This .car file represents a [Filecoin Piece](https://spec.filecoin.io/systems/filecoin_files/piece/) which is the main unit of negotiation for data that users store on the Filecoin network.

We will use Singularity to pack data into .CAR files. See the [Singularity Docs](https://github.com/tech-greedy/singularity/blob/main/getting-started.md) for more info.
[Example Python Notebook to pack CAR files](https://github.com/easierdata/easier/blob/main/code/Pynotebooks/Singularity_CARGenerator.ipynb)

### Distribute .CAR files to storage providers

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

### Use Singularity to make Filecoin deal.

We'll point you to the singularity docs for this step. See [this section](https://github.com/tech-greedy/singularity/blob/main/getting-started.md#deal-making) of the docs for more info on how to create a deal.

## Enrich STAC server with CIDs

### Use Deal Manifest File to create STAC metadata

If you are working with an SP, you will need to get the CIDs from them. Here is a [script]() you can follow to ask the SP for the CIDs. Once you have the CIDs, you can run the following command to enrich the STAC server with the CIDs.

```shell
$ python3 code/pyScripts/validate_stac.py --stac_file testdata/<filename>.json
$ make run-landsat-pgstac
```

### Run Sample Queries to Test STAC Server

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
  `<a href="https://github.com/easierdata/easier/compare" rel="noopener noreferrer" target="_blank">`
  `https://github.com/easierdata/easier/compare</a>`.

---

## FAQ

-- TODO

## License

[![License](http://img.shields.io/:license-mit-blue.svg?style=flat-square)](http://badges.mit-license.org)

- **[MIT license](http://opensource.org/licenses/mit-license.php)**
