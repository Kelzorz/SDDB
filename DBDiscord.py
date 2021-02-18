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
			raise Warning("Warning: client does not have administrator permissions on database guild")

	def use(self, name):
		"""Changes the active database"""
		if violates_str_rules(name) or " " in name:
			raise TypeError("Malformed use; illegal character")
		for d in db.categories:
			if d.name.lower() == name.lower():
				ad = d
				return True
		raise NameError("No database with name")

	def create_database(self, name):
		"""Creates a database and sets it to the active database"""
		if violates_str_rules(name) or " " in name:
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
		if violates_str_rules(name) or " " in name:
			raise TypeError("Malformed drop; illegal character")

		# TODO: everything
		pass

	def create_table(self, name, *args):
		"""Creates a table on the active database"""
		if ad = None:
			raise Exception("No active database")
		if violates_str_rules(name) or " " in name:
			raise TypeError("Malformed create; illegal character")
		if name.lower() == "master":
			raise NameError("master is a reserved table name")
		for t in ad.channels:
			if t.name.lower() == name.lower():
				raise NameError("Table with name already exists")

		# TODO: everything
		pass

	def drop_table(self, name):
		"""Drops the table on the active database"""
		if ad = None:
			raise Exception("No active database")
		if violates_str_rules(name) or " " in name:
			raise TypeError("Malformed drop; illegal character")

		# TODO: everything
		pass

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

		table = None
		for t in ad.channels:
			if t.name.lower() == against.lower():
				table = t
				break
		if table == None:
			raise NameError("No table with name: " + against)

		# MORE CODE GOES HERE

		# cleanup
		if adstore is not None: # restore ad pointer
			ad = adstore

		# TODO: return the results
		pass

	def violates_str_rules(self, *args):
		for checkstr in args:
			if not isinstance(checkstr, str):
				raise TypeError("Argument must be a str")
			if any(illegals in checkstr for illegals in [char(0xDB)]):
				return True
		return False