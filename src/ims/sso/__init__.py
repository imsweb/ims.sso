from Products.PluggableAuthService import registerMultiPlugin

from . import plugin

__version__ = "1.0.0"
try:
    registerMultiPlugin(plugin.ImsSsoPlugin.meta_type)
except RuntimeError:
    # refresh
    pass


def initialize(context):
    context.registerClass(
        plugin.ImsSsoPlugin,
        permission="Manage portal",
        constructors=(plugin.manage_addImsSsoForm, plugin.manage_addImsSso),
        visibility=None,
        icon="static/multiplugin.gif",
    )
