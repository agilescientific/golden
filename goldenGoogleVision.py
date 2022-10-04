import io
import os
import numpy as np
from collections import defaultdict
from google.cloud import vision
from oauth2client.client import GoogleCredentials
credentials = GoogleCredentials.get_application_default()
import googlemaps
from datetime import datetime
gmaps = googlemaps.Client(key='')
import geomMed as gm
import requests
from PIL import Image
from io import BytesIO
import urllib
from bs4 import BeautifulSoup
import json
import math
from secrets import meaningcloud


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

def _image_entropy(img):
    """calculate the entropy of an image"""
    hist = img.histogram()
    hist_size = sum(hist)
    hist = [float(h) / hist_size for h in hist]

    return -sum(p * math.log(p, 2) for p in hist if p != 0)

def square_im(img):
    x,y = img.size
    while x!=y:
        dy = 10
        
        if y-x<10:
            dy = 1
        bottom = img.crop((0, y - dy, x, y))
        top = img.crop((0, 0, x, dy))
        #remove the slice with the least entropy
        if _image_entropy(bottom) < _image_entropy(top):
            img = img.crop((0, 0, x, y - dy))
        else:
            img = img.crop((0, dy, x, y))
        x,y = img.size
    return(img)

def getThumb(imUrl):
    """
    If image isn't square, make it so, maximizing interest
    """
    # retrieve image data
    data = requests.get(imUrl).content
    im = Image.open(BytesIO(data)) 
    s = im.size
    if s[0]==s[1]:
        return(im)
    T = False
    if s[0]>s[1]: # landscape
        T = True
        im = im.transpose(method=Image.TRANSPOSE)
    square = square_im(im)
    if T:
        square = square.transpose(method=Image.TRANSPOSE)
    return(square)
     

def scrapeImages(url):
    """
    Return dict of images at url with nPix>160000 with googleVision labels and best 
    guess at location if likely a map
    """
    #Scrape images
    r = requests.get(url)
    data = r.text
    soup = BeautifulSoup(data,"html5lib")
    ims = {}
    # for every image with nPix>160000, get GV labels, add labels to dict
    maxPix, bigIm = 0,''
    for image in soup.find_all("img"):
        if image.get("src")!=None:
            imUrl = image.get("src")
            if not imUrl.startswith('http'): # need to add absolute path
                if imUrl[0]=='/':
                    base = url[:url.index('://')]+url[url.index('://'):]
                    imUrl = urllib.parse.urljoin(base,imUrl)
                else:
                    base = url[::-1][url[::-1].index('/'):][::-1]
                    imUrl = urllib.parse.urljoin(base,imUrl)
            size = get_image_size(imUrl)
            nPix = np.product(size)
            # Penalize long/wide images
            if max(size)>2.5*min(size):
                nPix/=10.
            if nPix > maxPix:
                maxPix,bigIm = nPix,imUrl          
            if nPix > 160000: # For interestingly large images
                # Add to dict
                ims[imUrl] = {'url':imUrl}
                labels = detect_labels_url(imUrl)
                # Add googleVision labels to dict
                allLabels = []
                for label in labels:
                    allLabels.append(label.description)
                if len(allLabels)>0:
                    ims[imUrl]['GVlabels'] = allLabels
                # if image is labelled as mappy, extract text, geocode, compute geometric median
                if 'map' in allLabels or 'drawing' in allLabels or 'diagram' in allLabels or\
                   'location' in allLabels or 'line' in allLabels or 'shape' in allLabels:
                    text = detect_text_url(imUrl)
                    strings = text[0].description.split('\n')
                    print(strings)
                    if len(strings)>0:
                        geoStrings = geocode_text(strings)
                        geoMed = getMedian(geoStrings)
                        ims[imUrl]['location'] = geoMed
                        
    # build square thumbnail for biggest image
    thumb = getThumb(bigIm)
    thumbName = bigIm[::-1][:bigIm[::-1].index('/')][::-1]
    thumb.save(thumbName+'_thumb.jpg',format='jpeg')
    # RETURN THUMBNAME?

    return(ims)


def analyse_text(t, txtf='plain'):
    url = "http://api.meaningcloud.com/topics-2.0"

    data = {
        'key': meaningcloud,
        'of': 'json',
        'txt': text,
        'lang': 'en',
        'txtf': txtf,  # could be plain or html
        'dm': 's',  # semantic disambiguation includes morphosyntactic disambiguation
        'rt': 'n',   # relaxed typography / strictness
        'sdg': 'l',  # Semantic disambiguation grouping (only if dm=s)
        'timeref': '2017-03-03 18:00:00 GMT-04:00',  # For interpreting relative time
        'st': 'n',
        'tt': 'a',  # topic types
        'uw': 'n',  # try to deal with unknown words (eg b/c typos)
        'ud': '',    # user dictionary
        }

    headers = {'content-type': 'application/x-www-form-urlencoded'}

    r = requests.request("POST", url, data=data, headers=headers)

    return r.json()


def get_people(j):
    return [x['form'] for x in j['entity_list'] if 'Person' in x['sementity']['type']]


def get_companies(j):
    return [x['form'] for x in j['entity_list'] if 'Company' in x['sementity']['type']]


def get_places(j):
    return [x['form'] for x in j['entity_list'] if 'Location' in x['sementity']['type']]


def get_elements(j):
    return [x['form'] for x in j['concept_list'] if 'Element' in x['sementity']['type']]

# Call like (for HTML)...  get_people(analyse_text(html, txtf='html'))
# Or like...  get_elements(analyse_text(html, 'html'))
