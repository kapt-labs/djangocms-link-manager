from django.apps import AppConfig

from .link_managers.bootstrap3_button_cmsplugin import Bootstrap3ButtonCMSPluginLinkManager
from .link_managers.cmsplugin_link import CMSPluginLinkLinkManager
from .link_manager_pool import link_manager_pool


class LinkManagerConfig(AppConfig):
    name = "djangocms_link_manager"
    verbose_name = "Link manager"

    def ready(self):
        from . import admin  # noqa: F401

        link_manager_pool.register(
            "Bootstrap3ButtonCMSPlugin", Bootstrap3ButtonCMSPluginLinkManager
        )
        link_manager_pool.register("LinkPlugin", CMSPluginLinkLinkManager)
