from subprocess import call

import face_recognition

class FryEmojiPlugin(object):
	def __init__(self, bot):
		self.pattern = '^\.fry\+$'
		self.bot = bot

	async def handler(self, event):
		msg_id = event.reply_to_msg_id
		if (event.reply_to_msg_id is None):
			await event.reply("Rispondi a un'immagine per friggerla.")
			return
		await self.bot.refreshHistory(event.to_id)
		photo_path = await self.bot.download_media_by_id(msg_id)
		emojified_path = self.emojify(photo_path)
		fried_path = self.fry(emojified_path)
		await event.reply(file=fried_path)
		call(["rm", fried_path])

	def fry(self, input_path):
		# It's really a mess of options, but it works.
		call(["mogrify", "-contrast", "-contrast", "-level", "25%", "-modulate", "80,200", "-modulate", "100,150", "-level", "25%", "-contrast", "-contrast", input_path])
		return input_path

	def emojify(self, input_path):
		"""
		Detects faces and superimposes an emoji over them. Currently targets only the first face.
		Returns the path to the new picture, deleting the old one.
		"""
		face_locations = face_recognition.face_locations(face_recognition.load_image_file(input_path))
		if (len(face_locations) == 0):
			return path
		# todo: handle more than one face
		(top, right, bottom, left) = face_locations[0]
		# For debug purposes, draw a rectangle over the face
		# draw_str = 'rectangle %d,%d %d,%d' % (left, top, right, bottom)
		# call(["mogrify", "-fill", "green", "-stroke", "black", "-draw", draw_str, input_path])
		output_path = input_path + ".composite.jpg"
		emoji_path = "/tmp/emoji.png"
		emoji_width = 160
		emoji_height = 160
		# Increase the size by 20%. Account for proper centering.
		scale_factor = 0.20
		size_str = "%dx%d" % ((right - left) * (1 + scale_factor), (bottom - top) * (1 + scale_factor))
		diff_x = (right - left) * (scale_factor / 2)
		diff_y = (bottom - top) * (scale_factor / 2)
		pos_str = "+%d+%d" % (left - diff_x, top - diff_y)
		geometry_str = size_str + pos_str
		call(["convert", input_path, emoji_path, "-geometry", geometry_str, "-composite", output_path])
		call(["rm", input_path])
		return output_path