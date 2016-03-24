import logging, uuid, os

from concurrent import futures
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPainter, QBrush, QPen

from database import db_constants
import utils
import app_constants

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

def _rounded_qimage(qimg, radius):
	r_image = QImage(qimg.width(), qimg.height(), QImage.Format_ARGB32)
	r_image.fill(Qt.transparent)
	p = QPainter()
	pen = QPen(Qt.darkGray)
	pen.setJoinStyle(Qt.RoundJoin)
	p.begin(r_image)
	p.setRenderHint(p.Antialiasing)
	p.setPen(Qt.NoPen)
	p.setBrush(QBrush(qimg))
	p.drawRoundedRect(0, 0, r_image.width(), r_image.height(), radius, radius)
	p.end()
	return r_image

def _task_thumbnail(gallery_or_path, img=None, width=app_constants.THUMB_W_SIZE,
						height=app_constants.THUMB_H_SIZE):
	"""
	"""
	log_i("Generating thumbnail")
	# generate a cache dir if required
	if not os.path.isdir(db_constants.THUMBNAIL_PATH):
		os.mkdir(db_constants.THUMBNAIL_PATH)

	try:
		if not img:
			img_path = utils.get_gallery_img(gallery_or_path)
		else:
			img_path = img
		if not img_path:
			raise IndexError
		for ext in utils.IMG_FILES:
			if img_path.lower().endswith(ext):
				suff = ext # the image ext with dot

		# generate unique file name
		file_name = str(uuid.uuid4()) + ".png"
		new_img_path = os.path.join(db_constants.THUMBNAIL_PATH, (file_name))
		if not os.path.isfile(img_path):
			raise IndexError

		# Do the scaling
		try:
			im_data = utils.PToQImageHelper(img_path)
			image = QImage(im_data['data'], im_data['im'].size[0], im_data['im'].size[1], im_data['format'])
			if im_data['colortable']:
				image.setColorTable(im_data['colortable'])
		except ValueError:
			image = QImage()
			image.load(img_path)
		if image.isNull():
			raise IndexError
		radius = 5
		image = image.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
		r_image = _rounded_qimage(image, radius)
		r_image.save(new_img_path, "PNG", quality=80)
	except IndexError:
		new_img_path = app_constants.NO_IMAGE_PATH

	return new_img_path

def _task_load_thumbnail(ppath, thumb_size, on_method=None, **kwargs):
	if ppath:
		img = QImage(ppath)
		if not img.isNull():
			size = img.size()
			if size.width() != thumb_size[0]:
				# TODO: use _task_thumbnail
				img = _rounded_qimage(img.scaled(thumb_size[0], thumb_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation), 5)
			if on_method:
				on_method(img, **kwargs)
			return img

class Executors:
	_thumbnail_exec = futures.ThreadPoolExecutor(3)
	_profile_exec = futures.ThreadPoolExecutor(2)
	
	@classmethod
	def generate_thumbnail(cls, gallery_or_path, img=None, width=app_constants.THUMB_W_SIZE,
						height=app_constants.THUMB_H_SIZE, on_method=None, blocking=False):
		log_i("Generating thumbnail")
		f = cls._thumbnail_exec.submit(_task_thumbnail, gallery_or_path, img=img, width=width, height=height)
		if on_method:
			f.add_done_callback(on_method)
		if blocking:
			return f.result()
		if not on_method:
			return f

		log_d("Returning future")

	@classmethod
	def load_thumbnail(cls, ppath, thumb_size=app_constants.THUMB_DEFAULT, on_method=None, **kwargs):
		"**kwargs will be passed to on_method"
		f = cls._profile_exec.submit(_task_load_thumbnail, ppath, thumb_size, on_method, **kwargs)
		return f

