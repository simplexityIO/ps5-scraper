# PS5 Scraper
*Developed in 2021*

Web scraper to notify user when PS5's are available for purchase at retailers.

## READ BEFORE USE
It is advised **NOT** to run this on your personal machine as retailers often do not take kindly if they think they are being scraped by a scalper. In such cases, retailers can choose to block that scalper's IP address from accessing their site for a period of time (potentially even permamently). Running this tool could cause a retailer to mistake the tool for a scalping bot and block access from the machine running the tool. I found good success running this tool from an AWS EC2 instance.

## History
This tool was created during the year following the release of the ninth generation game consoles: the PS5 and Xbox Series X. Even over half a year after its launch, the worldwide chip shortage combined with rampant scalping via bots meant that PS5's were only available for minutes at a time every couple weeks on retailer sites and therefore nearly impossible to purchase. This tool was created to help combat the advantage that scalping bots had over regular people by notifying users of the tool as soon as PS5's became in stock.

## How it works
Once started, the tool scrapes the site for the retailer specified waiting for PS5's to be available for purchase on the site. When the retailer releases new stock of PS5's, the tool will send an SMS to the user to notify them so that they can then attempt to quickly purchase one. The tool will also notify the user via SMS of any crashes it has. The tool will attempt to resume scraping after crashes, but if it crashes 3 times consecutively, it will terminate execution and notify the user via SMS that it has halted.

## Tool parameters
The tool must be supplied with a retailer whose site will be scraped. The current options are Target, Best Buy, and Walmart (though Walmart is currently WIP because they have sophisticated measures in place to prevent scraping). A batch file exists in the root which shows how to run the tool to scrape a particular retailer. There is a global in the tool for the max amount of consecutive crashes the tool will tolerate before it gives up attempting to resume scraping and halts execution. The current value for this global is 3.
