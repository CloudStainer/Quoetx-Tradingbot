import os
import sys
import asyncio
import colorama
import subfunction.sign_in as sign_in
import subfunction.run_browser as run_browser
from termcolor import colored
from playwright.async_api import async_playwright
from playwright._impl._errors import TargetClosedError

# Initialize colorama for Windows
colorama.init()

# Constants
ARGS = sys.argv[1:]
CACHE_DIR = './cache/'
CONFIG_DIR = './config/'
COOKIE_DIR = './cookies/'
RESULT_DIR = './results/'

def print_welcome_message(border_length=77):
    border_line = colored('*' * border_length, 'cyan')
    empty_line = colored('*' + ' ' * (border_length - 2) + '*', 'cyan')
    
    welcome_text = colored('Welcome to ', 'white') + colored('Auto Trading Bot', 'green')
    contact_text = colored('Contact us on ', 'white') + colored('Telegram', 'magenta') + colored(' to implement any strategy on your bot', 'white')

    # Calculate the spaces needed on each side of the centered text
    welcome_spaces = (border_length - 2 - len('Welcome to Auto Trading Bot')) // 2
    contact_spaces = (border_length - 2 - len('Contact us on Telegram to implement any strategy on your bot')) // 2

    # Create welcome and contact lines with proper spacing
    welcome_line = colored('*', 'cyan') + ' ' * welcome_spaces + welcome_text + ' ' * welcome_spaces + colored('*', 'cyan')
    contact_line = colored('*', 'cyan') + ' ' * contact_spaces + contact_text + ' ' * contact_spaces + colored(' *', 'cyan')

    print(border_line)
    print(empty_line)
    print(welcome_line)
    print(empty_line)
    print(contact_line)
    print(empty_line)
    print(border_line)

async def main():
    email = "nayrananda1998@gmail.com"
    password = "Ayush@9028"
    print_welcome_message()
    while True:
        logged = await sign_in.signin(email, password)
        if logged:
            user_input = {
                "account_type": "demo",
                "trading_type": "compounding",
                "bet_level": 3,
                "bet_amounts": [50, 100, 150],
                "financial_instruments": "cryptocurrency",
                "market_type": "otc",
                "time_option": 1,
                "trade_time": 60,
                "minimum_return": 90,
                "trade_option": "random",
                "profit_target": 500,
                "loss_target": 400
            }
            try:
                # Run the browser script
                await run_browser.run_main_script(user_input)
            except TargetClosedError:
                print("Context or page is closed")
            except Exception as e:
                print(f"An error occurred while running the browser script: {e}")
            break # Exit Main loop
        else:
            print(colored('Error connecting to qxbroker.com server.', 'red'))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        print("Done!")
        os._exit(0)