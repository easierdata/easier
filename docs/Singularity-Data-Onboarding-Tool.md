# Singularity - Data Onboarding Tool

Singularity offers a modular end-to-end solution designed to simplify the process of onboarding datasets to Filecoin storage providers.

:gear: [GitHub Repo](https://github.com/data-preservation-programs/singularity)
:green_book: [Documentation](https://data-programs.gitbook.io/singularity/overview/readme)
----



----

## Resources

Details [here](https://data-programs.gitbook.io/singularity/installation/install-from-source) on installing singularity from source.

Details [here](https://data-programs.gitbook.io/singularity/installation/install-from-docker) on installing via docker. Docker compose `.yml` can be found [here](https://github.com/data-preservation-programs/singularity/blob/main/docker-compose.yml) which installs a Postgres database image.
- [Singularity Workshop Guide](https://gist.github.com/SgtCoin/6a9513afedbf8875d01655f039ad9d2e) - A guide going through all the steps to prepare data with Singularity.
    1. Prepare an open dataset from S3
    2. Send deal to a local emulated storage provider `f02815405`
    3. Make retrievals from the emulated storage provider using HTTP and Bitswap

[Swagger page](http://127.0.0.1:9090/swagger/index.html#/) - Used alongside the singularity API service.  Useful for testing different HTTP Requests. The URL uses the default port of 9090. Modify if you’ve started the service on a different port.

[Data Preparation for Filecoin](https://github.com/filecoin-project/data-prep-tools/tree/main) - Repository containing notes and details related to data preparation

## Onboarding Data with Singularity

Singularity was designed with a modular approach to simplify the data onboarding process into four steps:

1. Initialize the Database
2. Connect to storage system by creating a ***storage profile***
3. Build a preparation by creating a ***preparation profile***
4. Run the preparation by initializing a ***task*** and starting the ***task runner***.
    - Two ***tasks*** must be ran to fully prepare a dataset. `start-scan` to scan the entire storage profile and `start-daggen` to build DAGs and generate CIDs.

After the running all the preparation tasks, you can run the command `singularity prep list-pieces <preparation id|name>` to view all the [pieces](https://spec.filecoin.io/systems/filecoin_files/piece/) generated.

## Additional Details

Singularity chunks content into a [fixed 1048576 byte sized blocks](https://github.com/data-preservation-programs/singularity/blame/0bcd9730627f30ed110c4a8cd3e09226e258fbde/pack/packutil/util.go#L25) (1MiB) instead of varied sizes e.g. [rabin chunking](https://docs.ipfs.tech/concepts/file-systems/#chunking).  The reasoning behind this is to estimate the CAR file size deterministically, so that the chunking strategy is determined by only looking at the size of the file.  While a larger block size would incur less overhead for data preparation e.g. less indexing and fewer rows to store block CIDs, the team behind Singularity selected a fixed max size of 1Mib as that is what has been historically used to work with the [bitswap protocol](https://specs.ipfs.tech/bitswap-protocol/#block-sizes).

---

Running the command `singularity prep list-pieces` prints details about the Merkle DAG generated when the storage source was scanned and ran through the `dag-gen` process. Below is an example of the `Pieces` section.

```bash
Pieces
PieceCID                                                          PieceSize    RootCID                                                      FileSize     StoragePath
baga6ea4seaqjc7tu6jzjk25pig66yjgt5mwvmh6femnh4tqu2bwsmcjrdhjc4jy  34359738368  bafkreihv6xzt6ilyxqjxv2wmixee57akes3teq326hby4rl65wc5jviqra  33288823369
baga6ea4seaqbfnvhtltzxkzcwtqggfczhaz47vnptjtuiet5im4u4sblcqw7yha  34359738368  bafkreihyc6emv45dbr2udpn5ygcji3ldgujyd4hyub3me445nqgqchvvd4  20434687249
baga6ea4seaqao7bk7tok526vmdk65ehjo7zemaca7tbddnn6whac5k34gcjnady  34359738368  bafybeidwz36ir3cfwdgerldhl4qkeiccdjans4h5d4hbq6lbvr7p4x622q  2334629
```

`PieceCID` also known as [*CommP* or *Piece Commitment*](https://github.com/filecoin-project/go-fil-commp-hashhash?tab=readme-ov-file), represents the content identifier (CID) of the CAR file, a serialized version of the Merkle DAG. It’s the main unit of negotiation for data on the Filecoin network and is designed for proving storage of arbitrary IPLD graphs and client data. The provider has to construct the CAR file out of the file received and derive the [**Piece CID**](https://spec.filecoin.io/#section-systems.filecoin_files.piece.data-representation) on their side. In order to avoid the client sending a different file to the one agreed, the Piece CID that the provider generates has to be the same as the one included in the deal negotiated earlier.

`PieceSize` also known as [sector size](https://spec.filecoin.io/#section-glossary.sector), represents target piece size of the CAR files used for piece commitment calculation.

⚠️ The default max size of a piece is 31.5GiB. More details on sector sizes can be found [here](https://spec.filecoin.io/#section-systems.filecoin_mining.sector).


`RootCID` commonly called **Payload CID**, that represents the content identifier (CID) associated with any of the blocks in the DAG.  **This CID is common between the CAR’ed and un-CAR’ed constructions and is important when data is transferred between the storage client and the storage provider. The retrieval deal is negotiated on the basis of the ***Payload CID***. When the retrieval deal is agreed, the retrieval miner starts sending the unsealed and “un-CAR’ed” file to the client. The transfer starts from the root node of the IPLD Merkle Tree and in this way the client can validate the ***Payload CID*** from the beginning of the transfer and verify that the file they are receiving is the file they negotiated in the deal and not random bits.

`FileSize` represents the actual size of the raw file content in the CAR file.

> 🤔 The piece with the smallest `FileSize` represents the **CAR Manifest** while the others represent the **CAR Data Payload**.
>
> The **CAR Manifest** is a snapshot of the source storage's unixfs directory > structure. It only contains the CIDs of unixfs-like objects, i.e., files and folders, that map to the raw blocks >found in the CAR Data Payload. Tools like go-car CLI commands can quickly print out the CIDss for all the unixfs objects.
>


---

#### **How to setup in-line prep**

Data onboarding requires double the hard drive capacity since the source data is duplicated into a collection of CAR files. Inline preparation can help save space by mapping the blocks of CAR files back to the original data source so that there is no need to store the exported CAR files. More info on this can be found [here](https://data-programs.gitbook.io/singularity/topics/inline-preparation).


  > ✅ Do not pass in the `--output` option in the `prep create` command to enable inline preparation.
  >
  > When an output source is designated, CAR files are exported to that location. CAR retrieval requests prioritize these directories. If the CAR files are removed by the user, the system reverts to fetching from the original data source.

#### Notes & Tips

<details>
  <summary><b>Resetting Database</b> - When testing, it’s useful to start with a fresh database by clearing out any content created from a previous run. </summary>

  ```bash
  NAME:
      singularity admin reset - Reset the database

  USAGE:
      singularity admin reset [command options] [arguments...]

  OPTIONS:
      --really-do-it  Really do it (default: false)
      --help, -h      show help
  ```

  > ⚠️ You must pass in the `--really-do-it` argument to reset the database.  This argument was added to minimize the chance of accidentally resetting the database.

</details>

<details>
  <summary><b>Connecting to a Postgres instance</b>: You can override the default sqlite3 database instance that Singularity uses by passing in the `-database-connection-string` option to the commands.</summary>

  ```bash
  Database Backend Support:
        Singularity supports multiple database backend: sqlite3, postgres, mysql5.7+
        Use '--database-connection-string' or $DATABASE_CONNECTION_STRING to specify the database connection string.
          Example for postgres  - postgres://user:pass@example.com:5432/dbname
          Example for mysql     - mysql://user:pass@tcp(localhost:3306)/dbname?parseTime=true
          Example for sqlite3   - sqlite:/absolute/path/to/database.db
                      or        - sqlite:relative/path/to/database.d

  Example command with option:
      `singularity --database-connection-string admin init`
  ```

>
> ⚠️ You must pass in the `--database-connection-string` option before the command name as it is a **GLOBAL** option. Additionally, it must be added to each succeeding command.

</details>

<details>
  <summary><b>Changing the go-log options</b> - You can control options such as log level and log format with environment variables. More details can be found at https://github.com/ipfs/go-log</summary>

  ```bash
  * GOLOG_LOG_LEVEL  - example values: debug, info, warn, error, dpanic, panic, fatal
  * GOLOG_LOG_FMT    - example values: color, nocolor, json
  ```

</details>

<details>
  <summary><b>Useful commands options</b>: Below are a list of options that I’ve used quite often for various purposes.</summary>

  > ⚠️ Options with the `🌐` tag are GLOBAL options that must be placed before the singularity command i.e. `singularity <GLOBAL option> <command>`.

- `--verbose`  Enable verbose output. This will print more columns for the result as well as full error trace (default: false) `🌐`
- `--json` Enable JSON output.  This is useful for instances when you would like to have the command output and logging output structure to be formatted as JSON `🌐`
- `--client-scan-concurrency` Option to pass into the `singularity storage create` command to set the max number of CPU cores for listing requests when scanning data source (default: 1)
- `--concurrency` Option to pass into the `singularity run dataset-worker` command to set the max number of CPU cores for concurrent workers to run (default: 1)
- `singularity prep list-pieces` List the generated `PieceCID` and `RootCID` of all pieces created.
- `singularity prep list`  List the name and ID’s of all preparations
- `singularity storage list` List the name and ID’s of all storage system connections
- `singularity storage explore <name|id> [path]`  Explore a specific storage by listing all content under a path.  To view content at the root path, pass in `/` for `[path]`
- `singularity prep explore <preparation id|name> <storage id|name> [path]`  Explore a preparation by listing all content under a path.  To view content at the root path, pass in `/` for `[path]`. Since the Merkle DAGs retain the file pathing, you can navigate a directory structure and identify the

</details>
