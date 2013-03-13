# Jobsearch

This is a set of Python scripts that allow you to search for jobs from the
command line.

Currently it searches Github Jobs, Indeed.com and YQL Craigslist JSON APIs
for data and presents the results in glorious 4-bit color.

The script operates in two modes -- "load" and "search."

# Loading Data

The `load` command retrieves job data and sends it to an ElasticSearch
instance to be indexed. Duplicates from a given web service are usually caught,
but cross-service duplicates are not.

## The "load.sh" script

I've included a `load.sh` script that I use to retrieve and index data every
day. It executes several `--load`` commands consecutively to build a nice set
of job data.

# Searching

The `search` command searches the ElasticSearch instance for jobs matching
a query. E.g.:

`./run.py search

# Requirements

- Python 2.7
- ElasticSearch
- An Indeed.com publisher ID to search Indeed (free)
