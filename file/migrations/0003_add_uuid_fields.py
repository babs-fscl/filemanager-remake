import uuid

from django.db import migrations, models


def _table_columns(connection, table_name):
    with connection.cursor() as cursor:
        return {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }


def _quote(schema_editor, name):
    return schema_editor.connection.ops.quote_name(name)


def _ensure_uuid_column(apps, schema_editor, model_name):
    model = apps.get_model('file', model_name)
    table_name = model._meta.db_table
    columns = _table_columns(schema_editor.connection, table_name)

    if 'uuid' not in columns:
        field = models.UUIDField(null=True, editable=False)
        field.set_attributes_from_name('uuid')
        schema_editor.add_field(model, field)

    table = _quote(schema_editor, table_name)
    pk = _quote(schema_editor, model._meta.pk.column)
    uuid_column = _quote(schema_editor, 'uuid')

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"SELECT {pk} FROM {table} WHERE {uuid_column} IS NULL")
        row_ids = [row[0] for row in cursor.fetchall()]
        for row_id in row_ids:
            cursor.execute(
                f"UPDATE {table} SET {uuid_column} = %s WHERE {pk} = %s",
                [str(uuid.uuid4()), row_id],
            )

    index_name = _quote(schema_editor, f"{table_name}_uuid_uniq")
    schema_editor.execute(
        f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table} ({uuid_column})"
    )


def add_uuid_fields(apps, schema_editor):
    _ensure_uuid_column(apps, schema_editor, 'Document')
    _ensure_uuid_column(apps, schema_editor, 'Project')


class Migration(migrations.Migration):

    dependencies = [
        ('file', '0002_multitenancy'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_uuid_fields, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='document',
                    name='uuid',
                    field=models.UUIDField(default=uuid.uuid4, editable=False, null=True, unique=True),
                ),
                migrations.AddField(
                    model_name='project',
                    name='uuid',
                    field=models.UUIDField(default=uuid.uuid4, editable=False, null=True, unique=True),
                ),
            ],
        ),
    ]
