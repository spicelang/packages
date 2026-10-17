# sqlite

Spice bindings for [SQLite](https://sqlite.org), an embedded, file-based SQL database.

## Installation

```toml
[dependencies]
sqlite = "^0.1.0"
```

```spice
import "spice_packages/sqlite/sqlite";
```

The package links against the system SQLite library, so its development files have to be installed:

| Platform      | Package                                                                  |
|---------------|--------------------------------------------------------------------------|
| Debian/Ubuntu | `libsqlite3-dev`                                                         |
| Fedora        | `sqlite-devel`                                                           |
| macOS         | `brew install sqlite` (add its `lib/pkgconfig` dir to `PKG_CONFIG_PATH`) |
| Windows       | `vcpkg install sqlite3:x64-windows` (add its `lib` dir to `LIBRARY_PATH`) |

## Quick start

```spice
import "spice_packages/sqlite/sqlite";

f<int> main() {
    SqliteDatabase db = SqliteDatabase(":memory:");
    if !db.isValid() {
        printf("Could not open database: %s\n", db.getErrorMessage());
        return 1;
    }

    Result<bool> createRes = db.exec("CREATE TABLE people (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)");
    assert createRes.isOk();

    SqliteStatement insertStmt = SqliteStatement(db, "INSERT INTO people (name, age) VALUES (?, ?)");
    insertStmt.bindText(1, "Ada");
    insertStmt.bindInt(2, 36l);
    assert insertStmt.step() == SqliteResultCode::DONE;
    printf("Inserted row id: %d\n", db.getLastInsertRowId());

    SqliteStatement selectStmt = SqliteStatement(db, "SELECT id, name, age FROM people ORDER BY id");
    while selectStmt.nextRow() {
        const long id = selectStmt.getColumnInt(0);
        const String name = selectStmt.getColumnText(1);
        const long age = selectStmt.getColumnInt(2);
        printf("id=%d name=%s age=%d\n", id, name.getRaw(), age);
    }
}
```

## API

| Type / function    | Members                                                                                         |
|--------------------|-------------------------------------------------------------------------------------------------|
| `SqliteDatabase`   | `SqliteDatabase(path, flags)`, `isValid`, `getErrorMessage`, `exec`, `getLastInsertRowId`, `getChanges` |
| `SqliteStatement`  | `SqliteStatement(db, sql)`, `isValid`, `bindInt`, `bindDouble`, `bindText`, `bindNull`, `step`, `nextRow`, `reset`, `getColumnCount`, `getColumnType`, `getColumnName`, `getColumnInt`, `getColumnDouble`, `getColumnText` |
| `getSqliteVersion` | Version of the linked SQLite library                                                            |

Bind indices are 1-based and column indices are 0-based, like in the SQLite C API. The open flags (`SQLITE_OPEN_READONLY`,
`SQLITE_OPEN_READWRITE`, `SQLITE_OPEN_CREATE`, ...) can be combined with `|`, and default to read/write + create.
