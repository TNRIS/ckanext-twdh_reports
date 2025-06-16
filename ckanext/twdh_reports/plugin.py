import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.twdh_reports.helpers as h

from ckanext.collection.interfaces import ICollection, CollectionFactory

from ckanext.twdh_reports.collections.user_collection import UserCollection
from ckanext.twdh_reports.blueprint import get_blueprint


class TwdhReportsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(ICollection, inherit=True)
    plugins.implements(plugins.IBlueprint, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "twdh_reports")

    # ICollection
    def get_collection_factories(self) -> dict[str, CollectionFactory]:

        return {
            "twdh-users": UserCollection,
            # 'twdh-group-stats': GroupStatsCollection,
        }

    # IBlueprint
    def get_blueprint(self):
        return get_blueprint()
    
    def get_helpers(self):
        return {
            "reset_totp_from_template": h.reset_totp_from_template
        }
