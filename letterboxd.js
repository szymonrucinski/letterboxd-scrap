/**
 * Letterboxd Movie Fetcher
 * Fetches movies from a Letterboxd profile using RSS feeds and web scraping.
 */

/**
 * @typedef {Object} Film
 * @property {string} title - Film title
 * @property {string|null} year - Release year
 * @property {string|null} rating - Star rating (e.g., "★★★★★")
 * @property {string|null} watchDate - Date watched
 * @property {string|null} link - Letterboxd URL
 * @property {boolean} rewatch - Whether it was a rewatch
 */

/**
 * Fetch watched films from RSS feed (includes ratings and watch dates)
 * @param {string} username - Letterboxd username
 * @returns {Promise<Film[]>}
 */
export async function fetchRecentActivity(username) {
  const url = `https://letterboxd.com/${username}/rss/`;
  const response = await fetch(url);
  const xml = await response.text();

  const films = [];
  const itemRegex = /<item>([\s\S]*?)<\/item>/g;
  let match;

  while ((match = itemRegex.exec(xml)) !== null) {
    const item = match[1];

    const titleMatch = item.match(/<title><!\[CDATA\[(.*?)\]\]><\/title>/) ||
                       item.match(/<title>(.*?)<\/title>/);
    const linkMatch = item.match(/<link>(.*?)<\/link>/);
    const descMatch = item.match(/<description><!\[CDATA\[([\s\S]*?)\]\]><\/description>/);

    if (!titleMatch) continue;

    const fullTitle = titleMatch[1];
    const titleYearMatch = fullTitle.match(/^(.+),\s*(\d{4})$/);

    const title = titleYearMatch ? titleYearMatch[1] : fullTitle;
    const year = titleYearMatch ? titleYearMatch[2] : null;

    let rating = null;
    let rewatch = false;
    let watchDate = null;

    if (descMatch) {
      const desc = descMatch[1];
      const ratingMatch = desc.match(/★+½?/);
      if (ratingMatch) rating = ratingMatch[0];
      rewatch = desc.includes('Rewatched');
      const dateMatch = desc.match(/Watched on\s+\w+\s+(\w+\s+\d+,\s+\d{4})/);
      if (dateMatch) watchDate = dateMatch[1];
    }

    films.push({
      title,
      year,
      rating,
      watchDate,
      link: linkMatch ? linkMatch[1] : null,
      rewatch
    });
  }

  return films;
}

/**
 * Fetch all watched films by scraping the films page
 * @param {string} username - Letterboxd username
 * @returns {Promise<Film[]>}
 */
export async function fetchWatchedFilms(username) {
  const films = [];
  let page = 1;

  while (page <= 50) {
    const url = `https://letterboxd.com/${username}/films/page/${page}/`;
    const response = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' }
    });

    if (!response.ok) break;

    const html = await response.text();
    const pageFilms = parseFilmsPage(html);

    if (pageFilms.length === 0) break;

    films.push(...pageFilms);
    page++;
  }

  return films;
}

/**
 * Fetch films from user's watchlist
 * @param {string} username - Letterboxd username
 * @returns {Promise<Film[]>}
 */
export async function fetchWatchlist(username) {
  const films = [];
  let page = 1;

  while (page <= 20) {
    const url = `https://letterboxd.com/${username}/watchlist/page/${page}/`;
    const response = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' }
    });

    if (!response.ok) break;

    const html = await response.text();
    const pageFilms = parseFilmsPage(html);

    if (pageFilms.length === 0) break;

    films.push(...pageFilms);
    page++;
  }

  return films;
}

/**
 * Parse films from Letterboxd HTML page
 * @param {string} html - HTML content
 * @returns {Film[]}
 */
function parseFilmsPage(html) {
  const films = [];
  const pattern = /data-target-link="(\/film\/[^"]+\/)"[^>]*>[\s\S]*?<img[^>]*alt="([^"]+)"/g;
  let match;

  while ((match = pattern.exec(html)) !== null) {
    const link = match[1];
    const title = decodeHtmlEntities(match[2]);

    films.push({
      title,
      year: null,
      rating: null,
      watchDate: null,
      link: `https://letterboxd.com${link}`,
      rewatch: false
    });
  }

  return films;
}

/**
 * Decode HTML entities
 * @param {string} str
 * @returns {string}
 */
function decodeHtmlEntities(str) {
  const entities = {
    '&#039;': "'",
    '&amp;': '&',
    '&lt;': '<',
    '&gt;': '>',
    '&quot;': '"'
  };
  return str.replace(/&#039;|&amp;|&lt;|&gt;|&quot;/g, m => entities[m]);
}

// Default export for convenience
export default {
  fetchRecentActivity,
  fetchWatchedFilms,
  fetchWatchlist
};
