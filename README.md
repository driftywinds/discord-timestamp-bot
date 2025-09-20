## Dynamic Discord Timestamp bot for Discord - Generate and use Discord's dynamic timestamps

Says what it does, you can try it out here - [https://003274.xyz/discord-timestamps](https://003274.xyz/discord-timestamps)

[![Pulls](https://img.shields.io/docker/pulls/driftywinds/twitchrise-bot.svg?style=for-the-badge)](https://img.shields.io/docker/pulls/driftywinds/twitchrise-bot.svg?style=for-the-badge)

Also available on Docker Hub - [```driftywinds/discord-timestamp-bot:latest```](https://hub.docker.com/repository/docker/driftywinds/discord-timestamp-bot/general)

### How to use: - 

1. Download the ```compose.yml``` and ```example.env``` files from the repo [here](https://github.com/driftywinds/discord-timestamp-bot).
2. Go to [Discord Developer Portal](https://discord.com/developers/applications) and register a new application. Go to the ```Installation``` section and enable these permissions on top of ```applications.commands``` =
  - ```Send Messages```
  - ```Use Slash Commands```
  - ```Send Links```
3. Go to the ```Bot``` section and enable all 3 ```Privileged Gateway Intents```.
4. Click on ```Reset Token``` and copy the new token generated.
5. Rename the ```example.env``` file from the repo to ```.env``` and replace the value of ```DISCORD_BOT_TOKEN``` with the one you just copied.
6. Run ```docker compose up -d```.
7. Go back to the ```Installation``` section and copy the ```Install Link``` to install your bot as an app or into a server.

<br>

You can check logs live with this command: - 
```
docker compose logs -f
```
### For dev testing: -
- have python3 installed on your machine
- clone the repo
- go into the directory and run these commands: -
```
python3 -m venv .venv
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt
```  
- configure ```.env``` variables.
- then run ```python3 bot.py```

