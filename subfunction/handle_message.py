import json
import subfunction.common as common
import datetime
import subfunction.strategies as strategies
from termcolor import colored
# import matplotlib.pyplot as plt
CACHE_DIR = './cache/'
CONFIG_DIR = './config/'

def rebuild_instruments(data):
    result = {'real': {}, 'otc': {}}
    
    for item in data:
        
        key1 = 'real' if item[11] == 0 else 'otc'
        key2 = item[3]
        if key2 not in result[key1]:
            result[key1][key2] = []
        result[key1][key2].append(item)
        # common.file_put_contents("instruments.json", result)
    
    # Sort each group by index 14 (bool) and index 18
    for key1 in result:
        for key2 in result[key1]:
            result[key1][key2].sort(key=lambda x: (x[14], x[18]), reverse=True)
    
    # Sort each category by the maximum value of index 18 in each group
    result['otc'] = dict(sorted(result['otc'].items(), key=lambda x: x[1][0][18], reverse=True))
    result['real'] = dict(sorted(result['real'].items(), key=lambda x: x[1][0][18], reverse=True))
    
    # Sort result categories 'otc' and 'real' by the maximum value of index 18
    #result = dict(sorted(result.items(), key=lambda x: next(iter(x[1].values()))[0][18], reverse=True))
    result = dict(sorted(result.items(), key=lambda x: x[1][list(x[1].keys())[0]][0][18], reverse=True))
    return result

async def main_script(window, event, message):
    new_order_file = f'{CACHE_DIR}new_order.json'
    if event == '↓':
        if all(s in message for s in ['"deals":[{"id":"', '"openTime":"', '"closeTime":"', '"profit":', '"percentProfit":', '"percentLoss":', '"closeMs":']):
            closed_order = json.loads('{' + common.gstrb ('{', '#ENDLINE', message))
            trade_data = json.loads(common.file_get_contents(new_order_file).strip() or '{"step": 0, "result": "?", "profit": 0}')
            if closed_order['deals'][0]['id'] == trade_data['opened_order']['id']:
                trade_data['closed_order'] = closed_order['deals'][0]
                trade_data['accountBalance'] += trade_data['closed_order']['profit']
                trade_data['result'] = 'win' if trade_data['closed_order']['profit'] > 0 else 'loss' if trade_data['closed_order']['profit'] < 0 else 'refund'
                trade_data['trade_state'] = 'analyzing'
                common.file_put_contents(new_order_file, json.dumps(trade_data))
                print(trade_data)

        elif all(s in message for s in ['"id":"', '"openTime":"', '"closeTime":"', '"profit":', '"percentProfit":', '"percentLoss":', '"accountBalance":', '"requestId":']):
            opened_order = json.loads('{' + common.gstrb ('{', '#ENDLINE', message))
        
            trade_data = json.loads(common.file_get_contents(new_order_file).strip() or '{"step": 0, "result": "?", "profit": 0}')
            # print(opened_order['requestId'], trade_data['orders/open']['requestId'])
            if opened_order['requestId'] == trade_data['orders/open']['requestId']:
                trade_data['accountBalance'] = opened_order['accountBalance']
                trade_data['opened_order'] = opened_order
                common.file_put_contents(new_order_file, json.dumps(trade_data))
    
        elif ',"AUDCAD","AUD/CAD","currency",' in message and ',"XAUUSD_otc","Gold (OTC)","commodity",' in message:
            instruments_list = '[' + common.gstrb ('[', '#ENDLINE', message)
            instruments_list = rebuild_instruments(json.loads(instruments_list))
            common.file_put_contents (f'{CONFIG_DIR}instruments_list.json', json.dumps(instruments_list))
            user_input = json.loads(common.file_get_contents (f'{CONFIG_DIR}user_input.json'))
            trade_data = json.loads(common.file_get_contents(new_order_file).strip() or '{"step": 0, "result": "?", "profit": 0}')
            open_order = strategies.strategies(user_input, instruments_list, trade_data)
            if open_order and open_order[0] == 'orders/open':
                return ['orders/open', json.dumps(open_order, separators=(',', ':'))]
            elif open_order and open_order[0] == 'window.close':
                await window.close()
            else:
                return ['console.log', f'Message received and handled: {message}']

       
    elif event == '↑':
        #print(f"[Socket:] => {int(time.time())} - {u_arrow}: {message}")
        return ['console.log', f'Message received and handled: {message}']