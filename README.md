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

## Fetch, Pack, Store, and Retrieve Data from IPFS

### [Fetch Landsat Data via API](https://github.com/easierdata/easier/blob/main/code/Pynotebooks/Inventory_check_Landsat.ipynb)

### [Car File Generation](https://github.com/easierdata/easier/blob/main/code/Pynotebooks/Singularity_CARGenerator.ipynb) (Some storage providers will generate CAR files for you. If not, you can use this script)

See the [Singularity Docs](https://github.com/tech-greedy/singularity/blob/main/getting-started.md) for more info. 

### Transfer Data to S3 Bucket holding area

### Create Filecoin Deal

### Pin Data to

### Fetch Landsat Data via STAC-API (Link to Blog Post)




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
