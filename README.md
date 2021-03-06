# Simple Discord Database
Using Discord as a simple database

## I'll take "not technically against the TOS" for 500, Alex
SDDB is the latest in a long linage of using things as databases that were never designed to be used as databases.  Mooching off someone else's existing publicly available storage capacity so that you don't have to stand up your own private storage.  Implementations of this concept can be done anywhere raw text can be uploaded, viewed, edited, and deleted.  SDDB implements this using a Discord guild (commonly called a server) and unlike most platforms does not violate the terms of service, which can be verified [here](https://discord.com/terms).

## Use Cases
SDDB was written to fulfill a very specific use case where I need to support my Discord chatbot's ever expanding scope creep without storing data locally; as it is hosted on grandma's old laptop with no battery life from 2007 that came in a box that looked like a cow and has a "certified Windows Vista" sticker on it.  As such SDDB was designed for light intensity persistent data storage through unexpected restarts and inevitable hardware failures.

SDDB exists in a niche for small to medium size applications that already connect or interact with Discord and have a need for infrequently accessed persistent data storage, such as configuration or personalization settings.  These applications can take advantage of Discord's existing capacity to store data therefore avoiding the need to stand up their own infrastructure.  SDDB uses the Discord API through Rapptz [Discord.py](https://github.com/Rapptz/discord.py) package and is subject to API rate limiters.  Therefore any application that would frequently hit the database will endure performance degradation globally across Discord.  Additionally any application with requirements exceeding the limitations below have long outgrown SDDB's usefulness and should probably stand up a proper database.

## Limitations
* SDDB uses the Discord API and is subject to it's API rate limiters.
* The Discord account using SDDB needs administrator permissions on the server used as a database.
* Database, table and column names only support alphanumeric characters.
* The delimiter character 0x2502 is not allowed under any circumstances.
* There is a limit of 1024 tables per database.
* There is a limit of 1024 rows per table.
* There is a hard limit of 2000 characters of data per row spread across all columns.
* NULL data is stored as the string 'NULL'.
* Only four datatypes are currently supported, strings, integers, floats, and dates.
* Database metadata is not cached and requires an API call (this is for my personal use case with limited memory but might be changed in the future as caching will reduce total API calls to Discord).
* Does not support multiple WHERE clauses, only one WHERE clause is allowed (multiple WHERE clauses coming soon, maybe).
* Data is stored in plaintext and is not encrypted, **do not store sensitive data with SDDB** (coming soon, maybe).

## Requirements
* Python 3.5.3 or higher
* Rapptz [Discord.py](https://github.com/Rapptz/discord.py)

## Quickstart

SDDB's database management system needs to be initialized with the client instance from Rapptz [Discord.py](https://github.com/Rapptz/discord.py) and the guild_id of the Discord server to be used as a database.
```python
import discord
import SDDB

client = discord.Client(intents = discord.Intents.all())
dbms = SDDB.DBMS(client, 000000000000000) # replace 0's with guild id
```
Once the DBMS has been initialized we need to create a database.
```python
await dbms.create_database("example")
```
Now we can create a table called person on the example database with three columns called firstname, lastname as strings and age as an integer and populate it with some data.
```python
await dbms.create_table("person", firstname="str", lastname="str", age="int") # fields are arguments with their datatypes
await dbms.insert_into("person", firstname="Bob", lastname="Smith", age="32") # create Bob
await dbms.insert_into("person", firstname="Morgan", lastname="Freeman") # we don't need to populate all fields
```
Now we can run some queries against this data on our database.
```python
await dbms.query(select="firstname", against="person", where="lastname = Smith") # get Bob
await dbms.query(select="*", against="person", where="age >= 32") # supports all comparison operators
await dbms.query(against="person") # all rows on person
```
If we want to update or delete rows we can do that too.
```python
await dbms.update(against="person", where="age = 32", age="50") # fields are updated by name
await dbms.delete(against="person", where="lastname = Freeman") # bye bye Morgan Freeman ;(
```

## Documentation

SDDB was written in an attempt to retain SQL-Like syntax in a pythonic environment.  Arguments are named and passed so as to mimic SQL syntax inside function calls. SQL keywords such as alter, select, where, and so on function as you would expect them to with the exception of 'from' which is a python reserved word and has been replaced with 'against' but otherwise functions the same as SQL 'from'.  Where appropriate, variably unknown fields are taken as \*\*kwargs.  With this in mind the SQL statement
```sql
SELECT firstname, lastname, age FROM person WHERE lastname = "Smith"
```
would be written as
```python
query(select="firstname, lastname, age", against="person", where="lastname = Smith")
```
and the SQL statement
```sql
CREATE TABLE person (firstname varchar[64], lastname varchar[64], age int)
```
would be written as
```python
create_table("person", firstname="str", lastname="str", age="int")
```

Below are the classes with their properties and methods included in SDDB.

### DBMS
Database Management System, main class for interacting with a database on Discord.

#### Properties
* `d`
The Rapptz [Discord.py](https://github.com/Rapptz/discord.py) client
* `db`
The guild being used as a database
* `ad`
The active database pointer

#### Methods
* `__init__(discord_client, database_guild)`
Constructor for the DBMS object, requires a Rapptz [Discord.py](https://github.com/Rapptz/discord.py) client object and the guild id of the Discord server to be used as a database

* `use(name)`
Switches the active database to database with 'name'

* `create_database(name)`
Creates a database with 'name' and sets the active database pointer to 'name'

* `drop_database(name)`
Drops a database with 'name' and sets the active database pointer to None

* `alter_database(name, rename)`
Alters the database with name, currently only supports rename

* `create_table(name, **kwargs)`
Creates a table with 'name' and columns defined in \*\*kwargs

* `drop_table(name)`
Drops the table with 'name'

* `alter_table(name, add="", drop="", modify="", rename="")`
Alters a table in accordance with SQL-like syntax, add column, drop column, modify column, rename table

* `query(select="*", against="", where="", use="")`
Issues a query in accordance with SQL-like syntax, returns a Table object

* `insert_into(against, use="", **kwargs)`
Inserts rows into a table in accordance with SQL-like syntax

* `update(agaisnt, where="", use="", **kwargs)`
Updates rows in a table matching the where clause in accordance with SQL-like syntax

* `delete(against, where="", use="")`
Deletes rows in a table matching the where clause in accordance with SQL-like syntax

### Table
A wrapper for the Table

#### Properties
* `table_name`
Name of the Table
* `headers`
A list of TableHeader objects
* `rows`
A list of TalbeRow objects

#### Methods
* `__init__(table_name, headers, rows=None, table_rows=None)`
Constructor for Table wrapper

* `__len__()`
Returns number of columns in table

* `__str__()`
Returns a string representation of the table

* `append(row)`
Appends a TableRow to rows

### TableRow
A wrapper for a row in a table

#### Properties
* `headers`
A list of TableHeader objects
* `records`
A list of TableRecord objects (cells) in the row

#### Methods
* `__init__(headers, records=None, table_records=None)`
Constructor for the TableRow wrapper

* `__len__()`
Returns the number of columns in row

* `__str__()`
Returns a string representation of the row

* `append_record(data)`
Appends a TableRecord to records

* `update_record(index, data)`
Changes the data in a TableRecord at records[index]

### TableRecord
A wrapper for a record (cell) in a table

#### Properties
* `datatype`
String representation for datatype (in the future will be instance of DATATYPE)
* `data`
Variable type data held in the record (cell)

#### Methods
* `__init__(datatype, data)`
Constructor for the TableRecord wrapper

* `__str__()`
Returns a string representation of the record

### TableHeader
A wrapper for the TableHeader

#### Properties
* `column_name`
String of column name
* `datatype`
List of string representations for datatypes (in the future will be instance of DATATYPE)
* `is_primary_key`
Boolean for primary key

#### Methods
* `__init__(hstr, pk=False)`
Constructor for the TableHeader wrapper

* `__str__()`
Returns a string representation of the header

### Clause
A wrapper for WHERE clauses

#### Properties
* `field`
String of field to be compared
* `optype`
Instance of OPTYPE
* `value`
String of comparison value

### DATATYPE
An enumeration of supported datatypes (not currently used)

	STR = 0
	INT = 1
	FLOAT = 2
	DATE = 3

### OPTYPE
An enumeration of supported WHERE operators

	EQ = 0
	NOT = 1
	LESS = 2
	GREATER = 3
	LESSEQ = 4
	GREATEREQ = 5

Maybe more coming soon ¯\\_(ツ)_/¯...