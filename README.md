# AggrDataSnap Usage Guide

## Description
AggrDataSnap is a command-line tool for managing NetApp storage aggregates. It retrieves and displays detailed storage and volume data, including size, usage, and allocation statistics. The tool supports exporting data in JSON, CSV, and TXT formats, offering an efficient solution for monitoring and analyzing storage resources.

## Requirements

- Python 3.x
- The following Python libraries:
  - `requests`
  - `docopt`
  - `hurry.filesize`
  - `prettytable`
  - `yaml`
  - `base64`

Install the required libraries using:
```bash
pip install requests docopt hurry.filesize prettytable PyYAML
```
## Usage
Run the program using the following syntax:
```bash
python snap_aggr.py <storage> <aggr>
```

## Options
- `<storage>`: The storage system address (e.g.,` netapp.example.com`)
- `<aggr>`: The name of the aggregate you want to query.

```bash
python snap_aggr.py netapp.example.com aggr1
```
This will fetch and display the aggregate and volume data, saving results in the following formats:

- JSON: aggr1/aggr1.json
- CSV: aggr1/aggr1.csv
- TXT: aggr1/aggr1.txt

### Additional Commands:
- To view the version information:
```bash
python snap_aggr.py --version

```
- To display help:
```bash
python snap_aggr.py -h

```