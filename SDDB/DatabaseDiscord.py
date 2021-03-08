import discord
import re
from enum import Enum
from datetime import datetime

# SDDB uses a Discord guild as a ghetto database and supports simple DB operations - create, select, update, delete.
# The │ character ASCII(0x2502) is used as a global delimiter, and is not allowed under any circumstances.
# A database is identified as a channel category in the Discord guild.
# - Databases can have multiple tables
# - Each Database has a master table that maps fields for each table in the database
# A table is identified as a text channel in the Discord guild.
# - Tables have columns as defined by it's record in the master table delimitated by the 0x2502 character.
# A row is identified as a text message in a text channel in the Discord guild.
# - Row columns are delimitated by the 0x2502 character.
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
			self.db = self.d.get_guild(database_guild)
			if self.db is None:
				raise Exception("guild does not exist: " + str(database_guild))
		else:
			raise TypeError("database_guild must be an int or guild object")
		if not self.db.me.guild_permissions.administrator:
			raise Warning("Warning: client does not have administrator permissions on database guild, CREATE and DROP operations may not be successful")

	def use(self, name):
		"""Changes the active database"""
		if self.violates_str_rules(name) or self.violates_name_rules(name) or " " in name:
			raise TypeError("Malformed use; illegal character")
		for d in self.db.categories:
			if d.name.lower() == name.lower():
				self.ad = d
				return True
		raise NameError("No database with name")

	async def create_database(self, name):
		"""Creates a database and sets it to the active database"""
		if self.violates_str_rules(name) or self.violates_name_rules(name) or " " in name:
			raise TypeError("Malformed create; illegal character")
		for d in self.db.categories:
			if d.name.lower() == name.lower():
				raise NameError("Database with name already exists")
		overwrites = {
		    self.db.default_role: discord.PermissionOverwrite(read_messages=False),
		    self.db.me: discord.PermissionOverwrite(read_messages=True)
		    }
		self.ad = await self.db.create_category(name, overwrites=overwrites ,reason="SDDB: New Database")
		await self.db.create_text_channel(name, category=self.ad, reason="SDDB: New Database")
		return True

	async def drop_database(self, name):
		"""Drops the database"""
		if self.violates_str_rules(name) or self.violates_name_rules(name) or " " in name:
			raise TypeError("Malformed drop; illegal character")
		for d in self.db.categories:
			if d.name.lower() == name.lower():
				for t in d.channels:
					await t.delete(reason="SDDB: Drop Database")
				await d.delete(reason="SDDB: Drop Database")
				self.ad = None
				return True
		raise NameError("Database with name does not exist")

	async def alter_database(self, name):
		"""Alters the database"""
		if self.violates_str_rules(name) or self.violates_name_rules(name) or " " in name:
			raise TypeError("Malformed alter; illegal character")
		if self.ad == None or (self.ad == None and use == ""):
			raise Exception("No active database")

		for d in self.db.categories:
			if d.name.lower() == name.lower():
				raise NameError("Database with name already exists")
		for d in self.db.categories:
			if d.name.lower() == self.ad.name.lower():
				master_table = None
				for t in self.ad.channels:
					if t.name.lower() == name.lower():
						raise NameError("Table exists with name, rename offending table and try again")
					if t.name.lower() == self.ad.name.lower():
						master_table = t
				await master_table.edit(name=name, reason="SDDB: Alter Database")
				await d.edit(name=name, reason="SDDB: Alter Database")
				self.ad = d # update the database pointer as it may have changed
				return True

	async def create_table(self, name, **kwargs):
		"""Creates a table on the active database"""
		if self.ad == None:
			raise Exception("No active database")
		if self.violates_str_rules(name) or self.violates_name_rules(name) or " " in name:
			raise TypeError("Malformed create; illegal character")
		if name.lower() == "master":
			raise NameError("master is a reserved table name")
		if self.ad.name.lower() == name.lower():
				raise NameError("Table cannot have same name as parent database")
		if len(self.ad.channels) == 1024:
			raise Exception("Maximum number of tables reached; 1024")

		table_header = ""

		for field in kwargs:
			if self.violates_str_rules(field) or self.violates_name_rules(field) or field == "" or " " in field:
				raise TypeError("Malformed create; illegal character")
			if self.violates_datatype_rules(kwargs[field]):
				raise TypeError("Malformed create; illegal datatype")
			table_header = table_header + str(field) + " " + str(kwargs[field]) + chr(0x2502)

		mt = None
		for t in self.ad.channels:
			if t.name.lower() == name.lower():
				raise NameError("Table with name already exists")
			if t.name.lower() == self.ad.name.lower():
				mt = t
		new_table = await self.db.create_text_channel(name, category=self.ad, reason="SDDB: New Table")
		await mt.send(name + chr(0x2502) + table_header)
		return True

	async def drop_table(self, name):
		"""Drops the table on the active database"""
		if self.ad == None:
			raise Exception("No active database")
		if self.violates_str_rules(name) or self.violates_name_rules(name) or " " in name:
			raise TypeError("Malformed drop; illegal character")
		if name.lower() == self.ad.name.lower():
			raise NameError("Cannot drop table; illegal operation")
		table = None
		master_table = None
		for t in self.ad.channels:
			if t.name.lower() == name.lower():
				table = t
			if t.name.lower() == self.ad.name.lower():
				master_table = t
		if table == None:
			raise NameError("Table with name does not exist")
		for record in await master_table.history(limit=1024).flatten():
			if record.content.split(chr(0x2502))[0].lower() == table.name.lower():
				await record.delete()
				break
		await table.delete(reason="SDDB: Drop Table")
		return True

	async def alter_table(self, name, add="", drop="", modify="", rename=""):
		"""Alters a table on the active database"""
		if self.ad == None:
			raise Exception("No active database")
		if self.violates_str_rules(name, drop, rename) or self.violates_name_rules(name):
			raise NameError("Malformed alter; illegal character")
		if name.lower() == self.ad.name.lower():
			raise NameError("Cannot alter master table")

		successful = False

		headers = None
		table = None
		header_row = None
		for t in self.ad.channels:
			if t.name.lower() == self.ad.name.lower():
				mt_records = await t.history(limit=1024).flatten()
				for record in mt_records:
					if name.lower() == record.content.split(chr(0x2502))[0]:
						headers = self.build_table_headers(record.content)
						header_row = record
						break
			if t.name.lower() == name.lower():
				table = t
		if table == None:
			raise NameError("No table with name: " + name)

		# add
		if add != "":
			new_col = add.split(" ", 1)
			if self.violates_name_rules(new_col[0]):
				raise NameError("Malformed alter; illegal character")
			if self.violates_datatype_rules(new_col[1]):
				raise TypeError("Malformed alter; illegal datatype")
			await header_row.edit(content=header_row.content + new_col[0] + " " + new_col[1] + chr(0x2502))
			for row in await table.history(limit=1024).flatten():
				await row.edit(content=row.content + "" + chr(0x2502))
			successful = True

		# drop
		if drop != "":
			if self.violates_name_rules(drop):
				raise NameError("Malformed alter; illegal character")
			column_exists = False
			for i in range(len(headers)):
				if headers[i].column_name.lower() == drop.lower():
					column_exists = True
					fractured_header = header_row.content.split(chr(0x2502))
					rebuilt_header = ""
					for x in range(len(fractured_header)):
						if x-1 != i:
							rebuilt_header += fractured_header[x] + chr(0x2502)
					await header_row.edit(content=rebuilt_header[:-1])
					for row in await table.history(limit=1024).flatten():
						fractured_row = row.content.split(chr(0x2502))
						rebuilt_row = ""
						for x in range(len(fractured_row)):
							if x != i:
								rebuilt_row += fractured_row[x] + chr(0x2502)
						await row.edit(content=rebuilt_row[:-1])
					successful = True
			if not column_exists:
				raise NameError("No column with name " + drop)

		# modify
		if modify != "":
			if self.violates_name_rules(modify):
				raise NameError("Malformed alter; illegal character")
			mod_col = modify.split(" ", 2)
			if self.violates_name_rules(mod_col[1]):
				raise NameError("Malformed alter; illegal character")
			if self.violates_datatype_rules(mod_col[2]):
				raise TypeError("Malformed alter; illegal datatype")
			header_exits = False
			for header in headers:
				if header.column_name.lower() == mod_col[0].lower():
					header_exits = True
					break
			if header_exits:
				fractured_header = header_row.content.split(mod_col[0], 1)
				fractured_header[1] = chr(0x2502) + fractured_header[1].split(chr(0x2502), 1)[1]
				await header_row.edit(content=fractured_header[0] + mod_col[1] + " " + mod_col[2] + fractured_header[1])
				successful = True
			else:
				raise NameError("No column with name " + mod_col[0])

		# rename
		if rename != "":
			if self.ad.name.lower() == rename.lower():
				raise NameError("Table cannot have same name as parent database")
			for t in self.ad.channels:
				if t.name.lower() == rename.lower():
					raise NameError("Table with name already exists")
			new_headers = ""
			for header in header_row.content.split(chr(0x2502)):
				if header.lower() == name.lower():
					header = rename
				new_headers += header + chr(0x2502)
			await header_row.edit(content=new_headers[:-1])
			await table.edit(name=rename, reason="SDDB: Alter Table")
			successful = True

		if successful:
			return True
		return False

	async def query(self, select="*", against="", where="", use=""):
		"""Queries the active database"""
		if self.ad == None or (self.ad == None and use == ""):
			raise Exception("No active database")
		if not isinstance(select, str) or not isinstance(against, str) or not isinstance(use, str) or not isinstance(where, str):
			raise TypeError("Malformed query; unexpected datatype, str only")
		if self.violates_str_rules(select, against, where, use):
			raise TypeError("Malformed query; illegal character")
		if select is "":
			raise NameError("Malformed query; invalid SELECT")
		if against is "":
			raise NameError("Malformed query; invalid AGAINST (FROM)")

		adstore = self.change_ad_pointer(use)

		headers = None
		table = None
		for t in self.ad.channels:
			if t.name.lower() == self.ad.name.lower():
				mt_records = await t.history(limit=1024).flatten()
				for record in mt_records:
					if against.lower() == record.content.split(chr(0x2502))[0]:
						headers = self.build_table_headers(record.content)
						break
			if t.name.lower() == against.lower():
				table = t
		if table == None:
			if adstore is not None:
				self.change_ad_pointer(adstore)
			raise NameError("No table with name: " + against)

		# validate select
		selected_cols = []
		if select != "*":
			selectables = select.split(",")
			for i in range(len(selectables)):
				selectables[i] = selectables[i].strip()
				selectables[i] = selectables[i].lower()
			for i in range(len(headers)):
				if headers[i].column_name.lower() in selectables:
					selected_cols.append(i)
					selectables.remove(headers[i].column_name.lower())
			if len(selectables) > 0:
				invalid_selected = ""
				for s in selectables:
					invalid_selected += " " + s
				if adstore is not None:
					self.change_ad_pointer(adstore)
				raise Exception("Malformed query; selected columns not in table headers," + invalid_selected)

		rawrows = await table.history(limit=1024).flatten()
		full_table = Table(against, headers, rawrows)
		match_table = Table(against, headers)
		clauses = self.parse_where(where)
		for row in full_table.rows:
			for clause in clauses: # TODO: this will need to be changed to support and/or operators
				if self.match_where(clause, row):
					match_table.append(row)

		# build the selected table
		if len(selected_cols) != 0:
			selected_headers = []
			selected_rows = []
			for i in selected_cols:
				selected_headers.append(match_table.headers[i])
			for row in match_table.rows:
				selected_records = []
				for i in range(len(row.records)):
					if i in selected_cols:
						selected_records.append(row.records[i])
				selected_rows.append(TableRow(selected_headers, table_records=selected_records))
			match_table = Table(against, selected_headers, table_rows=selected_rows)

		# cleanup
		if adstore is not None:
			self.change_ad_pointer(adstore)

		return match_table

	async def insert_into(self, against, use="", **kwargs):
		"""Insert a row into a table"""
		if self.ad == None or (self.ad == None and use == ""):
			raise Exception("No active database")
		if not isinstance(against, str) or not isinstance(use, str):
			raise TypeError("Malformed insert; table or use must be a str")
		if self.violates_str_rules(against) or self.violates_name_rules(against):
			raise TypeError("Malformed insert; illegal character")

		adstore = self.change_ad_pointer(use)

		table = None
		headers = None
		for t in self.ad.channels:
			if t.name.lower() == self.ad.name.lower():
				mt_records = await t.history(limit=1024).flatten()
				for record in mt_records:
					if against.lower() == record.content.split(chr(0x2502))[0].lower():
						headers = self.build_table_headers(record.content)
						break
			if t.name.lower() == against.lower():
				table = t
		if table == None:
			if adstore is not None:
				self.change_ad_pointer(adstore)
			raise NameError("No table with name: " + against)
		if len(kwargs) > len(headers):
			if adstore is not None:
				self.change_ad_pointer(adstore)
			raise Exception("Number of columns exceeds table definition")
		if len(await table.history(limit=1024).flatten()) == 1024:
			if adstore is not None:
				self.change_ad_pointer(adstore)
			raise Exception("Maximum number of records reached; 1024")

		new_row = TableRow(headers)
		for field in kwargs:
			valid_field = False
			for i in range(len(headers)):
				if field.lower() == headers[i].column_name.lower():
					new_row.update_record(i, kwargs[field])
					valid_field = True
			if not valid_field:
				if adstore is not None:
					self.change_ad_pointer(adstore)
				raise NameError("No field \"" + field + "\" exists on table")
		await table.send(str(new_row))

		# cleanup
		if adstore is not None:
			self.change_ad_pointer(adstore)

		return True

	async def update(self, against, where="", use="", **kwargs):
		"""Update a row in a table"""
		if self.ad == None or (self.ad == None and use == ""):
			raise Exception("No active database")
		if not isinstance(against, str) or not isinstance(use, str) or not isinstance(where, str):
			raise TypeError("Malformed update; table or use must be a str")
		if self.violates_str_rules(against, use, where) or self.violates_name_rules(against):
			raise TypeError("Malformed update; illegal character")

		adstore = self.change_ad_pointer(use)

		table = None
		headers = None
		for t in self.ad.channels:
			if t.name.lower() == self.ad.name.lower():
				mt_records = await t.history(limit=1024).flatten()
				for record in mt_records:
					if against.lower() == record.content.split(chr(0x2502))[0]:
						headers = self.build_table_headers(record.content)
						break
			if t.name.lower() == against.lower():
				table = t
		if table == None:
			if adstore is not None:
				self.change_ad_pointer(adstore)
			raise NameError("No table with name: " + against)
		if len(kwargs) > len(headers):
			if adstore is not None:
				self.change_ad_pointer(adstore)
			raise Exception("Number of columns exceeds table definition")

		# generate row objects from raw
		raw_rows = await table.history(limit=1024).flatten()
		rows = []
		for raw in raw_rows:
			tr = TableRow(headers)
			split_rows = raw.content.split(chr(0x2502))
			del split_rows[len(split_rows)-1]
			for i in range(len(split_rows)):
				tr.update_record(i, split_rows[i])
			rows.append(tr)
		
		clauses = self.parse_where(where)
		for i in range(len(rows)):
			for clause in clauses: # TODO: this will need to be changed to support and/or operators
				if self.match_where(clause, rows[i]):
					for field in kwargs:
						valid_field = False
						for x in range(len(headers)):
							if field.lower() == headers[x].column_name.lower():
								rows[i].update_record(x, kwargs[field])
								valid_field = True
						if not valid_field:
							if adstore is not None:
								self.change_ad_pointer(adstore)
							raise NameError("No field '" + field + "'' exists on table")
				else:
					rows[i] = None

		for i in range(len(rows)):
			if rows[i] is not None:
				#print(str(rows[i])) #
				await raw_rows[i].edit(content=str(rows[i]))

		# cleanup
		if adstore is not None:
			self.change_ad_pointer(adstore)

		return True

	async def delete(self, against, where="", use=""):
		"""Delete row(s) in a table"""
		if self.ad == None or (self.ad == None and use == ""):
			raise Exception("No active database")
		if not isinstance(against, str) or not isinstance(use, str) or not isinstance(where, str):
			raise TypeError("Malformed delete; table or use must be a str")
		if self.violates_str_rules(against, use, where) or self.violates_name_rules(against):
			raise TypeError("Malformed delete; illegal character")

		adstore = self.change_ad_pointer(use)

		table = None
		headers = None
		for t in self.ad.channels:
			if t.name.lower() == self.ad.name.lower():
				mt_records = await t.history(limit=1024).flatten()
				for record in mt_records:
					if against.lower() == record.content.split(chr(0x2502))[0]:
						headers = self.build_table_headers(record.content)
						break
			if t.name.lower() == against.lower():
				table = t
		if table == None:
			if adstore is not None:
				self.change_ad_pointer(adstore)
			raise NameError("No table with name: " + against)

		# generate row objects from raw
		raw_rows = await table.history(limit=1024).flatten()
		rows = []
		for raw in raw_rows:
			tr = TableRow(headers)
			split_rows = raw.content.split(chr(0x2502))
			del split_rows[len(split_rows)-1]
			for i in range(len(split_rows)):
				tr.update_record(i, split_rows[i])
			rows.append(tr)
		
		clauses = self.parse_where(where)
		for i in range(len(rows)):
			for clause in clauses: # TODO: this will need to be changed to support and/or operators
				if self.match_where(clause, rows[i]):
					pass # match found, leave for deletion
				else:
					rows[i] = None

		successful = False
		for i in range(len(rows)):
			if rows[i] is not None:
				await raw_rows[i].delete()
				successful = True

		# cleanup
		if adstore is not None:
			self.change_ad_pointer(adstore)

		if successful:
			return True
		return False

	# UTILS #

	def match_where(self, clause, row):
		"""Checks if a row matches a where clause"""
		if not isinstance(clause, Clause):
			raise TypeError("where clause must be an instance of Clause")
		if not isinstance(row, TableRow):
			raise TypeError("row must be an instance of TableRow")
		if clause.field is None:
			return True # always match an empty clause
		for i in range(len(row.headers)):
			if clause.field.lower() == row.headers[i].column_name.lower():
				if row.headers[i].datatype == "str":
					if clause.optype == OPTYPE.LESS or clause.optype == OPTYPE.GREATER or clause.optype == OPTYPE.LESSEQ or clause.optype == OPTYPE.GREATEREQ:
						raise TypeError("Malformed where clause; cannot preform numerical comparison operation on string")
				if row.headers[i].datatype == "int":
					clause.value = int(clause.value)
					row.records[i].data = int(row.records[i].data)
				if row.headers[i].datatype == "float":
					clause.value = float(clause.value)
					row.records[i].data = float(row.records[i].data)
				if row.headers[i].datatype == "date":
					clause.value = datetime.strptime(clause.value)
					row.records[i].data = datetime.strptime(row.records[i].data)

				if clause.optype == OPTYPE.EQ:
					if row.records[i].data == clause.value:
						return True
					return False
				if clause.optype == OPTYPE.NOT:
					if row.records[i].data != clause.value:
						return True
					return False
				if clause.optype == OPTYPE.LESS:
					if row.records[i].data < clause.value:
						return True
					return False
				if clause.optype == OPTYPE.GREATER:
					if row.records[i].data > clause.value:
						return True
					return False
				if clause.optype == OPTYPE.LESSEQ:
					if row.records[i].data <= clause.value:
						return True
					return False
				if clause.optype == OPTYPE.GREATEREQ:
					if row.records[i].data >= rclause.value:
						return True
					return False

	def parse_where(self, clause):
		"""Returns a list of Clause"""
		if not isinstance(clause, str):
			raise TypeError("where clause must be a str")

		if clause == "":
			return [Clause(None, None, None)]

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
				raise TypeError("Malformed statement; argument not a string")
			if any(illegals in checkstr for illegals in [chr(0x2502)]):
				return True
		return False

	def violates_name_rules(self, *args):
		for checkstr in args:
			if not isinstance(checkstr, str):
				raise TypeError("Malformed statement; argument not a string")
			for substr in checkstr.split(" "):
				if not substr.isalnum():
					return True
				if any(illegals == substr.lower() for illegals in ["select", "from", "against", "where", "use", "create", "alter", "drop", "delete", "and", "or", "in"]):
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
			return False
		return True

	def build_table_headers(self, stream):
		arr = stream.split(chr(0x2502))
		headers = []
		for i in range(len(arr)):
			if i != 0:
				headers.append(TableHeader(arr[i]))
		del headers[len(headers)-1] # Excess header
		return headers

	def change_ad_pointer(self, use):
		adstore = None
		if use != "": # change ad pointer for this operation
			for d in self.db.categories:
				if d.name.lower() == use.lower():
					adstore = self.ad.name
					self.ad = d
					break
			if adstore == None:
				raise NameError("No database with name: " + use)
			return adstore
		return None

class DATATYPE(Enum): # TODO: use this instead of strings
	STR = 0
	INT = 1
	FLOAT = 2
	DATE = 3

class OPTYPE(Enum):
	EQ = 0
	NOT = 1
	LESS = 2
	GREATER = 3
	LESSEQ = 4
	GREATEREQ = 5

class Clause:
	"""Wrapper for where clause"""
	def __init__(self, field, optype, value):
		self.field = field
		self.optype = optype
		self.value = value

class TableHeader:
	def __init__(self, hstr, pk=False):
		self.column_name = hstr.split(" ")[0]
		self.datatype = "str"
		try:
			self.datatype = hstr.split(" ")[1]
		except Exception as e:
			pass
		self.is_primary_key = pk

	def __str__():
		return self.column_name + " " + self.datatype

class Table:
	def __init__(self, table_name, headers, rows=None, table_rows=None):
		self.table_name = table_name
		self.headers = headers
		self.rows = []
		if rows is not None:
			for row in rows:
				self.rows.append(TableRow(headers, row))
		elif table_rows is not None:
			for row in table_rows:
				self.rows.append(row)

	def __len__(self):
		return len(self.headers)

	def __str__(self):
		rs = "table_name: " + self.table_name + "\n"
		for header in self.headers:
			rs += header.column_name + " " + header.datatype + chr(0x2502)
		for row in self.rows:
			rs += "\n" + str(row)
		return rs

	def append(self, row):
		if not isinstance(row, TableRow):
			raise TypeError("row must be a TableRow object")
		self.rows.append(row)

class TableRow:
	def __init__(self, headers, records=None, table_records=None):
		self.headers = headers
		self.records = []
		if records is not None:
			records_raw = records.content.split(chr(0x2502))
			del records_raw[len(records_raw)-1]
			if not len(records_raw) == len(self.headers):
				raise Exception("Number of records do not match expected headers")
			for i in range(len(self.headers)):
				self.records.append(TableRecord(self.headers[i], records_raw[i]))
		elif table_records is not None:
			if not len(table_records) == len(self.headers):
				raise Exception("Number of records do not match expected headers")
			for i in range(len(self.headers)):
				self.records.append(table_records[i])
		else:
			for i in range(len(self.headers)):
				self.records.append(TableRecord(self.headers[i], ""))

	def __len__(self):
		return len(self.records)

	def __str__(self):
		rs = ""
		for record in self.records:
			rs += str(record.data) + chr(0x2502)
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
		self.records[index] = TableRecord(self.headers[index], data.strip())

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
			self.data = datetime.strptime(data)

	def __str__():
		return str(self.data)
