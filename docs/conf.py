from importlib.metadata import version as meta_version

project = "ims.sso"
author = "Eric Wohnlich and Taina Dumay"

extensions = ["sphinx.ext.autodoc", "sphinx_tabs.tabs"]

source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "restructuredtext",
    ".md": "markdown",
}

html_logo = "images/plone.png"
html_favicon = "images/favicon.ico"

version = meta_version("ims.sso")

html_theme = "sphinx_rtd_theme"
html_domain_indices = True
