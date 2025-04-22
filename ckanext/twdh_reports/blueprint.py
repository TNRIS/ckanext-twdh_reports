from flask import Blueprint, render_template, request
from ckan.plugins import toolkit as tk

from ckanext.collection import shared
from ckanext.security.authenticator import reset_totp

twdh_reports = Blueprint("twdh_reports", __name__, template_folder="templates")


def reports():
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
# twdh_reports.add_url_rule("/api/util/collection/twdh-users/render", "user_report", user_report)


def get_blueprint():
    return twdh_reports
