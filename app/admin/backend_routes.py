import re
from flask import request, current_app, send_file
from flask_login import login_required, current_user
from . import admin_bp
from ..users import admin_required
from ..database.db_helper import (
    delete,
    update,
    insert,
    del_users,
    update_users,
    add_revision,
    del_revisions,
    del_records,
)
from ..database.backup import backup, restore


# The page receives the response to the report and the command to delete a report or a revision.
@admin_bp.route("/admin_dashboard_backend", methods=["POST", "DELETE"])
@admin_required
@login_required
def admin_dashboard_backend_page():
    if request.method == "POST":
        data = request.get_json(force=True)
        add_revision(
            int(data["record_id"]),
            current_user.id,
            int(data["status_id"]),
            data["description"],
        )
        return "OK"
    if request.method == "DELETE":
        data = request.get_json(force=True)
        category = data["category"]
        id = int(data["id"])
        if category == "record":
            del_records([id])
        if category == "revision":
            del_revisions([id])
        return "OK"


# The page handles the system modification signals which are sent from `/system`.
@admin_bp.route("/system_modification", methods=["POST", "DELETE", "UPDATE"])
@admin_required
@login_required
def system_modification_page():
    if request.method == "POST":
        # Add
        current_app.logger.info("POST /system_modification")
        data = request.get_json(force=True)
        if data.get("office") != None:
            args = {"description": data["value"], "office_id": data["office"]}
        else:
            args = {"description": data["value"]}
        if insert(data["category"], args):
            return "OK"
        else:
            return "Error", 400
    if request.method == "DELETE":
        # Delete
        current_app.logger.info("DELETE /system_modification")
        data = request.get_json(force=True)
        if delete(data["category"], data["id"]):
            return "OK"
        else:
            return "Error", 400
    if request.method == "UPDATE":
        # Update
        current_app.logger.info("UPDATE /system_modification")
        data = request.get_json(force=True)
        category = data[0]["category"]
        for r in data[1:]:
            new = {
                "id": r["id"],
                "description": r["description"],
                "sequence": r["sequence"],
            }
            if r.get("office_id", None):
                new["office_id"] = r["office_id"]
            if not update(category, new):
                return "Error", 400
        return "OK"


# The page handles the request to delete and update user's information.
@admin_bp.route("/manage_user_backend", methods=["DELETE", "UPDATE"])
@admin_required
@login_required
def manage_user_backend_page():
    if request.method == "DELETE":
        # Delete user
        current_app.logger.info("DELETE /manage_user_backend")
        data = request.get_json(force=True)
        del_users([data["user_id"]])
        return "OK"
    if request.method == "UPDATE":
        # Update user
        current_app.logger.info("UPDATE /manage_user_backend")
        data = request.get_json(force=True)
        update_users([data])
        return "OK"


@admin_bp.route("/backup_backend", methods=["POST", "DELETE", "UPDATE"])
@admin_required
@login_required
def backup_backend_page():
    if request.method == "POST":
        # do backup
        try:
            backup()
            return "OK"
        except:
            return "Error", 400
    if request.method == "DELETE":
        # delete backup
        backup_name = request.get_json(force=True)["name"]
        # TODO
    if request.method == "UPDATE":
        # restore to specific version
        backup_name = request.get_json(force=True)["name"]
        backup_name = re.search("Backup(.)*", backup_name).group()
        print(backup_name)
        restore(backup_name)
        return "OK"


@admin_bp.route("/backup/<string:filename>", methods=["GET"])
@admin_required
@login_required
def get_backup_file(filename):
    return send_file("../backup/" + filename, as_attachment=True)
