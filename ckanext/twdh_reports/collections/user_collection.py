import sqlalchemy as sa

from ckan import model
from ckan.types import Any
from ckan.plugins import toolkit as tk

from ckanext.collection.shared import collection, data, serialize, columns, filters


class UserSerializer(serialize.JsonSerializer):

    # form_template = "reports/reports.html"

    def stream(self):
        yield self.encoder.encode(
            [self.dictize_row(row) for row in self.attached.data],
        )

    def get_columns(self) -> dict[str, Any]:
        return {
            "fullname": "Full Name",
            "title": "Organization",
            "email": "Email",
            "role": "Role",
            "last_active": "Last Active",
            "action": "Action",
        }
    
    def dictize_row(self, row):
        return {
            "fullname": row[0],
            "title": row[1],
            "email": row[2],
            "role": row[3],
            "last_active": row[4],
            "action": f'''
            <form method="post" style="margin: 0;">
                <input type="hidden" name="reset_totp_user" value="{row[5]}" />
                <button type="submit" class="btn btn-sm btn-danger"
                        onclick="return confirm('Reset MFA for {row[5]}?');">
                    Reset MFA
                </button>
            </form>
        ''',
        }


    # def stream(self):
    #     yield tk.render(
    #         self.form_template,
    #         self.get_data(),
    #     )


class UserOrganizationRoleData(data.StatementSaData):
    """
    This class is used to generate data for the User Organization Role
    collection.
    """

    user_membership = sa.alias(model.Member)

    statement = (
        sa.select(
            model.User.fullname,
            model.Group.title,
            model.User.email,
            user_membership.c.capacity,
            model.User.last_active,
             model.User.name,
        )
        .join(user_membership, user_membership.c.table_id == model.User.id)
        .join(model.Group, model.Group.id == user_membership.c.group_id)
        .where(model.User.state == "active", model.Group.state == "active")
    )
    print(statement)


class UserCollection(collection.Collection):

    DataFactory = UserOrganizationRoleData
    ColumnsFactory = columns.Columns.with_attributes(
        names=("fullname", "title", "email", "role", "last_active", "action")
    )
    # FiltersFactory = filters.Filters()
    SerializerFactory = UserSerializer
