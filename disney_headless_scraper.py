#!/usr/bin/env python3
"""
Disney Cruise Line Headless Browser Scraper
Scrapes actual pricing for October 2026 7-night double dip cruises
"""

import asyncio
import json
import re
from playwright.async_api import async_playwright

async def scrape_disney_cruises():
    """Scrape Disney cruise website using headless browser"""

    results = {
        "october_2026_7night_double_dips": [],
        "scraped_prices": [],
        "errors": []
    }

    async with async_playwright() as p:
        # Launch browser with stealth settings
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        page = await context.new_page()

        try:
            print("Navigating to Disney Cruise Line website...")

            # Try the cruise search page
            await page.goto(
                'https://disneycruise.disney.go.com/cruises-destinations/list/',
                wait_until='networkidle',
                timeout=60000
            )

            print("Page loaded, waiting for content...")
            await page.wait_for_timeout(3000)

            # Get page content
            content = await page.content()
            print(f"Page content length: {len(content)}")

            # Try to find cruise cards or listings
            cruise_elements = await page.query_selector_all('[class*="cruise"], [class*="itinerary"], [class*="card"]')
            print(f"Found {len(cruise_elements)} potential cruise elements")

            # Try to search for October 2026 cruises
            print("\nLooking for date/month filters...")

            # Check for any filter dropdowns
            filters = await page.query_selector_all('select, [class*="filter"], [class*="dropdown"]')
            print(f"Found {len(filters)} filter elements")

            # Get all text content for analysis
            all_text = await page.inner_text('body')

            # Look for October 2026 mentions
            oct_matches = re.findall(r'October\s*\d{1,2}.*?2026|Oct\s*\d{1,2}.*?2026', all_text, re.I)
            if oct_matches:
                print(f"Found October 2026 references: {oct_matches[:5]}")
                results['october_references'] = oct_matches[:10]

            # Look for price patterns
            prices = re.findall(r'\$[\d,]+(?:\.\d{2})?', all_text)
            if prices:
                print(f"Found prices: {prices[:10]}")
                results['prices_found'] = list(set(prices))[:20]

            # Look for 7-night mentions
            seven_night = re.findall(r'7[- ]?night.*?(?:Bahamas|Caribbean|double|dip)', all_text, re.I)
            if seven_night:
                print(f"Found 7-night references: {seven_night[:5]}")
                results['seven_night_references'] = seven_night[:10]

            # Try to take a screenshot for debugging
            await page.screenshot(path='disney_cruise_page.png')
            print("Screenshot saved to disney_cruise_page.png")

            # Try a direct search URL for October 2026
            print("\nTrying direct search for October 2026...")
            search_url = 'https://disneycruise.disney.go.com/cruises-destinations/list/?destinationType=caribbean&ships=disney-dream&startDate=2026-10-01&endDate=2026-10-31'

            await page.goto(search_url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(3000)

            search_content = await page.inner_text('body')

            # Look for cruise listings
            cruise_cards = await page.query_selector_all('[class*="cruise-card"], [class*="itinerary-card"], [data-cruise]')
            print(f"Found {len(cruise_cards)} cruise cards in search results")

            for i, card in enumerate(cruise_cards[:5]):
                try:
                    card_text = await card.inner_text()
                    results['scraped_prices'].append({
                        'index': i,
                        'text': card_text[:500]
                    })
                except Exception as e:
                    pass

            # Save page content for analysis
            with open('disney_page_content.txt', 'w') as f:
                f.write(search_content[:50000])
            print("Page content saved to disney_page_content.txt")

        except Exception as e:
            error_msg = f"Error during scraping: {str(e)}"
            print(error_msg)
            results['errors'].append(error_msg)

        finally:
            await browser.close()

    return results

async def search_specific_cruise():
    """Try to find the specific Oct 2-9 Disney Dream sailing"""

    results = {"cruise_details": None, "errors": []}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        page = await context.new_page()

        try:
            # Try different URLs for the specific cruise
            urls_to_try = [
                # General search with filters
                'https://disneycruise.disney.go.com/cruises-destinations/list/?ships=disney-dream&startDate=2026-10-01&endDate=2026-10-15',
                # Bahamas cruises
                'https://disneycruise.disney.go.com/cruises-destinations/list/?destinationType=bahamas&startDate=2026-10-01&endDate=2026-10-31',
            ]

            for url in urls_to_try:
                print(f"\nTrying: {url}")
                try:
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    await page.wait_for_timeout(2000)

                    content = await page.inner_text('body')

                    # Look for October 2 sailing
                    if 'October 2' in content or 'Oct 2' in content:
                        print("Found October 2 reference!")

                        # Extract surrounding context
                        matches = re.findall(r'.{0,100}October 2.{0,200}', content, re.I | re.S)
                        for match in matches[:3]:
                            print(f"Context: {match}")
                            results['cruise_details'] = match

                    # Look for prices
                    prices = re.findall(r'\$[\d,]+', content)
                    if prices:
                        print(f"Prices found: {prices[:5]}")
                        results['prices'] = prices[:10]

                except Exception as e:
                    print(f"Error with {url}: {e}")
                    continue

        except Exception as e:
            results['errors'].append(str(e))

        finally:
            await browser.close()

    return results

async def main():
    print("=" * 60)
    print("Disney Cruise Line Headless Browser Scraper")
    print("=" * 60)
    print()

    # Run main scrape
    results = await scrape_disney_cruises()

    # Run specific search
    specific = await search_specific_cruise()
    results['specific_search'] = specific

    # Save results
    with open('headless_scrape_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print("Results saved to headless_scrape_results.json")
    print("=" * 60)

    return results

if __name__ == "__main__":
    asyncio.run(main())
