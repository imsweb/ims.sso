from Products.PluggableAuthService import registerMultiPlugin

from . import plugin

__version__ = "1.0.0a1"


def initialize(context):
    registerMultiPlugin(plugin.ImsSsoPlugin.meta_type)
    context.registerClass(
        plugin.ImsSsoPlugin,
        permission="Manage portal",
        constructors=(plugin.manage_addImsSsoForm, plugin.manage_addImsSso),
        visibility=None,
        icon="static/multiplugin.gif",
    )
