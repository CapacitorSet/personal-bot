from subprocess import call

import face_recognition

class FryPlugin(object):
	def __init__(self, bot):
		self.pattern = '^\.fry$'
		self.bot = bot

	async def handler(self, event):
		msg_id = event.reply_to_msg_id
		if (event.reply_to_msg_id is None):
			await event.reply("Rispondi a un'immagine per friggerla.")
			return
		await self.bot.refreshHistory(event.to_id)
		photo_path = await self.bot.download_media_by_id(msg_id)
		fried_path = self.fry(photo_path)
		await event.reply(file=fried_path)
		call(["rm", fried_path])

	def fry(self, input_path):
		# It's really a mess of options, but it works.
		call(["mogrify", "-contrast", "-contrast", "-level", "25%", "-modulate", "80,200", "-modulate", "100,150", "-level", "25%", "-contrast", "-contrast", input_path])
		return input_path