"""Technical infrastructure: database engine, session factory, ORM tables.

Deliberately free of re-exports — importing `app.infra.models` for table
metadata must not spin up the SQLAlchemy engine as a side effect.
"""
