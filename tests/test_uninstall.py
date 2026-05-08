import pytest

from ims.users.interfaces import IBrowserLayer

PACKAGE_NAME = "ims.users"


class TestUninstall:
    @pytest.fixture(autouse=True)
    def uninstalled(self, installer):
        installer.uninstall_product(PACKAGE_NAME)

    def test_product_uninstalled(self, installer):
        """Test if ims.users is cleanly uninstalled."""
        assert not installer.is_product_installed(PACKAGE_NAME)

    def test_browserlayer_removed(self, browser_layers):
        """Test that IBrowserLayer is removed."""
        assert IBrowserLayer not in browser_layers
