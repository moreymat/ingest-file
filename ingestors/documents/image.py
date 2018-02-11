import logging
from datetime import datetime
from PIL import ExifTags

from ingestors.base import Ingestor
from ingestors.support.ocr import OCRSupport
from ingestors.support.plain import PlainTextSupport

log = logging.getLogger(__name__)


class ImageIngestor(Ingestor, OCRSupport, PlainTextSupport):
    """Image file ingestor class.

    Extracts the text from images using OCR.
    """

    MIME_TYPES = [
        'image/x-portable-graymap',
        'image/png',
        'image/jpeg',
        'image/gif',
        'image/pjpeg',
        'image/bmp',
        'image/x-windows-bmp',
        'image/x-portable-bitmap',
        'application/postscript',
        'image/vnd.dxf',
    ]
    EXTENSIONS = [
        'jpg',
        'jpeg',
        'png',
        'gif',
        'bmp'
    ]
    SCORE = 5

    def parse_exif_date(self, date):
        try:
            return datetime.strptime(date, '%Y:%m:%d %H:%M:%S')
        except Exception:
            return None

    def extract_exif(self, img):
        if not hasattr(img, '_getexif'):
            return

        exif = img._getexif()
        if exif is None:
            return

        make, model = '', ''
        for num, value in exif.items():
            try:
                tag = ExifTags.TAGS[num]
            except KeyError:
                log.warning("Unknown EXIF code: %s", num)
                continue
            if tag == 'DateTimeOriginal':
                self.update('created_at', self.parse_exif_date(value))
            if tag == 'DateTime':
                self.update('date', self.parse_exif_date(value))
            if tag == 'Make':
                make = value
            if tag == 'Model':
                model = value

        generator = ' '.join((make, model))
        self.update('generator', generator.strip())

    def ingest(self, file_path):
        self.result.flag(self.result.FLAG_IMAGE)
        with open(file_path, 'r') as fh:
            data = fh.read()

        image = self.parse_image(data)
        self.extract_exif(image)

        text = self.extract_text_from_image(data, image=image)
        self.extract_plain_text_content(text)