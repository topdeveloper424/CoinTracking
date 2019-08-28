from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
import time
from datetime import datetime
from ctapi import CTAPI


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

TRADES_RANGE_NAME = 'Trades!A2:N'
BALANCES_RANGE_NAME = 'Balances!A2:I'
SUMMARY_RANGE_NAME = 'Historycal Summary!A2:E'
CURRENCY_RANGE_NAME = 'Historical Currency!A2:D'
GROUP_RANGE_NAME = 'Grouped Balance!A2:D'
GAINS_RANGE_NAME = 'Gains!A2:I'

class CoinTracker():
    def __init__(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.


        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('sheets', 'v4', credentials=creds)
        self.sheet = service.spreadsheets()
        self.sheet_id = None
        with open("setting.json") as f:
            settings = json.load(f)
            api_key = settings["api_key"]
            api_secret = settings["api_secret"]
            self.sheet_id = settings["sheet_id"]



        self.api = CTAPI(api_key, api_secret)


    def scrape_trades(self):
        trades = self.api.getTrades()
        trade_list = []
        if trades['success']:
            for t in trades['result']:
                if t != 'success' and t != 'method':
                    row = trades['result'][t]
                    item = []
                    item.append(row['buy_amount'])
                    item.append(row['buy_currency'])
                    item.append(row['sell_amount'])
                    item.append(row['sell_currency'])
                    item.append(row['fee_amount'])
                    item.append(row['fee_currency'])
                    item.append(row['type'])
                    item.append(row['exchange'])
                    item.append(row['group'])
                    item.append(row['comment'])
                    item.append(row['imported_from'])
                    item.append(row['time'])
                    item.append(row['imported_time'])
                    item.append(row['trade_id'])
                    trade_list.append(item)
        else:
            print("got no orders")
        body = {
            'values':trade_list
        }
        self.sheet.values().clear(spreadsheetId=self.sheet_id, range=TRADES_RANGE_NAME, body={}).execute()
        time.sleep(1)
        self.sheet.values().append(spreadsheetId=self.sheet_id,range=TRADES_RANGE_NAME,valueInputOption="USER_ENTERED", body=body).execute()
    def scrape_balances(self):
        balance_list = []
        balances = self.api.getBalance()
        if balances['success'] == 1:
            details = balances['result']['details']
            for key in details:
                balance = details[key]
                item = []
                item.append(balance['coin'])
                item.append(balance['amount'])
                item.append(balance['value_fiat'])
                item.append(balance['value_btc'])
                item.append(balance['price_fiat'])
                item.append(balance['price_btc'])
                item.append(balance['change1h'])
                item.append(balance['change24h'])
                item.append(balance['change7d'])
                item.append(balance['change30d'])
                balance_list.append(item)
        body = {
            'values':balance_list
        }
        self.sheet.values().clear(spreadsheetId=self.sheet_id, range=BALANCES_RANGE_NAME, body={}).execute()
        time.sleep(1)
        self.sheet.values().append(spreadsheetId=self.sheet_id,range=BALANCES_RANGE_NAME,valueInputOption="USER_ENTERED", body=body).execute()
    
    def scrape_summary(self):
        summary_list = []
        summaries = self.api.getHistoricalSummary()
        if summaries['success'] == 1:
            result = summaries['result']['historical']
            coins = result['Coins']
            currencies = result['Currencies']
            commodities = result['Commodities']
            total = result["Total"]
            key_array = []
            for key in coins:
                key_array.append(key)
            key_array.sort(reverse = True)
            for key in key_array:
                coin_row = coins[key]
                currency_row = currencies[key]
                commodity_row = commodities[key]
                total_row = total[key]

                st_time = int(key)
                time_obj = datetime.fromtimestamp(st_time)
                time_str = time_obj.strftime("%m/%d/%Y %H:%M:%S")
                item = []
                item.append(time_str)
                item.append(coin_row)
                item.append(currency_row)
                item.append(commodity_row)
                item.append(total_row)
                summary_list.append(item)

        body = {
            'values':summary_list
        }
        self.sheet.values().clear(spreadsheetId=self.sheet_id, range=SUMMARY_RANGE_NAME, body={}).execute()
        time.sleep(1)
        self.sheet.values().append(spreadsheetId=self.sheet_id,range=SUMMARY_RANGE_NAME,valueInputOption="USER_ENTERED", body=body).execute()
    def scrape_currency(self):
        currency_list =[]
        currencies = self.api.getHistoricalCurrency()
        if currencies['success'] == 1:
            result = currencies['result']['historical']
            for key in result:
                history = result[key]
                key_array = []
                for t in history:
                    key_array.append(t)
                key_array.sort(reverse = True)
                for t in key_array:
                    row = history[t]
                    item = []
                    st_time = int(t)
                    time_obj = datetime.fromtimestamp(st_time)
                    time_str = time_obj.strftime("%m/%d/%Y %H:%M:%S")
                    item.append(time_str)
                    item.append(row['amount'])
                    item.append(row['fiat'])
                    item.append(row['btc'])
                    currency_list.append(item)
        body = {
            'values':currency_list
        }
        self.sheet.values().clear(spreadsheetId=self.sheet_id, range=CURRENCY_RANGE_NAME, body={}).execute()
        time.sleep(1)
        self.sheet.values().append(spreadsheetId=self.sheet_id,range=CURRENCY_RANGE_NAME,valueInputOption="USER_ENTERED", body=body).execute()


    def scrape_grouped(self):
        group_list = []
        groups = self.api.getGroupedBalance()
        if groups['success'] == 1:
            detail = groups['result']['details']
            for group in detail:
                group_row = detail[group]
                for currency in group_row:
                    row = group_row[currency]
                    print(row)
                    item = []
                    item.append(group)
                    item.append(currency)
                    if 'amount' in row:
                        item.append(row['amount'])
                    else:
                        item.append('')
                    if 'fiat' in row:
                        item.append(row['fiat'])
                    else:
                        item.append('')
                    if 'btc' in row:
                        item.append(row['btc'])
                    else:
                        item.append('')
                    group_list.append(item)
        body = {
            'values':group_list
        }
        self.sheet.values().clear(spreadsheetId=self.sheet_id, range=GROUP_RANGE_NAME, body={}).execute()
        time.sleep(1)
        self.sheet.values().append(spreadsheetId=self.sheet_id,range=GROUP_RANGE_NAME,valueInputOption="USER_ENTERED", body=body).execute()


    def scrape_gains(self):
        gains_list = []
        gains = self.api.getGains()
        if gains['success'] == 1:
            detail = gains['result']['gains']
            for key in detail:
                row = detail[key]
                item = []
                item.append(row['coin'])
                item.append(row['amount'])
                item.append(row['cost_per_unit'])
                item.append(row['current_price'])
                item.append(row['change_percent'])
                item.append(row['cost'])
                item.append(row['current_value'])
                item.append(row['unrealized'])
                item.append(row['realized'])
                gains_list.append(item)
        body = {
            'values':gains_list
        }
        self.sheet.values().clear(spreadsheetId=self.sheet_id, range=GAINS_RANGE_NAME, body={}).execute()
        time.sleep(1)
        self.sheet.values().append(spreadsheetId=self.sheet_id,range=GAINS_RANGE_NAME,valueInputOption="USER_ENTERED", body=body).execute()



    def start_scrape(self):
        self.scrape_trades()
        self.scrape_balances()
        self.scrape_summary()
        self.scrape_currency()
        self.scrape_grouped()
        self.scrape_gains()


def main():
    tracker = CoinTracker()
    tracker.start_scrape()
    
if __name__ == "__main__":main()
    

