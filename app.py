import flask
from mcstatus import MinecraftServer
from flask import request, send_file, make_response
import re
import redis
import json
import requests
from imagegeneration import sign, advancement
import datetime
import discord
from flask_cors import CORS


app = flask.Flask("api")
CORS(app)

r = redis.Redis(host='redis')

def jsonify(_dict, status=200, indent=4, sort_keys=True):
  response = make_response(json.dumps(_dict, indent=indent, sort_keys=sort_keys))
  response.headers['Content-Type'] = 'application/json; charset=utf-8'
  response.headers['mimetype'] = 'application/json'
  response.status_code = status
  return response


@app.route('/', methods=['GET'])
def home():
    return "<h1>Obsidion Minecraft API</h1>"



@app.route('/api/v1/server/java', methods=['GET'])
def java():
    if 'server' in request.args:
        server = request.args['server']
    else:
        return "Error: No server or port provided"
    
    if 'port' in request.args:
        port = request.args['port']
        server_r = f"{server}:{port}"
    else:
        server_r = server
        
    if r.exists(server_r):
        data =  json.loads(r.get(server_r))
        return jsonify(data)
    else:
        mc_server = MinecraftServer.lookup(server_r)

        try:
            query = mc_server.status()
            data = vars(query)
            data['version'] = vars(data['version'])
            data['players'] = vars(data['players'])
            if "extra" in data["description"]:
                # when they use this other format
                motd = ""
                for var in data["description"]["extra"]:
                    motd += var["text"]
            elif "text" in data["description"]:
                motd = data["description"]["text"]
            else:
                motd = data["description"]
            data['description'] = re.sub(r"(§.)", "", motd).strip()
            names=[]
            if data['players']['sample']:
                for player in data["players"]["sample"]:
                    names.append({'name': re.sub(r"(§.)", "", player.name), 'id': player.id})
                data["players"]["sample"] = names
            data['success'] = True
            data["cachetime"] = str(datetime.datetime.now(datetime.timezone.utc).timestamp())
            r.set(server_r, json.dumps(data), ex=600)
            return jsonify(data)
        except Exception as e:
            raise e
            return jsonify({'success': False}), 501

@app.route('/api/v1/server/bedrock', methods=['GET'])
def bedrock():
    if 'server' in request.args:
        server = request.args['server']
    else:
        return "Error: No server or port provided" 
        
    port = int(request.args['port']) if 'port' in request.args else 19132
    if r.exists(f"{server}:{port}"):
        data =  json.loads(r.get(f"{server}:{port}"))
    else:
        mc_server = MinecraftServer.lookup(f"{server}:{port}")
        try:
            query = mc_server.query()
            data = vars(query)
            data['software'] = vars(data['software'])
            data['players'] = vars(data['players'])
            data["cachetime"] = str(datetime.datetime.now(datetime.timezone.utc).timestamp())
            r.set(f"{server}:{port}", json.dumps(data), ex=600)
        except Exception as e:
            data = {'success': False}
            return jsonify(data), 501

    return jsonify(data)


@app.route('/api/v1/mojang/check', methods=['GET'])
def m_status():
    sites=["www.minecraft.net/en-us", "account.mojang.com", "authserver.mojang.com", "api.mojang.com", "textures.minecraft.net"]
    status = {}   
    for site in sites:
        response = requests.get(f"https://{site}")
        status[site] = "green" if response.status_code == requests.codes.ok else "red" 
    return jsonify(status)
    
    

@app.route('/api/v1/profile/<uuid>', methods=['GET'])
def profile(uuid):
    if r.exists(uuid):
        data = json.loads(r.get(uuid))
        print(r.ttl(uuid))
    else:
        legacy = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}").json()
        data = {'names': requests.get(f"https://api.mojang.com/user/profiles/{uuid}/names").json()}
        if 'legacy' in legacy['properties'][0]:
            data['legacy'] =  True
        else:
            data['legacy'] = False
        data["cachetime"] = str(datetime.datetime.now(datetime.timezone.utc).timestamp())
        r.set(uuid, json.dumps(data), ex=86400)
    return jsonify(data)


@app.route('/api/v1/images/sign', methods=['GET'])
def create_sign():
    line1 = request.args['line1'] if 'line1' in request.args else ""
    line2 = request.args['line2'] if 'line2' in request.args else ""
    line3 = request.args['line3'] if 'line3' in request.args else ""
    line4 = request.args['line4'] if 'line4' in request.args else ""
    return sign(line1, line2, line3, line4)

@app.route('/api/v1/images/advancement', methods=['GET'])
def create_advancement():
    item = request.args['item'] if 'item' in request.args else None
    title = request.args['title'] if 'title' in request.args else None
    text = request.args['text'] if 'text' in request.args else None
    return advancement(item, title, text)

@app.route('/api/v1/permissions', methods=['GET'])
def get_permissions():
    permission = request.args['permission'] if 'permission' in request.args else None
    perms = discord.Permissions(int(permission))
    response = {"permissions": []}

    for perm, value in perms:
        response["permissions"].append([perm, value])
    response = flask.jsonify(response)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


# @app.route('/api/v1/images/splashtext', methods=['GET'])
# def create_splashtext():
#     text = request.args['text'] if 'text' in request.args else None
#     return splashtext(text)

# @app.route('/api/v1/images/deathmessage', methods=['GET'])
# def create_death_message():
#     xp = request.args['xp'] if 'item' in request.args else None
#     text = request.args['text'] if 'text' in request.args else None
#     return death_message(xp, text)



if __name__ == '__main__':
      app.run(host='0.0.0.0', port=3000)