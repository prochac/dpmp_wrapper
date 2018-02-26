import pickle
import requests
from PIL import Image
from PIL import ImageEnhance
from io import BytesIO
import numpy
import os

dir_path = os.path.dirname(os.path.realpath(__file__))


def get_captcha(url: str) -> str:
    res = requests.get(url)
    images = numpy.array([
        numpy.asarray(__filter_image(img_crop))
        for img_crop in __crop_image(Image.open(BytesIO(res.content)))
    ])
    with open('{}/classifier.pkl'.format(dir_path), 'rb') as f:
        classifier = pickle.load(f)

    images = images.reshape((len(images), -1))
    predicted = classifier.predict(images)
    return ''.join(predicted)


def __crop_image(image: Image) -> list:
    ret = []
    for i in range(5):
        ret.append(image.crop((i * 30, 0, 30 + i * 30, 45)))
    return ret


def __filter_image(image: Image) -> Image:
    image = image.convert('L')
    image = ImageEnhance.Contrast(image).enhance(20.0)
    image = image.convert('1')
    image = __delete_solo_pixels(image)
    return image


def __delete_solo_pixels(image: Image, level=5) -> Image:
    pixels = image.load()
    for i in range(image.size[0]):
        for j in range(image.size[1]):
            try:
                n = bool(pixels[i - 1, j])
            except IndexError:
                n = True
            try:
                w = bool(pixels[i, j - 1])
            except IndexError:
                w = True
            try:
                e = bool(pixels[i, j + 1])
            except IndexError:
                e = True
            try:
                s = bool(pixels[i + 1, j])
            except IndexError:
                s = True
            try:
                nw = bool(pixels[i - 1, j - 1])
            except IndexError:
                nw = True
            try:
                se = bool(pixels[i + 1, j + 1])
            except IndexError:
                se = True
            try:
                sw = bool(pixels[i + 1, j - 1])
            except IndexError:
                sw = True
            try:
                ne = bool(pixels[i - 1, j + 1])
            except IndexError:
                ne = True
            neighbor_sum = 0
            for not_neighbor in [n, s, e, w, nw, se, sw, ne]:
                neighbor_sum = neighbor_sum + int(not_neighbor)

            if neighbor_sum > level:
                pixels[i, j] = True
    return image
