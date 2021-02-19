import discord
from datetime import datetime

# DBDiscord uses a Discord guild as a ghetto database and supports simple DB operations - create, select, update, delete.
# The █ character (0xDB) is used as a global delimiter, and is not allowed under any circumstances.
# A database is identified as a channel category in the Discord guild.
# - Databases can have multiple tables
# A table is identified as a text channel in the Discord guild.
# - Tables have columns as defined in the text channel with the same name as the DB delimitated by the 0xDB character.
# A row is identified as a text message in a text channel in the Discord guild.
# - Rows columns are delimitated by the 0xDB character. 
# from is a Python keyword and cannot be used as a variable, against is used instead.

class DBDiscord:
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
		for d in db.categories:
			if d.name.lower() == name.lower():
				ad = d
				return True
		raise NameError("No database with name")

	def create_database(self, name):
		"""Creates a database and sets it to the active database"""
		if violates_str_rules(name) or violates_name_rules(name) or " " in name:
			raise TypeError("Malformed create; illegal character")
		for d in db.categories:
			if d.name.lower() == name.lower():
				raise NameError("Database with name already exists")
		overwrites = {
		    guild.default_role: discord.PermissionOverwrite(read_messages=False),
		    guild.me: discord.PermissionOverwrite(read_messages=True)
		    }
		self.ad = await db.create_category(name, overwrites=overwrites ,reason="DBDiscord: New Database")
		await db.create_text_channel(name, category=ad, reason="DBDiscord: New Database")
		return

	def drop_database(self, name):
		"""Drops the database"""
		if violates_str_rules(name) or violates_name_rules(name) " " in name:
			raise TypeError("Malformed drop; illegal character")
		for d in db.categories:
			if d.name.lower() == name.lower():
				for t in d.channels:
					await t.delete(reason="DBDiscord: Drop Database")
				await d.delete(reason="DBDiscord: Drop Database")
				return
		raise NameError("Database with name does not exist")

	def create_table(self, name, *args):
		"""Creates a table on the active database"""
		if ad = None:
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
		for t in ad.channels:
			if t.name.lower() == name.lower():
				raise NameError("Table with name already exists")
			if t.name.lower() == ad.name.lower():
				mt = t
		new_table = await db.create_text_channel(name, category=ad, reason="DBDiscord: New Table")
		await mt.send(new_table.id + chr(0xDB) + name + chr(0xDB) + table_header)

	def drop_table(self, name):
		"""Drops the table on the active database"""
		if ad = None:
			raise Exception("No active database")
		if violates_str_rules(name) or violates_name_rules(name) or " " in name:
			raise TypeError("Malformed drop; illegal character")
		if name.lower() == ad.name.lower():
			raise NameError("Cannot drop table; illegal operation")
		for t in ad.channels:
			if t.name.lower() == name.lower():
				t.delete(reason="DBDiscord: Drop Table")
				return
		raise NameError("Table with name does not exist")

	def query(self, select="*", against="", where="", use=""):
		"""Queries the active database"""
		if ad = None:
			raise Exception("No active database")
		if not isinstance(select, str) or not isinstance(against, str) or isinstance(where, str):
			raise TypeError("Malformed query; unexpected datatype, str only")
		if violates_str_rules(select, against, where, use):
			raise TypeError("Malformed query; illegal character")
		if select is "":
			raise NameError("Malformed query; invalid SELECT")
		if against is "":
			raise NameError("Malformed query; invalid FROM (AGAINST)")

		adstore = None
		if use is not "": # change ad pointer for this query
			for d in db.categories:
				if d.name.lower() == d.lower():
					adstore = ad
					ad = d
					break
			if adstore == None:
				raise NameError("No database with name: " + use)

		headers = None
		table = None
		for t in ad.channels:
			if t.name.lower() == ad.name.lower():
				mt_records = await t.history(limit=1024).flatten()
				for record in mt_records:
					if ad.name.lower() == record.content.split(chr(0xDB))[2]:
						headers = build_table_headers(record.content)
						break
			if t.name.lower() == against.lower():
				table = t
		if table == None:
			raise NameError("No table with name: " + against)

		rawrows = await table.history(limit=1024).flatten()

		# MORE CODE GOES HERE

		# cleanup
		if adstore is not None: # restore ad pointer
			ad = adstore

		# TODO: return the results
		pass

	def insert_into(self, table, use="", *args):
		"""Insert a row into a table"""
		pass

	def upsert_into(self, table use= "", *args):
		"""Upsert a row into a table"""
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
			if any(illegals in checkstr.lower() for illegals in ["select", "from", "where", "use", "create", "drop"])
		return False

	def violates_datatype_rules(self, *args):
		valids = 0
		for checkstr in args:
			if not isinstance(checkstr, str):
				raise TypeError("Argument must be a str")
			if any(legals == checkstr.lower() for legals in ["int", "str", "float", "date"]):
				valids += 1
			if valids == len(args):
				return True
		return False

	def build_table_headers(self, stream):
		arr = stream.split(chr(0xDB))
		headers = []
		for i in range(len(arr)):
			if i == 0:
				headers.append(TableHeader(arr[i], pk=True))
			else:
				headers.append(TableHeader(arr[i]))
		return headers

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
	def __init__(self, table_name, header, rows):
		self.table_name = table_name
		self.rows = []
		self.header = header
		for i in range(len(headers)):
			self.rows.append(TableRow(header[i], rows[i]))

class TableRow:
	def __init__(self, header, records):
		self.header = header
		self.row = []
		record_raw = records.split(chr(0xDB))
		for record in record_raw:
			self.row.append(TableRecord(self.header.datatype, record))

class TableRecord:
	def __init__(self, datatype, data):
		self.datatype = datatype
		self.data = data