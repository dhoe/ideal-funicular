# TaskMaitre Automation

Automated login and data extraction for playground.enoent.org/taskmaitre using Puppeteer.

## Features

- Automated login with access code
- Retrieves all projects without a next task
- Takes screenshots at each step for debugging
- Saves results to JSON file
- Supports headless and visible browser modes

## Prerequisites

- Node.js (v14 or higher)
- Chrome or Chromium browser installed

## Installation

1. Install dependencies:
```bash
npm install
```

2. Set up your Chrome path (optional - if Chrome is not in the default location):
```bash
cp .env.example .env
# Edit .env and set your CHROME_PATH
```

## Usage

### Basic usage (headless mode):

```bash
node puppeteer-login.js
```

### With visible browser (for debugging):

```bash
HEADLESS=false node puppeteer-login.js
```

### With custom Chrome path:

```bash
CHROME_PATH=/path/to/chrome node puppeteer-login.js
```

## Configuration

You can modify the configuration directly in `puppeteer-login.js`:

```javascript
const CONFIG = {
  siteUrl: 'https://playground.enoent.org/taskmaitre',
  accessCode: 'taskmaster2025',
  chromePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
  headless: process.env.HEADLESS !== 'false',
  timeout: 30000
};
```

## Output

The script generates the following files:

- `initial-page.png` - Screenshot of the page before login
- `after-login.png` - Screenshot after entering access code
- `error.png` - Screenshot if an error occurs
- `access-denied.png` - Screenshot if access is denied
- `projects-without-next-task.json` - JSON file with extracted projects

## HTTP Client Alternative

If Puppeteer doesn't work in your environment, there's also an HTTP client-based approach:

```bash
node login.js
```

This uses axios + cheerio to make HTTP requests instead of launching a browser. However, it may not work if the site requires JavaScript execution or has complex authentication.

## Troubleshooting

### 403 Access Denied

If you're getting 403 errors:
- The site might be IP-restricted
- Try running from a different network
- Check if the access code has changed
- Verify the site URL is correct

### Chrome/Chromium not found

Set the `CHROME_PATH` environment variable to point to your Chrome installation:

**macOS:**
```bash
export CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

**Linux:**
```bash
export CHROME_PATH="/usr/bin/google-chrome"
# or
export CHROME_PATH="/usr/bin/chromium-browser"
```

**Windows (PowerShell):**
```powershell
$env:CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
```

### Page structure is different

The script tries multiple selectors to find projects. If it doesn't find any:
1. Run with `HEADLESS=false` to see what the page looks like
2. Check the screenshots in the output directory
3. Look at the "Page structure" output in the console
4. Modify the selectors in the `getProjects()` method

## Customization

To customize for different sites or data extraction:

1. **Change the target site:** Modify `CONFIG.siteUrl` and `CONFIG.accessCode`

2. **Adjust login selectors:** Update the `accessCodeSelectors` array in the `login()` method

3. **Modify project extraction:** Update the `projectSelectors` array and filtering logic in `getProjects()`

4. **Change filtering criteria:** Modify the filter in `getProjectsWithoutNextTask()` to match your needs

## Example Output

```
=== Projects WITHOUT Next Task (3) ===

1. Project Alpha - Status: Completed - No upcoming tasks

2. Project Beta - Status: On Hold

3. Project Gamma - Status: Archived
```

## License

ISC
