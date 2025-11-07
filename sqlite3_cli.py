#!/usr/bin/env python3
"""
Pure Python SQLite3 CLI - Compatible with sqlite3 command-line tool
Uses only Python standard library (sqlite3, sys, os, csv, etc.)
"""

import sqlite3
import sys
import os
import csv
import re
from io import StringIO
from typing import List, Tuple, Any, Optional


class SQLite3CLI:
    """SQLite3 command-line interface implementation in pure Python"""

    def __init__(self, database: str = ":memory:"):
        self.database = database
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

        # Output settings
        self.mode = "list"  # list, csv, column, line, html, insert, quote, tabs, tcl
        self.separator = "|"
        self.headers = False
        self.nullvalue = ""
        self.width = []  # Column widths for column mode
        self.echo = False
        self.bail_on_error = False

        # Command history
        self.history = []

    def connect(self):
        """Connect to the database"""
        try:
            self.conn = sqlite3.connect(self.database)
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def execute_sql(self, sql: str) -> bool:
        """Execute SQL statement and display results"""
        try:
            if self.echo:
                print(sql)

            self.cursor.execute(sql)

            # Check if this is a SELECT or similar query that returns rows
            if self.cursor.description:
                self.display_results(self.cursor.fetchall(), self.cursor.description)
            else:
                # For INSERT, UPDATE, DELETE, etc.
                self.conn.commit()

            return True
        except sqlite3.Error as e:
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
        help_text = """.bail on|off           Stop after hitting an error. Default OFF
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
.separator STRING    Change separator used by output mode and .import
.show                Show the current values for various settings
.tables ?PATTERN?    List names of tables matching pattern
.width NUM NUM ...   Set column widths for column mode"""
        print(help_text)

    def show_tables(self, pattern: str = ""):
        """Show all tables matching pattern"""
        if pattern:
            sql = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ? ORDER BY name"
            self.cursor.execute(sql, (pattern,))
        else:
            sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            self.cursor.execute(sql)

        tables = [row[0] for row in self.cursor.fetchall()]
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
        if table:
            sql = "SELECT sql FROM sqlite_master WHERE name = ? AND sql IS NOT NULL"
            self.cursor.execute(sql, (table,))
        else:
            sql = "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"
            self.cursor.execute(sql)

        for row in self.cursor.fetchall():
            if row[0]:
                print(row[0] + ";")

    def show_databases(self):
        """Show attached databases"""
        self.cursor.execute("PRAGMA database_list")
        results = self.cursor.fetchall()
        for seq, name, file in results:
            print(f"{name}: {file}")

    def show_indices(self, table: str = ""):
        """Show indices for table or all indices"""
        if table:
            sql = "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name = ? ORDER BY name"
            self.cursor.execute(sql, (table,))
        else:
            sql = "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
            self.cursor.execute(sql)

        for row in self.cursor.fetchall():
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

        # Get all tables
        if table:
            self.cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name = ?", (table,))
        else:
            self.cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")

        tables = self.cursor.fetchall()

        for table_name, create_sql in tables:
            if create_sql:
                print(create_sql + ";")

                # Dump data
                self.cursor.execute(f"SELECT * FROM {table_name}")
                rows = self.cursor.fetchall()

                if rows:
                    # Get column info
                    self.cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in self.cursor.fetchall()]

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
            self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name = ? AND sql IS NOT NULL", (table,))
        else:
            self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")

        for row in self.cursor.fetchall():
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
        print(f"SQLite version 3.x (Python implementation)")
        print(f"Enter \".help\" for usage hints.")

        buffer = ""

        while True:
            try:
                if buffer:
                    prompt = "   ...> "
                else:
                    prompt = "sqlite> "

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

    # Parse command-line arguments
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == "-help" or arg == "--help":
            print("Usage: sqlite3_cli.py [OPTIONS] [DATABASE]")
            print("Options:")
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
            sys.exit(0)
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
    cli = SQLite3CLI(database)

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
