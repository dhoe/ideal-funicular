const axios = require('axios');
const fs = require('fs');
const { HttpsProxyAgent } = require('https-proxy-agent');

// Semantic Scholar API configuration
const SEMANTIC_SCHOLAR_API = 'https://api.semanticscholar.org/graph/v1/paper/search';

/**
 * Search for papers on Semantic Scholar
 * @param {string} query - The search query
 * @param {number} limit - Maximum number of results (default: 100, max: 100)
 * @returns {Promise<Object>} - Search results
 */
async function searchPapers(query, limit = 100) {
  console.log(`Searching Semantic Scholar for: "${query}"\n`);

  // Setup proxy if configured
  const proxyUrl = process.env.https_proxy || process.env.HTTPS_PROXY;
  const httpsAgent = proxyUrl ? new HttpsProxyAgent(proxyUrl) : undefined;

  if (proxyUrl) {
    console.log(`Using proxy: ${proxyUrl}\n`);
  }

  const config = {
    params: {
      query: query,
      limit: limit,
      fields: 'paperId,title,abstract,year,authors,publicationDate,citationCount,url,venue,publicationTypes,isOpenAccess,openAccessPdf'
    },
    headers: {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Accept': 'application/json',
      'Accept-Language': 'en-US,en;q=0.9',
      'Accept-Encoding': 'gzip, deflate, br',
      'Connection': 'keep-alive'
    },
    httpsAgent,
    timeout: 15000,
    validateStatus: (status) => status < 500 // Don't throw on 4xx errors
  };

  try {
    const response = await axios.get(SEMANTIC_SCHOLAR_API, config);

    if (response.status === 403) {
      console.error('❌ Access denied (403). Trying without proxy...\n');

      // Retry without proxy
      const configNoProxy = { ...config, httpsAgent: undefined };
      try {
        const retryResponse = await axios.get(SEMANTIC_SCHOLAR_API, configNoProxy);
        if (retryResponse.status === 200) {
          return retryResponse.data;
        }
      } catch (retryError) {
        console.error('Retry without proxy also failed.');
      }

      throw new Error('Access denied. The Semantic Scholar API may be blocking requests from this network. Try:\n' +
        '  1. Running from a different network\n' +
        '  2. Using an API key (see https://www.semanticscholar.org/product/api)\n' +
        '  3. Accessing the website directly: https://www.semanticscholar.org/');
    }

    if (response.status === 429) {
      throw new Error('Rate limit exceeded. Please wait a few minutes and try again.');
    }

    if (response.status !== 200) {
      throw new Error(`API returned status ${response.status}: ${response.statusText}`);
    }

    return response.data;
  } catch (error) {
    if (error.response) {
      console.error('Error searching Semantic Scholar:', error.message);
      console.error('Status:', error.response.status);
      console.error('Data:', error.response.data);
    } else if (error.request) {
      console.error('Network error:', error.message);
    } else {
      console.error('Error:', error.message);
    }
    throw error;
  }
}

/**
 * Format and display search results
 * @param {Object} results - Search results from Semantic Scholar
 */
function displayResults(results) {
  if (!results.data || results.data.length === 0) {
    console.log('No papers found.');
    return;
  }

  console.log(`Found ${results.total} total papers (showing ${results.data.length})\n`);
  console.log('=' .repeat(80));

  results.data.forEach((paper, index) => {
    console.log(`\n${index + 1}. ${paper.title}`);
    console.log('-'.repeat(80));
    console.log(`Year: ${paper.year || 'N/A'}`);
    console.log(`Authors: ${paper.authors?.map(a => a.name).join(', ') || 'N/A'}`);
    console.log(`Citations: ${paper.citationCount || 0}`);
    console.log(`Venue: ${paper.venue || 'N/A'}`);
    console.log(`Open Access: ${paper.isOpenAccess ? 'Yes' : 'No'}`);
    if (paper.openAccessPdf?.url) {
      console.log(`PDF: ${paper.openAccessPdf.url}`);
    }
    console.log(`URL: ${paper.url || 'N/A'}`);

    if (paper.abstract) {
      const abstractPreview = paper.abstract.substring(0, 200);
      console.log(`\nAbstract: ${abstractPreview}${paper.abstract.length > 200 ? '...' : ''}`);
    }
  });

  console.log('\n' + '='.repeat(80));
}

/**
 * Save results to a JSON file
 * @param {Object} results - Search results
 * @param {string} filename - Output filename
 */
function saveResults(results, filename) {
  const outputPath = `./${filename}`;
  fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
  console.log(`\nResults saved to: ${outputPath}`);
}

/**
 * Main function
 */
async function main() {
  const query = 'emotional regulation essential tremor';
  const limit = 50; // Get up to 50 papers

  try {
    console.log('🔍 Semantic Scholar Paper Search');
    console.log('='.repeat(80));
    console.log(`Query: ${query}`);
    console.log(`Limit: ${limit} papers\n`);

    const results = await searchPapers(query, limit);

    displayResults(results);

    // Save results to file
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `semantic-scholar-results-${timestamp}.json`;
    saveResults(results, filename);

    // Summary statistics
    console.log('\n📊 Summary Statistics:');
    console.log(`Total papers found: ${results.total}`);
    console.log(`Papers retrieved: ${results.data?.length || 0}`);

    if (results.data && results.data.length > 0) {
      const openAccessCount = results.data.filter(p => p.isOpenAccess).length;
      const avgCitations = results.data.reduce((sum, p) => sum + (p.citationCount || 0), 0) / results.data.length;
      const yearsSet = new Set(results.data.map(p => p.year).filter(y => y));

      console.log(`Open access papers: ${openAccessCount} (${(openAccessCount/results.data.length*100).toFixed(1)}%)`);
      console.log(`Average citations: ${avgCitations.toFixed(1)}`);
      console.log(`Year range: ${Math.min(...yearsSet)} - ${Math.max(...yearsSet)}`);
    }

  } catch (error) {
    console.error('\n❌ Failed to complete search:', error.message);
    process.exit(1);
  }
}

// Run the script
if (require.main === module) {
  main();
}

module.exports = { searchPapers, displayResults, saveResults };
