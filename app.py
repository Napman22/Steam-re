import creds 
import random
import requests
from bs4 import BeautifulSoup
from steam_web_api import Steam
from flask import Flask, request, render_template, jsonify
import re  


app = Flask(__name__)

key = creds.key
steam = Steam(key)

def extract_steam_id_from_url(url):
    # Match SteamID64 URL
    match = re.match(r'https?://steamcommunity\.com/profiles/(\d+)', url)
    if match:
        return match.group(1)
    
    # Match Custom URL
    match = re.match(r'https?://steamcommunity\.com/id/(\w+)', url)
    if match:
        custom_id = match.group(1)
        return resolve_custom_url_to_steam_id(custom_id)
    
    return None

def resolve_custom_url_to_steam_id(custom_id):
    api_url = f'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={key}&vanityurl={custom_id}'
    response = requests.get(api_url)
    data = response.json()
    
    if data['response']['success'] == 1:
        return data['response']['steamid']
    return None


def unplayedGames(user_id):
    user_games = steam.users.get_owned_games(user_id)
    unplayedGames = []

    if 'games' in user_games:
        for game in user_games['games']:
            playtime = game.get('playtime_forever', 0)  # Get playtime in minutes, default to 0 if not found
            if playtime == 0:
                unplayedGames.append(game)
    
    return unplayedGames

def gameTags(app_id):
    url = f"https://store.steampowered.com/app/{app_id}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    tag_container = soup.find('div', id="glanceCtnResponsiveRight")
    
    if not tag_container:
        return []
    
    tags = tag_container.find_all('a', class_='app_tag')
    tag_list = [tag.text.strip() for tag in tags]
    
    return tag_list

def gamePhotos(app_id):
    url = f"https://store.steampowered.com/app/{app_id}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    tag_container = soup.find('div', id="gameHeaderImageCtn")
    
    if not tag_container:
        return []
    
    photo = tag_container.find_all('img')
    image_urls = []
    for img in photo:
        img_src = img.get('src')
        if img_src:
            img_url = requests.compat.urljoin(url, img_src)
            image_urls.append(img_url)

    return image_urls[0]

def gameDescription(app_id):
    url = f"https://store.steampowered.com/app/{app_id}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    desc_container = soup.find('div', class_="game_description_snippet")
    
    if not desc_container:
        return []
    
    desciption = desc_container.get_text()
    
    print(desciption)
    return desciption

    

@app.route('/', methods=['GET', 'POST'])
def index():
    steam_id = ''
    if request.method == 'POST':
        steam_id = request.form.get('steam_id')
        profile_url = request.form['steam_id']
        user_id = extract_steam_id_from_url(profile_url)
        
        if not user_id:
            return render_template('index.html', error="Invalid Steam profile URL.")
        

        if not unplayedGames(user_id):
            return render_template('index.html', error="No unplayed games found or invalid Steam ID.")
        
        randomGame = random.choice(unplayedGames(user_id))
        app_id = randomGame['appid']
        tags = gameTags(app_id)
        photo = gamePhotos(app_id)
        desc = gameDescription(app_id)

        return render_template('index.html', game=randomGame['name'], 
                               steam_id=steam_id,app_id=app_id, tags=tags if tags else 'No tags found', 
                               photo=photo if photo else 'No Photos found',
                               desc = desc if desc else 'No Description found'
                               )

    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
