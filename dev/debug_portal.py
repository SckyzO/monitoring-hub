import asyncio

from playwright.async_api import async_playwright


async def debug_portal():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Listen for console logs and errors
        errors = []
        page.on(
            "console",
            lambda msg: print(f"CONSOLE: {msg.text}") if msg.type == "error" else None,
        )
        page.on("pageerror", lambda exc: errors.append(exc))

        print("🔍 Navigating to local portal...")
        try:
            await page.goto("http://localhost:8080/index_v2.html", wait_until="load")
            # Wait a bit for charts to animate
            await asyncio.sleep(2)

            # Take a screenshot for context (optional, I can't see it but can be useful for you)
            await page.screenshot(path="debug_screenshot.png")

            if errors:
                print(f"❌ Found {len(errors)} JavaScript errors:")
                for err in errors:
                    print(f"  - {err}")
            else:
                print("✅ No critical JavaScript errors found during load.")

        except Exception as e:
            print(f"Failed to connect to portal: {e}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_portal())
