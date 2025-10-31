const axios = require('axios');
const cheerio = require('cheerio');
const { HttpsProxyAgent } = require('https-proxy-agent');

const BASE_URL = 'https://playground.enoent.org/taskmaitre';
const ACCESS_CODE = 'taskmaster2025';

class TaskMaitreClient {
  constructor() {
    const proxyUrl = process.env.https_proxy || process.env.HTTPS_PROXY;
    const httpsAgent = proxyUrl ? new HttpsProxyAgent(proxyUrl) : undefined;

    this.client = axios.create({
      baseURL: BASE_URL,
      headers: {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      },
      maxRedirects: 5,
      withCredentials: true,
      httpsAgent
    });
    this.cookies = {};
  }

  // Helper to manage cookies
  updateCookies(headers) {
    const setCookie = headers['set-cookie'];
    if (setCookie) {
      setCookie.forEach(cookie => {
        const [nameValue] = cookie.split(';');
        const [name, value] = nameValue.split('=');
        this.cookies[name] = value;
      });
    }
  }

  getCookieHeader() {
    return Object.entries(this.cookies)
      .map(([name, value]) => `${name}=${value}`)
      .join('; ');
  }

  async login() {
    try {
      console.log('Attempting to access the site...');

      // First, get the login page
      const initialResponse = await this.client.get('/', {
        validateStatus: () => true // Accept any status code
      });

      this.updateCookies(initialResponse.headers);
      console.log('Initial response status:', initialResponse.status);

      const $ = cheerio.load(initialResponse.data);

      // Look for login form
      const forms = $('form');
      console.log(`Found ${forms.length} form(s) on the page`);

      // Try to find the access code input field
      const accessCodeInput = $('input[name*="access"], input[name*="code"], input[name*="password"], input[type="password"], input[type="text"]').first();

      if (accessCodeInput.length > 0) {
        const inputName = accessCodeInput.attr('name') || 'access_code';
        const formAction = $('form').attr('action') || '/';

        console.log(`Found input field: ${inputName}`);
        console.log(`Form action: ${formAction}`);

        // Submit the access code
        const formData = new URLSearchParams();
        formData.append(inputName, ACCESS_CODE);

        const loginResponse = await this.client.post(formAction, formData, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': this.getCookieHeader()
          },
          validateStatus: () => true,
          maxRedirects: 5
        });

        this.updateCookies(loginResponse.headers);
        console.log('Login response status:', loginResponse.status);

        if (loginResponse.status === 200 || loginResponse.status === 302) {
          console.log('Login successful!');
          return true;
        }
      } else {
        console.log('No access code input found. Site might not require login or structure is different.');
        console.log('Page title:', $('title').text());
        console.log('First 500 chars of body:', $('body').text().substring(0, 500));
      }

      return false;
    } catch (error) {
      console.error('Login error:', error.message);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', error.response.data.substring(0, 500));
      }
      return false;
    }
  }

  async getProjects() {
    try {
      console.log('\nFetching projects...');

      const response = await this.client.get('/', {
        headers: {
          'Cookie': this.getCookieHeader()
        }
      });

      const $ = cheerio.load(response.data);

      // Try to find projects in the page
      // This will need to be adjusted based on the actual HTML structure
      const projects = [];

      // Look for common project selectors
      $('.project, .task, [class*="project"], [class*="task"]').each((i, elem) => {
        const text = $(elem).text().trim();
        if (text) {
          projects.push({
            element: elem.name,
            class: $(elem).attr('class'),
            text: text.substring(0, 100)
          });
        }
      });

      console.log(`Found ${projects.length} potential project elements`);

      // Also log the page structure for debugging
      console.log('\nPage structure:');
      console.log('Title:', $('title').text());
      console.log('Main content classes:', $('main, .main, #main, .content, #content').attr('class'));

      return projects;
    } catch (error) {
      console.error('Error fetching projects:', error.message);
      return [];
    }
  }

  async getProjectsWithoutNextTask() {
    await this.login();
    const projects = await this.getProjects();

    // Filter projects without a next task
    // This logic will need to be refined based on actual HTML structure
    const projectsWithoutNext = projects.filter(project => {
      // Add filtering logic here once we understand the structure
      return true;
    });

    console.log('\nProjects without next task:');
    console.log(JSON.stringify(projectsWithoutNext, null, 2));

    return projectsWithoutNext;
  }
}

// Run the script
(async () => {
  const client = new TaskMaitreClient();
  await client.getProjectsWithoutNextTask();
})();
