#!/usr/bin/env python
import HTMLParser

import argparse
import datetime
import os
import dateutil.parser
import dateutil
import html2text
import providers
import pydoc

from itertools import chain
from termcolor import colored
from pyelasticsearch import ElasticSearch


es = ElasticSearch(os.environ['ELASTIC_SEARCH_URL'])

default_providers = {
    'github': providers.Github(),
    'indeed': providers.Indeed(os.environ['INDEED_API_KEY']),
    'craigslist': providers.Craigslist()
}

parser = argparse.ArgumentParser(description='Search for jobs.')
parser.add_argument('--load', dest='load', action='store_true', help='load jobs')
parser.add_argument('--search', dest='search', action='store_true', help='find jobs')
parser.add_argument('--shell', dest='shell', action='store_true', help='interactive shell')
parser.add_argument('--location', dest='location', help='job location')
parser.add_argument('--query', dest='query', help='job query (e.g., "python"')
parser.add_argument('--show-description', dest='show_desc', action='store_true', help='show job descriptions')
parser.add_argument('--num-results', dest='num_results', help='number of results to include', default=100)
parser.add_argument('--max-age', dest='max_age', help='max age (days) of jobs', default=100)
parser.add_argument('--provider', nargs='*', dest='providers',
                    help='job provider', action='append')
parser.add_argument('--exclude-provider', nargs='*', dest='exclude_providers',
                    help='exclude a job provider', action='append')


def get_providers(provider_input):
    """
    Return a set of providers by looking up, in `default_providers`, a provider
    for each provider name  given in the iterable ``provider_input``.
    """
    if not provider_input:
        return set()

    found = {default_providers.get(provider, None) for provider in
             chain.from_iterable(provider_input)}

    return filter(None, found)


def get_job_output(job):
    job['title'] = colored(job['title'], 'green')
    job['location'] = colored(job['location'], 'cyan')
    job['company'] = colored(job['company'], 'blue')

    try:
        job['description'] = html2text.html2text(job['description'])
    except HTMLParser.HTMLParseError:
        pass

    if args.show_desc:
        line = u'{title} ({age} days ago)\n{company} ({location})\n{description}{url}\n{id}\n\n'
    else:
        line = u'{title} ({age} days ago)\n{company} ({location})\n{url}\n{id}\n\n'

    return line.format(**job)


def load(args):
    """
    Load jobs.
    """
    chosen_providers = get_providers(args.providers) or set(default_providers.values())
    excluded_providers = get_providers(args.exclude_providers) or set()

    for provider in chosen_providers - excluded_providers:
        data = provider.get(location=args.location, query=args.query)
        result = es.bulk_index(provider.name.lower(), 'job', data)

        print 'Loaded {name} Data: '.format(name=provider.name)
        print 'Result: ', result


def search(args):
    """
    Search jobs.
    """
    result = es.search({
        'query': {
            'text': {
                '_all': args.query
            }
        },

        'size': args.num_results
    })

    jobs = []
    output = u''

    print 'max age', args.max_age

    for result in result['hits']['hits']:
        data = result['_source']
        created_at = dateutil.parser.parse(data['created_at'])
        data['age'] = (
            datetime.datetime.now() - created_at.replace(tzinfo=None)).days

        if args.max_age and data['age'] > int(args.max_age):
            continue

        if 'company' not in data:
            data['company'] = ''

        jobs.append(data)

    jobs.sort(key=lambda job: job['age'])

    for job in jobs:
        output += get_job_output(job)

    pydoc.pager(output.encode('utf-8'))


def shell(args):
    """
    A poor man's interactive shell.
    """
    import ipdb; ipdb.set_trace()


if __name__ == '__main__':
    args = parser.parse_args()
    if args.search:
        search(args)
    elif args.load:
        load(args)
    elif args.shell:
        shell(args)
