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
            "name": "Username",
            "fullname": "Full Name",
            "title": "Organization",
            "email": "Email",
            "role": "Role",
            "last_active": "Last Active",
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
            model.User.name,
            model.User.fullname,
            model.Group.title,
            model.User.email,
            user_membership.c.capacity,
            model.User.last_active,
        )
        .join(user_membership, user_membership.c.table_id == model.User.id)
        .join(model.Group, model.Group.id == user_membership.c.group_id)
        .where(model.User.state == "active", model.Group.state == "active")
    )
    print(statement)


class UserCollection(collection.Collection):

    DataFactory = UserOrganizationRoleData
    ColumnsFactory = columns.Columns.with_attributes(
        names=("name", "fullname", "title", "email", "role", "last_active")
    )
    # FiltersFactory = filters.Filters()
    SerializerFactory = UserSerializer
