"""
Python 3.6+ module for interacting with Amazon's Alexa Web Information Service (AWIS)
Adapted from official Java sample code available here:
    https://aws.amazon.com/code/alexa-web-information-service-query-example-in-java/?tag=code%23keywords%23awis

As such, this code will adhere to the Apache License 2.0

Copyright 2018 Hyunjin Kim

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import datetime
import hashlib
import hmac
import itertools
from collections import namedtuple
from io import BytesIO
from multiprocessing.pool import ThreadPool
from typing import Iterable, List
from urllib.parse import quote

import lxml.etree as ET
import requests

TrafficHistory = namedtuple(
    'TrafficHistory',
    ('date', 'page_view_per_million', 'page_view_per_user', 'rank', 'reach'))

VALID_RESPONSE_GROUPS = {
    'RelatedLinks', 'Categories', 'Rank', 'RankByCountry', 'UsageStats',
    'AdultContent', 'Speed', 'Language', 'OwnedDomains', 'LinksInCount',
    'SiteData'
}

ALGORITHM = 'AWS4-HMAC-SHA256'
HASH_ALGORITHM = 'HmacSHA256'
DATE_STAMP_FORMAT = '%Y%m%d'
MAX_SEARCH_RANGE = 31
SERVICE_NAME = 'awis'
SERVICE_HOST = 'awis.amazonaws.com'
SERVICE_URI = '/api'


class AWIS:
    def __init__(self,
                 access_id: str, secret_key: str,
                 service_region: str = 'us-west-1'):
        self.access_id = access_id
        self.secret_access_key = secret_key

        self.SERVICE_REGION = service_region
        self.SERVICE_ENDPOINT = f'awis.{service_region}.amazonaws.com'
        self.AWS_BASE_URL = f'https://{SERVICE_HOST}{SERVICE_URI}'

    def get_signature_key(self,
                          datestamp: str,
                          region_name: str,
                          service_name: str) -> bytes:
        """
        Generate a V4 Signature key for the service/region
        :param key: Initial key secret
        :param datestamp: Date in YYYYMMDD format
        :param region_name: AWS region for the signature
        :param service_name: AWS Service name
        :return: signature
        """
        # First convert inputs (str) into bytes
        datestamp = datestamp.encode('utf-8')
        region_name = region_name.encode('utf-8')
        service_name = service_name.encode('utf-8')

        k_secret = ('AWS4' + self.secret_access_key).encode('utf-8')
        k_date = hmac.new(k_secret, datestamp, hashlib.sha256).digest()
        k_region = hmac.new(k_date, region_name, hashlib.sha256).digest()
        k_service = hmac.new(k_region, service_name, hashlib.sha256).digest()
        k_signing = hmac.new(k_service, b'aws4_request', hashlib.sha256).digest()
        return k_signing

    def url_info(self, url: str, response_groups: Iterable[str]) -> dict:
        """
        Get the UrlInfo of a website.
        Consult https://docs.aws.amazon.com/AlexaWebInfoService/latest/ApiReference_UrlInfoAction.html

        :param url: URL of website
        :param response_groups: List of response groups.
        """
        str_response_groups = ','.join(response_groups)

        if not set(response_groups) <= self.valid_response_groups:
            raise NameError('Not all response groups are valid')

        canonical_query = f'Action=urlInfo&ResponseGroup={quote(str_response_groups)}&Url={quote(url)}'
        response = self.request(canonical_query)
        return self.parse_url_info(response.content)

    def traffic_history(self, url: str, search_range: int = MAX_SEARCH_RANGE, start_date: str = None,
                        search_reverse: bool = False) -> List[TrafficHistory]:
        """
        Get the traffic history of a website.
        Consult https://docs.aws.amazon.com/AlexaWebInfoService/latest/ApiReference_TrafficHistoryAction.html

        :param url: URL of website
        :param search_range: Number of days to return. Default 31. Larger search range will result in more requests.
        :param start_date: The start date (within 4 years) in YYYYMMDD format.
        Default: search_range days ago from today
        :param search_reverse: Instead of searching forward from the start_date, searches backwards.
        """
        if search_range < 1:
            raise ValueError('search_range must be at least 1.')
        if start_date is None:
            date = datetime.date.today() - datetime.timedelta(search_range)
        else:
            date = datetime.datetime.strptime(start_date, DATE_STAMP_FORMAT).date()
        if search_reverse:
            date -= datetime.timedelta(days=search_range)

        if date + datetime.timedelta(days=search_range) >= datetime.date.today():
            raise ValueError("Cannot search past today's date")

        # Calculate number of requests required
        quotient, remainder = divmod(search_range, MAX_SEARCH_RANGE)
        num_requests = quotient + min(remainder, 1)

        queries = []
        for i in range(num_requests):
            instance_search_range = MAX_SEARCH_RANGE if i != num_requests - 1 else remainder
            str_date = date.strftime(DATE_STAMP_FORMAT)
            canonical_query = f'Action=TrafficHistory&Range={instance_search_range}&ResponseGroup=History' \
                              f'&Start={str_date}&Url={quote(url)}'
            queries.append(canonical_query)
            date += datetime.timedelta(days=instance_search_range)
        bulk_responses = self.bulk_request(queries)
        return list(itertools.chain.from_iterable([
            self.parse_traffic_history(r.content)
            for r in bulk_responses]))

    def bulk_request(self, queries: List[str]) -> List[requests.Response]:
        session = requests.session()
        with ThreadPool(8) as pool:
            async_requests = [pool.apply_async(self.create_request, (query, session)) for query in queries]
            responses = [p.get() for p in async_requests]
        return responses

    @staticmethod
    def parse_traffic_history(content) -> List[TrafficHistory]:
        tree = ET.parse(BytesIO(content))
        root = tree.getroot()
        aws_tag = '{http://awis.amazonaws.com/doc/2005-07-11}'
        output = []
        for element in root.iter(aws_tag + 'Data'):
            date = element.find(aws_tag + 'Date').text
            pageview_el = element.find(aws_tag + 'PageViews')
            pageview_pmil = int(pageview_el.find(aws_tag + 'PerMillion').text)
            pageview_puser = float(pageview_el.find(aws_tag + 'PerUser').text)
            rank = int(element.find(aws_tag + 'Rank').text)
            reach = int(element.find(f'{aws_tag}Reach/{aws_tag}PerMillion').text)
            traffic_history_record = TrafficHistory(date, pageview_pmil, pageview_puser, rank, reach)
            output.append(traffic_history_record)
        return output

    @staticmethod
    def parse_url_info(content):
        # TODO: Write actual parsing
        return content

    def create_request(self, canonical_query: str, session=None) -> requests.Request:
        amz = self.amz_date()
        ds = self.date_stamp
        canonical_headers = f'host:{self.SERVICE_ENDPOINT}\nx-amz-date:{amz}\n'
        signed_headers = 'host;x-amz-date'
        payload_hash = self.sha256('')
        canonical_request = f'GET\n{SERVICE_URI}\n{canonical_query}\n{canonical_headers}\n' \
                            f'{signed_headers}\n{payload_hash}'
        credential_scope = f'{ds}/{self.SERVICE_REGION}/{SERVICE_NAME}/aws4_request'
        string_to_sign = f'{ALGORITHM}\n{amz}\n{credential_scope}\n{self.sha256(canonical_request)}'
        signing_key = self.get_signature_key(ds, self.SERVICE_REGION, SERVICE_NAME)
        signature = self.hmac_sha256(string_to_sign.encode('utf-8'), signing_key).hex()
        uri = f'{self.AWS_BASE_URL}?{canonical_query}'
        authorisation = f'{ALGORITHM} Credential={self.access_id}/{credential_scope}, SignedHeaders=' \
                        f'{signed_headers}, Signature={signature}'
        request_properties = {
            'Accept': 'application/xml',
            'Content-Type': 'application/xml',
            'X-Amz-Date': amz,
            'Authorization': authorisation
        }

        if not session:
            session = requests
        return requests.get(uri, headers=request_properties)

    @staticmethod
    def amz_date() -> str:
        now = datetime.datetime.utcnow()
        return now.strftime('%Y%m%dT%H%M%SZ')

    @staticmethod
    def sha256(text_to_hash: str) -> bytes:
        m = hashlib.sha256()
        m.update(text_to_hash.encode('utf-8'))
        return m.digest().hex()

    @staticmethod
    def hmac_sha256(data: bytes, key: bytes) -> bytes:
        hmac_signature = hmac.new(key, data, hashlib.sha256)
        return hmac_signature.digest()

    @property
    def date_stamp(self) -> str:
        now = datetime.datetime.utcnow()
        return now.strftime(DATE_STAMP_FORMAT)
