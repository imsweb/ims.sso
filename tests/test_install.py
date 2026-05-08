class TestSetupInstall:
    def test_addon_installed(self, installer, package_name):
        assert installer.is_product_installed(package_name) is True

    def test_profile(self, setup_tool, package_name):
        vrs = setup_tool.getLastVersionForProfile(f"{package_name}:default")
        assert vrs != "unknown"
