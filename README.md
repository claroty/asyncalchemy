# AsyncAlchemy
A thin async wrapper for [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) sessions.

Besides being async, the wrapper manages the context of the session for the execution block.Commits incoming changes if successfull or rolls back changes if an exceptions occurs.\
*Note*: The upcoming SQLAlchemy 1.4 version will include built-in async functionality, it's recommended to upgrade to it once it's [released](https://github.com/sqlalchemy/sqlalchemy/releases).


## Install
### Pip
```bash
pip install asyncalchemy
```

### From Source
The project uses [poetry](https://github.com/python-poetry/poetry) for dependency management and packaging.\
To run from source clone project and:
```bash
pip install poetry
poetry install
```


## Usage
### Basic Example
```python
from asyncalchemy import create_session_factory

# Create AsyncAlchemy session factory
session_factory = create_session_factory(db_uri, Base)

# Create session
async with session_factory() as session:
    await session.query(Something).filter_by(something="else")
```

### Example With Extra Params
```python
from sqlalchemy.pool import NullPool

from asyncalchemy import create_session_factory

# Create session factory with additional SQLAlchemy params
session_factory = create_session_factory(db_uri, Base, poolclass=NullPool)

# Create session
async with session_factory() as session:
    await second_session.add(Something)
    await second_session.flush()

    # Reuse session
    async with session_factory(reuse_session=session) as second_session:
        await session.delete(Something)
```
