from flask import Blueprint, render_template, request
from ckan.plugins import toolkit as tk

from ckanext.collection import shared
from ckanext.security.authenticator import reset_totp

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

    reset_username = request.form.get("reset_totp_user")
    result_message = None

    if reset_username:
        try:
            reset_totp(reset_username)
            result_message = f"TOTP reset successful for {reset_username}"
        except Exception as e:
            result_message = f"TOTP reset failed: {str(e)}"

    return render_template("reports/reports.html", collection=collection.serializer.serialize(),result_message=result_message)


twdh_reports.add_url_rule("/ckan-admin/reports", "reports", reports, methods=["GET", "POST"])

def get_blueprint():
    return twdh_reports
