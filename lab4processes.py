# Project Name: Lab 4: Web API access, multithreading, multiprocessing, review of iterables and GUI
# Name :        Yin Chang
# Discription:  The app lets the user choose their news sources,  get the latest headlines from their news sources, and read the news article online.
# Module:       lab4processes.py
# Discription:  multiprocessing

import os
import dotenv
import requests
import tkinter as tk
import tkinter.messagebox as tkmb
import re
import webbrowser
import multiprocessing as mp

'''-------------------Step 1: Fetch data--------------------'''
""" An API call to get the names (and other info of your choosing) of all news sources that are in English and are from the US. """
dotenv.load_dotenv()
url = ('https://newsapi.org/v2/sources?'
       'language=en&'
       'country=us&'
       f'apiKey={os.getenv("API_KEY")}')

page = requests.get(url)
content = page.json()
articlesList = content['sources']
# Create a list of tuple to hold the resource ids and names
resources = [(news['id'], news['name']) for news in articlesList]

'''-------------------Step 2: GUI--------------------'''
""" An API call to get the names (and other info of your choosing) of all news sources that are in English and are from the US. """


class displayWin(tk.Toplevel):  # inherit from tkinter Tk class
    """ A dialog window shows up to let the user chooses countries."""

    def __init__(self, master, newsHeadlines):
        """ A  listbox that can show 10 lines of text. Each line of text is a country name from the database, the list of names are sorted in alphabetical order."""
        super().__init__(master)
        # Create a list of formatted content to be inserted into listbox
        displayContent = ["{} : {}".format(
            line[0], line[1]) for line in newsHeadlines]
        # Create a list of the URLs of headlines
        self._urlList = [line[2] for line in newsHeadlines]

        self.geometry("+100+100")
        # A title
        self.title("Headlines")
        # A Line of instruction
        tk.Label(self, text="Click on a headline to read the article").grid()
        # A listbox of 20 items with a scrollbar
        self._F = tk.Frame(self)
        self._F.grid()
        self._S = tk.Scrollbar(self._F)
        self._LB = tk.Listbox(self._F, height=20, width=120,
                              yscrollcommand=self._S.set)
        self._S.config(command=self._LB.yview)
        self._LB.grid()
        self._S.grid(row=0, column=1, sticky='ns')
        self._LB.insert(tk.END, *displayContent)
        # Ａs the user clicks on a listbox item, call browseNews function
        self._LB.bind('<<ListboxSelect>>', self._browseNews)

        self.protocol("WM_DELETE_WINDOW", self._close)

    def _browseNews(self, event):
        """ A callback function to open a browser tab on user's computer"""
        index = self._LB.curselection()
        webbrowser.open(self._urlList[index[0]])

    def _close(self):
        """ If User click X, clear choice and go back to main window"""
        self._LB.select_clear(0, tk.END)
        self.destroy()


'''-------------------Global Functions for the processes to run--------------------'''


def remove_tags(text):
    """ A function to remove html tag in the headline"""
    TAG_RE = re.compile(r'<[^>]+>')
    return TAG_RE.sub('', text)


def callApi(queue, resourceId):
    """ Make a API call to get the headlines of a chosen news source and put the list of all headlines into queue """
    url = ('http://newsapi.org/v2/top-headlines?sources={}&'
           'pageSize=100&'     # set the number of results to maximum
           f'apiKey={os.getenv("API_KEY")}'.format(resourceId))
    content = requests.get(url).json()
    articles = content['articles']
    nameTitleUrl = [[news['source']['name'], news['title'], news['url']]
                    for news in articles]
    for line in nameTitleUrl:  # Remove html tags in headlines
        line[1] = remove_tags(line[1])
    queue.put(nameTitleUrl)


'''-------------------End of Global Functions Defining--------------------'''


class mainWin(tk.Tk):
    """ A window for user to choose news resources """

    def __init__(self):
        """ Create A listbox of all the news resources """
        super().__init__()
        self._resourceName = [line[1] for line in resources]
        self.title("Latest Headlines")                             # A title
        # A Line of instruction
        tk.Label(self, text="Choose your news resources").grid()
        # A listbox of 20 items with a scrollbar
        self._F = tk.Frame(self)
        self._F.grid()
        self._S = tk.Scrollbar(self._F)
        self._LB = tk.Listbox(self._F, height=20, width=50,
                              selectmode="multiple", yscrollcommand=self._S.set)
        self._S.config(command=self._LB.yview)
        self._LB.grid()
        self._S.grid(row=0, column=1, sticky='ns')
        self._LB.insert(tk.END, *self._resourceName)
        tk.Button(self, text="OK", command=self._processChoice).grid(
            row=3, pady=2)  # click OK to lock the choice

    def _processChoice(self):
        """ Call _callApi function to fetch data and create a topwindow to display news. """
        if self._LB.curselection():  # If the user makes at least one choice, a display window shows up.
            '''-------------------Step 4: Multiprocessing--------------------'''
            self._chosenResources = [resources[index][0]
                                     for index in self._LB.curselection()]
            processes = []                       # Create a list of for child processes
            self._newsHeadlines = []             # Create a container to hold data in queue
            self._queue = mp.Queue()

            # Create processes for each data fetching and put the returned data into queue
            for resourceId in self._chosenResources:
                p = mp.Process(target=callApi, args=(self._queue, resourceId))
                p.start()
                processes.append(p)

            for p in processes:  # Wait for the child processes
                p.join()

            self._newsHeadlines = self._comsumer()
            # Sort the list by resource name
            self._newsHeadlines = sorted(
                self._newsHeadlines, key=lambda x: x[0])
            # Pass the data to a display window
            display = displayWin(self, self._newsHeadlines)

        else:  # Pop up a messagebox window to let the user know they need to select a news source.
            tkmb.showinfo(
                "Note", "Choose one or more news source", parent=self)

    def _comsumer(self):
        """ Get the data from the queue and return the whole list bact to mainWindow  """
        tempL = []
        while not self._queue.empty():
            tempL.extend(self._queue.get())
        return tempL


def main():
    """ A main function to create a main wondow object and run it """
    if __name__ == '__main__':
        mp.set_start_method('spawn')
        a = mainWin()
        a.mainloop()


main()
