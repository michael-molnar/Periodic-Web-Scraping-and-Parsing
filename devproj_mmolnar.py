"""
Periodically Web Scraping PR Newswire and Yahoo Finance 
AIDI 1100 - Final Project

Michael Molnar
100806823
"""

# Import needed libraries 
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
import requests 
from bs4 import BeautifulSoup
import yfinance as yf 
import os 
from pynput import keyboard
import time
from datetime import date

# Create to global variables
# baseurl is to simplify web requests  
global baseurl
baseurl = 'https://www.prnewswire.com/'

# latest_href will keep track of the most recent processed news article
global latest_href 
latest_href = ''

"""
initial_run will be called upon starting of the module 
This will ensure the plots folder exists and then will retrieve the most recent 
news article on PR Newsire.  It will parse this article for its details,
print them and append to a csv file.  It will return two things - the symbols 
contained in the article and the title of the article.  It also sets
latest_href to be this article so future scans know what has already been proceseed.  
"""
def initial_run():
    # On first run, create "Plots" folder if it does not exist
    # This program can be restarted at any time, so check if it already exists
    if not os.path.exists('Plots'):
	    os.makedirs('Plots')

    # Request the content of PR Newswire News Release List
    page = requests.get('https://www.prnewswire.com/news-releases/news-releases-list/', timeout=1000)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Find the most current news artic;e       
    article = soup.find('a', attrs={'class':'news-release'})
    # Extract its hrf 
    url = article.attrs['href']
    # Extract its title
    title = article.text
    
    # Request and parse the article
    page2 = requests.get(baseurl + url)
    soup2 = BeautifulSoup(page2.text, 'html.parser')

    # Extract the publcation date
    results = soup2.find_all('p', attrs={'class':'mb-no'})
    day = results[0].text

    # Extract all symbols from the article 
    results2 = soup2.find_all('a', attrs={'class':'ticket-symbol'})
    # Create a list for if there is more than one
    symbols = []
    for symbol in results2:
        symbols.append(symbol.text)
    # Remove any publicates
    symbols = set(symbols)

    # Set symbols to None if there were none
    if not symbols:
        symbols = None

    # Create a dictionary for the newest article 
    newest_dict = {'Title' : title,
              'URL' : url,
              'Date' : day,
              'Symbols' : symbols
             }
    # Turn into a DataFrame and append to the csv file 
    # The tile will be created here if it does not already exist 
    article_data = pd.DataFrame(newest_dict, index=[0])
    article_data.to_csv('article_data.csv', mode='a', index=False, header=False)

    # Update the global variable latest_href as a reference point
    global latest_href 
    latest_href = url

    # Print the summary to the screen
    print("Title: ", title)
    print('Date: ', day)
    print('Stock Symbols Mentioned: ', symbols)
    print('\n')
    
    return symbols, title

"""
This function will be called on each scan.  It requests and parses the news article
list and extracts all of the hrefs.  It returns a list of these. 
"""
def get_new_news():

    # After the initial run, make a new request to the article list
    to_add_page = requests.get('https://www.prnewswire.com/news-releases/news-releases-list/')
    to_add_soup = BeautifulSoup(to_add_page.content, 'html.parser')
    # Find all articles on the main page
    to_add_articles = to_add_soup.find_all('a',attrs={'class':'news-release'})
    # Get the hrefs for each and append to a list
    to_add_hrefs = []
    for article in to_add_articles:
        to_add_hrefs.append(article.attrs['href'])

    # Return this list for use in check_if_new
    return to_add_hrefs

"""
This function will take as input the return of get_new_news.  It creates a new list - 
to_process - by checking each of the hrefs against the last processed article.  
It is processing from newest to oldest, so as soon as it reaches that, it discards the rest.
It returns the list of hrefs that have not yet been processed.  
"""
def check_if_new(article_list): 

    # Check to see if the articles in the list have already been processed
    to_process = []
    
    if article_list:
        for url in article_list:
        # If it has not, add it to list and move on
            if url != latest_href:
                to_process.append(url)
            else:
           # As soon as you reach an already parsed article, stop 
               break
    if to_process:
        print('There is new news!\n')

    else:
        print('There is no new news\n')
    # Return the list of hrefs to be processed 
    return to_process

"""
This function takes as input the list of hrefs that have not been processed yet.  
For each of these it requests and parses the article.  It extracts all of the desired
information - title, publication date, and stock symbols.  Since articles may 
contain zero, one, or more stock symbols - with duplication in some cases - this 
ensures that only the unique values are kept.  A dictionary is created for each href,
all of which are returned as a list.  
"""
def get_details(to_process_list):
    new_data = []
    # For each article to be processed, create a dictionary
    for entry in to_process_list:
        dict_new = {}
        # Request and parse the article
        page3 = requests.get(baseurl + entry, timeout=1000)
        soup3 = BeautifulSoup(page3.text, 'html.parser')
        
        # The title is located in h1   
        h1 = soup3.h1
        title = h1.contents[0].strip()
        dict_new['Title'] = title
        # The URL was in the element of to_process_list
        dict_new['URL'] = entry

        # The date is located in the class "mb-no"      
        results3 = soup3.find_all('p', attrs={'class':'mb-no'})
        dict_new['Date'] = results3[0].text

        # Ticket symbols are located in the class "ticket-symbol"    
        results4 = soup3.find_all('a', attrs={'class':'ticket-symbol'})

        # Creating a list of unique symbols in teh article
        symbols = []
        for symbol in results4:
            symbols.append(symbol.text)
        # Remove duplicates
        symbols = set(symbols)

        # If there are no symbols, set the value to None
        if not symbols:
            symbols = None
        
        dict_new['Symbols'] = symbols
        # Append this article's dictionary to the list    
        new_data.append(dict_new)
    # Return the list of dictionaries 
    return new_data

"""
This function is called if the scan found new articles to be processed.  It takes the 
list of dictionaries and creates a data frame of them.  Before appending to the csv 
file it reverses the data frame, ensuring that the csv is written continuously from 
oldest to newest.  Finally it resets latest_href to be the newest of these 
unprocessed articles.  
"""
def store_articles(article_dicts):
    # Take the list of dictionaries and convert to dataframe 
    new_articles = pd.DataFrame(article_dicts)
    # Reverse so that proper order is maintained in the csv
    new_articles = new_articles[::-1]
    # Append to "article_data.csv"
    new_articles.to_csv('article_data.csv', mode='a', index=False, header=False)

    # Set the new latest href to be the newest unprocessed article
    global latest_href
    latest_href = new_articles['URL'][0]

    # Return the dataframe
    return new_articles

"""
This function takes as input a stock symbol.  It uses yfinance to retrieve the historic 
stock information for it.  What returns is a data frame, and a column is added to 
include the stock symbol.  The data is appended to a second csv file and then dataframe
is returned.  
"""
def get_tickers(sym):

    # Use yfinance to retrieve historical stock information by symbol 
    stock = yf.Ticker(sym)
    # Get the history for the past five days
    stock_hist = stock.history(period='5d')
    # A data frame is created, so create a new column containing the stock symbol
    stock_hist['Symbol'] = sym

    # Append to csv file
    stock_hist.to_csv('stock_data.csv', mode='a', header=False)

    # Return the dataframe for plotting
    return stock_hist

"""
This functon takes three inputs - the data frame created by the get_tickers function, 
and the symbol and article title from the dictionary created by get_details.  It creates 
two subplots - one displaying opens and closes for the last five days, the other
showing volume for the same timeframe.  The article title is printed above the plot
and the symbol is used in the plot titles.  Plots are displayed on screen for 10 
seconds and then saved to the Plots folder - named according to their symbol and 
today's date.  
"""
def make_plots(stocks_df, sym, headline):
        
    fig = plt.figure(figsize=(15,5))
    # The first subplot consists of the opens as closes for the stock over the last five days
    # These are plotted as lines on the same axis
    ax1 = fig.add_subplot(1,2,1)
    ax1.plot(stocks_df['Open'], color='blue', marker='o', label='Opens')
    ax1.plot(stocks_df['Close'], color='red', marker='o', label='Closes')
    ax1.set_title('"{}" Opens and Closes (last 5 days)'.format(sym))
    ax1.set_ylabel ('Price ($)', fontsize=12)
    ax1.legend(loc='best')
    plt.xticks(stocks_df.index, rotation=20)
    
    # The second subplot is the volume over the last five days
    ax2 = fig.add_subplot(1,2, 2)
    ax2 = plt.plot(stocks_df['Volume'], color='black', marker='o')
    ax2 = plt.ticklabel_format(style='plain', axis='y')
    ax2 = plt.title('"{}" Volumes (last 5 days)'.format(sym))
    plt.xticks(stocks_df.index, rotation=20)

    # Add the title of the article to the top of the plot
    plt.text(0.5, 0.98, 'Headline: {}'.format(headline),
    ha='center', va='top', transform=fig.transFigure, fontsize=10)

    # Instead of having the user close the plot for the code to continue, 
    # I show the plot for 10 seconds and then close it automatically.
    plt.show(block=False)
    plt.pause(10)
    plt.close()

    # Get today's date for file naming - format with underscores
    today = date.today()
    today = today.strftime('%m_%d_%Y')

    # Save the plot with the stock symbol and today's date for future reference
    fig.savefig('Plots\{}_{}.png'.format(sym, today))



if __name__ == "__main__":
    # Upon running the module a welcome is printed to the user  
    print('...............')
    print('Hello!')
    print('I will scan PR Newswire every minute and show you new stock information!')
    print("Plots will be saved with stock symbols and today's date")
    # Inform the user how to stop the program 
    print('Press "ESC" at any time to quit')
    print('...............')
    print('\nHere is the latest article:\n')
    
    # Run the initial scan 
    syms, title = initial_run()
    if not syms:
        pass
    # If the latest article contains stock symbols, get history and plot each
    else:
        for sym in syms:
            stock_history = get_tickers(sym)
            make_plots(stock_history, sym, title)

    # Enter the main body of the program 
    # Set break_program to allow it to run continuously 
    break_program = False
    
    """
    This function resolves allowing the user to stop the scan.
    If the user pressers the "ESC" key, a message is printed and break_program is 
    set to true, ending the program.  All other key presses are ignored.  
    """
    def on_press(key):
        global break_program
        if key == keyboard.Key.esc:
            print ('Shutting down....')
            print('Bye!')
            break_program = True
            return False

    # Set a keyboard listener using the above function 
    with keyboard.Listener(on_press=on_press) as listener:
        # Get the starting time 
        start = time.time()
        # Enter the main loop 
        while break_program == False:
            # Since the program will loop continuously, add a tiny sleep here to 
            # prevent the CPU from consuing resources 
            time.sleep(0.25)
            # Check the current time
            current = time.time() 
            # If one minute has passed since the last scan, it is time to scan again 
            if current > (start + 60):
                print('Scanning....')  
                
                # For each scan, first get the articles
                new_articles = get_new_news()
                # Then check for which are unprocessed 
                unprocessed = check_if_new(new_articles)
                # Then get the details of these
                new_details = get_details(unprocessed)
                # If there are new articles, store the details to the csv file
                if new_details:
                    store_articles(new_details)

                # For each of the unprocessed articles, print the details 
                for detail in new_details:
                    title = detail['Title']
                    day = detail['Date']
                    syms = detail['Symbols']
                    print("Title: ",title)
                    print('Date: ', day)
                    print('Stock Symbols Mentioned: ', syms)
                    print('\n')
                    # Check if the article contained any stock symbols
                    if not syms:
                        pass
                    else:
                        # If it did, for each stock symbol get the info and make the plots
                        for sym in syms:
                            stock_history = get_tickers(sym)
                            make_plots(stock_history, sym, title)

                # Lastly, reset the start time at the completion of this scan
                start = time.time()
            # If one minute has not passed since the last scan, do nothing
            else:
                continue
    
        listener.join()
