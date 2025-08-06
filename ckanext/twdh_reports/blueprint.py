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

import logging
log = logging.getLogger(__name__)

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

    return redirect(tk.h.url_for('/ckan-admin/approval-report'))



twdh_reports.add_url_rule("/ckan-admin/reports", "reports", reports, methods=["GET", "POST"])
twdh_reports.add_url_rule("/ckan-admin/approval-report", "approval_report", approval_report)

def get_blueprint():
    return twdh_reports
