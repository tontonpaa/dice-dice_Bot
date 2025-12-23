import os
import discord
from discord.ext import commands
from discord import app_commands
import subprocess
import sys
import re
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

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$$', intents=intents)

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
