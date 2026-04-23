const { Actor } = require('apify');

Actor.main(async () => {
    const input = await Actor.getInput();
    const keyword = input.keyword || 'restaurants in Mumbai';

    // Launch Puppeteer browser
    const browser = await Actor.launchPuppeteer();
    const page = await browser.newPage();

    // Go to Google Maps search page
    const url = `https://www.google.com/maps/search/${encodeURIComponent(keyword)}`;
    await page.goto(url, { waitUntil: 'networkidle2' });

    // Wait for search results to load (adjust selector as needed)
    await page.waitForSelector('div[role="article"]');

    // Extract data from search results
    const results = await page.evaluate(() => {
        const cards = Array.from(document.querySelectorAll('div[role="article"]'));
        return cards.slice(0, 10).map(card => {
            const name = card.querySelector('h3 span')?.textContent || '';
            const address = card.querySelector('span[jsan*="address"]')?.textContent || '';
            return { name, address };
        });
    });

    // Output data
    await Actor.pushData(results);

    await browser.close();
});
