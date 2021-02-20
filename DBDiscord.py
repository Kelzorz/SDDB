import discord
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
		elif isinstance(database_guild, int)
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

	def create_database(self, name):
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

	def drop_database(self, name):
		"""Drops the database"""
		if violates_str_rules(name) or violates_name_rules(name) " " in name:
			raise TypeError("Malformed drop; illegal character")
		for d in self.db.categories:
			if d.name.lower() == name.lower():
				for t in d.channels:
					await t.delete(reason="DBDiscord: Drop Database")
				await d.delete(reason="DBDiscord: Drop Database")
				return
		raise NameError("Database with name does not exist")

	def create_table(self, name, *args):
		"""Creates a table on the active database"""
		if self.ad == None:
			raise Exception("No active database")
		if violates_str_rules(name) or violates_name_rules(name) or " " in name:
			raise TypeError("Malformed create; illegal character")
		if name.lower() == "master":
			raise NameError("master is a reserved table name")

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

	def drop_table(self, name):
		"""Drops the table on the active database"""
		if self.ad == None:
			raise Exception("No active database")
		if violates_str_rules(name) or violates_name_rules(name) or " " in name:
			raise TypeError("Malformed drop; illegal character")
		if name.lower() == self.ad.name.lower():
			raise NameError("Cannot drop table; illegal operation")
		for t in self.ad.channels:
			if t.name.lower() == name.lower():
				t.delete(reason="DBDiscord: Drop Table")
				return
		raise NameError("Table with name does not exist")

	def query(self, select="*", against="", where="", use=""):
		"""Queries the active database"""
		if self.ad == None or (self.ad == None and use == ""):
			raise Exception("No active database")
		if not isinstance(select, str) or not isinstance(against, str) or isinstance(where, str):
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
		for row in full_table.rows:
			pass # TODO: match the where clause and append to match_table


		# MORE CODE GOES HERE

		# cleanup
		if adstore is not None:
			change_ad_pointer(adstore)

		# TODO: return match table
		pass

	def insert_into(self, against, **kwargs, use=""):
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

	def update(self, against, **kwargs, where="", use=""):
		"""Update a row in a table"""
		if self.ad == None or (self.ad == None and use == ""):
			raise Exception("No active database")
		if not isinstance(against, str) or not isinstance(use, str):
			raise TypeError("Malformed update; table or use must be a str")
		if violates_str_rules(against, use) or violates_name_rules(against, use):
			raise TypeError("Malformed update; illegal character")

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

		all_rows = await table.history(limit=1024).flatten()
		matching_rows = []
		for row in all_rows:
			pass # TODO: match where clause to rows	

		# new_row = TableRow(headers)
		# for field in kwargs:
		# 	valid_field = False
		# 	for i in range(len(headers)):
		# 		if field.lower() == headers[i].column_name.lower():
		# 			new_row.update_record(i, kwargs[field])
		# 			valid_field = True
		# 	if not valid_field:
		# 		raise NameError("No field \"" + field + "\" exists on table")
		pass

	def delete(self, against, where):
		"""Delete row(s) in a table"""
		pass

	# UTILS #

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
				if any(illegals in substr.lower() for illegals in ["select", "from", "where", "use", "create", "drop", "delete", "in"]):
				return True
		return False

	def violates_datatype_rules(self, *args):
		valids = 0
		for checkstr in args:
			if not isinstance(checkstr, str):
				raise TypeError("Argument must be a str")
			if any(legals == checkstr.lower() for legals in ["str", "int", "float", "date"]):
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

class TableHeader:
	def __init__(self, hstr, pk=False):
		self.column_name = hstr.split(" ")[0]
		self.datatype = "str"
		try:
			self.datatype  hstr.split(" ")[1]
		except Exception as e:
			pass
		self.is_primary_key = pk

class Table:
	def __init__(self, table_name, headers, rows=None):
		self.table_name = table_name
		self.headers = headers
		self.rows = []
		if rows is not None
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
			rs += str(record.data) += chr(0xDB)
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
		self.records[index] = TableRecord(headers[index], data)

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
