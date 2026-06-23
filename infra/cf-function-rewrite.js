function isNum(s, n) {
  if (s.length !== n) return false;
  for (var i = 0; i < s.length; i++) {
    var c = s.charCodeAt(i);
    if (c < 48 || c > 57) return false;
  }
  return true;
}

function handler(event) {
  var req = event.request;
  var host = (req.headers.host && req.headers.host.value) || "";

  // Canonical host: redirect www -> apex
  if (host === "www.short-stack.net") {
    var qs = "";
    if (req.querystring && Object.keys(req.querystring).length) {
      var parts = [];
      for (var k in req.querystring) {
        parts.push(k + "=" + req.querystring[k].value);
      }
      qs = "?" + parts.join("&");
    }
    return {
      statusCode: 301,
      statusDescription: "Moved Permanently",
      headers: { "location": { "value": "https://short-stack.net" + req.uri + qs } }
    };
  }

  var uri = req.uri;

  // Old Ghost dated permalinks -> flat slug:
  //   /YYYY/MM/DD/slug/  or  /YYYY/MM/slug/   ->   /slug/
  var seg = uri.split("/");
  if (seg[seg.length - 1] === "") seg.pop();   // drop trailing slash
  var dated =
    (seg.length === 5 && isNum(seg[1], 4) && isNum(seg[2], 2) && isNum(seg[3], 2)) ||
    (seg.length === 4 && isNum(seg[1], 4) && isNum(seg[2], 2));
  if (dated) {
    return {
      statusCode: 301,
      statusDescription: "Moved Permanently",
      headers: { "location": { "value": "/" + seg[seg.length - 1] + "/" } }
    };
  }

  // Clean URLs -> index.html
  if (uri.endsWith("/")) {
    req.uri = uri + "index.html";
  } else if (!uri.includes(".")) {
    req.uri = uri + "/index.html";
  }
  return req;
}
