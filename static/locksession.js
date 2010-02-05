//
// Javascript Library for LockSession
//
// Ben Adida (ben@eecs.harvard.edu)
//
// 20007-10-11
//

// requires hmac
// requires mootools

SSL_HOST = "https://localhost"

LockSession = {};

function hash_to_sorted_query_string(hash) {
    var params_hash = $H(hash);
    var keys = params_hash.keys().sort();

    var params_str = keys.map(function(k) {return k + '=' + encodeURIComponent(hash[k]);}).join('&');

    return params_str;
}

LockSession.receiveToken = function(token) {
    LockSession.TOKEN = token;

    LockSession.cleanup();
    LockSession.setupPage();

    // add the token to the URL so that going back and forth will work nicely
    // without having to reload the token
    document.location.replace(document.location.href + '#[' + LockSession.TOKEN + ']');
};

window.deliverToken = LockSession.receiveToken;

LockSession.getToken = function() {
    var iframe = document.createElement('iframe');
    iframe.src = SSL_HOST + '/locksession/token_get_ssl';
    iframe.id = 'locksession_frame';
    iframe.style.height=0;
    iframe.style.width=0;
    iframe.style.visibility = 'hidden';
    document.body.appendChild(iframe);
};

LockSession.cleanup = function() {
    var iframe = $('locksession_frame');
    document.body.removeChild(iframe);
};

LockSession.load_token_from_url = function () {
    // get the fragment
    var fragment = document.location.hash.substring(1);

    // get the token out of there, there may be some other fragment
    var match = fragment.match(/\[(.*)\]/)

    if (!match) {
	return false;
    }

    var token = match[1];

    var new_href = document.location.href.replace('[' + token + ']', '');
    LockSession.TOKEN = token;

    // for now don't change the URL
    //document.location.replace(new_href);
    return true;
};

LockSession.sign = function(str) {
    if (!LockSession.TOKEN) {
	throw 'Oy, no token and trying to sign!';
    }

    // alert('signing: ' + str);

    return hex_hmac_sha1(LockSession.TOKEN, str);
};

// assumes an absolute url
LockSession.patch_url = function(url) {
    var parsed_current = parseUri(document.location);
    var parsed_next = parseUri(url);

    // don't affect other sites
    if (parsed_current.host != parsed_next.host) {
	return url;
    }

    var new_url = parsed_next.path + '?';

    // timestamp
    parsed_next.queryKey['ls_timestamp'] = new Date().toISO8601(5);

    // parameter string
    var params_str = hash_to_sorted_query_string(parsed_next.queryKey);
    new_url += params_str;

    // the string to sign inludes a '?' no matter what. And the timestamp of course.
    var string_to_sign = new_url;

    new_url += '&ls_sig=' + encodeURIComponent(LockSession.sign(string_to_sign));

    // prepend the protocol and host and such
    new_url = parsed_next.protocol + '://' + parsed_next.authority + new_url;

    // append the existing hash and the token
    new_url += '#' + parsed_next.anchor + '[' + LockSession.TOKEN + ']';

    return new_url;
};

LockSession.patch_hrefs = function() {
    var anchors = document.getElementsByTagName('a');

    var onclick = function(anchor) {
	document.location = LockSession.patch_url(this.href);
	return false;
    };

    // go through all of them
    for (var i=0; i<anchors.length; i++) {
	anchors[i].onclick = onclick;
    }
};

LockSession.form_submit = function(form) {
    // add the timestamp
    var ls_ts_input = form.getElementById(LockSession.FORM_INPUT_ID);
    if (!ls_ts_input) {
	ls_ts_input = document.createElement('input');
	ls_ts_input.type= 'hidden';
	ls_ts_input.id = LockSession.FORM_INPUT_ID;
	form.appendChild(ls_ts_input);
    }

    ls_ts_input.name = 'ls_timestamp';
    ls_ts_input.value = new Date().toISO8601(5);

    var inputs = form.getElementsByTagName('input');

    var params = {};

    // go through the inputs, creating the string
    for (var i=0; i < inputs.length; i++) {
	// don't add the input if it has no name
	if (!inputs[i].name)
	    continue;

	params[inputs[i].name] = inputs[i].value;
    }

    var params_str = hash_to_sorted_query_string(params);

    var hmac_input = document.createElement('input');
    hmac_input.type = 'hidden';
    hmac_input.name = 'ls_sig';

    // get the normalized path
    hmac_input.value = LockSession.sign(parseUri(form.action).path +'?'+ params_str);

    form.appendChild(hmac_input);

    form.action += '#' + '[' + LockSession.TOKEN + ']';
};

LockSession.patch_forms = function() {
    var forms = document.getElementsByTagName('form');
    
    for (var i=0; i <forms.length; i++) {
	forms[i].onsubmit = function() {LockSession.form_submit(this);};
    }
};

LockSession.patch_ajax = function() {
    // move the xmlhttprequest open method
    XMLHttpRequest.prototype.__open = XMLHttpRequest.prototype.open;

    XMLHttpRequest.prototype.open = function(method, url, async, username, password) {
	parsed_url = parseUri(url);

	var new_url = parsed_url.path + '?';

	// timestamp
	parsed_url.queryKey['ls_timestamp'] = new Date().toISO8601(5);

	// parameter string
	var params_str = hash_to_sorted_query_string(parsed_url.queryKey);
	new_url += params_str;

	// the string to sign inludes a '?' no matter what. And the timestamp of course.
	var string_to_sign = new_url;

	new_url += '&ls_sig=' + encodeURIComponent(LockSession.sign(string_to_sign));

	return this.__open(method,new_url,async,username,password);
    };
};

LockSession.setupPage = function() {
    LockSession.patch_hrefs();
    LockSession.patch_forms();
    LockSession.patch_ajax();
};

window.onload = function() {
    // try getting the token from the URL
    LockSession.load_token_from_url();

    // try going and getting the token
    if (LockSession.TOKEN) {
	LockSession.setupPage();
    } else {
	LockSession.getToken();
    }
};
    
