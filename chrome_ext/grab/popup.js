// Copyright (c) 2014 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
// Modified by Agile Geoscience

/**
 * Get the current tab URL.
 *
 * @param {function(string)} callback - called when the URL of the current tab
 *   is found.
 */
function getCurrentTabUrl(callback) {
  // Query filter to be passed to chrome.tabs.query - see
  // https://developer.chrome.com/extensions/tabs#method-query
  var queryInfo = {
    active: true,
    currentWindow: true
  };

  chrome.tabs.query(queryInfo, function(tabs) {
    // chrome.tabs.query invokes the callback with a list of tabs that match the
    // query. When the popup is opened, there is certainly a window and at least
    // one tab, so we can safely assume that |tabs| is a non-empty array.
    // A window can only have one active tab at a time, so the array consists of
    // exactly one tab.
    var tab = tabs[0];

    // A tab is a plain object that provides information about the tab.
    // See https://developer.chrome.com/extensions/tabs#type-Tab
    var url = tab.url;

    // tab.url is only available if the "activeTab" permission is declared.
    // If you want to see the URL of other tabs (e.g. after removing active:true
    // from |queryInfo|), then the "tabs" permission is required to see their
    // "url" properties.
    console.assert(typeof url == 'string', 'tab.url should be a string');

    callback(url);
  });
}

/**
 * Get the current tab Title.
 *
 * @param {function(string)} callback - called when the URL of the current tab
 *   is found.
 */
function getCurrentTabTitle(callback) {
  // Query filter to be passed to chrome.tabs.query - see
  // https://developer.chrome.com/extensions/tabs#method-query
  var queryInfo = {
    active: true,
    currentWindow: true
  };

  chrome.tabs.query(queryInfo, function(tabs) {
    // chrome.tabs.query invokes the callback with a list of tabs that match the
    // query. When the popup is opened, there is certainly a window and at least
    // one tab, so we can safely assume that |tabs| is a non-empty array.
    // A window can only have one active tab at a time, so the array consists of
    // exactly one tab.
    var tab = tabs[0];

    // A tab is a plain object that provides information about the tab.
    // See https://developer.chrome.com/extensions/tabs#type-Tab
    var title = tab.title;


    callback(title);
  });

}

/**
 * Save pin info:
 * @param {string} nurl - Target url to save.
 * @param {string} html_content - HTML content of the current tab
 *   
 */
function savePin(nurl,html_content) {

  // var apiurl = 'http://127.0.0.1:5000/store'
  var apiurl = 'http://127.0.0.1:5000/store';
  var x = new XMLHttpRequest();
  x.open('POST', apiurl);
  // The Google image search API responds with JSON, so let Chrome parse it.
  x.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
  
  document.getElementById('status').textContent = "Saving...";
  // x.responseType = 'json';
  x.onreadystatechange = function() {
    if (x.readyState == XMLHttpRequest.DONE) {
        //console.log(x.responseText);
        document.getElementById("pinIt").disabled = true;
        document.getElementById('status').textContent = "Saved!";

        idx = x.responseText;
        var apiurl = 'http://127.0.0.1:5000/gvis';
        var gx = new XMLHttpRequest();
        gx.open('POST', apiurl);
        // The Google image search API responds with JSON, so let Chrome parse it.
        gx.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        gx.send(JSON.stringify({
          "timestamp" : d
        }));
    }
  }

  x.onerror = function() {
    errorCallback('Network error.');
  };

  var tzRe = /\(([\w\s]+)\)/; // Look for "(", any words (\w) or spaces (\s), and ")"
  var d = new Date().toString();
  var tz = tzRe.exec(d)[1]; // timezone, i.e. "Pacific Daylight Time"


  x.send(JSON.stringify({
    "title": nurl,
    "image": "placeholder.png",
    "tags": document.getElementById('tags').value,
    "html": 'html_content',
    "timestamp": d,
    "locations": "",
    "insights": "",
    "img_dict": ""
  }));
  //alert(html_content);
}

function renderStatus(statusText) {
  document.getElementById('status').textContent = statusText;
}

function renderUrl(urlText) {
  document.getElementById('url_to_save').value = urlText;
}

function renderTitle(title) {
  document.getElementById('site_title').textContent = title;
}

document.addEventListener('DOMContentLoaded', function() {
  getCurrentTabUrl(function(url) {
    // Load current URLs
    renderUrl(url);
    renderTitle(url);

    // Load HTML source
    chrome.runtime.onMessage.addListener(function(request, sender) {
      if (request.action == "getSource") {
          // message.innerText = request.source;
          html_content = request.source;
          message.innerText = '';
        }
    });

    // title = getCurrentTabTitle(); // WHAT?
    title = "New Loc"

    document.getElementById("pinIt").addEventListener("click", function(){
          savePin(title, url, html_content);
    });


  });
});


function onWindowLoad() {

  var message = document.querySelector('#message');

  chrome.tabs.executeScript(null, {
    file: "getPagesSource.js"
  }, function() {
    // If you try and inject into an extensions page or the webstore/NTP you'll get an error
    if (chrome.runtime.lastError) {
      message.innerText = 'There was an error parsing the site : \n' + chrome.runtime.lastError.message;
    }
  });

}

window.onload = onWindowLoad;

