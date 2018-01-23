#!/usr/bin/env python3

import base64
import json

import pytest
from hamcrest import assert_that
from hamcrest import equal_to
from hamcrest import has_key
from hamcrest import is_
from hamcrest import not_none

from test_helpers import PostRequestsInterceptor
from test_helpers import DemoZuulProxyRunner
from test_helpers import post


@pytest.fixture(scope="module")
def interceptor():
    # PostRequestsInterceptor is a daemon thread,
    # so will be terminated as soon as tests finish.
    return PostRequestsInterceptor().start()


@pytest.fixture(scope="module", autouse=True)
def start_sut():
    # Sut is started as detached process, so should be terminated explicitly.
    sut = DemoZuulProxyRunner().start()
    yield
    sut.stop()


def test_response_is_present(interceptor):
    post('{"image": "foo"}')
    data = interceptor.get_last_intercepted_data()

    assert_that(data,
                not_none(),
                'There should be response to a valid request')


def test_response_is_json(interceptor):
    post('{"image": "bar"}')
    data = interceptor.get_last_intercepted_data()

    assert_that(json.loads(data),
                not_none(),
                'Response should be a valid JSON')


def test_response_contains_image_key(interceptor):
    post('{"image": "woot"}')
    data = interceptor.get_last_intercepted_data()

    assert_that(json.loads(data),
                has_key('image'),
                'JSON object should contain "image" field')


@pytest.mark.parametrize('image_content',
                         ['',
                          'test',
                          'тестовая картинка',
                          '0123456789',
                          '==========',
                          '++++++++++',
                          '//////////',
                          'ABCDEFGHIJKLMNOPQRSTUVWXYZ' * 10])
def test_image_value_is_base64_encoded(image_content, interceptor):
    post('{"image": "%s"}' % image_content)
    data = interceptor.get_last_intercepted_data()

    assert_that(base64.b64decode(json.loads(data)['image']),
              is_(equal_to(image_content.encode())),
                '"image" field in JSON response should contain'
                ' base64-encoded value that was sent to Demo Zuul Proxy')


if __name__ == '__main__':
    pytest.main()