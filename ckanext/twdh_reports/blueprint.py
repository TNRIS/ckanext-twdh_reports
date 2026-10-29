from flask import Blueprint, render_template, request, redirect, flash
from ckan.plugins import toolkit as tk

from ckanext.collection import shared
from ckanext.security.authenticator import reset_totp

from typing import cast

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
from ckan.common import _, config, request, current_user
from ckan.types import Context

import io
import traceback
import contextlib
from ckan.lib.search import check, query_for
from ckanext.datastore import helpers as datastore_helpers


import logging
log = logging.getLogger(__name__)

twdh_reports = Blueprint("twdh_reports", __name__, template_folder="templates")


def get_search_index_report_context():

    package_query = query_for(model.Package)

    pkgs_q = model.Session.query(model.Package).filter_by(
        state=model.State.ACTIVE)
    pkgs = {pkg.id for pkg in pkgs_q}
    indexed_pkgs = set(package_query.get_all_entity_ids(max_results=len(pkgs)))
    pkgs_not_indexed = pkgs - indexed_pkgs
    unindexed = []
    for pkg_id in pkgs_not_indexed:
        pkg = model.Session.query(model.Package).get(pkg_id)
        assert pkg
        unindexed.append(
            {
                "modified": pkg.metadata_modified.strftime('%Y-%m-%d'), 
                "name": pkg.name, 
                "title": pkg.title
            }
        )


    return unindexed

    """
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    search_index_status = "OK"
    search_index_error = None

    try:
        with contextlib.redirect_stdout(stdout_buffer):
            with contextlib.redirect_stderr(stderr_buffer):
                _check()

    except Exception:
        search_index_status = "FAILED"
        search_index_error = traceback.format_exc()

    return {
        "search_index_status": search_index_status,
        "search_index_stdout": stdout_buffer.getvalue() or "(empty)",
        "search_index_stderr": stderr_buffer.getvalue() or "(empty)",
        "search_index_error": search_index_error,
    }
    """

def get_user_activity_report_context():
    collection = shared.get_collection("twdh-users", None)

    reset_username = request.form.get("reset_totp_user")
    result_message = None

    if reset_username:
        try:
            reset_totp(reset_username)
            result_message = f"TOTP reset successful for {reset_username}"
        except Exception as e:
            result_message = f"TOTP reset failed: {str(e)}"

    return {
        "collection": collection.serializer.serialize() if collection else None,
        "result_message": result_message,
    }

def get_dataset_approval_report_context():
    
    results = tk.get_action("package_search")

    search_params = {
        "fq": "+state:active",
        "include_private": True,
    }

    base_results = results(
        {"ignore_auth": True},
        search_params,
    )["results"]

    datasets_needing_review = [
        d for d in base_results
        if d.get("data_admin_approved", "") != "approved"
        or d.get("private", True)
    ]

    datasets = []

    for ds in datasets_needing_review:
        status = None

        if ds.get("data_admin_approved") != "approved":
            status = "Ready to Approve"
        elif ds.get("private") is True and ds.get("data_admin_approved") == "approved":
            status = "Ready to Publish"

        owner = ""

        creator_user_id = ds.get("creator_user_id")
        if creator_user_id:
            try:
                user_dict = logic.get_action("user_show")(
                    {"ignore_auth": True},
                    {"id": creator_user_id},
                )
                owner = user_dict.get("name", "")
            except Exception:
                owner = ""

        datasets.append({
            "id": ds["id"],
            "title": ds.get("title") or ds.get("name"),
            "organization": ds.get("organization", {}).get("title", ""),
            "owner": owner,
            "status": status,
        })

    return {
        "datasets": datasets,
    }

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

def activity_report():
    try:
        context = cast(
            Context, {
                "model": model,
                "user": current_user.name,
                "auth_user_obj": current_user
            }
        )
        logic.check_access('sysadmin', context)

    except logic.NotAuthorized:
        base.abort(403, _('Need to be system administrator to administer'))

    collection = shared.get_collection("twdh-users", None)

    reset_username = request.form.get("reset_totp_user")
    result_message = None

    if reset_username:
        try:
            reset_totp(reset_username)
            result_message = f"TOTP reset successful for {reset_username}"
        except Exception as e:
            result_message = f"TOTP reset failed: {str(e)}"

    return render_template("reports/activity.html", collection=collection.serializer.serialize(),result_message=result_message)


def approval_report():
    try:
        context = cast(
            Context, {
                "model": model,
                "user": current_user.name,
                "auth_user_obj": current_user
            }
        )
        logic.check_access('sysadmin', context)

    except logic.NotAuthorized:
        base.abort(403, _('Need to be system administrator to administer'))

    # Fetch datasets needing approval/publishing
    results = tk.get_action('package_search')

    search_params = {
            'fq': '+state:active',
            'include_private': True,
        }
    base_results = results(
            {'ignore_auth': True},
            search_params
        )['results']
    
    datasets_needing_review = [
    d for d in base_results
    if d.get('data_admin_approved', '') != 'approved' or d.get('private', True)
]

    datasets = []
    for ds in datasets_needing_review:
        status = None
        if ds.get('data_admin_approved') != 'approved':
            status = 'Ready to Approve'
        elif ds.get('private') is True and ds.get('data_admin_approved') == 'approved':
            status = 'Ready to Publish'
        
        user_dict = logic.get_action('user_show')(
            {'ignore_auth': True},
            {'id': ds['creator_user_id']}
        )
        # if status:
        datasets.append({
                'id': ds['id'],
                'title': ds.get('title', ds['name']),
                'organization': ds.get('organization', {}).get('title', ''),
                'owner': user_dict['name'],
                'status': status
            })

    return render_template("reports/approval.html", datasets=datasets)

def send_editor_approval_notification(user_email: str, user_name: str, dataset_title: str, dataset_url: str):
    
    log.info(f"Sending approval notification to Editor: {user_email}")
    try:
        subject = "Your Data Resource is Published!"
        extra_vars = {
            "user_name": user_name,
            "dataset_title": dataset_title,
            "dataset_url": dataset_url,
            "site_title": tk.config.get('ckan.site_title'),
            "site_url": tk.config.get('ckan.site_url')
        }

        body = tk.render("emails/editor_approved.txt", extra_vars)
        body_html = tk.render("emails/editor_approved.html", extra_vars)

        tk.mail_recipient(user_name, user_email, subject, body, body_html)
        log.info("Approval notification sent to Editor successfully.")
    except Exception as e:
        log.error(f"Failed to send approval notification to Editor: {e}")

def search_index():
    try:
        context = cast(
            Context, {
                "model": model,
                "user": current_user.name,
                "auth_user_obj": current_user
            }
        )
        logic.check_access('sysadmin', context)

    except logic.NotAuthorized:
        base.abort(403, _('Need to be system administrator to administer'))

    pkgs = get_search_index_report_context()

    return render_template("reports/search_index.html", pkgs=pkgs)

def resource_size_report():
    """
    Report resource sizes and DataStore column counts.

    """

    context = cast(
        Context,
        {
            "model": model,
            "user": current_user.name,
            "auth_user_obj": current_user,
        }
    )

    try:
        logic.check_access("sysadmin", context)
    except logic.NotAuthorized:
        base.abort(
            403,
            _("Need to be system administrator to administer")
        )

    max_file_size = int(
        config.get(
            "ckan.resource_proxy.max_file_size",
            1048576
        )
    )

    max_columns = int(
        config.get("ckan.max_resource_columns", 40)
    )

    # Summary
    summary = {
        "total": 0,
        "within_limit": 0,
        "too_large": 0,
        "unknown": 0,
        "too_many_columns": 0,
        "unknown_columns": 0,
        "issues": 0,
    }

    resource_rows = []

    datasets = tk.get_action(
        "current_package_list_with_resources"
    )(
        {
            "user": current_user.name,
            "ignore_auth": True
        },
        {
            "limit": 100000
        }
    )

    for dataset in datasets:

        if dataset.get("type") != "dataset":
            continue

        for resource in dataset.get("resources", []):

            summary["total"] += 1

            # ----------------------------------
            # Resource size
            # ----------------------------------

            size = resource.get("size")
            size_bytes = None

            try:
                if size is not None and size != "":
                    size_bytes = int(size)

                    if size_bytes < 0:
                        size_bytes = None

            except (ValueError, TypeError):
                size_bytes = None

            if size_bytes is None:

                size_status = "Unknown"
                size_display = "Unknown"

                summary["unknown"] += 1

            elif size_bytes > max_file_size:

                size_status = "Too Large"
                size_display = "{:.2f} MiB".format(
                    size_bytes / (1024 * 1024)
                )

                summary["too_large"] += 1

            else:

                size_status = "Within Limit"
                size_display = "{:.2f} MiB".format(
                    size_bytes / (1024 * 1024)
                )

                summary["within_limit"] += 1

            # ----------------------------------
            # DataStore column count
            # ----------------------------------

            column_count = None
            column_status = "N/A"

            resource_views = []

            if resource.get("datastore_active", False):
                try:
                    resource_views = tk.get_action("resource_view_list")(
                        {
                            "user": current_user.name,
                            "ignore_auth": True
                        },
                        {"id": resource["id"]}
                    )
                except Exception:
                    log.exception(
                        "Failed to retrieve views for resource %s",
                        resource["id"]
        )

            has_table_view = any(
                view.get("view_type") == "datatablesview_plus"
                for view in resource_views
            )

            
            if resource.get("datastore_active", False) and has_table_view:

                try:
                    data_dictionary = (
                        datastore_helpers.datastore_dictionary(
                            resource["id"]
                        )
                    )

                    column_count = len(data_dictionary)

                    if column_count > max_columns:

                        column_status = "Too Many"
                        summary["too_many_columns"] += 1

                    else:
                        column_status = "OK"

                except Exception:

                    column_status = "Unknown"
                    summary["unknown_columns"] += 1

                    log.exception(
                        "Could not retrieve DataStore columns "
                        "for resource %s",
                        resource.get("id")
                    )

            # ----------------------------------
            # Overall status
            # ----------------------------------

            has_issue = (
                size_status in ("Too Large", "Unknown")
                or column_status in ("Too Many", "Unknown")
            )

            if has_issue:
                summary["issues"] += 1

            # ----------------------------------
            # Resource details
            # ----------------------------------
            if has_issue:
                resource_rows.append({
                    "dataset": (
                        dataset.get("title")
                        or dataset.get("name")
                    ),
                    "dataset_name": dataset.get("name"),
                    "resource": (
                        resource.get("name")
                    ),
                    "resource_id": resource.get("id"),
                    "format": resource.get("format") or "Unknown",
                    "size_bytes": size_bytes,
                    "size_display": size_display,
                    "size_status": size_status,
                    "column_count": column_count,
                    "column_status": column_status,
                    "has_issue": has_issue,
                })

    resource_rows.sort(
        key=lambda row: (
            not row["has_issue"],
            row["dataset"].lower(),
            row["resource"].lower()
        )
    )

    return render_template(
        "reports/resource_size.html",
        resources=resource_rows,
        summary=summary,
        max_file_size=max_file_size,
        max_columns=max_columns,
    )

@twdh_reports.route('/ckan-admin/approval-report/patch/<id>', methods=['POST'])
def handle_dataset_patch(id):
    try:
        context = {
            'model': model,
            'session': model.Session,
            'user': current_user.name,
            'auth_user_obj': current_user
        }
        logic.check_access('sysadmin', context)
    except logic.NotAuthorized:
        base.abort(403, _('Only system administrators can perform this action'))

    data = {
        'id': id
    }

    if 'data_admin_approved' in request.form:
        data['data_admin_approved'] = request.form['data_admin_approved']
        data['private'] = False

    if 'private' in request.form:
        data['private'] = request.form['private']

    try:
        tk.get_action('package_patch')(context, data)
    except logic.ValidationError as e:
        flash(_('Validation Error: {}').format(e.error_summary), 'error')

    try:
        complete_data = tk.get_action('package_patch')({'allow_state_change': True}, data)
    except logic.ValidationError as e:
        return redirect(tk.h.url_for('/ckan-admin/approval-report'))
    
    # Send mail to editor
    try:
        creator_id = complete_data.get('creator_user_id')
        if creator_id:
            creator = tk.get_action('user_show')({}, {'id': creator_id})
            editor_name = creator.get('fullname') or creator.get('display_name') or creator.get('name', '')
            editor_email = creator.get('email', '')
            dataset_url = f"{tk.config.get('ckan.site_url')}/dataset/{complete_data['name']}"
            send_editor_approval_notification(
                user_email=editor_email,
                user_name=editor_name,
                dataset_title=complete_data.get('title', ''),
                dataset_url=dataset_url
            )
    except Exception as e:
        log.warning(f"Could not send approval notification to Editor: {e}")

    return redirect(tk.h.url_for('/ckan-admin/approval-report'))



twdh_reports.add_url_rule("/ckan-admin/reports", "reports", reports, methods=["GET", "POST"])
twdh_reports.add_url_rule("/ckan-admin/activity-report", "activity_report", activity_report)
twdh_reports.add_url_rule("/ckan-admin/approval-report", "approval_report", approval_report)
twdh_reports.add_url_rule("/ckan-admin/search-index", "search_index", search_index)
twdh_reports.add_url_rule("/ckan-admin/resource-size-report","resource_size_report",resource_size_report)

def get_blueprint():
    return twdh_reports
