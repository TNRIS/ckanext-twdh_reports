from flask import Blueprint, render_template
from ckan.plugins import toolkit as tk

from ckanext.collection import shared

from typing import cast

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
from ckan.common import _, config, request, current_user
from ckan.types import Context

twdh_reports = Blueprint("twdh_reports", __name__, template_folder="templates")

def reports():
    try:
        context = cast(
            Context, {
                "model": model,
                "user": current_user.name,
                "auth_user_obj": current_user
            }
        )
        logic.check_access(u'sysadmin', context)

    except logic.NotAuthorized:
        base.abort(403, _(u'Need to be system administrator to administer'))

    collection = shared.get_collection("twdh-users", None)
    return render_template("reports/reports.html", collection=collection.serializer.serialize())


twdh_reports.add_url_rule("/ckan-admin/reports", "reports", reports)

def get_blueprint():
    return twdh_reports
