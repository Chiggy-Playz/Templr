import asyncio
import importlib
from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.future import Connection

from app.database import meta
from app.config import settings

# # this is the Alembic Config object, which provides
# # access to the values within the .ini file in use.
config = context.config


def load_all_models() -> None:
    """Dynamically import all Python modules inside any 'models' subpackage."""
    app_dir = Path(__file__).resolve().parent.parent.parent
    project_root = app_dir.parent
    sys.path.append(str(project_root))
    base_package = "app"

    for models_file in app_dir.rglob("models.py"):
        # Construct the package name
        try:
            rel_path = models_file.relative_to(app_dir)
            parts = rel_path.with_suffix(
                ""
            ).parts  # removes '.py' suffix and gets parts

            module_path = f"{base_package}." + ".".join(parts)
            print(f"Importing: {module_path}")
            importlib.import_module(module_path)
        except ValueError:
            continue


load_all_models()

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = meta

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


async def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=str(settings.database_url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run actual sync migrations.

    :param connection: connection to the database.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = create_async_engine(str(settings.database_url))

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


loop = asyncio.get_event_loop()
if context.is_offline_mode():
    task = run_migrations_offline()
else:
    task = run_migrations_online()

loop.run_until_complete(task)
