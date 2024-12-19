import time
import json
from subfunction import common
import random
from subfunction import print_table
from termcolor import colored

CACHE_DIR = './cache/'

def get_time_next(seconds):
    ft = int(time.time()) + seconds
    left = ft % 60
    return ft - left if left < 30 else ft + (60 - left)

def format_number(value, decimal_places=2):
    if isinstance(value, float):
        return round(value, decimal_places)
    elif isinstance(value, int):
        return value

def format_strtime(time, suff={}):
    h, remainder = divmod(time, 3600)
    m, s = divmod(remainder, 60)
    return ' '.join(f"{val}{unit}" for val, unit in ((h, suff.get('h', 'H')), (m, suff.get('m', 'M')), (s, suff.get('s', 'sec'))) if val)

def calculate_stats(rows):
    unique_assets, total_amount = set(), 0
    counts = {'call': 0, 'put': 0, 'win': 0, 'loss': 0, 'refund': 0}
    
    for row in rows:
        #row = [strip_ansi(value) if isinstance(value, str) else value for value in row]
        unique_assets.add(row[1])
        try:
            total_amount += row[3]
        except ValueError:
            continue
        if row[5] in counts:
            counts[row[5]] += 1
        if row[6] in counts:
            counts[row[6]] += 1

    average_return = (row[9]*100)/total_amount if total_amount else 0

    return {
        "Total Round": rows[-1][0],
        "Asset": len(unique_assets),
        "Action Call": counts['call'],
        "Action Put": counts['put'],
        "Total Win": counts['win'],
        "Total Loss": counts['loss'],
        "Total Refund": counts['refund'],
        "ACCURACY%": f"{(counts['win']/(counts['win']+counts['loss']))*100}%"
    }

def get_trade_option(user_input):
    if user_input['trade_option'] == 'random':
        return random.choice(['call', 'put'])
    # Else return a specified one
    return user_input['trade_option']

def strategies(user_input={}, instruments_list={}, trade_data={}):

    # Get market type and financial instruments
    market_type = user_input.get('market_type', 'all')
    financial_instruments = user_input.get('financial_instruments', 'all')
    market_type = next(iter(instruments_list)) if market_type == 'all' else market_type
    financial_instruments = next(iter(instruments_list[market_type])) if financial_instruments == 'all' else financial_instruments

    asset_info = instruments_list[market_type][financial_instruments][0]
    asset, asset_return, asset_is_active = asset_info[1], asset_info[18], asset_info[14]

    # Return False if asset is not active or minimum return% not match or an open orders is waiting
    if not asset_is_active or user_input['minimum_return'] > asset_return or trade_data['result'] == '??':
        return False

    trade_option = get_trade_option(user_input)
    #random.choice(['call', 'put']) if user_input['trade_option'] == 'random' else user_input['trade_option']

    is_demo = {'demo':1, 'live':0}[user_input['account_type']]
    bet_level = user_input['bet_level'] - 1

    # Adjust step based on trade result
    if trade_data['result'] == {'martingale':'win','compounding':'loss'}[user_input['trading_type']] or bet_level <= trade_data['step'] and trade_data['result'] in ['win','loss']:
        trade_data['step'] = 0
    elif trade_data['result'] == {'martingale':'loss','compounding':'win'}[user_input['trading_type']]:
        trade_data['step'] += 1

    # Update profit based on the result of the previous trade
    if trade_data.get('orders/open', False) and trade_data['result'] in ['win','loss']:
        trade_data['profit'] += trade_data['closed_order']['profit']

    new_order = {
        "orders/open": {
            "asset": asset,
            "amount": user_input['bet_amounts'][trade_data['step']],
            "time": user_input['trade_time'] if user_input['time_option'] == 100 else get_time_next(user_input['trade_time']),
            "action": trade_option,
            "isDemo": is_demo,
            "tournamentId": 0,
            "requestId": int(time.time())+7,
            "optionType": user_input['time_option']
        },
        "step": trade_data['step'],
        "result": '??',
        "profit": trade_data['profit'],
    }

    # Save new order to cache file
    common.file_put_contents(f'{CACHE_DIR}new_order.json', json.dumps(new_order))

    # Retrieve and update the last orders
    rows = json.loads(common.file_get_contents(f'{CACHE_DIR}orders.json').strip() or '[]')
    print("=======================================")
    if trade_data.get('orders/open', False):
        row = [
            len(rows)+1,
            trade_data['orders/open']['asset'],
            trade_data['closed_order']['percentProfit'],#{'win':trade_data['closed_order']['percentProfit'],'refund':0,'loss':-100}[trade_data['result']],
            trade_data['orders/open']['amount'],
            format_strtime(user_input['trade_time']),
            trade_data['orders/open']['action'],
            trade_data['result'],
            format_number(trade_data['accountBalance']),
            format_number(trade_data['closed_order']['profit']),
            format_number(trade_data['profit']),
        ]
        rows.append(row)

    # Save updated orders to cache file
    common.file_put_contents(f'{CACHE_DIR}orders.json', json.dumps(rows))

    header = ['No', 'Asset', 'Return%', 'Amount', 'Time', 'Action', 'Result', 'accountBalance', 'Profit', 'TotalProfit']
    # Initialize PrettyTablePrint with header
    printer = print_table.PrettyTablePrint(header)
    # Calculate column widths based on rows
    #printer.column_widths = printer.get_column_widths(rows)
    # Set column widths
    printer.column_widths = [7, 17, 7, 7, 7, 7, 7, 15, 7, 15]

    # Print header if it's the first print; otherwise, print the row
    if trade_data.get('orders/open', False):
        row[1] = colored(row[1], {'real':'blue','otc':'cyan'}[market_type])
        row[2] = f'{row[2]}%'#row[2] = colored(f'{row[2]}%', {'positive':'green','zero':'yellow','negative':'red'}[get_sign(row[2])])
        row[5] = colored(row[5], {'call':'green','put':'red'}[row[5]])
        row[6] = colored(row[6], {'win':'green','refund':'yellow','loss':'red'}[row[6]])
        #row[8] = colored(row[8], {'positive':'green','zero':'yellow','negative':'red'}[get_sign(row[8])])
        row[9] = colored(row[9], {'positive':'green','zero':'yellow','negative':'red'}[common.get_sign(row[9])])
        printer.print_row(row)
    else:
        printer.print_header()

    # Print message and exit if targets are reached
    if user_input['profit_target'] <= trade_data['profit'] or trade_data['profit'] <= -user_input['loss_target']:
        # Print the footer
        printer.print_footer()
        # Determine if the profit is positive or not
        isProfit = trade_data['profit'] > 0
        # Determine color and message based on profit
        color = 'green' if isProfit else 'red'
        message = "Profit target reached!" if isProfit else "Loss target reached!"
        print(colored(message, color))
        stats = calculate_stats(json.loads(common.file_get_contents(f'{CACHE_DIR}orders.json').strip() or '[]'))
        for key, value in stats.items():
            print(f"{key}: {value}")
        return ['window.close', True]

    return ['orders/open', new_order['orders/open']]