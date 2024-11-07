import pandas as pd
import csv as csv

#portfolio_summary_path = 'cqa_portfolio/PortfolioSummary_12_8_2023.csv'
portfolio_summary_path = './PortfolioSummary_10_31_2024.csv'
open_positions_path = './OpenPosition_10_31_2024.csv'

with open(portfolio_summary_path, 'r') as file:
    portfolio_summary_head = [next(file) for _ in range(5)]
with open(open_positions_path, 'r') as file:
    open_positions_head = [next(file) for _ in range(5)]

print(f"Summary Head (5): {portfolio_summary_head}, Open Positions (5): {open_positions_head}")

open_positions_df = pd.read_csv(open_positions_path)


with open(portfolio_summary_path, 'r') as file:
    for _ in range(5):  # Skip the first 5 lines
        next(file)
    portfolio_summary_head = [next(file) for _ in range(5)]

print(f"Summary Head (Next 5){portfolio_summary_head}, Open DF: {open_positions_df.head()}")


# Function to handle uneven number of elements in a line for the Portfolio Summary file
# def process_line_safe(line):
#     elements = [elem.replace('"', '').strip() for elem in line.split(',') if elem.strip() != '']
#     if len(elements) % 2 != 0:  # Ensure an even number of elements
#         #print(f"Line: {line}, Elements: {elements}")
#         return {}
#     return {elements[i]: elements[i + 1] for i in range(0, len(elements), 2)}
#
#
portfolio_summary_data = {}
# with open(portfolio_summary_path, 'r') as file:
#     for _ in range(5):  # Skip the first 5 lines
#         next(file)
#     for line in file:
#         print(line)
#         line_data = process_line_safe(line)
#         print(f"Processed Line: {line_data}")
#         portfolio_summary_data.update(line_data)



def process_line_csv(line):
    # Create a CSV reader which will handle the commas inside quotes correctly
    reader = csv.reader([line])
    line_elements = next(reader)  # Parse the line into list elements
    # Create a dictionary by pairing up elements (key, value)
    return {line_elements[i].strip(): line_elements[i + 1].strip() for i in range(0, len(line_elements), 2)}

# Use this function to process lines from the CSV
with open(portfolio_summary_path, 'r') as file:
    # Skip the metadata lines
    for _ in range(5):
        next(file)
    # Read and process the remaining lines
    for line in file:
        line_data = process_line_csv(line)
        portfolio_summary_data.update(line_data)


print(list(portfolio_summary_data.keys()))


# Convert the Portfolio Summary data into a DataFrame
portfolio_summary_df = pd.DataFrame([portfolio_summary_data])

# Convert 'MarketValue' to a float for calculations in Open Positions DataFrame
open_positions_df['MarketValue'] = open_positions_df['MarketValue'].replace('[\$,]', '', regex=True).astype(float)

# Define compliance checks based on the rules
# Split 'Trades Made/Allowed' into two separate integers
trades_made, trades_allowed = map(int, portfolio_summary_data['Trades Made/Allowed:'].split('/'))
trade_limit_compliance = trades_made <= trades_allowed

# Count the number of unique stocks in long and short positions
unique_stocks_long = open_positions_df[open_positions_df['Quantity'] > 0]['Symbol'].nunique()
unique_stocks_short = open_positions_df[open_positions_df['Quantity'] < 0]['Symbol'].nunique()
stocks_count_compliance = (unique_stocks_long >= 40) and (unique_stocks_short >= 40)

# Check for stock prices above $5
stock_price_compliance = all(open_positions_df['LastPrice'] >= 5)


# Function to safely convert string values to float
def safe_convert_to_float(value):
    if isinstance(value, str):
        return float(value.replace('$', '').replace(',', '').strip())
    return value

# Print out the keys to identify the correct ones
print("Keys in portfolio summary data:", portfolio_summary_data.keys())

# Access the 'Portfolio Value' and 'Cash Balance' using the correct keys from the print statement
# You need to replace 'Portfolio Value' and 'Cash Balance' with the correct keys from your print output
portfolio_value_key = next((key for key in portfolio_summary_data.keys() if 'Portfolio Value:' in key), None)
cash_balance_key = next((key for key in portfolio_summary_data.keys() if 'Cash Balance:' in key), None)

if portfolio_value_key and cash_balance_key:
    portfolio_value = safe_convert_to_float(portfolio_summary_data[portfolio_value_key])
    cash_balance = safe_convert_to_float(portfolio_summary_data[cash_balance_key])
    cash_percentage = (cash_balance / portfolio_value) * 100
else:
    print("Correct keys for portfolio value and cash balance not found in the dictionary")

print(portfolio_summary_data['Portfolio Value:'])

# Convert 'Portfolio Value' and 'Cash Balance' to floats for calculations
portfolio_value = safe_convert_to_float(portfolio_summary_data['Portfolio Value:'])
cash_balance = safe_convert_to_float(portfolio_summary_data['Cash Balance:'])
cash_percentage = (cash_balance / portfolio_value) * 100

# Check for cash compliance (no more than 5% weight in cash)
cash_compliance = cash_percentage <= 5

# Check for maximum position weight compliance (no position should exceed 5% of the portfolio value)
position_weights = (open_positions_df['MarketValue'].abs() / portfolio_value) * 100
max_position_weight_compliance = all(position_weights <= 5)
print(f"max_position_weight_compliance: {max_position_weight_compliance}")
if max_position_weight_compliance is False:
    for i, weight in enumerate(position_weights):
        if weight >= 5:
            print(f"WEIGHTS TO BE REBALANCED: {open_positions_df['Symbol'][i]}: {weight}")

# Calculate the dollar neutrality ratio
long_market_value = open_positions_df[open_positions_df['Quantity'] > 0]['MarketValue'].sum()
short_market_value = open_positions_df[open_positions_df['Quantity'] < 0]['MarketValue'].sum()
dollar_neutrality_ratio = long_market_value / -short_market_value

# Compile all the compliance checks into a dictionary
compliance_checks = {
    'Trade Limit Compliance': trade_limit_compliance,
    'Stock Count Compliance': stocks_count_compliance,
    'Stock Price Compliance': stock_price_compliance, #This only matters for initial purchases
    'Cash Compliance': cash_compliance,
    'Max Position Weight Compliance': max_position_weight_compliance,
    'Dollar Neutrality Ratio': dollar_neutrality_ratio
}

print(compliance_checks)
