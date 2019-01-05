import asyncio
from getpass import getpass

from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.network import ConnectionTcpAbridged

from plugins.FryPlugin import FryPlugin

# Create a global variable to hold the loop we will be using
loop = asyncio.get_event_loop()

class InteractiveTelegramClient(TelegramClient):
	def __init__(self, session_user_id, api_id, api_hash,
				 proxy=None):
		"""
		Initializes the InteractiveTelegramClient.
		:param session_user_id: Name of the *.session file.
		:param api_id: Telegram's api_id acquired through my.telegram.org.
		:param api_hash: Telegram's api_hash.
		:param proxy: Optional proxy tuple/dictionary.
		"""
		super().__init__(
			session_user_id, api_id, api_hash,
			connection=ConnectionTcpAbridged,
			proxy=proxy
		)

		# Store {message.id: message} map here so that we can download
		# media known the message ID, for every message having media.
		self.found_media = {}

		print('Connecting to Telegram servers...')
		try:
			loop.run_until_complete(self.connect())
		except ConnectionError:
			print('Initial connection failed. Retrying...')
			loop.run_until_complete(self.connect())
		print('Connected.')

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
		fryPlugin = FryPlugin(self)
		self.add_event_handler(fryPlugin.handler, events.NewMessage(pattern=fryPlugin.pattern))

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

		return await self.download_media(msg.media, file='/tmp/telethon-media/')