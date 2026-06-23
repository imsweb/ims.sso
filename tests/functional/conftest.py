import pytest
from plone.app.testing import SITE_OWNER_NAME, SITE_OWNER_PASSWORD
from plone.testing.zope import Browser


@pytest.fixture
def app(functional):
    """Note that these fixtures are elsewhere defined on the integration layer, we need functional here"""
    return functional["app"]


@pytest.fixture
def portal(functional):
    return functional["portal"]


@pytest.fixture
def http_request(functional):
    return functional["request"]


@pytest.fixture
def browser(app):
    browser = Browser(app)
    browser.handleErrors = False
    browser.addHeader("Authorization", f"Basic {SITE_OWNER_NAME}:{SITE_OWNER_PASSWORD}")
    return browser
