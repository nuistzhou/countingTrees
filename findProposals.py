import os
import glob
import numpy as np
import cv2
from PIL import Image
from skimage.feature import peak_local_max
from config import Parameters
import matplotlib.pyplot as plt


def cropImage(filename, chopsize):
    image_raw = cv2.imread(filename)
    height, width, bands = image_raw.shape
    image_raw = np.transpose(image_raw, axes = (1,0,2))
    pixelAddX = width%chopsize
    pixelAddY = height%chopsize
    chopColNr = width/chopsize
    chopRowNr = height/chopsize

    if pixelAddX != 0:
        chopColNr += 1
    if pixelAddY != 0:
        chopRowNr += 1
    chopList = list()

    for j in range(chopRowNr):
        for i in range(chopColNr):
            tempArray = np.zeros((chopsize, chopsize, 3), dtype = np.uint8)
            # chop at the right bottom corner
            if i == chopColNr - 1 and j == chopRowNr -1:
                chopArray = image_raw[i * chopsize: (i * chopsize + pixelAddX),
                            j * chopsize: (j * chopsize + pixelAddY), :]
                tempArray[:pixelAddX, :pixelAddY, :] = chopArray
            # chop at the right edge
            elif i == chopColNr -1:
                chopArray = image_raw[i * chopsize: (i * chopsize + pixelAddX),
                            j * chopsize: (j + 1) * chopsize, :]
                tempArray[:pixelAddX, :, :] = chopArray
            # chop at the bottom line
            elif j == chopRowNr -1:
                chopArray = image_raw[i * chopsize: (i + 1) * chopsize,
                            j * chopsize: (j * chopsize + pixelAddY), :]
                tempArray[:, :pixelAddY, :] = chopArray
            # normal chop does not need adding pixels
            else:
                tempArray[:, :, :] = image_raw[i * chopsize: (i + 1) * chopsize,
                                     j * chopsize: (j + 1) * chopsize, :
                                     ]
            chopList.append(tempArray)
    return chopList, chopColNr, chopRowNr

def createImageFromCrops(chopsize, chopList, chopColNr, chopRowNr):
    array = np.zeros((chopsize * chopColNr, chopsize * chopRowNr, 3), dtype = np.uint8)
    counter = 0
    for j in range(chopRowNr):
        for i in range(chopColNr):
            array[i * chopsize: (i + 1) * chopsize, j * chopsize : (j + 1) * chopsize, :] = chopList[counter]
            counter += 1
    array_new = np.transpose(array, (1,0,2))
    img = Image.fromarray(array_new, 'RGB')
    img.save('/Users/ping/Documents/thesis/data/rgb_image_ssearch/my.png')
    img.show()

def averageCocotrees():
    # Load images into a list of Numpy Array
    imageDir = "/Users/ping/Documents/thesis/data/patchImages/lower/coco"
    os.chdir(imageDir)
    filenameList = glob.glob("*.png")
    w, h = Image.open(filenameList[0]).size
    nrFiles = len(filenameList)

    # Create a numpy array of floats to store the average (assume RGB images)
    avgImageArr = np.zeros((h, w, 3), np.float)
    # Build up average pixel intensities, casting each image as an array of floats
    for im in filenameList:
        imgArr = np.array(Image.open(im), dtype=np.float)
        avgImageArr = avgImageArr + imgArr / nrFiles
    avgImageArr = np.array(np.round(avgImageArr), dtype=np.uint8)
    avgImg = Image.fromarray(avgImageArr, 'RGB')
    avgImg.save(Parameters.avgCocoImg)

def putImgAtCenter(img, targetSize):
    imgArray = np.float32(cv2.imread(img)) / 255.
    imgArray -= np.average(imgArray[:])

    w, h = imgArray.shape[:2]
    centerX = targetSize/2 - 1
    centerY = targetSize/2 -1
    avgImageArr = np.zeros((targetSize, targetSize, 3), np.float32)

    if w <= targetSize and h <= targetSize:
        avgImageArr[centerX : centerX + w, centerY : centerY + h,:] = imgArray
    avgImg = Image.fromarray(avgImageArr, 'RGB')
    avgImg.save(Parameters.avgCocoImgEnlarged)
    return avgImageArr

def detectProposals(chopArrayList, avgCocoArray):
    """Return the array of proposal centers' pixel coordinates"""
    f_avgCoco = np.fft.fft2(np.fft.fftshift(avgCocoArray, axes=(0,1)), axes=(0, 1))
    proposalCentersList = list()
    for chopArray in chopArrayList[:1]:
        f_chop = np.fft.fft2(chopArray, axes=(0, 1))
        multiplication = np.multiply(f_avgCoco, f_chop)
        f_inversed = np.real(np.fft.ifft2(multiplication,axes=(0,1)))
        f_inversed = np.average(f_inversed,axis=2)
        peak_localmax = peak_local_max(f_inversed, indices = True)
        peak_localmax_5 = peak_local_max(f_inversed, min_distance = 5, indices = True)
        peak_localmax_10 = peak_local_max(f_inversed, min_distance = 10, indices = True)
        peak_localmax_15 = peak_local_max(f_inversed, min_distance = 15, indices = True)

        plt.figure(1), plt.imshow(f_inversed)
        plt.figure(2)

        plt.subplot(2, 2, 1), plt.imshow(chopArray), \
        plt.plot(peak_localmax[:, 1], peak_localmax[:, 0], 'r+'), plt.title("Minimum peaks distance Not set")
        plt.subplot(2, 2, 2), plt.imshow(chopArray), \
        plt.plot(peak_localmax_5[:, 1], peak_localmax_5[:, 0], 'r+'), plt.title("Minimum peaks distance = 5 pixels")
        plt.subplot(2, 2, 3), plt.imshow(chopArray), \
        plt.plot(peak_localmax_10[:, 1], peak_localmax_10[:, 0], 'r+'),plt.title("Minimum peaks distance = 10 pixels")
        plt.subplot(2, 2, 4), plt.imshow(chopArray), \
        plt.plot(peak_localmax_15[:, 1], peak_localmax_15[:, 0], 'r+'),plt.title("Minimum peaks distance = 15 pixels")
        proposalCentersList.append(peak_localmax)
    return proposalCentersList

def calRecallWithAnnotations():



if __name__ == "__main__":
    rgb_image_filename = "/Users/ping/Documents/thesis/data/rgb_image_ssearch/rgb_image_ssearch.tif"
    chopsize = 1024
    chopList, chopColNr, chopRowNr = cropImage(rgb_image_filename, chopsize)
    # newImage = createImageFromCrops(chopsize, chopList, chopColNr, chopRowNr)
    averageCocotrees()
    avgCocoArray = putImgAtCenter(Parameters.avgCocoImg, chopsize)
    proposalCenterList = detectProposals(chopList, avgCocoArray)
    print 'end'

