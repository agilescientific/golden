import io
import os
import numpy as np
from collections import defaultdict
from google.cloud import vision
from oauth2client.client import GoogleCredentials
credentials = GoogleCredentials.get_application_default()
import googlemaps
from datetime import datetime
gmaps = googlemaps.Client(key='AIzaSyB9lTkL2nX1SYDnI7zino6IqiiPudgqVvI')
import geomMed as gm
import requests
from PIL import Image
from io import BytesIO
import urllib
from bs4 import BeautifulSoup
import json


def get_image_size(url):
    try:
        data = requests.get(url).content
        im = Image.open(BytesIO(data))    
        return im.size
    except:
        return((0,0))

def detect_labels_local(path):
    """Detects labels in the file."""
    vision_client = vision.Client()
    with io.open(path, 'rb') as image_file:
        content = image_file.read()
    image = vision_client.image(content=content)
    labels = image.detect_labels()
    return(labels)

def detect_labels_url(url):
    """Detects labels in the file."""
    vision_client = vision.Client()
    image = vision_client.image(source_uri=url)
    labels = image.detect_labels()
    return(labels)

def detect_text_local(path):
    """Detects text in the file."""
    vision_client = vision.Client()
    with io.open(path, 'rb') as image_file:
        content = image_file.read()
    image = vision_client.image(content=content)
    texts = image.detect_text()
    return(texts)

def detect_text_url(url):
    """Detects text in the file."""
    vision_client = vision.Client()
    image = vision_client.image(source_uri=url)
    texts = image.detect_text()
    return(texts)

def geocode_text(text):
    """Get geocode result for each element of a list of strings, return a dict"""
    d = {}
    for l in text:
        if len(l)>1:
            try:
                int(l)
            except:
                geocode_result = gmaps.geocode(l)
                d[l] = geocode_result
    return(d)

def getMedian(d):
    """ 
    Calculate geometric median of points found by geocode_text
    Input: dict 
    Output: [lat,long]
    """
    pts = []
    for k in d.keys():
        if len(d[k])>0:
            pts.append([d[k][0]['geometry']['location']['lat'],\
                     d[k][0]['geometry']['location']['lng']])
    if len(pts)>0:
        geomMed = gm.getMed(pts)
        return(geomMed)
    return(None)

def scrapeImages(url):
    """
    Return dict of images at url with nPix>160000 with googleVision labels and best 
    guess as location if likely a map
    """
    #Scrape images
    r = requests.get(url)
    data = r.text
    soup = BeautifulSoup(data,"html5lib")
    ims = {}
    # for every image with nPix>160000, get GV labels, add labels to dict
    for image in soup.find_all("img"):
        if image.get("src")!=None:
            imUrl = image.get("src")
            if np.product(get_image_size(imUrl))>160000: 
                print(image.get("src"))

                labels = detect_labels_url(imUrl)
                ims[imUrl] = {'url':imUrl}
                allLabels = []
                for label in labels:
                    allLabels.append(label.description)
                if len(allLabels)>0:
                    ims[imUrl]['GVlabels'] = allLabels
                if 'map' in allLabels or 'drawing' in allLabels or 'diagram' in allLabels or\
                   'location' in allLabels:
                    text = detect_text_url(imUrl)
                    strings = text[0].description.split('\n')
                    if len(strings)>0:
                        geoStrings = geocode_text(strings)
                        geoMed = getMedian(geoStrings)
                        ims[imUrl]['location'] = geoMed
    return(ims)
                
                
    