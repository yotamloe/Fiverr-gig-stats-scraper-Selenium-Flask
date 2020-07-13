import os
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import csv
from selenium.webdriver.chrome.options import Options
from flask import Flask, redirect, url_for, render_template, request, send_file


def get_data(url, data, options):
    # init driver
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.get(url)

    # get title
    title = driver.find_element_by_class_name("text-display-3").text

    # get about this gig
    about_this_gig = driver.find_element_by_class_name("description-content").text

    # get average rating score
    try:
        avg_rating = driver.find_element_by_class_name("total-rating-out-five").text
        avg_rating = float(avg_rating)
    except:
        print("no ratings yet")
        avg_rating = 0

    # get number of reviews
    try:
        num_of_ratings = driver.find_element_by_class_name("total-rating").text
        num_of_ratings = num_of_ratings.replace(")", "")
        num_of_ratings = num_of_ratings.replace("(", "")
    except:
        print("no ratings at all")
        num_of_ratings = 0

    # get number of likes
    try:
        likes = driver.find_element_by_class_name("collect-count").text
    except:
        likes = 0

    # get data from the pricing section
    pricing_tab = driver.find_element_by_class_name("package-content").text
    pricing_tab = pricing_tab.split('\n')
    plan = pricing_tab[0]
    price = pricing_tab[1]
    price = price.replace("₪", "")
    description = pricing_tab[2]
    delivery = pricing_tab[3]

    # append records
    data['Title'].append(title)
    data['About'].append(about_this_gig)
    data['Likes'].append(likes)
    data['Avg rating'].append(avg_rating)
    data['Num of reviews'].append(num_of_ratings)
    data['Plan'].append(plan)
    data['Price'].append(price)
    data['Plan desc'].append(description)
    data['Delivery'].append(delivery)

    driver.quit()


def set_up_driver_options():
    WINDOW_SIZE = "100,100"
    chrome_options = Options()
    chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
    return chrome_options


def find_all_gigs(source_url, chrome_options):
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.get(source_url)
    urls = driver.find_elements_by_css_selector(".text-display-7 a")
    links = []
    for url in urls:
        links.append(url.get_attribute("href"))
    driver.quit()
    return links


app = Flask(__name__)

@app.route("/")
def home():
    return render_template('home.html')

@app.route('/', methods=['POST'])
def my_form_post():
    source_url = request.form['source_url']
    chrome_options = set_up_driver_options()
    gigs = find_all_gigs(source_url, chrome_options)

    # set up data structure
    data = {'id': [], 'Title': [], 'About': [], 'Likes': [], 'Avg rating': [], 'Num of reviews': [],
            'Plan': [], 'Price': [], 'Plan desc': [], 'Delivery': []}

    # append records loop
    i = 0
    for url in gigs:
        data['id'].append(i)
        get_data(url, data, chrome_options)
        i += 1

    print(data)
    table = pd.DataFrame.from_dict(data)
    stats = table.copy()
    stats.drop(columns=['About'])
    table.to_csv('data.csv', index=False)
    stats.drop(columns=['About']).to_json('data.json',orient='table')

    return render_template('download.html')

@app.route('/downloadcsv')
def download_csv():
    return send_file('data.csv', as_attachment=True)

@app.route('/downloadjson')
def download_json():
    return send_file('data.json', as_attachment=True)


if __name__ == "__main__":
    app.run(host=os.getenv('IP', '0.0.0.0'), debug=True,
            port=int(os.getenv('PORT', 4444)))
