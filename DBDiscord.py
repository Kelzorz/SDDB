import discord
import re
from enum import Enum
from datetime import datetime

# DBDiscord uses a Discord guild as a ghetto database and supports simple DB operations - create, select, update, delete.
# The █ character (0xDB) is used as a global delimiter, and is not allowed under any circumstances.
# A database is identified as a channel category in the Discord guild.
# - Databases can have multiple tables
# - Each Database has a master table that maps fields for each table in th database
# A table is identified as a text channel in the Discord guild.
# - Tables have columns as defined by it's record in the master table delimitated by the 0xDB character.
# A row is identified as a text message in a text channel in the Discord guild.
# - Row columns are delimitated by the 0xDB character.
# - Primary key is the message id.
# "from" is a Python keyword and cannot be used as a variable, "against" is used instead for SQL-like syntax.

class DBMS:
	def __init__(self, discord_client, database_guild):
		if not isinstance(discord_client, discord.Client):
			raise TypeError("discord_client must be a discord.Client")
		self.d = discord_client
		self.db = None
		self.ad = None # Active database pointer
		if isinstance(database_guild, discord.Guild):
			self.db = database_guild
		elif isinstance(database_guild, int):
			self.db = d.get_guild(database_guild)
			if self.db is None:
				raise Exception("guild does not exist: " + str(database_guild))
		else:
			raise TypeError("database_guild must be an int or guild object")
		if not self.db.me.guild_permissions.administrator:
			raise Warning("Warning: client does not have administrator permissions on database guild, CREATE and DROP operations may not be successful")

	def use(self, name):
		"""Changes the active database"""
		if violates_str_rules(name) or violates_name_rules(name) or " " in name:
			raise TypeError("Malformed use; illegal character")
		for d in self.db.categories:
			if d.name.lower() == name.lower():
				self.ad = d
				return True
		raise NameError("No database with name")

	async def create_database(self, name):
		"""Creates a database and sets it to the active database"""
		if violates_str_rules(name) or violates_name_rules(name) or " " in name:
			raise TypeError("Malformed create; illegal character")
		for d in self.db.categories:
			if d.name.lower() == name.lower():
				raise NameError("Database with name already exists")
		overwrites = {
		    guild.default_role: discord.PermissionOverwrite(read_messages=False),
		    guild.me: discord.PermissionOverwrite(read_messages=True)
		    }
		self.ad = await self.db.create_category(name, overwrites=overwrites ,reason="DBDiscord: New Database")
		await self.db.create_text_channel(name, category=self.ad, reason="DBDiscord: New Database")
		return

	async def drop_database(self, name):
		"""Drops the database"""
		if violates_str_rules(name) or violates_name_rules(name) or " " in name:
			raise TypeError("Malformed drop; illegal character")
		for d in self.db.categories:
			if d.name.lower() == name.lower():
				for t in d.channels:
					await t.delete(reason="DBDiscord: Drop Database")
				await d.delete(reason="DBDiscord: Drop Database")
				return
		raise NameError("Database with name does not exist")

	async def create_table(self, name, *args):
		"""Creates a table on the active database"""
		if self.ad == None:
			raise Exception("No active database")
		if violates_str_rules(name) or violates_name_rules(name) or " " in name:
			raise TypeError("Malformed create; illegal character")
		if name.lower() == "master":
			raise NameError("master is a reserved table name")
		if len(self.ad.channels) == 1024:
			raise Exception("Maximum number of tables reached; 1024")

		table_header = ""
		for i in range(len(args)):
			if not isinstance(args[i], str):
				args[i] = str(args[i]) # cast all to string
			if violates_str_rules(args[i]) or violates_name_rules(args[i]):
				raise TypeError("Malformed create; illegal character")
			col = args[i].split(" ", 1)
			if len(col) == 1:
				col.append("str")
			if violates_datatype_rules(col[1]):
				raise TypeError("Malformed create; illegal datatype")
			table_header = table_header + str(col[0]) + " " + str(col[1]) + chr(0xDB)

		mt = None
		for t in self.ad.channels:
			if t.name.lower() == name.lower():
				raise NameError("Table with name already exists")
			if t.name.lower() == self.ad.name.lower():
				mt = t
		new_table = await self.db.create_text_channel(name, category=self.ad, reason="DBDiscord: New Table")
		await mt.send(new_table.id + chr(0xDB) + name + chr(0xDB) + table_header)

	async def drop_table(self, name):
		"""Drops the table on the active database"""
		if self.ad == None:
			raise Exception("No active database")
		if violates_str_rules(name) or violates_name_rules(name) or " " in name:
			raise TypeError("Malformed drop; illegal character")
		if name.lower() == self.ad.name.lower():
			raise NameError("Cannot drop table; illegal operation")
		table = None
		master_table = None
		for t in self.ad.channels:
			if t.name.lower() == name.lower():
				table = t
			if t.name.lower() == self.ad.name():
				master_table = t
		if table == None:
			raise NameError("Table with name does not exist")
		for record in master_table.history(limit=1024).flatten():
			if record.content.lower().split(chr(0xDB)[0] == table.name.lower()):
				await record.delete()
				break
		await table.delete(reason="DBDiscord: Drop Table")

	async def query(self, select="*", against="", where="", use=""):
		"""Queries the active database"""
		if self.ad == None or (self.ad == None and use == ""):
			raise Exception("No active database")
		if not isinstance(select, str) or not isinstance(against, str) or isinstance(use, str) or isinstance(where, str):
			raise TypeError("Malformed query; unexpected datatype, str only")
		if violates_str_rules(select, against, where, use):
			raise TypeError("Malformed query; illegal character")
		if select is "":
			raise NameError("Malformed query; invalid SELECT")
		if against is "":
			raise NameError("Malformed query; invalid FROM (AGAINST)")

		adstore = change_ad_pointer(use)

		headers = None
		table = None
		for t in self.ad.channels:
			if t.name.lower() == self.ad.name.lower():
				mt_records = await t.history(limit=1024).flatten()
				for record in mt_records:
					if self.ad.name.lower() == record.content.split(chr(0xDB))[2]:
						headers = build_table_headers(record.content)
						break
			if t.name.lower() == against.lower():
				table = t
		if table == None:
			raise NameError("No table with name: " + against)

		rawrows = await table.history(limit=1024).flatten()
		full_table = Table(against, headers, rawrows)
		match_table = Table(against, headers)
		clauses = parse_where(where)
		for row in full_table.rows:
			for clause in clauses: # TODO: this will need to be changed to support and/or operators
				if match_where(clause, row):
					match_table.append(row)

		# MORE CODE GOES HERE?

		# cleanup
		if adstore is not None:
			change_ad_pointer(adstore)

		return match_table

	async def insert_into(self, against, use="", **kwargs):
		"""Insert a row into a table"""
		if self.ad == None or (self.ad == None and use == ""):
			raise Exception("No active database")
		if not isinstance(against, str) or not isinstance(use, str):
			raise TypeError("Malformed insert; table or use must be a str")
		if violates_str_rules(against, use) or violates_name_rules(against, use):
			raise TypeError("Malformed insert; illegal character")

		adstore = None
		change_ad_pointer(use)

		table = None
		for t in self.ad.channels:
			if t.name.lower() == self.ad.name.lower():
				mt_records = await t.history(limit=1024).flatten()
				for record in mt_records:
					if self.ad.name.lower() == record.content.split(chr(0xDB))[2]:
						headers = build_table_headers(record.content)
						break
			if t.name.lower() == against.lower():
				table = t
		if table == None:
			raise NameError("No table with name: " + against)
		if len(kwargs) > len(headers):
			raise Exception("Number of columns exceeds table definition")
		if len(await table.history(limit=1024).flatten()) == 1024:
			raise Exception("Maximum number of records reached; 1024")

		new_row = TableRow(headers)
		for field in kwargs:
			valid_field = False
			for i in range(len(headers)):
				if field.lower() == headers[i].column_name.lower():
					new_row.update_record(i, kwargs[field])
					valid_field = True
			if not valid_field:
				raise NameError("No field \"" + field + "\" exists on table")
		await table.send(str(new_row))

		# cleanup
		if adstore is not None:
			change_ad_pointer(adstore)

	async def update(self, against, where="", use="", **kwargs):
		"""Update a row in a table"""
		if self.ad == None or (self.ad == None and use == ""):
			raise Exception("No active database")
		if not isinstance(against, str) or not isinstance(use, str) or not isinstance(where, str):
			raise TypeError("Malformed update; table or use must be a str")
		if violates_str_rules(against, use, where) or violates_name_rules(against, use):
			raise TypeError("Malformed update; illegal character")

		adstore = None
		change_ad_pointer(use)

		table = None
		headers = None
		for t in self.ad.channels:
			if t.name.lower() == self.ad.name.lower():
				mt_records = await t.history(limit=1024).flatten()
				for record in mt_records:
					if self.ad.name.lower() == record.content.split(chr(0xDB))[2]:
						headers = build_table_headers(record.content)
						break
			if t.name.lower() == against.lower():
				table = t
		if table == None:
			raise NameError("No table with name: " + against)
		if len(kwargs) > len(headers):
			raise Exception("Number of columns exceeds table definition")

		# generate row objects from raw
		raw_rows = await table.history(limit=1024).flatten()
		rows = []
		for raw in raw_rows:
			tr = TableRow(headers)
			for data in raw_rows.content.split(chr(0xDB)):
				tr.append_record(data)
			rows.append(tr)
		
		clauses = parse_where(where)
		for i in range(len(rows)):
			for clause in clauses: # TODO: this will need to be changed to support and/or operators
				if match_where(clause, rows[i]):
					for field in kwargs:
						valid_field = False
						for i in range(len(headers)):
							if field.lower() == headers[i].column_name.lower():
								rows[i].update_record(i, kwargs[field])
								valid_field = True
						if not valid_field:
							raise NameError("No field \"" + field + "\" exists on table")
				else:
					rows[i] = None

		for i in range(len(rows)):
			if rows[i] is not None:
				await raw_rows[i].edit(content=str(rows[i]))

		# cleanup
		if adstore is not None:
			change_ad_pointer(adstore)

	async def delete(self, against, where, use=""):
		"""Delete row(s) in a table"""
		if self.ad == None or (self.ad == None and use == ""):
			raise Exception("No active database")
		if not isinstance(against, str) or not isinstance(use, str) or not isinstance(where, str):
			raise TypeError("Malformed delete; table or use must be a str")
		if violates_str_rules(against, use, where) or violates_name_rules(against, use):
			raise TypeError("Malformed delete; illegal character")

		adstore = None
		change_ad_pointer(use)

		table = None
		for t in self.ad.channels:
			if t.name.lower() == self.ad.name.lower():
				mt_records = await t.history(limit=1024).flatten()
				for record in mt_records:
					if self.ad.name.lower() == record.content.split(chr(0xDB))[2]:
						headers = build_table_headers(record.content)
						break
			if t.name.lower() == against.lower():
				table = t
		if table == None:
			raise NameError("No table with name: " + against)

		# generate row objects from raw
		raw_rows = await table.history(limit=1024).flatten()
		rows = []
		for raw in raw_rows:
			tr = TableRow(headers)
			for data in raw_rows.content.split(chr(0xDB)):
				tr.append_record(data)
			rows.append(tr)
		
		clauses = parse_where(where)
		for i in range(len(rows)):
			for clause in clauses: # TODO: this will need to be changed to support and/or operators
				if match_where(clause, rows[i]):
					for field in kwargs:
						valid_field = False
						for i in range(len(headers)):
							if field.lower() == headers[i].column_name.lower():
								valid_field = True
						if not valid_field:
							raise NameError("No field \"" + field + "\" exists on table")
				else:
					rows[i] = None

		for i in range(len(rows)):
			if rows[i] is not None:
				await raw_rows[i].delete()

		# cleanup
		if adstore is not None:
			change_ad_pointer(adstore)
		pass

	# UTILS #

	class Clause:
		"""Wrapper for where clause"""
		class OPTYPE(Enum):
			EQ = 0
			NOT = 1
			LESS = 2
			GREATER = 3
			LESSEQ = 4
			GREATEREQ = 5

		def __init__(self, field, optype, value):
			self.field = field
			self.optype = optype
			self.value = value

	def match_where(self, clause, row):
		"""Checks if a row matches a where clause"""
		if not isinstance(clause, list):
			raise TypeError("where clause must be list of Clause")
		if not isinstance(row, TableRow):
			raise TypeError("row must be an instance of TableRow")
		if not isinstance(clause, Clause):
			raise TypeError("where clause must be list of Clause")
			for i in range(len(row.headers)):
				if clause.field.lower() == row.headers[i].column_name.lower():
					if row.headers[i].datatype == "str":
						if clause.optype == LESS or clause.optype == GREATER or clause.optype == LESSEQ or clause.optype == GREATEREQ:
							raise TypeError("Malformed where clause; cannot preform numerical comparison operation on string")
					if row.headers[i].datatype == "int":
						clause.value = int(clause.value)
					if row.headers[i].datatype == "float":
						clause.value = float(clause.value)
					if row.headers[i].datatype == "date":
						clause.value = datetime.strptime(clause.value)

					if clause.optype == EQ:
						if clause.value == row.records[i].data:
							return True
						return False
					if clause.optype == NOT:
						if clause.value != row.records[i].data:
							return True
						return False
					if clause.optype == LESS:
						if clause.value < row.records[i].data:
							return True
						return False
					if clause.optype == GREATER:
						if clause.value > row.records[i].data:
							return True
						return False
					if clause.optype == LESSEQ:
						if clause.value <= row.records[i].data:
							return True
						return False
					if clause.optype == GREATEREQ:
						if clause.value >= row.records[i].data:
							return True
						return False

	def parse_where(self, clause):
		"""Returns a list of Clause"""
		if not isinstance(clause, str):
			raise TypeError("where clause must be a str")

		sc = re.split(">=|=>", clause, maxsplit=1)
		if len(sc) > 1:
			sc[0] = sc[0].strip()
			sc[1] = sc[1].strip()
			return [Clause(sc[0], OPTYPE.GREATEREQ, sc[1])]
		sc = re.split("<=|=<", clause, maxsplit=1)
		if len(sc) > 1:
			sc[0] = sc[0].strip()
			sc[1] = sc[1].strip()
			return [Clause(sc[0], OPTYPE.LESSEQ, sc[1])]
		sc = clause.split(">", 1)
		if len(sc) > 1:
			sc[0] = sc[0].strip()
			sc[1] = sc[1].strip()
			return [Clause(sc[0], OPTYPE.GREATER, sc[1])]
		sc = clause.split("<", 1)
		if len(sc) > 1:
			sc[0] = sc[0].strip()
			sc[1] = sc[1].strip()
			return [Clause(sc[0], OPTYPE.LESS, sc[1])]
		sc = re.split("!=|=!", clause, maxsplit=1)
		if len(sc) > 1:
			sc[0] = sc[0].strip()
			sc[1] = sc[1].strip()
			return [Clause(sc[0], OPTYPE.NOT, sc[1])]
		sc = clause.split("==", 1)
		if len(sc) > 1:
			sc[0] = sc[0].strip()
			sc[1] = sc[1].strip()
			return [Clause(sc[0], OPTYPE.EQ, sc[1])]
		sc = clause.split("=", 1)
		if len(sc) > 1:
			sc[0] = sc[0].strip()
			sc[1] = sc[1].strip()
			return [Clause(sc[0], OPTYPE.EQ, sc[1])]

		raise Exception("Unable to parse query; malformed where clause")
		pass # TODO: support and/or operations for multiple clauses

	def violates_str_rules(self, *args):
		for checkstr in args:
			if not isinstance(checkstr, str):
				raise TypeError("Argument must be a str")
			if any(illegals in checkstr for illegals in [chr(0xDB)]):
				return True
		return False

	def violates_name_rules(self, *args):
		for checkstr in args:
			if not isinstance(checkstr, str):
				raise TypeError("Argument must be a str")
			if not checkstr.isalnum():
				return True
			for substr in checkstr.split(" "):
				if any(illegals in substr.lower() for illegals in ["select", "from", "against", "where", "use", "create", "drop", "delete", "and", "or", "in"]):
					return True
		return False

	def violates_datatype_rules(self, *args):
		valids = 0
		for checkstr in args:
			if not isinstance(checkstr, str):
				raise TypeError("Argument must be a str")
			if any(legals == checkstr.lower() for legals in ["str", "num", "date", "int", "float"]):
				valids += 1
			if valids == len(args):
				return True
		return False

	def build_table_headers(self, stream):
		arr = stream.split(chr(0xDB))
		headers = []
		for i in range(len(arr)):
			headers.append(TableHeader(arr[i]))
		return headers

	def change_ad_pointer(self, use):
		adstore = None
		if use != "": # change ad pointer for this operation
			for d in self.db.categories:
				if d.name.lower() == use.lower():
					adstore = self.ad
					self.ad = d
					break
			if adstore == None:
				raise NameError("No database with name: " + use)
			return adstore
		return None

class DATATYPE(Enum): # TODO: use this instead of strings
	STR = 0
	NUM = 1
	DATE = 2

class TableHeader:
	def __init__(self, hstr, pk=False):
		self.column_name = hstr.split(" ")[0]
		self.datatype = "str"
		try:
			self.datatype = hstr.split(" ")[1]
		except Exception as e:
			pass
		self.is_primary_key = pk

class Table:
	def __init__(self, table_name, headers, rows=None):
		self.table_name = table_name
		self.headers = headers
		self.rows = []
		if rows is not None:
			for row in rows:
				self.rows.append(TableRow(headers, row))

	def __len__(self):
		return len(self.headers)

	def __str__(self):
		rs = "table_name: " + self.table_name + "\n\n"
		for header in self.headers:
			rs += header.column_name + " " + header.datatype + chr(0xDB)
		for row in self.rows:
			rs += "\n" + str(row)

	def append(self, row):
		if not isinstance(row, TableRow):
			raise TypeError("row must be a TableRow object")
		self.rows.append(row)

class TableRow:
	def __init__(self, headers, records=None):
		self.headers = headers
		self.records = []
		if records is not None:
			records_raw = records.split(chr(0xDB))
			if not len(records_raw) == len(self.headers):
				raise Exception("Number of records do not match expected headers")
			for i in range(len(self.headers)):
				self.records.append(TableRecord(self.headers[i], records_raw[i]))
		else:
			for i in range(len(self.headers)):
				self.records.append(TableRecord(self.headers[i], "NULL"))

	def __len__(self):
		return len(self.records)

	def __str__(self):
		rs = ""
		for record in self.records:
			rs += str(record.data) + chr(0xDB)
		return rs

	def append_record(self, data):
		if len(self.records) == len(self.headers):
			raise Exception("Number of columns exceeds table definition")
		self.records.append(TableRecord(self.headers[len(self.records)], data))

	def update_record(self, index, data):
		if not isinstance(index, int):
			raise TypeError("index must be an int")
		if index > len(self.headers) or index < 0:
			raise IndexError("index out of bounds")
		if self.headers[index].is_primary_key == True:
			raise Exception("Cannot update primary key")
		self.records[index] = TableRecord(headers[index], data.strip())

class TableRecord:
	def __init__(self, datatype, data):
		self.datatype = datatype
		self.data = data
		if datatype == "str":
			return
		elif datatype == "int":
			self.data = int(data)
		elif datatype == "float":
			self.data = float(data)
		elif datatype == "date":
			self.data = datetime(data)
