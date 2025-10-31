const axios = require('axios');
const { HttpsProxyAgent } = require('https-proxy-agent');

const BASE_URL = 'https://playground.enoent.org/taskmaitre';

async function debugRequest() {
  const proxyUrl = process.env.https_proxy || process.env.HTTPS_PROXY;
  const httpsAgent = proxyUrl ? new HttpsProxyAgent(proxyUrl) : undefined;

  console.log('=== Environment ===');
  console.log('Proxy URL:', proxyUrl);
  console.log('Target URL:', BASE_URL);
  console.log('\n=== Making Request ===\n');

  const config = {
    method: 'GET',
    url: BASE_URL,
    httpsAgent,
    validateStatus: () => true, // Don't throw on any status
    maxRedirects: 5,
    headers: {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
      'Accept-Language': 'en-US,en;q=0.5',
      'Accept-Encoding': 'gzip, deflate, br',
      'DNT': '1',
      'Connection': 'keep-alive',
      'Upgrade-Insecure-Requests': '1',
      'Sec-Fetch-Dest': 'document',
      'Sec-Fetch-Mode': 'navigate',
      'Sec-Fetch-Site': 'none',
      'Sec-Fetch-User': '?1'
    }
  };

  try {
    console.log('REQUEST HEADERS:');
    console.log(JSON.stringify(config.headers, null, 2));
    console.log('\n');

    const response = await axios(config);

    console.log('RESPONSE STATUS:', response.status, response.statusText);
    console.log('\nRESPONSE HEADERS:');
    console.log(JSON.stringify(response.headers, null, 2));
    console.log('\nRESPONSE DATA:');
    console.log(response.data);

    // Try with access code in query
    console.log('\n\n=== Trying with query parameter ===\n');
    const withQuery = await axios({
      ...config,
      url: BASE_URL + '?access_code=taskmaster2025'
    });
    console.log('Status:', withQuery.status);
    console.log('Data:', withQuery.data);

    // Try with auth header
    console.log('\n\n=== Trying with Authorization header ===\n');
    const withAuth = await axios({
      ...config,
      headers: {
        ...config.headers,
        'Authorization': 'Bearer taskmaster2025'
      }
    });
    console.log('Status:', withAuth.status);
    console.log('Data:', withAuth.data);

    // Try with Basic auth
    console.log('\n\n=== Trying with Basic auth ===\n');
    const withBasic = await axios({
      ...config,
      auth: {
        username: '',
        password: 'taskmaster2025'
      }
    });
    console.log('Status:', withBasic.status);
    console.log('Data:', withBasic.data);

  } catch (error) {
    console.error('ERROR:', error.message);
    if (error.response) {
      console.log('\nERROR RESPONSE STATUS:', error.response.status);
      console.log('ERROR RESPONSE HEADERS:', error.response.headers);
      console.log('ERROR RESPONSE DATA:', error.response.data);
    }
    if (error.request) {
      console.log('\nREQUEST CONFIG:', error.config);
    }
  }
}

debugRequest();
