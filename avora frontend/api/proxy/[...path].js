import { Buffer } from 'node:buffer';

function removeTrailingSlash(value) {
  return value.replace(/\/+$|^$/g, '');
}

function getRawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

export default async function handler(req, res) {
  const analyticsUrl = process.env.ANALYTICS_SERVICE_URL;
  if (!analyticsUrl) {
    res.statusCode = 503;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ error: 'Analytics proxy not configured. Set ANALYTICS_SERVICE_URL in Vercel.' }));
    return;
  }

  const path = req.url.replace(/^\/api\/proxy/, '') || '/';
  const target = `${removeTrailingSlash(analyticsUrl)}${path}`;

  const headers = { ...req.headers };
  delete headers.host;
  delete headers['content-length'];

  const init = {
    method: req.method,
    headers,
  };

  if (req.method !== 'GET' && req.method !== 'HEAD') {
    init.body = await getRawBody(req);
  }

  try {
    const upstream = await fetch(target, init);
    res.statusCode = upstream.status;
    upstream.headers.forEach((value, name) => {
      if (name.toLowerCase() === 'transfer-encoding') return;
      res.setHeader(name, value);
    });
    const body = await upstream.arrayBuffer();
    res.end(Buffer.from(body));
  } catch (error) {
    res.statusCode = 502;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ error: 'Analytics service unreachable from Vercel.', details: String(error) }));
  }
}
