from pkg_resources import resource_listdir, resource_filename
from subprocess import call
import face_recognition
import os
import random

emojis_path = resource_filename("plugins", "emoji")
emojis = list(filter(lambda x:".png" in x, resource_listdir("plugins", "emoji")))

def pick_random_emoji():
	position = random.randint(0, len(emojis)-1)
	return os.path.join(emojis_path, emojis[position])

class FryEmojiPlugin(object):
	def __init__(self, bot):
		self.pattern = '^\.fry\+$'
		self.bot = bot

	async def handler(self, event):
		try:
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
		except Exception as e:
			print(e)

	def fry(self, input_path):
		# It's really a mess of options, but it works.
		call(["mogrify", "-contrast", "-contrast", "-level", "25%", "-modulate", "80,200", "-modulate", "100,150", "-level", "25%", "-contrast", "-contrast", input_path])
		return input_path

	def emojify(self, input_path):
		"""
		Detects faces and superimposes an emoji over them.
		Returns the path to the new picture, deleting the old one.
		"""
		faces = face_recognition.face_locations(face_recognition.load_image_file(input_path))
		if (len(faces) == 0):
			return path

		imagemagick_cmd = ["convert", input_path]
		# Poor man's flatMap
		for face in faces:
			imagemagick_cmd.extend(self.get_params_for_face(face))
		output_path = input_path + ".composite.jpg"
		imagemagick_cmd.append(output_path)
		call(imagemagick_cmd)
		call(["rm", input_path])
		return output_path

	def get_params_for_face(self, face):
		"""
		Takes a tuple for the face position, returns a piece of ImageMagick commands.
		"""
		(top, right, bottom, left) = face
		# For debug purposes, draw a rectangle over the face
		# draw_str = 'rectangle %d,%d %d,%d' % (left, top, right, bottom)
		# return ["-fill", "green", "-stroke", "black", "-draw", draw_str]
		emoji_path = pick_random_emoji()
		# Increase the size by 20%. Account for proper centering.
		scale_factor = 0.20
		size_str = "%dx%d" % ((right - left) * (1 + scale_factor), (bottom - top) * (1 + scale_factor))
		diff_x = (right - left) * (scale_factor / 2)
		diff_y = (bottom - top) * (scale_factor / 2)
		pos_str = "+%d+%d" % (left - diff_x, top - diff_y)
		geometry_str = size_str + pos_str
		return [emoji_path, "-geometry", geometry_str, "-composite"]