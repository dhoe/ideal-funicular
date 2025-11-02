# Semantic Scholar Paper Search

This script uses the [Semantic Scholar API](https://api.semanticscholar.org/) to search for academic papers on emotional regulation in essential tremor.

## Features

- Search the Semantic Scholar database for relevant papers
- Filter results by various fields (title, abstract, authors, year, etc.)
- Display paper details including:
  - Title and authors
  - Publication year and venue
  - Citation count
  - Abstract preview
  - Open access status and PDF links
  - Semantic Scholar URL
- Save results to a timestamped JSON file
- Show summary statistics (total papers, open access percentage, citation averages, etc.)

## Installation

Install dependencies:

```bash
npm install
```

## Usage

### Run the script directly:

```bash
node semantic-scholar-search.js
```

### Or use the npm script:

```bash
npm run search-papers
```

## Configuration

The script can be customized by editing the `main()` function in `semantic-scholar-search.js`:

```javascript
const query = 'emotional regulation essential tremor';  // Change search query
const limit = 50;  // Adjust number of results (max: 100)
```

## Output

The script produces two types of output:

1. **Console output**: Formatted display of search results with paper details
2. **JSON file**: Complete results saved to `semantic-scholar-results-YYYY-MM-DD.json`

## Example Output

```
🔍 Semantic Scholar Paper Search
================================================================================
Query: emotional regulation essential tremor
Limit: 50 papers

Found 42 total papers (showing 42)

1. Emotional Regulation and Essential Tremor: A Systematic Review
--------------------------------------------------------------------------------
Year: 2023
Authors: Smith, J., Jones, A.
Citations: 15
Venue: Journal of Neurology
Open Access: Yes
PDF: https://...
URL: https://www.semanticscholar.org/paper/...

Abstract: This systematic review examines the relationship between...

...

📊 Summary Statistics:
Total papers found: 42
Papers retrieved: 42
Open access papers: 18 (42.9%)
Average citations: 12.3
Year range: 2010 - 2024
```

## API Documentation

This script uses the Semantic Scholar Academic Graph API:
- Endpoint: `https://api.semanticscholar.org/graph/v1/paper/search`
- Documentation: https://api.semanticscholar.org/
- Rate limits: Free tier allows reasonable usage for research purposes
- No API key required for basic searches

## Proxy Support

The script automatically detects and uses proxy settings from environment variables:
- `https_proxy`
- `HTTPS_PROXY`

## Troubleshooting

### 403 Forbidden Error

If you receive a 403 error, it may be due to:
1. Rate limiting (wait a few minutes and try again)
2. Proxy configuration blocking the API
3. Network restrictions

Try:
- Running with a different network connection
- Disabling proxy temporarily (if applicable)
- Reducing the `limit` parameter
- Adding delays between requests

### Module Not Found

If you see "Cannot find module 'axios'", run:
```bash
npm install
```

## Research Topic

This script searches for papers on **emotional regulation in essential tremor**. Essential tremor is a neurological disorder causing involuntary shaking, and understanding emotional regulation in patients can help improve treatment and quality of life.

## License

ISC
