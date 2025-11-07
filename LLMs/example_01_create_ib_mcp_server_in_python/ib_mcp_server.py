import os
import datetime
import time
import json
from decimal import Decimal
import threading
import argparse
import queue
import readline

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.utils import iswrapper
from ibapi.common import TickerId, OrderId
from ibapi.ticktype import TickTypeEnum
from ibapi.order_state import OrderState

# --- LLM Integration Imports ---
import google.generativeai as genai
from dotenv import load_dotenv

# --- Custom JSON Encoder for Decimal types ---
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)

# --- Helper function for thread-safe printing ---
_print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with _print_lock:
        # Save the current content of the input buffer
        buffer = readline.get_line_buffer()
        # Erase the current line, print the message, then restore the input buffer
        print('\r\x1b[K', end='')
        print(*args, **kwargs)
        print(f"{buffer}", end='', flush=True)




# Get the absolute path of the directory containing the script
script_dir = os.path.abspath(os.path.dirname(__file__))
# Construct the absolute path to the .env file
dotenv_path = os.path.join(script_dir, '.env')
# Load the .env file if it exists, overriding any existing environment variables
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path, override=True)
else:
    safe_print("WARNING: .env file not found. LLM integration may not work if GEMINI_API_KEY is not set elsewhere.")

# --- Configuration ---
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7497
DEFAULT_CLIENT_ID = 1

# --- Global Data Storage ---
account_summary_data = {}
positions_data = {}
latest_prices = {}
historical_data_cache = {}
pnl_data = {}
open_orders_data = {}
next_order_id = -1
order_status_updates = {}
req_id_to_symbol_map = {}
ib_api_errors = {} # To store errors from the IB API

# --- Gemini API Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    safe_print("WARNING: GEMINI_API_KEY environment variable not set. LLM integration will not work.")
else:
    genai.configure(api_key=GEMINI_API_KEY)


class IBKRClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

class IBKRWrapper(EWrapper):
    def __init__(self):
        EWrapper.__init__(self)
        self.nextValidOrderId_event = threading.Event()
        self.historicalData_event = threading.Event()
        self.accountSummary_event = threading.Event()
        self.positions_event = threading.Event()
        self.historical_data_lock = threading.Lock()

    @iswrapper
    def error(self, reqId: TickerId, errorCode: int, errorString: str, contract=None, advancedOrderRejectJson=''):
        global ib_api_errors
        safe_print(f"Error. Id: {reqId}, Code: {errorCode}, Msg: {errorString}")
        ib_api_errors[reqId] = {"errorCode": errorCode, "errorString": errorString}
        if advancedOrderRejectJson:
            safe_print(f"Advanced Order Reject JSON: {advancedOrderRejectJson}")

    @iswrapper
    def nextValidId(self, orderId: OrderId):
        global next_order_id
        next_order_id = orderId
        safe_print(f"Next Valid Order ID received: {orderId}")
        self.nextValidOrderId_event.set()

    @iswrapper
    def managedAccounts(self, accountsList: str):
        safe_print(f"Managed accounts: {accountsList}")

    @iswrapper
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        if account not in account_summary_data:
            account_summary_data[account] = {}
        account_summary_data[account][tag] = value

    @iswrapper
    def accountSummaryEnd(self, reqId: int):
        safe_print(f"Account Summary End. ReqId: {reqId}")
        self.accountSummary_event.set()

    @iswrapper
    def position(self, account: str, contract: Contract, pos: Decimal, avgCost: float):
        if account not in positions_data:
            positions_data[account] = []
        positions_data[account].append({
            "contract": contract.symbol, "secType": contract.secType,
            "exchange": contract.exchange, "position": pos, "avgCost": avgCost
        })

    @iswrapper
    def positionEnd(self):
        safe_print("Position End.")
        self.positions_event.set()

    @iswrapper
    def tickPrice(self, reqId: TickerId, tickType: int, price: float, attrib):
        symbol = req_id_to_symbol_map.get(reqId, f"Unknown_ReqId_{reqId}")
        if reqId not in latest_prices:
            latest_prices[reqId] = {}
        
        tick_name = TickTypeEnum.to_str(tickType)
        latest_prices[reqId][tick_name.lower()] = price
        safe_print(f"Tick Price. ReqId: {reqId} ({symbol}), Type: {tick_name}, Price: {price}")

        if all(k in latest_prices[reqId] for k in ['bid', 'ask', 'last']):
            safe_print(f"Snapshot for {symbol} complete. Cancelling market data.")
            self.cancelMktData(reqId)

    @iswrapper
    def historicalData(self, reqId: int, bar):
        with self.historical_data_lock:
            if reqId not in historical_data_cache:
                historical_data_cache[reqId] = []
            historical_data_cache[reqId].append(bar)

    @iswrapper
    def historicalDataEnd(self, reqId: int, startDateStr: str, endDateStr: str):
        safe_print(f"HistoricalDataEnd. ReqId: {reqId}")
        self.historicalData_event.set()

    @iswrapper
    def orderStatus(self, orderId: OrderId, status: str, filled: Decimal, remaining: Decimal,
                    avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float,
                    clientId: int, whyHeld: str, mktCapPrice: float):
        order_status_updates[orderId] = {
            "status": status, "filled": filled, "remaining": remaining,
            "avgFillPrice": avgFillPrice
        }
        safe_print(f"OrderStatus. Id: {orderId}, Status: {status}, Filled: {filled}, Remaining: {remaining}")

    @iswrapper
    def openOrder(self, orderId: OrderId, contract: Contract, order: Order, orderState: OrderState):
        safe_print(f"OpenOrder. Id: {orderId}, Symbol: {contract.symbol}, Action: {order.action}, Status: {orderState.status}")
        order_key = str(orderId)
        open_orders_data[order_key] = {
            "symbol": contract.symbol,
            "action": order.action,
            "quantity": order.totalQuantity,
            "orderType": order.orderType,
            "status": orderState.status
        }
        order_status_updates[orderId] = {"status": orderState.status}

    @iswrapper
    def openOrderEnd(self):
        safe_print("OpenOrderEnd.")

    @iswrapper
    def pnl(self, reqId: int, dailyPnL: float, unrealizedPnL: float, realizedPnL: float):
        pnl_data[reqId] = {
            "dailyPnL": dailyPnL,
            "unrealizedPnL": unrealizedPnL,
            "realizedPnL": realizedPnL
        }
        safe_print(f"PnL. ReqId: {reqId}, DailyPnL: {dailyPnL}, UnrealizedPnL: {unrealizedPnL}, RealizedPnL: {realizedPnL}")

    @iswrapper
    def connectionClosed(self):
        safe_print("--- IB API Connection Closed ---")
        self.connection_lost = True


class TradingApp(IBKRWrapper, IBKRClient):
    def __init__(self, host, port, client_id):
        IBKRWrapper.__init__(self)
        IBKRClient.__init__(self, wrapper=self)
        self.host = host
        self.port = port
        self.client_id = client_id
        self.req_id_counter = 0
        self.model = None
        self.request_queue = queue.Queue()
        self.is_running = True
        self.connection_lost = False

    def start(self):
        if not self.connect_and_setup():
            return # Initial connection failed, exit

        if GEMINI_API_KEY:
            try:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                safe_print("Gemini model initialized successfully.")
            except Exception as e:
                safe_print(f"Error initializing Gemini model: {e}")
        
        # Start the user input thread
        input_thread = threading.Thread(target=self.user_input_loop, daemon=True)
        input_thread.start()

        self.main_loop()

    def connect_and_setup(self):
        safe_print(f"Connecting to TWS/IB Gateway at {self.host}:{self.port} with Client ID: {self.client_id}...")
        self.connect(self.host, self.port, self.client_id)
        
        api_thread = threading.Thread(target=self.run, daemon=True)
        api_thread.start()

        safe_print("Waiting for connection and next valid order ID...")
        self.nextValidOrderId_event.clear()
        if not self.nextValidOrderId_event.wait(timeout=15):
            safe_print("--- CONNECTION FAILED: Could not get next valid order ID. ---")
            self.disconnect()
            return False

        safe_print("Connection and setup complete.")
        self.initial_data_fetch()
        return True

    def user_input_loop(self):
        while self.is_running:
            try:
                # Use a standard input prompt
                user_input = input("Your trading request: ")
                if user_input:
                    self.request_queue.put(user_input)
                if user_input.lower() == 'exit':
                    self.is_running = False
            except (KeyboardInterrupt, EOFError):
                self.is_running = False
                self.request_queue.put('exit')

    def main_loop(self):
        safe_print("\n--- Entering LLM Interaction Loop ---")
        safe_print("Welcome to the AI Trading Assistant.")
        safe_print("Please type your trading requests below. To exit the server, type 'exit'.")
        
        try:
            while self.is_running:
                if self.connection_lost:
                    self.handle_reconnect()
                    continue

                try:
                    user_request = self.request_queue.get(timeout=1)
                    if user_request.lower() == 'exit':
                        self.is_running = False
                        break
                    
                    if self.model:
                        self.process_user_request_with_llm(user_request)
                    else:
                        safe_print("LLM is not initialized. Cannot process request.")
                except queue.Empty:
                    continue # No user input, continue loop
        except KeyboardInterrupt:
            self.is_running = False
        
        finally:
            safe_print("\nUser interrupted. Shutting down.")
            self.disconnect()
            safe_print("Disconnected from TWS/IB Gateway.")

    def handle_reconnect(self):
        safe_print("\n--- CONNECTION LOST ---")
        max_retries = 5
        retry_delay = 10  # seconds

        for i in range(max_retries):
            safe_print(f"Attempting to reconnect ({i+1}/{max_retries}) in {retry_delay} seconds...")
            time.sleep(retry_delay)
            
            if self.isConnected():
                self.disconnect()
                time.sleep(1)

            if self.connect_and_setup():
                safe_print("--- RECONNECTION SUCCESSFUL ---")
                self.connection_lost = False
                return

        safe_print("--- FAILED TO RECONNECT after multiple attempts. Shutting down. ---")
        self.is_running = False

    def initial_data_fetch(self):
        safe_print("\n--- Fetching Initial Account Data ---")
        self.get_account_info()

        # Wait for the essential data to arrive
        if self.accountSummary_event.wait(timeout=10) and self.positions_event.wait(timeout=10):
            summary = account_summary_data.get(list(account_summary_data.keys())[0], {}) if account_summary_data else {}
            positions = positions_data.get(list(positions_data.keys())[0], []) if positions_data else []

            if not summary and not positions:
                safe_print("No account summary or position data received.")
                return
        else:
            safe_print("--- WARNING: Timed out waiting for initial account data. ---")

    def get_next_req_id(self):
        self.req_id_counter += 1
        return self.req_id_counter

    def get_req_id_for_symbol(self, symbol_key):
        for req_id, symbol in req_id_to_symbol_map.items():
            if symbol == symbol_key:
                return req_id
        return None

    def create_contract(self, symbol, sec_type="STK", exchange="SMART", currency="USD"):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = currency
        return contract

    def get_account_info(self):
        safe_print("Requesting account summary and positions...")
        self.accountSummary_event.clear()
        self.positions_event.clear()
        req_id = self.get_next_req_id()
        self.reqAccountSummary(req_id, "All", "AccountType,NetLiquidation,TotalCashValue,BuyingPower")
        self.reqPositions()

    def get_last_price(self, symbol):
        contract = self.create_contract(symbol)
        req_id = self.get_next_req_id()
        req_id_to_symbol_map[req_id] = symbol
        self.reqMktData(req_id, contract, "", True, False, [])
        safe_print(f"Requested last price for {symbol} (ReqId: {req_id})")

    def get_historical_data(self, symbol, duration_str="10 D", bar_size_setting="1 day"):
        contract = self.create_contract(symbol)
        req_id = self.get_next_req_id()
        req_id_to_symbol_map[req_id] = f"{symbol}_HIST"
        self.historicalData_event.clear()
        self.reqHistoricalData(req_id, contract, "", duration_str, bar_size_setting, "ADJUSTED_LAST", 1, 1, False, [])
        safe_print(f"Requested historical data for {symbol} (ReqId: {req_id})")
        return req_id

    def place_order(self, contract, order):
        global next_order_id
        order.orderId = next_order_id
        self.placeOrder(order.orderId, contract, order)
        safe_print(f"Placed Order ID {order.orderId} for {order.action} {order.totalQuantity} {contract.symbol}")
        next_order_id += 1

    def get_pnl(self):
        # For simplicity, assumes single account.
        account_code = next(iter(account_summary_data), None)
        if not account_code:
            safe_print("Cannot get PnL: Account code not available.")
            return

        req_id = self.get_next_req_id()
        safe_print(f"Requesting PnL for account {account_code} (ReqId: {req_id})")
        self.reqPnL(req_id, account_code, "")
        # PnL data will be printed when it arrives in the `pnl` callback.
        # To make this synchronous for the LLM, we might need an event.
        # For now, we'll let the LLM know the request was sent.

    def get_open_orders(self):
        safe_print("Requesting open orders...")
        open_orders_data.clear() # Clear old data
        self.reqOpenOrders()
        # Data is received asynchronously via openOrder and openOrderEnd.
        # We'll rely on the LLM seeing the printed output for now.

    def cancel_order_by_id(self, order_id: int):
        safe_print(f"Requesting to cancel order ID: {order_id}")
        self.cancelOrder(order_id, "")

    def process_user_request_with_llm(self, user_request: str):
        global ib_api_errors
        safe_print("\n--- Processing request with LLM ---")

        # Check for and include API errors in the context
        error_context = ""
        if ib_api_errors:
            error_context = f"""
        **Recent IB API Errors:**
        The following errors were recently received from the Interactive Brokers API. You MUST inform the user about them and suggest a course of action. For example, if a market data subscription is required, tell the user they need to subscribe. After reporting, the error will be cleared.
        {json.dumps(ib_api_errors)}
        """
            ib_api_errors.clear() # Clear errors after reporting them
        
        # Prune data for clarity
        positions_summary = [f"{pos['position']} shares of {pos['contract']}" for pos_list in positions_data.values() for pos in pos_list]
        open_orders_summary = [f"ID {oid}: {order['action']} {order['quantity']} {order['symbol']} ({order['status']})" for oid, order in open_orders_data.items()]

        prompt_context = f"""
        You are an AI trading assistant. Your primary function is to understand a user's request and respond in a structured JSON format. You have access to the user's account summary, current positions, and open orders.
        {error_context}
        **Available Data:**
        - Account Summary: {json.dumps(account_summary_data, cls=DecimalEncoder)}
        - Positions: {json.dumps(positions_summary)}
        - Open Orders: {json.dumps(open_orders_summary)}

        **Instructions:**
        Based on the user's request, the available data, and ANY RECENT ERRORS, choose one of the following actions. Your capabilities are limited to the actions below. You CANNOT create trading strategies, perform complex financial analysis, or provide investment advice.

        **Priority 1: Handle Errors**
        - If there is a recent error in the "Recent IB API Errors" section, your primary task is to inform the user about it. Use the "answer_question" action to deliver a clear, user-friendly message explaining the error and what they can do about it.

        **Available Actions:**
        1.  **answer_question**: If there is a recent error, use this to explain it. Also use this if the user asks a question that can be answered using the "Available Data" (e.g., "What is my net liquidation value?", "Do I have any positions in AAPL?"). The `response` parameter should contain the direct answer.

        2.  **place_order**: If the user wants to buy or sell a security. To close a position, formulate a SELL order for the entire quantity.

        3.  **get_data**: If the user asks for data that is NOT in the "Available Data" (e.g., "What is the latest price of GOOG?", "Show me my P&L").

        4.  **get_open_orders**: If the user asks to see their current open or working orders.

        5.  **cancel_order**: If the user wants to cancel an existing order. You MUST have the `order_id`. If the `order_id` is not provided in the user's request, you MUST use the "clarify" action to ask for it.

        6.  **clarify**: If the user's request is ambiguous or you need more information to proceed (e.g., asking for an order ID to cancel).
        
        7.  **unsupported_request**: If the user asks for something you cannot do, like creating a trading strategy, performing analysis, or giving advice.

        **JSON Output Structure:**
        - "action": "answer_question" | "place_order" | "get_data" | "get_open_orders" | "cancel_order" | "clarify" | "unsupported_request"
        - "parameters": A dictionary of parameters for the chosen action.

        **Parameter Details:**
        - For "answer_question":
            - "response": (string) The natural language answer to the user's question or a description of an API error.
        - For "place_order":
            - "symbol": (string)
            - "quantity": (integer)
            - "order_type": "MKT" | "LMT"
            - "trade_action": "BUY" | "SELL"
            - "limit_price": (float, optional for LMT orders)
        - For "get_data":
            - "data_type": "price" | "historical" | "pnl"
            - "symbol": (string, required for 'price' and 'historical')
        - For "get_open_orders":
            - No parameters needed.
        - For "cancel_order":
            - "order_id": (integer) The ID of the order to cancel.
        - For "clarify":
            - "response": (string) Your clarifying question to the user.
        - For "unsupported_request":
            - "response": (string) A polite message explaining your limitations.

        **Example Scenarios:**
        - User Request: "What is my buying power?" -> {{{{ "action": "answer_question", "parameters": {{{{ "response": "Your current buying power is [Value from Account Summary]."}}}} }}
        - Recent Error: {{{{ "2": {{{{ "errorCode": 10089, "errorString": "Requested market data requires additional subscription..."}}}} }}}} -> {{{{ "action": "answer_question", "parameters": {{{{ "response": "I couldn't get the market data you requested. It seems you need an additional subscription for it. Please check your Interactive Brokers account settings."}}}} }}}}
        - User Request: "Buy 10 shares of MSFT." -> {{{{ "action": "place_order", "parameters": {{{{ "symbol": "MSFT", "quantity": 10, "order_type": "MKT", "trade_action": "BUY"}}}} }}}}
        - User Request: "Show me my P&L." -> {{{{ "action": "get_data", "parameters": {{{{ "data_type": "pnl"}}}} }}}}
        - User Request: "Cancel order 123." -> {{{{ "action": "cancel_order", "parameters": {{{{ "order_id": 123}}}} }}}}
        - User Request: "Cancel my last order." -> {{{{ "action": "clarify", "parameters": {{{{ "response": "I need the order ID to cancel it. What is the order ID?"}}}} }}}}
        - User Request: "Create a moving average strategy for me." -> {{{{ "action": "unsupported_request", "parameters": {{{{ "response": "I am a simple trading assistant and cannot create complex trading strategies. I can help with account info, placing orders, and getting basic data."}}}} }}}}


        **Current User Request:** "{user_request}"

        JSON Response:
        """
        
        try:
            response = self.model.generate_content(prompt_context)
            llm_json_str = response.text.strip().replace("`", "").replace("json", "")
            # safe_print(f"LLM Response:\n{llm_json_str}") # Suppress raw JSON output
            
            decision = json.loads(llm_json_str)
            self.execute_decision(decision, user_request)

        except Exception as e:
            safe_print(f"Error processing LLM response: {e}")

    def execute_decision(self, decision: dict, original_user_request: str):
        action = decision.get("action")
        params = decision.get("parameters", {})

        if action == "answer_question":
            safe_print(f"LLM: {params.get('response')}")

        elif action == "place_order":
            contract = self.create_contract(params.get("symbol"))
            order = Order()
            order.action = params.get("trade_action")
            order.totalQuantity = int(params.get("quantity"))
            order.orderType = params.get("order_type")
            if order.orderType == "LMT":
                order.lmtPrice = float(params.get("limit_price"))
            self.place_order(contract, order)

        elif action == "get_data":
            data_type = params.get("data_type")
            symbol = params.get("symbol")
            if data_type == "price":
                self.get_last_price(symbol)
            elif data_type == "historical":
                req_id = self.get_historical_data(symbol)
                safe_print(f"Waiting for historical data for {symbol}...")
                if self.historicalData_event.wait(timeout=15):
                    self.process_historical_data(req_id, symbol, original_user_request)
                else:
                    safe_print(f"Timeout waiting for historical data for {symbol}.")
            elif data_type == "pnl":
                self.get_pnl()
        
        elif action == "get_open_orders":
            self.get_open_orders()

        elif action == "cancel_order":
            order_id = params.get("order_id")
            if order_id:
                self.cancel_order_by_id(int(order_id))
            else:
                safe_print("LLM decided to cancel order but provided no ID.")

        elif action == "clarify":
            safe_print(f"LLM: {params.get('response')}")

        elif action == "unsupported_request":
            safe_print(f"LLM: {params.get('response')}")
            
        else:
            safe_print("LLM returned an unknown action.")

    def process_historical_data(self, req_id, symbol, original_user_request=""):
        data = historical_data_cache.get(req_id, [])
        if not data:
            safe_print(f"No historical data found for {symbol}.")
            return

        safe_print(f"\n--- Historical Data for {symbol} (first 10 bars) ---")
        formatted_data = []
        for bar in data[:10]:
            formatted_data.append(f"Date: {bar.date}, Close: {bar.close}")
            safe_print(f"Date: {bar.date}, Open: {bar.open}, High: {bar.high}, Low: {bar.low}, Close: {bar.close}, Volume: {bar.volume}")
        safe_print("--- End of Data ---")

        # Re-engage the LLM with the new data
        safe_print("\n--- Re-engaging LLM with historical data ---")
        prompt_context = f"""
        You are an AI trading assistant. You have just received the following historical data for {symbol}:
        {', '.join(formatted_data)}

        The user's original query was: \"{original_user_request}\"\n        Please provide a natural language summary or answer based on this new data, keeping the original request in mind.

        **Available Data:**
        - Account Summary: {json.dumps(account_summary_data, cls=DecimalEncoder)}
        - Positions: {json.dumps(positions_data, cls=DecimalEncoder)}
        - Newly Fetched Historical Data for {symbol}: {', '.join(formatted_data)}
        
        **Instructions:**
        Formulate a direct answer to the user's likely question about this historical data.

        **JSON Output Structure:**
        {{ 
          "action": "answer_question",
          "parameters": {{
            "response": \"(Your natural language answer here)\" 
          }}
        }}

        JSON Response:
        """
        try:
            response = self.model.generate_content(prompt_context)
            llm_json_str = response.text.strip().replace("`", "").replace("json", "")
            # safe_print(f"LLM Response:\n{llm_json_str}") # Suppress raw JSON output
            
            decision = json.loads(llm_json_str)
            self.execute_decision(decision, original_user_request)

        except Exception as e:
            safe_print(f"Error processing LLM response after historical data: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactive Brokers LLM Trading Assistant")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--client_id", type=int, default=DEFAULT_CLIENT_ID)
    args = parser.parse_args()

    app = TradingApp(args.host, args.port, args.client_id)
    app.start()
