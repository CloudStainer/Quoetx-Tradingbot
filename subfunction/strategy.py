# strategies.py

import json
import time
import common
from datetime import datetime, timedelta

class VolumeOscillator:
    def __init__(self):
        self.current_bar = None
        self.previous_bar = None
        self.last_update_time = None
        self.bar_color = None
        self.next_trade_time = None
        self.analysis_time = None
        self.last_trade_time = None

    def update_from_data(self, data):
        """Update Volume Oscillator state from WebSocket data"""
        try:
            # Parse volume data from WebSocket message
            volume_data = json.loads('{' + data.split('{', 1)[1].split('#ENDLINE')[0])
            print(volume_data)
            
            if 'volume' in volume_data:
                # Extract the latest volume bar
                latest_bar = volume_data['volume'][-1]
                current_time = datetime.fromtimestamp(latest_bar['time'])
                
                # Calculate oscillator value
                if latest_bar['volume'] > latest_bar['prev_volume']:
                    self.bar_color = 'green'
                else:
                    self.bar_color = 'red'
                
                self.current_bar = {
                    'time': current_time,
                    'color': self.bar_color,
                    'value': latest_bar['volume'] - latest_bar['prev_volume']
                }
                
                return True
        except Exception as e:
            print(f"Error updating Volume Oscillator: {e}")
        return False

    def get_signal(self):
        """Get trading signal based on Volume Oscillator"""
        if not self.current_bar:
            return None
            
        if self.bar_color == 'green':
            return 'call'
        elif self.bar_color == 'red':
            return 'put'
        return None

    def schedule_next_trade(self, current_time):
        """Schedule the next trade time based on current time"""
        # Round to nearest minute
        current_minute = current_time.replace(second=0, microsecond=0)
        
        # Set analysis time to next minute
        self.analysis_time = current_minute + timedelta(minutes=1)
        
        # Set trade execution time to minute after analysis
        self.next_trade_time = self.analysis_time + timedelta(minutes=1)
        
        return self.next_trade_time

def get_minute_start(timestamp):
    """Get the start of the minute for a given timestamp"""
    dt = datetime.fromtimestamp(timestamp)
    return dt.replace(second=0, microsecond=0)

def strategy(user_input, instruments_list, trade_data):
    """
    Main strategy implementation using Volume Oscillator with precise timing
    """
    # Initialize Volume Oscillator if not exists
    if 'volume_oscillator' not in trade_data:
        vo = VolumeOscillator()
    print(vo.get_signal())
    current_time = datetime.now()

    # If in clock time mode
    if user_input['time_option'] == 1:
        
        # If this is the first trade or we need to schedule next trade
        if not vo.next_trade_time:
            vo.schedule_next_trade(current_time)
            return None

        # If we're in analysis period (01:01 in the example)
        if vo.analysis_time and current_time >= vo.analysis_time and current_time < vo.next_trade_time:
            # Get and store the signal for next trade
            signal = vo.get_signal()
            if signal:
                trade_data['next_signal'] = signal
            return None

        # If it's time for the next trade (01:02 in the example)
        if vo.next_trade_time and current_time >= vo.next_trade_time:
            if 'next_signal' in trade_data:
                signal = trade_data['next_signal']
                # Clear stored signal
                del trade_data['next_signal']
                
                # Schedule next analysis and trade times
                vo.schedule_next_trade(current_time)
                
                # Return trade parameters
                return {
                    "asset": trade_data.get('current_asset'),
                    "amount": user_input['bet_amounts'][trade_data['step']],
                    "time": int(vo.next_trade_time.timestamp()),
                    "action": signal,
                    "isDemo": 1 if user_input['account_type'] == 'demo' else 0
                }
    
    return None