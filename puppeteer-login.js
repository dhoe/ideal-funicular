const puppeteer = require('puppeteer-core');
const fs = require('fs');

// Configuration
const CONFIG = {
  siteUrl: 'https://playground.enoent.org/taskmaitre',
  accessCode: 'taskmaster2025',
  // You'll need to set this to your Chrome/Chromium executable path
  // Common paths:
  // macOS: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
  // Linux: '/usr/bin/google-chrome' or '/usr/bin/chromium-browser'
  // Windows: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
  chromePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
  headless: process.env.HEADLESS !== 'false', // Set HEADLESS=false to see the browser
  timeout: 30000
};

class TaskMaitreAutomation {
  constructor(config) {
    this.config = config;
    this.browser = null;
    this.page = null;
  }

  async initialize() {
    console.log('Launching browser...');

    try {
      this.browser = await puppeteer.launch({
        executablePath: this.config.chromePath,
        headless: this.config.headless,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--disable-gpu'
        ]
      });

      this.page = await this.browser.newPage();

      // Set a realistic viewport
      await this.page.setViewport({ width: 1920, height: 1080 });

      // Set user agent
      await this.page.setUserAgent(
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      );

      console.log('Browser launched successfully');
      return true;
    } catch (error) {
      console.error('Failed to launch browser:', error.message);
      console.error('\nMake sure you have Chrome/Chromium installed and set the CHROME_PATH environment variable.');
      console.error('Example: CHROME_PATH=/usr/bin/chromium-browser node puppeteer-login.js');
      return false;
    }
  }

  async login() {
    try {
      console.log(`\nNavigating to ${this.config.siteUrl}...`);

      // Navigate to the site
      const response = await this.page.goto(this.config.siteUrl, {
        waitUntil: 'networkidle2',
        timeout: this.config.timeout
      });

      console.log(`Response status: ${response.status()}`);

      if (response.status() === 403) {
        console.error('Received 403 Forbidden. The site might be IP-restricted or require special access.');

        // Take a screenshot for debugging
        await this.page.screenshot({ path: 'access-denied.png' });
        console.log('Screenshot saved as access-denied.png');

        return false;
      }

      // Wait a bit for the page to fully load
      await this.page.waitForTimeout(2000);

      // Take a screenshot of the initial page
      await this.page.screenshot({ path: 'initial-page.png' });
      console.log('Initial page screenshot saved as initial-page.png');

      // Get page title
      const title = await this.page.title();
      console.log(`Page title: ${title}`);

      // Check for input fields that might be the access code field
      const accessCodeSelectors = [
        'input[type="password"]',
        'input[name*="access"]',
        'input[name*="code"]',
        'input[name*="password"]',
        'input[placeholder*="access"]',
        'input[placeholder*="code"]',
        'input[placeholder*="password"]'
      ];

      let accessCodeInput = null;
      for (const selector of accessCodeSelectors) {
        try {
          accessCodeInput = await this.page.$(selector);
          if (accessCodeInput) {
            console.log(`Found access code input using selector: ${selector}`);
            break;
          }
        } catch (e) {
          // Selector not found, continue
        }
      }

      if (!accessCodeInput) {
        console.log('\nNo access code input found. Checking page content...');

        // Get all input fields
        const allInputs = await this.page.$$('input');
        console.log(`Found ${allInputs.length} input field(s) on the page`);

        if (allInputs.length > 0) {
          // Use the first input field as a fallback
          accessCodeInput = allInputs[0];
          const inputType = await accessCodeInput.evaluate(el => el.type);
          const inputName = await accessCodeInput.evaluate(el => el.name);
          console.log(`Using first input field (type: ${inputType}, name: ${inputName})`);
        }
      }

      if (accessCodeInput) {
        console.log(`\nEntering access code...`);
        await accessCodeInput.click();
        await accessCodeInput.type(this.config.accessCode, { delay: 100 });

        // Look for submit button
        const submitSelectors = [
          'button[type="submit"]',
          'input[type="submit"]',
          'button',
          'input[type="button"]'
        ];

        let submitButton = null;
        for (const selector of submitSelectors) {
          const buttons = await this.page.$$(selector);
          if (buttons.length > 0) {
            submitButton = buttons[0];
            console.log(`Found submit button using selector: ${selector}`);
            break;
          }
        }

        if (submitButton) {
          console.log('Clicking submit button...');
          await Promise.all([
            submitButton.click(),
            this.page.waitForNavigation({ waitUntil: 'networkidle2', timeout: this.config.timeout }).catch(() => {
              console.log('No navigation occurred after clicking submit');
            })
          ]);
        } else {
          // Try pressing Enter
          console.log('No submit button found, trying Enter key...');
          await accessCodeInput.press('Enter');
          await this.page.waitForTimeout(2000);
        }

        // Take screenshot after login
        await this.page.screenshot({ path: 'after-login.png' });
        console.log('After-login screenshot saved as after-login.png');

        console.log('Login attempt completed');
        return true;
      } else {
        console.log('Could not find access code input field');

        // Log page content for debugging
        const bodyText = await this.page.evaluate(() => document.body.innerText);
        console.log('\nPage content (first 500 chars):');
        console.log(bodyText.substring(0, 500));

        return false;
      }
    } catch (error) {
      console.error('Error during login:', error.message);

      // Take error screenshot
      try {
        await this.page.screenshot({ path: 'error.png' });
        console.log('Error screenshot saved as error.png');
      } catch (screenshotError) {
        // Ignore screenshot errors
      }

      return false;
    }
  }

  async getProjects() {
    try {
      console.log('\n=== Retrieving Projects ===');

      // Wait for page to load
      await this.page.waitForTimeout(2000);

      // Try to find project elements - adjust selectors based on actual page structure
      const projectSelectors = [
        '.project',
        '[data-testid*="project"]',
        '[class*="project"]',
        '[class*="task"]',
        '.task',
        'li',
        'tr'
      ];

      let projects = [];

      for (const selector of projectSelectors) {
        try {
          const elements = await this.page.$$(selector);
          if (elements.length > 0) {
            console.log(`Found ${elements.length} elements using selector: ${selector}`);

            for (const element of elements) {
              const text = await element.evaluate(el => el.innerText);
              const hasNextTask = text.toLowerCase().includes('next');

              projects.push({
                text: text.trim(),
                hasNextTask,
                selector
              });
            }

            if (projects.length > 0) break;
          }
        } catch (e) {
          // Selector not valid, continue
        }
      }

      if (projects.length === 0) {
        console.log('No projects found with standard selectors.');
        console.log('Analyzing page structure...');

        // Get the page HTML structure
        const structure = await this.page.evaluate(() => {
          const getStructure = (element, depth = 0) => {
            if (depth > 3) return null;
            const tag = element.tagName.toLowerCase();
            const className = element.className;
            const id = element.id;
            const childCount = element.children.length;

            let info = `${'  '.repeat(depth)}<${tag}`;
            if (id) info += ` id="${id}"`;
            if (className) info += ` class="${className}"`;
            info += `> (${childCount} children)`;

            return info;
          };

          const body = document.body;
          const result = [];

          const traverse = (element, depth = 0) => {
            if (depth > 3) return;
            result.push(getStructure(element, depth));
            for (let child of element.children) {
              traverse(child, depth + 1);
            }
          };

          traverse(body);
          return result.join('\n');
        });

        console.log('\nPage structure:');
        console.log(structure);
      }

      return projects;
    } catch (error) {
      console.error('Error retrieving projects:', error.message);
      return [];
    }
  }

  async getProjectsWithoutNextTask() {
    const projects = await this.getProjects();

    const projectsWithoutNext = projects.filter(project => !project.hasNextTask);

    console.log(`\n=== Projects WITHOUT Next Task (${projectsWithoutNext.length}) ===`);
    projectsWithoutNext.forEach((project, index) => {
      console.log(`\n${index + 1}. ${project.text.substring(0, 200)}`);
    });

    // Save results to file
    fs.writeFileSync('projects-without-next-task.json', JSON.stringify(projectsWithoutNext, null, 2));
    console.log('\nResults saved to projects-without-next-task.json');

    return projectsWithoutNext;
  }

  async close() {
    if (this.browser) {
      console.log('\nClosing browser...');
      await this.browser.close();
    }
  }
}

// Main execution
(async () => {
  const automation = new TaskMaitreAutomation(CONFIG);

  try {
    const initialized = await automation.initialize();
    if (!initialized) {
      console.error('\nFailed to initialize browser. Exiting.');
      process.exit(1);
    }

    const loggedIn = await automation.login();
    if (!loggedIn) {
      console.error('\nLogin failed. Check the screenshots for more details.');
    } else {
      await automation.getProjectsWithoutNextTask();
    }
  } catch (error) {
    console.error('Unexpected error:', error);
  } finally {
    await automation.close();
  }
})();
