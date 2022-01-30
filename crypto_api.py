# Import the required libraries and dependencies
import os
import pandas as pd
import questionary
from tabulate import tabulate
from MCForecastTools import MCSimulation
import datetime
# import hvplot.pandas
# import matplotlib.pyplot as plt
from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()


# Use Questionary's 'text' option to ask user for their first name
print()
first_name = questionary.text("What's your first name").ask()

# Use Questionary's 'checkbox' option to offer the ability to choose more than one from a list
print()
crypto_set = questionary.checkbox(
    f'{first_name}, please select which cryptos for which you would like to check current pricing:',
    choices=[
        "bitcoin",
        "ethereum",
        "litecoin",
        "solana",
        "cardano",
        "binancecoin"
    ]).ask()
print()

# Get the current prices from CG API
cg_set_result = cg.get_price(ids= crypto_set, vs_currencies='usd')

# Convert the dictionary to pandas dataframe and print using the tabulate module
crytpo_df = pd.DataFrame(cg_set_result)
print("Here's the latest prices:")
print(tabulate(crytpo_df, headers='keys', tablefmt='psql'))
print()

# Select a cryptocurrency to run MC Simulation
coin = questionary.select(
    'Please select a cryptocurrency to run a 2 year simulation based on 3 years of historical data',
    choices=[
        "bitcoin",
        "ethereum",
        "litecoin",
        "solana",
        "cardano",
        "binancecoin"
]).ask()
print()

# Set a variable days to the time period for pulling historical data, and convert to a string
days = str(3*365)

# Get the historical data for the chosen cryptocurrency
response_three_year = cg.get_coin_market_chart_by_id(id=coin, vs_currency='usd', days=days, interval='daily')

# Convert the response to a pandas dataframe
df_three_year = pd.DataFrame(response_three_year)

# Slice the dataframe to yield two columns only: date and closing price
prices_df = pd.DataFrame(df_three_year['prices'].to_list(), columns=['date','close'])

# Convert the Unix timestamp to datetime
prices_df['date'] = pd.to_datetime(prices_df['date'],unit='ms')

# Set the date column to be the index
prices_df.set_index('date')

# Create a two level index with the MultiIndex function so it will pass to MCSimulation
arrays = [[ 'Coin', 'Coin'], ['date','close']]
prices_df.columns=pd.MultiIndex.from_arrays(arrays)

# Configure the Monte Carlo Simulation to forecast two years cumulative returns with 500 samples
MC_two_year = MCSimulation(
  portfolio_data = prices_df,
  weights = [1],
  num_simulation = 500,
  num_trading_days = 365*2
)

# Drop rows that have null values 
MC_two_year.portfolio_data.dropna(inplace=True)

# Run a Monte Carlo simulation to forecast two years cumulative returns
MC_two_year.calc_cumulative_return()
# Visualize the 2-year Monte Carlo simulation by creating an overlay line plot
MC_sim_line_plot = MC_two_year.plot_simulation()
# Save the plot for future use as a PDF file
MC_sim_line_plot.get_figure().savefig("MC_two_year_sim_plot.pdf", bbox_inches="tight")

# Generate summary statistics from the Monte Carlo simulation
# Set the summary statistics equal to a variable for future use
print()
MC_summary_statistics = MC_two_year.summarize_cumulative_return()
print()

# Print the summary statistics Series
print(f'Here are the summary statistics for the 2-year forecast of returns for {coin}:')
print(MC_summary_statistics)

# Forecast the range of values of the crypto portfolio
# Using the lower and upper `95%` confidence intervals from the summary statistics,
# calculate the range of the probable cumulative returns for the current crypto portfolio
investment_amount = 10_000
ci_95_lower_cumulative_return = MC_summary_statistics[8] * investment_amount
ci_95_upper_cumulative_return = MC_summary_statistics[9] * investment_amount
ci_mean_cumulative_return = MC_summary_statistics[1] * investment_amount

# Print results in terms of projected growth of initial `investment amount`
print()
print(f"There is a 95% chance that an initial investment of ${investment_amount:,} in {coin}\n"
  f"over the next 2 years will end within in the range of:\n"
  f"  ${ci_95_lower_cumulative_return:,.0f} and ${ci_95_upper_cumulative_return:,.0f}.")
print()
print(f"The mean forecast would result in your initial investment of ${investment_amount:,} in {coin} yielding a balance of\n"
  f"  ${ci_mean_cumulative_return:,.0f}." )
print()

# Ask the user if they would like to view a PDF file of their simulation plot
view_plot = questionary.confirm(
    'Would you like to see a simulation plot?'
).ask()
if view_plot:
    os.startfile('MC_two_year_sim_plot.pdf')
    print('If your file does not pop up, it should show up in the \n'
      'taskbar at the bottom of your screen. You can just click it to open.')
print()
print('Thank you for using Crypto Forecaster!')