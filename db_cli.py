#!/usr/bin/env python3
"""
Universal Database CLI - Compatible with both SQLite3 and DuckDB
Supports sqlite3 (standard library) and duckdb (if installed)
"""

import sys
import os
import csv
import re
from io import StringIO
from typing import List, Tuple, Any, Optional
from abc import ABC, abstractmethod


class DatabaseBackend(ABC):
    """Abstract base class for database backends"""

    @abstractmethod
    def connect(self, database: str):
        """Connect to database"""
        pass

    @abstractmethod
    def close(self):
        """Close database connection"""
        pass

    @abstractmethod
    def execute(self, sql: str):
        """Execute SQL statement"""
        pass

    @abstractmethod
    def fetchall(self):
        """Fetch all results"""
        pass

    @abstractmethod
    def commit(self):
        """Commit transaction"""
        pass

    @abstractmethod
    def get_description(self):
        """Get cursor description"""
        pass

    @abstractmethod
    def get_error_class(self):
        """Get the error exception class"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get backend name"""
        pass


class SQLiteBackend(DatabaseBackend):
    """SQLite database backend"""

    def __init__(self):
        import sqlite3
        self.sqlite3 = sqlite3
        self.conn = None
        self.cursor = None

    def connect(self, database: str):
        self.conn = self.sqlite3.connect(database)
        self.cursor = self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.close()

    def execute(self, sql: str):
        self.cursor.execute(sql)

    def fetchall(self):
        return self.cursor.fetchall()

    def commit(self):
        self.conn.commit()

    def get_description(self):
        return self.cursor.description

    def get_error_class(self):
        return self.sqlite3.Error

    def get_name(self) -> str:
        return "SQLite"


class DuckDBBackend(DatabaseBackend):
    """DuckDB database backend"""

    def __init__(self):
        try:
            import duckdb
            self.duckdb = duckdb
            self.conn = None
        except ImportError:
            raise ImportError("duckdb module not installed. Install with: pip install duckdb")

    def connect(self, database: str):
        # DuckDB uses :memory: for in-memory databases, same as SQLite
        self.conn = self.duckdb.connect(database)

    def close(self):
        if self.conn:
            self.conn.close()

    def execute(self, sql: str):
        self.result = self.conn.execute(sql)

    def fetchall(self):
        return self.result.fetchall()

    def commit(self):
        self.conn.commit()

    def get_description(self):
        return self.result.description

    def get_error_class(self):
        return self.duckdb.Error

    def get_name(self) -> str:
        return "DuckDB"


class DatabaseCLI:
    """Universal database command-line interface for SQLite and DuckDB"""

    def __init__(self, database: str = ":memory:", db_type: str = "auto"):
        self.database = database
        self.backend: Optional[DatabaseBackend] = None

        # Determine backend type
        if db_type == "auto":
            self.db_type = self._detect_db_type(database)
        else:
            self.db_type = db_type.lower()

        # Initialize backend
        if self.db_type == "duckdb":
            self.backend = DuckDBBackend()
        else:
            self.backend = SQLiteBackend()

        # Output settings
        self.mode = "list"  # list, csv, column, line, html, insert, quote, tabs, tcl
        self.separator = "|"
        self.headers = False
        self.nullvalue = ""
        self.width = []  # Column widths for column mode
        self.echo = False
        self.bail_on_error = False

        # Transaction tracking
        self.in_transaction = False

        # Command history
        self.history = []

    def _detect_db_type(self, database: str) -> str:
        """Auto-detect database type from filename"""
        if database == ":memory:":
            return "sqlite"

        ext = os.path.splitext(database)[1].lower()
        if ext in ('.duckdb', '.ddb'):
            return "duckdb"
        else:
            # Default to SQLite for .db, .sqlite, .sqlite3, or no extension
            return "sqlite"

    def connect(self):
        """Connect to the database"""
        try:
            self.backend.connect(self.database)
            return True
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    def close(self):
        """Close database connection"""
        if self.backend:
            self.backend.close()

    def execute_sql(self, sql: str) -> bool:
        """Execute SQL statement and display results"""
        try:
            if self.echo:
                print(sql)

            # Check for transaction control statements
            sql_upper = sql.strip().upper()
            if sql_upper.startswith('BEGIN'):
                self.in_transaction = True
            elif sql_upper in ('COMMIT', 'END'):
                self.in_transaction = False
            elif sql_upper == 'ROLLBACK':
                self.in_transaction = False

            self.backend.execute(sql)

            # Check if this is a SELECT or similar query that returns rows
            # Exclude INSERT, UPDATE, DELETE which may return counts in DuckDB
            is_modification = sql_upper.startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER'))

            description = self.backend.get_description()
            if description and not is_modification:
                self.display_results(self.backend.fetchall(), description)
            else:
                # For INSERT, UPDATE, DELETE, etc.
                # Fetch results to clear them (DuckDB returns counts)
                if description:
                    self.backend.fetchall()
                # Only auto-commit if not in an explicit transaction
                if not self.in_transaction:
                    self.backend.commit()

            return True
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            if self.bail_on_error:
                sys.exit(1)
            return False

    def display_results(self, rows: List[Tuple], description: Tuple):
        """Display query results based on current mode"""
        if not rows and not self.headers:
            return

        columns = [col[0] for col in description]

        if self.mode == "list":
            self._display_list(rows, columns)
        elif self.mode == "csv":
            self._display_csv(rows, columns)
        elif self.mode == "column":
            self._display_column(rows, columns)
        elif self.mode == "line":
            self._display_line(rows, columns)
        elif self.mode == "html":
            self._display_html(rows, columns)
        elif self.mode == "insert":
            self._display_insert(rows, columns)
        elif self.mode == "quote":
            self._display_quote(rows, columns)
        elif self.mode == "tabs":
            self._display_tabs(rows, columns)
        elif self.mode == "tcl":
            self._display_tcl(rows, columns)

    def _format_value(self, value: Any) -> str:
        """Format a value for output"""
        if value is None:
            return self.nullvalue
        return str(value)

    def _display_list(self, rows: List[Tuple], columns: List[str]):
        """Display in list mode (separator-delimited)"""
        if self.headers:
            print(self.separator.join(columns))
        for row in rows:
            print(self.separator.join(self._format_value(v) for v in row))

    def _display_csv(self, rows: List[Tuple], columns: List[str]):
        """Display in CSV mode"""
        output = StringIO()
        writer = csv.writer(output)

        if self.headers:
            writer.writerow(columns)
        for row in rows:
            writer.writerow([self._format_value(v) for v in row])

        print(output.getvalue(), end='')

    def _display_column(self, rows: List[Tuple], columns: List[str]):
        """Display in column mode (aligned columns)"""
        # Calculate column widths
        widths = [len(col) for col in columns]
        for row in rows:
            for i, value in enumerate(row):
                widths[i] = max(widths[i], len(self._format_value(value)))

        # Apply custom widths if set
        if self.width:
            for i, w in enumerate(self.width):
                if i < len(widths) and w > 0:
                    widths[i] = w

        # Print headers
        if self.headers:
            header_parts = []
            for col, width in zip(columns, widths):
                header_parts.append(col.ljust(width))
            print("  ".join(header_parts))
            print("  ".join("-" * w for w in widths))

        # Print rows
        for row in rows:
            row_parts = []
            for value, width in zip(row, widths):
                row_parts.append(self._format_value(value).ljust(width))
            print("  ".join(row_parts))

    def _display_line(self, rows: List[Tuple], columns: List[str]):
        """Display in line mode (one value per line)"""
        for i, row in enumerate(rows):
            for col, value in zip(columns, row):
                print(f"{col:>15} = {self._format_value(value)}")
            if i < len(rows) - 1:
                print()

    def _display_html(self, rows: List[Tuple], columns: List[str]):
        """Display in HTML mode"""
        print("<TABLE>")
        if self.headers:
            print("<TR>", end='')
            for col in columns:
                print(f"<TH>{col}</TH>", end='')
            print("</TR>")
        for row in rows:
            print("<TR>", end='')
            for value in row:
                print(f"<TD>{self._format_value(value)}</TD>", end='')
            print("</TR>")
        print("</TABLE>")

    def _display_insert(self, rows: List[Tuple], columns: List[str]):
        """Display as INSERT statements"""
        table = "table"  # Default table name
        for row in rows:
            values = []
            for value in row:
                if value is None:
                    values.append("NULL")
                elif isinstance(value, str):
                    escaped = value.replace("'", "''")
                    values.append(f"'{escaped}'")
                else:
                    values.append(str(value))
            print(f"INSERT INTO {table} VALUES({','.join(values)});")

    def _display_quote(self, rows: List[Tuple], columns: List[str]):
        """Display with SQL quoting"""
        for row in rows:
            parts = []
            for value in row:
                if value is None:
                    parts.append("NULL")
                elif isinstance(value, str):
                    escaped = value.replace("'", "''")
                    parts.append(f"'{escaped}'")
                elif isinstance(value, (int, float)):
                    parts.append(str(value))
                else:
                    parts.append(f"'{str(value)}'")
            print(self.separator.join(parts))

    def _display_tabs(self, rows: List[Tuple], columns: List[str]):
        """Display in tab-separated mode"""
        if self.headers:
            print("\t".join(columns))
        for row in rows:
            print("\t".join(self._format_value(v) for v in row))

    def _display_tcl(self, rows: List[Tuple], columns: List[str]):
        """Display in TCL list mode"""
        for row in rows:
            parts = []
            for value in row:
                v = self._format_value(value)
                if ' ' in v or '{' in v or '}' in v:
                    v = '{' + v + '}'
                parts.append(v)
            print(" ".join(parts))

    def execute_meta_command(self, command: str) -> bool:
        """Execute meta-commands (commands starting with .)"""
        parts = command[1:].split(None, 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "help":
            self.show_help()
        elif cmd == "quit" or cmd == "exit":
            return False
        elif cmd == "tables":
            self.show_tables(args)
        elif cmd == "schema":
            self.show_schema(args)
        elif cmd == "databases":
            self.show_databases()
        elif cmd == "indices" or cmd == "indexes":
            self.show_indices(args)
        elif cmd == "mode":
            self.set_mode(args)
        elif cmd == "separator":
            self.separator = args if args else "|"
        elif cmd == "headers":
            self.set_headers(args)
        elif cmd == "nullvalue":
            self.nullvalue = args
        elif cmd == "echo":
            self.set_echo(args)
        elif cmd == "bail":
            self.set_bail(args)
        elif cmd == "width":
            self.set_width(args)
        elif cmd == "read":
            self.read_file(args)
        elif cmd == "output":
            self.set_output(args)
        elif cmd == "dump":
            self.dump_database(args)
        elif cmd == "show":
            self.show_settings()
        else:
            print(f"Error: unknown command or invalid arguments: \"{command}\". Enter \".help\" for help", file=sys.stderr)

        return True

    def show_help(self):
        """Display help message"""
        help_text = f""".bail on|off           Stop after hitting an error. Default OFF
.databases           List names and files of attached databases
.dump ?TABLE?        Render database content as SQL
.echo on|off         Turn command echo on or off
.exit                Exit this program
.headers on|off      Turn display of headers on or off
.help                Show this message
.indices ?TABLE?     Show names of indexes
.mode MODE           Set output mode
   csv              Comma-separated values
   column           Left-aligned columns
   html             HTML <table> code
   insert           SQL insert statements
   line             One value per line
   list             Values delimited by separator
   quote            Escape answers as for SQL
   tabs             Tab-separated values
   tcl              TCL list elements
.nullvalue STRING    Use STRING in place of NULL values
.output FILENAME     Send output to FILENAME
.output stdout       Send output to the screen
.quit                Exit this program
.read FILENAME       Execute SQL in FILENAME
.schema ?TABLE?      Show the CREATE statements
.separator STRING    Change separator used by output mode
.show                Show the current values for various settings
.tables ?PATTERN?    List names of tables matching pattern
.width NUM NUM ...   Set column widths for column mode

Database type: {self.backend.get_name()}"""
        print(help_text)

    def show_tables(self, pattern: str = ""):
        """Show all tables matching pattern"""
        if self.db_type == "duckdb":
            # DuckDB uses information_schema
            if pattern:
                sql = "SELECT table_name FROM information_schema.tables WHERE table_schema='main' AND table_name LIKE ? ORDER BY table_name"
                self.backend.execute(sql)
                # DuckDB doesn't support parameterized queries the same way, use string formatting
                sql = f"SELECT table_name FROM information_schema.tables WHERE table_schema='main' AND table_name LIKE '{pattern}' ORDER BY table_name"
                self.backend.execute(sql)
            else:
                sql = "SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY table_name"
                self.backend.execute(sql)
        else:
            # SQLite uses sqlite_master
            if pattern:
                sql = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ? ORDER BY name"
                self.backend.execute(sql)
            else:
                sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                self.backend.execute(sql)

        tables = [row[0] for row in self.backend.fetchall()]
        if tables:
            # Display in columns
            max_width = max(len(t) for t in tables) if tables else 0
            cols = max(1, 80 // (max_width + 2))
            for i, table in enumerate(tables):
                print(table.ljust(max_width + 2), end='')
                if (i + 1) % cols == 0:
                    print()
            if len(tables) % cols != 0:
                print()

    def show_schema(self, table: str = ""):
        """Show schema for table or all tables"""
        if self.db_type == "duckdb":
            # DuckDB doesn't have sqlite_master, need to reconstruct from information_schema
            if table:
                # Show CREATE TABLE for specific table
                try:
                    result = self.backend.conn.execute(f"SELECT sql FROM duckdb_tables() WHERE table_name = '{table}'")
                    for row in result.fetchall():
                        if row[0]:
                            print(row[0] + ";")
                except:
                    # Fallback: describe the table
                    print(f"-- Schema for {table}")
                    self.backend.execute(f"DESCRIBE {table}")
                    for row in self.backend.fetchall():
                        print(f"-- {row}")
            else:
                # Show all tables
                try:
                    result = self.backend.conn.execute("SELECT sql FROM duckdb_tables() WHERE sql IS NOT NULL ORDER BY table_name")
                    for row in result.fetchall():
                        if row[0]:
                            print(row[0] + ";")
                except:
                    print("-- Schema information not available in this format for DuckDB")
        else:
            # SQLite
            if table:
                sql = "SELECT sql FROM sqlite_master WHERE name = ? AND sql IS NOT NULL"
                self.backend.execute(sql)
            else:
                sql = "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"
                self.backend.execute(sql)

            for row in self.backend.fetchall():
                if row[0]:
                    print(row[0] + ";")

    def show_databases(self):
        """Show attached databases"""
        if self.db_type == "duckdb":
            self.backend.execute("SELECT database_name, path FROM duckdb_databases()")
        else:
            self.backend.execute("PRAGMA database_list")

        for row in self.backend.fetchall():
            if self.db_type == "duckdb":
                print(f"{row[0]}: {row[1] if row[1] else ':memory:'}")
            else:
                seq, name, file = row
                print(f"{name}: {file}")

    def show_indices(self, table: str = ""):
        """Show indices for table or all indices"""
        if self.db_type == "duckdb":
            if table:
                sql = f"SELECT index_name FROM duckdb_indexes() WHERE table_name = '{table}' ORDER BY index_name"
            else:
                sql = "SELECT index_name FROM duckdb_indexes() ORDER BY index_name"
            self.backend.execute(sql)
        else:
            if table:
                sql = "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name = ? ORDER BY name"
                self.backend.execute(sql)
            else:
                sql = "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
                self.backend.execute(sql)

        for row in self.backend.fetchall():
            print(row[0])

    def set_mode(self, mode: str):
        """Set output mode"""
        mode = mode.lower()
        valid_modes = ["csv", "column", "html", "insert", "line", "list", "quote", "tabs", "tcl"]
        if mode in valid_modes:
            self.mode = mode
            # Set default separator for modes
            if mode == "csv":
                self.separator = ","
            elif mode == "tabs":
                self.separator = "\t"
            elif mode == "list":
                self.separator = "|"
        else:
            print(f"Error: mode should be one of: {' '.join(valid_modes)}", file=sys.stderr)

    def set_headers(self, value: str):
        """Set headers on/off"""
        value = value.lower()
        if value in ("on", "1", "yes", "true"):
            self.headers = True
        elif value in ("off", "0", "no", "false", ""):
            self.headers = False
        else:
            print(f"Error: headers should be on or off", file=sys.stderr)

    def set_echo(self, value: str):
        """Set echo on/off"""
        value = value.lower()
        if value in ("on", "1", "yes", "true"):
            self.echo = True
        elif value in ("off", "0", "no", "false", ""):
            self.echo = False
        else:
            print(f"Error: echo should be on or off", file=sys.stderr)

    def set_bail(self, value: str):
        """Set bail on/off"""
        value = value.lower()
        if value in ("on", "1", "yes", "true"):
            self.bail_on_error = True
        elif value in ("off", "0", "no", "false", ""):
            self.bail_on_error = False
        else:
            print(f"Error: bail should be on or off", file=sys.stderr)

    def set_width(self, widths: str):
        """Set column widths"""
        try:
            self.width = [int(w) for w in widths.split()]
        except ValueError:
            print(f"Error: width values should be integers", file=sys.stderr)

    def read_file(self, filename: str):
        """Execute SQL from file"""
        if not filename:
            print("Error: .read requires a filename", file=sys.stderr)
            return

        try:
            with open(filename, 'r') as f:
                content = f.read()
                self.execute_commands(content)
        except IOError as e:
            print(f"Error: {e}", file=sys.stderr)

    def set_output(self, filename: str):
        """Redirect output to file"""
        if filename == "stdout" or filename == "":
            sys.stdout = sys.__stdout__
        else:
            try:
                sys.stdout = open(filename, 'w')
            except IOError as e:
                print(f"Error: {e}", file=sys.stderr)

    def dump_database(self, table: str = ""):
        """Dump database as SQL"""
        # Begin transaction
        print("BEGIN TRANSACTION;")

        if self.db_type == "duckdb":
            # DuckDB dump approach
            if table:
                # Export specific table
                try:
                    # Get table schema
                    result = self.backend.conn.execute(f"SELECT sql FROM duckdb_tables() WHERE table_name = '{table}'")
                    for row in result.fetchall():
                        if row[0]:
                            print(row[0] + ";")

                    # Get data
                    self.backend.execute(f"SELECT * FROM {table}")
                    rows = self.backend.fetchall()

                    if rows:
                        for row in rows:
                            values = []
                            for value in row:
                                if value is None:
                                    values.append("NULL")
                                elif isinstance(value, str):
                                    escaped = value.replace("'", "''")
                                    values.append(f"'{escaped}'")
                                else:
                                    values.append(str(value))
                            print(f"INSERT INTO {table} VALUES({','.join(values)});")
                except Exception as e:
                    print(f"-- Error dumping table: {e}", file=sys.stderr)
            else:
                # Dump all tables
                result = self.backend.conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'")
                tables = result.fetchall()

                for (table_name,) in tables:
                    # Get table schema
                    try:
                        schema_result = self.backend.conn.execute(f"SELECT sql FROM duckdb_tables() WHERE table_name = '{table_name}'")
                        for row in schema_result.fetchall():
                            if row[0]:
                                print(row[0] + ";")

                        # Get data
                        data_result = self.backend.conn.execute(f"SELECT * FROM {table_name}")
                        rows = data_result.fetchall()

                        if rows:
                            for row in rows:
                                values = []
                                for value in row:
                                    if value is None:
                                        values.append("NULL")
                                    elif isinstance(value, str):
                                        escaped = value.replace("'", "''")
                                        values.append(f"'{escaped}'")
                                    else:
                                        values.append(str(value))
                                print(f"INSERT INTO {table_name} VALUES({','.join(values)});")
                    except Exception as e:
                        print(f"-- Error dumping table {table_name}: {e}", file=sys.stderr)
        else:
            # SQLite dump approach
            # Get all tables
            if table:
                self.backend.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name = ?")
            else:
                self.backend.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")

            tables = self.backend.fetchall()

            for table_name, create_sql in tables:
                if create_sql:
                    print(create_sql + ";")

                    # Dump data
                    self.backend.execute(f"SELECT * FROM {table_name}")
                    rows = self.backend.fetchall()

                    if rows:
                        for row in rows:
                            values = []
                            for value in row:
                                if value is None:
                                    values.append("NULL")
                                elif isinstance(value, str):
                                    escaped = value.replace("'", "''")
                                    values.append(f"'{escaped}'")
                                else:
                                    values.append(str(value))
                            print(f"INSERT INTO {table_name} VALUES({','.join(values)});")

            # Get indices
            if table:
                self.backend.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name = ? AND sql IS NOT NULL")
            else:
                self.backend.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")

            for row in self.backend.fetchall():
                if row[0]:
                    print(row[0] + ";")

        print("COMMIT;")

    def show_settings(self):
        """Show current settings"""
        print(f"        echo: {('on' if self.echo else 'off')}")
        print(f"     headers: {('on' if self.headers else 'off')}")
        print(f"        mode: {self.mode}")
        print(f"   nullvalue: \"{self.nullvalue}\"")
        print(f"      output: stdout")
        print(f"   separator: \"{self.separator}\"")
        print(f"     backend: {self.backend.get_name()}")
        if self.width:
            print(f"       width: {' '.join(str(w) for w in self.width)}")

    def execute_commands(self, text: str):
        """Execute multiple SQL commands from text"""
        # Split by semicolons, but handle meta-commands separately
        buffer = ""
        in_string = False
        quote_char = None

        for line in text.split('\n'):
            line = line.strip()

            # Skip comments
            if line.startswith('--'):
                continue

            # Handle meta-commands
            if line.startswith('.'):
                if not self.execute_meta_command(line):
                    return False
                continue

            # Accumulate SQL statement
            buffer += line + " "

            # Check for string quotes
            for char in line:
                if char in ('"', "'") and (quote_char is None or quote_char == char):
                    if quote_char is None:
                        quote_char = char
                        in_string = True
                    else:
                        quote_char = None
                        in_string = False

            # Execute when we hit a semicolon outside of strings
            if ';' in line and not in_string:
                statements = buffer.split(';')
                for stmt in statements[:-1]:
                    stmt = stmt.strip()
                    if stmt:
                        self.execute_sql(stmt)
                buffer = statements[-1]

        # Execute any remaining statement
        buffer = buffer.strip()
        if buffer and not buffer.startswith('.'):
            self.execute_sql(buffer)

        return True

    def interactive_mode(self):
        """Run interactive REPL"""
        db_name = self.backend.get_name()
        print(f"{db_name} CLI (Python implementation)")
        print(f"Enter \".help\" for usage hints.")

        buffer = ""

        while True:
            try:
                if buffer:
                    prompt = "   ...> "
                else:
                    prompt = f"{self.db_type}> "

                line = input(prompt)

                # Handle meta-commands
                if line.strip().startswith('.'):
                    if not self.execute_meta_command(line.strip()):
                        break
                    continue

                # Accumulate SQL statement
                buffer += line + " "

                # Execute when we hit a semicolon
                if ';' in line:
                    self.execute_sql(buffer.strip().rstrip(';'))
                    buffer = ""

            except EOFError:
                print()  # Newline for clean exit
                break
            except KeyboardInterrupt:
                print()
                buffer = ""
                continue

    def run_command(self, command: str):
        """Run a single SQL command"""
        self.execute_commands(command)


def main():
    """Main entry point"""
    database = ":memory:"
    commands = []
    init_file = None
    db_type = "auto"

    # Parse command-line arguments
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg in ("-help", "--help"):
            print("Usage: db_cli.py [OPTIONS] [DATABASE]")
            print("Options:")
            print("  -db TYPE         Database type: sqlite, duckdb (default: auto-detect)")
            print("  -init FILE       Read/process named file")
            print("  -header          Turn headers on")
            print("  -noheader        Turn headers off")
            print("  -echo            Print commands before execution")
            print("  -bail            Stop after hitting an error")
            print("  -csv             Set mode to CSV")
            print("  -column          Set mode to column")
            print("  -line            Set mode to line")
            print("  -list            Set mode to list")
            print("  -html            Set mode to HTML")
            print("  -separator SEP   Set separator for list mode")
            print("  -nullvalue TEXT  Set text string for NULL values")
            print("  DATABASE         Database file (default: :memory:)")
            print("  COMMAND          SQL command to execute")
            print("")
            print("Database auto-detection:")
            print("  .db, .sqlite, .sqlite3 -> SQLite")
            print("  .duckdb, .ddb -> DuckDB")
            sys.exit(0)
        elif arg == "-db":
            i += 1
            if i < len(sys.argv):
                db_type = sys.argv[i]
        elif arg == "-init":
            i += 1
            if i < len(sys.argv):
                init_file = sys.argv[i]
        elif arg == "-header":
            commands.append(".headers on")
        elif arg == "-noheader":
            commands.append(".headers off")
        elif arg == "-echo":
            commands.append(".echo on")
        elif arg == "-bail":
            commands.append(".bail on")
        elif arg == "-csv":
            commands.append(".mode csv")
        elif arg == "-column":
            commands.append(".mode column")
        elif arg == "-line":
            commands.append(".mode line")
        elif arg == "-list":
            commands.append(".mode list")
        elif arg == "-html":
            commands.append(".mode html")
        elif arg == "-separator":
            i += 1
            if i < len(sys.argv):
                commands.append(f".separator {sys.argv[i]}")
        elif arg == "-nullvalue":
            i += 1
            if i < len(sys.argv):
                commands.append(f".nullvalue {sys.argv[i]}")
        elif not arg.startswith('-'):
            # First non-option arg is database, rest are commands
            if database == ":memory:":
                database = arg
            else:
                commands.append(arg)
        else:
            print(f"Error: unknown option: {arg}", file=sys.stderr)
            sys.exit(1)

        i += 1

    # Create CLI instance
    try:
        cli = DatabaseCLI(database, db_type)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not cli.connect():
        sys.exit(1)

    try:
        # Execute init file if specified
        if init_file:
            cli.read_file(init_file)

        # Execute commands from arguments
        for cmd in commands:
            if cmd.startswith('.'):
                cli.execute_meta_command(cmd)
            else:
                cli.execute_sql(cmd)

        # If commands were provided, don't enter interactive mode
        if not commands:
            # Check if stdin is a pipe
            if not sys.stdin.isatty():
                # Read from stdin
                content = sys.stdin.read()
                cli.execute_commands(content)
            else:
                # Interactive mode
                cli.interactive_mode()
    finally:
        cli.close()


if __name__ == "__main__":
    main()
