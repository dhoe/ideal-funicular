# Pure Python SQLite3 CLI

A pure Python implementation of the SQLite3 command-line interface, compatible with the standard `sqlite3` tool. Uses only Python standard library dependencies.

## Features

- **Full SQLite3 CLI compatibility** - Supports most features of the standard sqlite3 CLI
- **Interactive REPL mode** - Command-line interface with prompt
- **Multiple output formats** - csv, column, html, insert, line, list, quote, tabs, tcl
- **Meta-commands** - Full support for `.tables`, `.schema`, `.dump`, `.mode`, etc.
- **SQL execution** - Execute SQL from command line, files, or stdin
- **Zero external dependencies** - Uses only Python standard library

## Installation

No installation required! Just ensure you have Python 3.6+ installed.

```bash
# Make executable (Unix/Linux/macOS)
chmod +x sqlite3_cli.py

# Or run with Python
python3 sqlite3_cli.py
```

## Usage

### Interactive Mode

```bash
# In-memory database
./sqlite3_cli.py

# Open/create a database file
./sqlite3_cli.py mydata.db
```

Example session:
```
SQLite version 3.x (Python implementation)
Enter ".help" for usage hints.
sqlite> CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT);
sqlite> INSERT INTO users VALUES (1, 'Alice', 'alice@example.com');
sqlite> INSERT INTO users VALUES (2, 'Bob', 'bob@example.com');
sqlite> SELECT * FROM users;
1|Alice|alice@example.com
2|Bob|bob@example.com
sqlite> .mode column
sqlite> .headers on
sqlite> SELECT * FROM users;
id  name   email
--  -----  -------------------
1   Alice  alice@example.com
2   Bob    bob@example.com
sqlite> .quit
```

### Execute SQL from Command Line

```bash
./sqlite3_cli.py mydata.db "SELECT * FROM users WHERE id=1"
```

### Execute SQL from File

```bash
./sqlite3_cli.py mydata.db < script.sql

# Or using .read command
./sqlite3_cli.py mydata.db ".read script.sql"
```

### Command-Line Options

```bash
./sqlite3_cli.py [OPTIONS] [DATABASE] [SQL]

Options:
  -help                Show help message
  -init FILE          Read/process named file on startup
  -header             Turn headers on
  -noheader           Turn headers off
  -echo               Print commands before execution
  -bail               Stop after hitting an error
  -csv                Set mode to CSV
  -column             Set mode to column
  -line               Set mode to line
  -list               Set mode to list (default)
  -html               Set mode to HTML
  -separator SEP      Set separator for list mode
  -nullvalue TEXT     Set text string for NULL values
```

Examples:
```bash
# CSV output with headers
./sqlite3_cli.py -csv -header mydata.db "SELECT * FROM users"

# Column mode
./sqlite3_cli.py -column -header mydata.db "SELECT * FROM users"

# Custom separator
./sqlite3_cli.py -separator "," mydata.db "SELECT * FROM users"
```

## Meta-Commands

All standard SQLite meta-commands are supported:

| Command | Description |
|---------|-------------|
| `.help` | Show help message |
| `.quit` or `.exit` | Exit the program |
| `.tables ?PATTERN?` | List tables matching pattern |
| `.schema ?TABLE?` | Show CREATE statements |
| `.databases` | List attached databases |
| `.indices ?TABLE?` | Show indexes |
| `.dump ?TABLE?` | Dump database as SQL |
| `.read FILENAME` | Execute SQL from file |
| `.mode MODE` | Set output mode |
| `.headers on\|off` | Turn headers on/off |
| `.separator STRING` | Change output separator |
| `.nullvalue STRING` | Set NULL display value |
| `.echo on\|off` | Echo commands |
| `.bail on\|off` | Stop on errors |
| `.width NUM ...` | Set column widths |
| `.output FILENAME` | Redirect output to file |
| `.show` | Show current settings |

## Output Modes

### list (default)
```
1|Alice|alice@example.com
2|Bob|bob@example.com
```

### csv
```
1,Alice,alice@example.com
2,Bob,bob@example.com
```

### column
```
id  name   email
1   Alice  alice@example.com
2   Bob    bob@example.com
```

### line
```
         id = 1
       name = Alice
      email = alice@example.com

         id = 2
       name = Bob
      email = bob@example.com
```

### html
```html
<TABLE>
<TR><TD>1</TD><TD>Alice</TD><TD>alice@example.com</TD></TR>
<TR><TD>2</TD><TD>Bob</TD><TD>bob@example.com</TD></TR>
</TABLE>
```

### insert
```sql
INSERT INTO table VALUES(1,'Alice','alice@example.com');
INSERT INTO table VALUES(2,'Bob','bob@example.com');
```

### tabs
```
1	Alice	alice@example.com
2	Bob	bob@example.com
```

## Examples

### Create and Populate Database

```bash
./sqlite3_cli.py mydata.db << 'EOF'
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL,
    stock INTEGER
);

INSERT INTO products VALUES (1, 'Laptop', 999.99, 15);
INSERT INTO products VALUES (2, 'Mouse', 29.99, 50);
INSERT INTO products VALUES (3, 'Keyboard', 79.99, 30);

.mode column
.headers on
SELECT * FROM products;
EOF
```

### Export to CSV

```bash
./sqlite3_cli.py -csv -header mydata.db "SELECT * FROM products" > products.csv
```

### Dump Database

```bash
./sqlite3_cli.py mydata.db .dump > backup.sql
```

### Restore Database

```bash
./sqlite3_cli.py newdata.db < backup.sql
```

### Query with Formatting

```bash
./sqlite3_cli.py mydata.db << 'EOF'
.mode column
.headers on
.width 5 20 10 8
SELECT * FROM products WHERE price < 100;
EOF
```

## Compatibility

This implementation aims to be compatible with the standard SQLite3 CLI for most common use cases. It supports:

- ✅ All basic SQL operations (SELECT, INSERT, UPDATE, DELETE, etc.)
- ✅ Interactive REPL mode
- ✅ Batch mode (reading from files/stdin)
- ✅ All major output modes
- ✅ Common meta-commands
- ✅ Command-line options
- ✅ Multiple statements in one execution

### Differences from Standard CLI

- Written in pure Python (standard CLI is in C)
- Uses Python's sqlite3 module (standard CLI uses SQLite C library)
- Some advanced features may not be implemented
- Performance may be slower for very large datasets

## Dependencies

**None!** Uses only Python standard library:
- `sqlite3` - Database interface
- `sys` - System operations
- `os` - Operating system interface
- `csv` - CSV file handling
- `re` - Regular expressions
- `io.StringIO` - String I/O

## Requirements

- Python 3.6 or higher
- No external packages needed

## Use Cases

- **Portable SQLite tool** - Run SQLite CLI anywhere Python is installed
- **Embedded in Python projects** - Import as a module
- **Learning tool** - Understand SQLite CLI implementation
- **Cross-platform** - Works identically on Windows, macOS, and Linux
- **Scripting** - Easy to modify for custom behavior

## License

Free to use and modify.

## Contributing

Feel free to extend this implementation with additional features!
