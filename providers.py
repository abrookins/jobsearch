import json
import logging
import urllib
import requests


logger = logging.getLogger(__file__)


class BaseProvider(object):

    @property
    def name(self):
        return self.__class__.__name__

    def make_url(self, **kwargs):
        """
        Make a URL for this provider.
        """
        for key in kwargs:
            kwargs[key] = urllib.quote_plus(str(kwargs[key]))
        return self.url.format(**kwargs)

    def prepare_document(self, doc, **kwargs):
        """
        Prepare a JSON document for storage.
        """
        raise NotImplementedError

    def get_documents(self, data):
        """
        Return a list of individual documents to be processed by
        :fn:`prepare_document`.
        """
        return data

    def get(self, **kwargs):
        """
        Get jobs for this provider and return them
        """
        url = self.make_url(**kwargs)
        try:
            r = requests.get(url)
        except requests.exceptions.ConnectionError:
            logger.exception('Could not connect to URL: %s' % url)
            return

        try:
            data = json.loads(r.content)
        except TypeError:
            logger.exception('Could not load JSON response from: %s' % url)
            return

        return [self.prepare_document(d, **kwargs) for d in
                self.get_documents(data)]


class Github(BaseProvider):

    url = 'http://jobs.github.com/positions.json?description=' \
          '{query}&location={location}'

    def prepare_document(self, doc, **kwargs):
        return {
            'id': doc['id'],
            'created_at': doc['created_at'],
            'title': doc['title'],
            'location': doc['location'],
            'description': doc['description'],
            'company': doc['company'],
            'company_url': doc['company_url'],
            'url': doc['url']
        }


class Indeed(BaseProvider):

    url = 'http://api.indeed.com/ads/apisearch?publisher={api_key}&q=' \
          '{query}&l={location}&v=2&format=json'

    def __init__(self, api_key, *args, **kwargs):
        self.api_key = api_key

    def make_url(self, **kwargs):
        kwargs['api_key'] = self.api_key
        return super(Indeed, self).make_url(**kwargs)

    def get_documents(self, docs):
        return docs['results']

    def prepare_document(self, doc, **kwargs):
        return {
            'id': doc['jobkey'],
            'created_at': doc['date'],
            'title': doc['jobtitle'],
            'location': doc['formattedLocation'],
            'description': doc['snippet'],
            'company': doc['company'],
            'url': doc['url']
        }


class Craigslist(BaseProvider):
    url = "http://query.yahooapis.com/v1/public/yql?q=select%20*%20from" \
          "%20craigslist.search%20where%20location%3D%22{location}%22%20and%20" \
          "type%3D%22jjj%22%20and%20query%3D%22{query}%22&format=json" \
          "&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&callback="

    def get_documents(self, docs):
        return docs['query']['results']['RDF']['item']

    def prepare_document(self, doc, **kwargs):
        return {
            'id': doc['link'],
            'created_at': doc['date'],
            'title': doc['title'][0],
            'location': kwargs['location'],
            'description': doc['description'],
            'url': doc['link']
        }

