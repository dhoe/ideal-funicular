# Universal Database CLI

A pure Python database CLI that supports both **SQLite3** and **DuckDB** with a unified interface. Compatible with the standard sqlite3 CLI tool while extending support to DuckDB.

## Features

- **Multi-database support** - Works with both SQLite and DuckDB
- **Auto-detection** - Automatically selects the right database based on file extension
- **CLI compatibility** - Compatible with sqlite3 CLI commands and options
- **Multiple output formats** - csv, column, html, insert, line, list, quote, tabs, tcl
- **Meta-commands** - Full support for `.tables`, `.schema`, `.dump`, `.mode`, etc.
- **Transaction support** - Proper handling of BEGIN/COMMIT/ROLLBACK
- **Minimal dependencies** - Only needs DuckDB if you want to use it (SQLite is built-in)

## Installation

### Requirements

- Python 3.6 or higher
- `sqlite3` module (included in Python standard library)
- `duckdb` module (optional, only if you want to use DuckDB)

### Install DuckDB (Optional)

```bash
pip install duckdb
```

### Make Executable

```bash
chmod +x db_cli.py
```

## Usage

### Database Type Auto-Detection

The CLI automatically detects which database to use based on the file extension:

- `.db`, `.sqlite`, `.sqlite3` → **SQLite**
- `.duckdb`, `.ddb` → **DuckDB**
- `:memory:` → **SQLite** (default)

You can override auto-detection with the `-db` flag:

```bash
./db_cli.py -db duckdb mydata.db    # Force DuckDB
./db_cli.py -db sqlite mydata.duckdb # Force SQLite
```

### Interactive Mode

```bash
# SQLite (auto-detected from .db extension)
./db_cli.py mydata.db

# DuckDB (auto-detected from .duckdb extension)
./db_cli.py mydata.duckdb

# In-memory database (SQLite by default)
./db_cli.py
```

Example session:

```
sqlite> CREATE TABLE users (id INT, name TEXT, email TEXT);
sqlite> INSERT INTO users VALUES (1, 'Alice', 'alice@example.com');
sqlite> .mode column
sqlite> .headers on
sqlite> SELECT * FROM users;
id  name   email
--  -----  -------------------
1   Alice  alice@example.com
sqlite> .quit
```

### Command-Line Execution

```bash
# Execute SQL directly
./db_cli.py mydata.db "SELECT * FROM users"

# Execute SQL from file
./db_cli.py mydata.db < script.sql
./db_cli.py mydata.db ".read script.sql"

# Export to CSV
./db_cli.py -csv -header mydata.db "SELECT * FROM users" > output.csv
```

### Command-Line Options

```bash
./db_cli.py [OPTIONS] [DATABASE] [SQL]

Options:
  -db TYPE            Database type: sqlite, duckdb (default: auto-detect)
  -help, --help       Show help message
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

## Meta-Commands

All standard SQLite meta-commands are supported for both databases:

| Command | Description |
|---------|-------------|
| `.help` | Show help message with database type |
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
| `.show` | Show current settings (includes backend type) |

## Examples

### SQLite Examples

```bash
# Create and populate a SQLite database
./db_cli.py mydata.db << 'EOF'
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

### DuckDB Examples

```bash
# Create and populate a DuckDB database
./db_cli.py mydata.duckdb << 'EOF'
CREATE TABLE sales (
    id INTEGER,
    product VARCHAR,
    amount DOUBLE,
    sale_date DATE
);

INSERT INTO sales VALUES
    (1, 'Laptop', 999.99, '2025-01-01'),
    (2, 'Mouse', 29.99, '2025-01-02'),
    (3, 'Keyboard', 79.99, '2025-01-03');

.mode column
.headers on
SELECT product, SUM(amount) as total
FROM sales
GROUP BY product
ORDER BY total DESC;
EOF
```

### Cross-Database Compatibility

The same SQL often works on both databases:

```bash
# Works with both SQLite and DuckDB
./db_cli.py -column -header mydata.db "
SELECT
    name,
    COUNT(*) as count,
    AVG(price) as avg_price
FROM products
GROUP BY name
HAVING count > 1
"
```

### Export and Import

```bash
# Dump SQLite database
./db_cli.py mydata.db .dump > backup.sql

# Restore to SQLite
./db_cli.py newdata.db < backup.sql

# Restore to DuckDB (if SQL is compatible)
./db_cli.py newdata.duckdb < backup.sql

# Export to CSV
./db_cli.py -csv -header mydata.db "SELECT * FROM products" > products.csv
```

### Transactions

Both databases support proper transaction handling:

```bash
./db_cli.py mydata.db << 'EOF'
BEGIN TRANSACTION;
INSERT INTO products VALUES (4, 'Monitor', 299.99, 10);
INSERT INTO products VALUES (5, 'Webcam', 89.99, 20);
COMMIT;

BEGIN TRANSACTION;
DELETE FROM products WHERE stock < 5;
ROLLBACK;  -- Changes are rolled back
EOF
```

## Output Modes

### list (default)
```
1|Laptop|999.99
2|Mouse|29.99
```

### csv
```
1,Laptop,999.99
2,Mouse,29.99
```

### column
```
id  name    price
1   Laptop  999.99
2   Mouse   29.99
```

### line
```
      id = 1
    name = Laptop
   price = 999.99

      id = 2
    name = Mouse
   price = 29.99
```

### html
```html
<TABLE>
<TR><TD>1</TD><TD>Laptop</TD><TD>999.99</TD></TR>
<TR><TD>2</TD><TD>Mouse</TD><TD>29.99</TD></TR>
</TABLE>
```

### insert
```sql
INSERT INTO table VALUES(1,'Laptop',999.99);
INSERT INTO table VALUES(2,'Mouse',29.99);
```

### tabs
```
1	Laptop	999.99
2	Mouse	29.99
```

## Database Differences

While the CLI provides a unified interface, there are some differences between SQLite and DuckDB:

### SQLite
- **File format**: Single file database
- **Data types**: Dynamic typing
- **Best for**: Embedded databases, mobile apps, simple data storage
- **Meta-commands**: Uses `sqlite_master` system table

### DuckDB
- **File format**: Column-oriented storage
- **Data types**: Strong typing with VARCHAR, DOUBLE, etc.
- **Best for**: Analytics, OLAP queries, larger datasets
- **Meta-commands**: Uses `information_schema` and DuckDB system functions

### Type Compatibility

When writing cross-compatible SQL:

```sql
-- Use common types
CREATE TABLE example (
    id INTEGER,           -- Works in both
    name TEXT,            -- SQLite: TEXT, DuckDB: VARCHAR
    amount REAL,          -- SQLite: REAL, DuckDB: DOUBLE
    created_date TEXT     -- Store dates as text for compatibility
);
```

## Advanced Usage

### Using with Scripts

Create a SQL script file:

```sql
-- setup.sql
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER,
    message TEXT,
    timestamp TEXT
);

INSERT INTO logs VALUES (1, 'Application started', '2025-01-01 00:00:00');
INSERT INTO logs VALUES (2, 'User logged in', '2025-01-01 00:05:00');

.mode column
.headers on
SELECT * FROM logs;
```

Execute with either database:

```bash
./db_cli.py mydata.db -init setup.sql
./db_cli.py mydata.duckdb -init setup.sql
```

### Batch Processing

```bash
# Process multiple databases
for db in *.db; do
    echo "Processing $db..."
    ./db_cli.py "$db" "SELECT COUNT(*) FROM users"
done

# Process DuckDB files
for db in *.duckdb; do
    echo "Processing $db..."
    ./db_cli.py "$db" ".tables"
done
```

### Combining with Other Tools

```bash
# Pipe to other commands
./db_cli.py -csv mydata.db "SELECT * FROM users" | grep "alice"

# Use with awk
./db_cli.py -tabs mydata.db "SELECT name, email FROM users" | awk '{print $1}'

# Count results
./db_cli.py -list mydata.db "SELECT * FROM products" | wc -l
```

## Performance Notes

- **SQLite**: Optimized for transactional workloads (OLTP)
- **DuckDB**: Optimized for analytical workloads (OLAP)

Choose the right database for your use case:

- Use **SQLite** for: Applications, websites, mobile apps, simple data storage
- Use **DuckDB** for: Data analysis, reporting, aggregations, data science workflows

## Troubleshooting

### DuckDB Not Installed

If you try to open a `.duckdb` file without DuckDB installed:

```
Error: duckdb module not installed. Install with: pip install duckdb
```

Solution:
```bash
pip install duckdb
```

### Force Database Type

If auto-detection fails or you want to use a specific database:

```bash
./db_cli.py -db sqlite myfile.duckdb  # Use SQLite for .duckdb file
./db_cli.py -db duckdb myfile.db      # Use DuckDB for .db file
```

### Compatibility Issues

Some SQL syntax is database-specific. If you encounter errors:

1. Check the database type with `.show`
2. Consult SQLite or DuckDB documentation for syntax differences
3. Use common SQL subset for maximum compatibility

## Dependencies

### Required (Built-in)
- `sqlite3` - SQLite database interface
- `sys` - System operations
- `os` - Operating system interface
- `csv` - CSV file handling
- `abc` - Abstract base classes
- `typing` - Type hints

### Optional
- `duckdb` - DuckDB database interface (install separately)

## License

Free to use and modify.

## See Also

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [SQLITE3_CLI.md](SQLITE3_CLI.md) - SQLite-only implementation
