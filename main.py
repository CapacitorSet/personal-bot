import asyncio
import os
import sys
import time
from getpass import getpass
from subprocess import call

from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.network import ConnectionTcpAbridged
from telethon.utils import get_display_name

# Create a global variable to hold the loop we will be using
loop = asyncio.get_event_loop()

def get_env(name, message, cast=str):
	"""Helper to get environment variables interactively"""
	if name in os.environ:
		return os.environ[name]
	while True:
		value = input(message)
		try:
			return cast(value)
		except ValueError as e:
			print(e, file=sys.stderr)
			time.sleep(1)


class InteractiveTelegramClient(TelegramClient):
	"""Full featured Telegram client, meant to be used on an interactive
	   session to see what Telethon is capable off -

	   This client allows the user to perform some basic interaction with
	   Telegram through Telethon, such as listing dialogs (open chats),
	   talking to people, downloading media, and receiving updates.
	"""

	def __init__(self, session_user_id, api_id, api_hash,
				 proxy=None):
		"""
		Initializes the InteractiveTelegramClient.
		:param session_user_id: Name of the *.session file.
		:param api_id: Telegram's api_id acquired through my.telegram.org.
		:param api_hash: Telegram's api_hash.
		:param proxy: Optional proxy tuple/dictionary.
		"""
		# The first step is to initialize the TelegramClient, as we are
		# subclassing it, we need to call super().__init__(). On a more
		# normal case you would want 'client = TelegramClient(...)'
		super().__init__(
			# These parameters should be passed always, session name and API
			session_user_id, api_id, api_hash,

			# You can optionally change the connection mode by passing a
			# type or an instance of it. This changes how the sent packets
			# look (low-level concept you normally shouldn't worry about).
			# Default is ConnectionTcpFull, smallest is ConnectionTcpAbridged.
			connection=ConnectionTcpAbridged,

			# If you're using a proxy, set it here.
			proxy=proxy
		)

		# Store {message.id: message} map here so that we can download
		# media known the message ID, for every message having media.
		self.found_media = {}

		# Calling .connect() may raise a connection error False, so you need
		# to except those before continuing. Otherwise you may want to retry
		# as done here.
		print('Connecting to Telegram servers...')
		try:
			loop.run_until_complete(self.connect())
		except ConnectionError:
			print('Initial connection failed. Retrying...')
			loop.run_until_complete(self.connect())

		# If the user hasn't called .sign_in() or .sign_up() yet, they won't
		# be authorized. The first thing you must do is authorize. Calling
		# .sign_in() should only be done once as the information is saved on
		# the *.session file so you don't need to enter the code every time.
		if not loop.run_until_complete(self.is_user_authorized()):
			print('First run. Sending code request...')
			user_phone = input('Enter your phone: ')
			loop.run_until_complete(self.sign_in(user_phone))

			self_user = None
			while self_user is None:
				code = input('Enter the code you just received: ')
				try:
					self_user =\
						loop.run_until_complete(self.sign_in(code=code))

				# Two-step verification may be enabled, and .sign_in will
				# raise this error. If that's the case ask for the password.
				# Note that getpass() may not work on PyCharm due to a bug,
				# if that's the case simply change it for input().
				except SessionPasswordNeededError:
					pw = getpass('Two step verification is enabled. '
								 'Please enter your password: ')

					self_user =\
						loop.run_until_complete(self.sign_in(password=pw))

		@self.on(events.NewMessage(pattern='\.fry ?.*'))
		async def handler(event):
			msg_id = event.reply_to_msg_id
			if (event.reply_to_msg_id is None):
				await event.reply("Rispondi a un'immagine per friggerla.")
				return
			print("Refreshing history...")
			await self.refreshHistory(event.to_id)
			print("Downloading...")
			out_path = await self.download_media_by_id(msg_id)
			# It's really a mess of options, but it works.
			call(["mogrify", "-contrast", "-contrast", "-level", "25%", "-modulate", "80,200", "-modulate", "100,150", "-level", "25%", "-contrast", "-contrast", out_path])
			await event.reply(file=out_path)
			call(["rm", out_path])

	async def refreshHistory(self, chat_id):
		messages = await self.get_messages(chat_id, limit=200)

		for msg in messages:
			if getattr(msg, 'media', None):
				self.found_media[msg.id] = msg

	async def download_media_by_id(self, media_id):
		try:
			msg = self.found_media[int(media_id)]
		except (ValueError, KeyError):
			# ValueError when parsing, KeyError when accessing dictionary
			print('Invalid media ID given or message not found!')
			return

		return await self.download_media(
			msg.media,
			file='/tmp/telethon-media/'
		)

if __name__ == '__main__':
	SESSION = os.environ.get('TG_SESSION', 'bot')
	API_ID = os.environ.get('API_ID', '')
	API_HASH = os.environ.get('API_HASH', '')
	client = InteractiveTelegramClient(SESSION, API_ID, API_HASH)
	client.run_until_disconnected()