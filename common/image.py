from __future__ import annotations
import os
import numpy as np
from scipy.ndimage import uniform_filter, gaussian_filter
import skimage


## Main Image Object Class
class Image:
    def __init__(self, data: np.ndarray, title: str=""):
        self.data = data
        self.set_default()
        self.title = title

    def set_default(self, img: Image=None):
        if img is None:
            self.title = ""
            self.dtype = "img"
            self.shifted = False
            self.axis_off = False
        else:
            self.title = img.title
            self.dtype = img.dtype
            self.shifted = img.shifted
            self.axis_off = img.axis_off
        return self

    @property
    def shape(self):
        return self.data.shape

    def info(self):
        print(f">> {[self.title]}: {self.data.shape} dtype={self.dtype}", end=", ")
        print(f"shifted={self.shifted}, axis_off={self.axis_off}")
        return self

    def data_info(self):
        print(f">> shape={self.data.shape}, dtype={self.data.dtype}", end=", ")
        print(f"min={self.data.min():.2f}, max={self.data.max():.2f}")
        return self

    def copy(self):
        img = Image(self.data, self.title)
        img.dtype = self.dtype
        img.shifted = self.shifted
        img.axis_off = self.axis_off
        return img
    
    def clip(self, min=1e-6):
        img = Image(np.clip(self.data, min, self.data.max()), self.title)
        img.dtype = self.dtype
        img.shifted = self.shifted
        img.axis_off = self.axis_off
        return img

    def add_title(self, title: str):
        self.title = title + self.title
        return self

    def set_title(self, title: str):
        self.title = title
        return self

    def set_dtype(self, dtype: str):
        self.dtype = dtype
        return self

    def set_shifted(self, shifted: bool):
        self.shifted = shifted
        return self

    def set_axis_off(self, axis_off: bool):
        self.axis_off = axis_off
        return self

    def __pow__(self, n):
        img = Image(self.data**n)
        img.set_default(self)
        return img
    
    def __add__(self, img: Image):
        img = Image(self.data + img.data)
        img.set_default(self)
        return img

    def __sub__(self, img: Image):
        img = Image(self.data - img.data)
        img.set_default(self)
        return img

    def __mul__(self, img: Image):
        img = Image(self.data * img.data)
        img.set_default(self)
        return img

    def __truediv__(self, img: Image):
        img = Image(self.data / img.data)
        img.set_default(self)
        return img

    def __abs__(self):
        img = Image(np.abs(self.data))
        img.set_default(self)
        return img


class Imread(Image):
    def __init__(self, filename: str, path: str=None):
        if path is not None:
            filename = os.path.join(path, filename)
        if filename.endswith("csv"):
            self.data = np.genfromtxt(filename, delimiter=',')
        else:
            self.data = skimage.io.imread(filename)
        self.set_default()
        self.title = os.path.basename(filename)[:-4]


class Gray(Image):
    def __init__(self, img: Image):
        self.data = img.data
        if self.data.ndim > 2:
            if self.data.shape[-1] > 3:
                self.data = skimage.color.rgba2rgb(self.data)
            self.data = skimage.color.rgb2gray(self.data)
        self.set_default(img)


class Resize(Image):
    def __init__(self, img: Image, shape: tuple):
        self.data = skimage.transform.resize(img.data, shape)
        self.set_default(img)


class Rescale(Image):
    def __init__(self, img: Image, min_max: tuple):
        img_min_max = img.data.min(), img.data.max()
        self.data = np.interp(img.data, img_min_max, min_max)
        self.set_default(img)
        
class Rotate(Image):
    def __init__(self, img: Image, angle: int):
        self.data = skimage.transform.rotate(img.data, angle, resize=True)
        self.set_default(img)

class Gaussian(Image):
    def __init__(self, img: Image, sigma=1):
        self.data = gaussian_filter(img.data, sigma=sigma)
        self.set_default(img)


class Uniform(Image):
    def __init__(self, img: Image, size=1):
        self.data = uniform_filter(img.data, size=size, mode="nearest")
        self.set_default(img)


if __name__ == "__main__":

    import skimage
    from viewer import Viewer

    viewer = Viewer()

    if 0:
        img1 = Image(skimage.data.astronaut()).set_title("Astronaut").add_title("(raw)")
        img2 = Resize(img1.copy(), (400, 300)).add_title("(resized)")
        img3 = Gray(img2.copy()).add_title("(gray)")

        img1.set_dtype("img")
        img2.set_dtype("amp").set_shifted(True)
        img3.set_dtype("ang").set_shifted(True)

        viewer.set_default()
        viewer.show(img1, img2, img3)

    if 0:
        raw = Image(skimage.data.astronaut()).set_title("RAW").info()
        img = Gray(raw.copy()).add_title("(gray)")
        img = Resize(img, (300, 200)).info().data_info()

        viewer.show(raw, img)
        
    if 1:
        raw = Image(skimage.data.astronaut()).set_title("RAW").info()
        img1 = Resize(Gray(raw.copy()), (300, 500)).add_title("(gray)")
        img2 = Rotate(img1, 90).info().data_info()
        img3 = Rotate(img1, 180).info().data_info()
        img4 = Rotate(img1, 270).info().data_info()
        
        viewer.show(raw, img1, img2, img3)
