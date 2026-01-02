import os
import discord
from discord.ext import commands
from discord import app_commands
import random
import math
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# 必要なインテントの設定
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$$', intents=intents)

@bot.tree.command(
    name="dd", 
    description="CoC6版準拠のダイスロールを行います。",
)
# 実行可能な場所の設定 (サーバー, 個人DM, グループDM/他人のDM)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
# インストール方法の設定 (サーバーへの導入, ユーザー自身への導入)
@app_commands.allowed_installs(guilds=True, users=True)
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
    """1d100 を振り、CoC6版の判定基準で結果を表示します。"""
    is_ephemeral = True if シークレット == 1 else False
    await interaction.response.defer(ephemeral=is_ephemeral)

    try:
        rolls = [random.randint(1, 面数) for _ in range(回数)]
        total_sum = sum(rolls)
        roll_expr = f"{回数}d{面数}"
        
        embed_color = 0x2ecc71
        judgment_text = "判定なし"
        
        if 目標値 is not None:
            special_threshold = math.floor(目標値 / 5)
            
            if 1 <= total_sum <= 5:
                judgment_text = "✨ **決定的成功（クリティカル）！！**"
                embed_color = 0x206694
            elif 96 <= total_sum <= 100:
                judgment_text = "💀 **致命的失敗（ファンブル）！！**"
                embed_color = 0xe74c3c
            elif total_sum <= special_threshold:
                judgment_text = "⭐ **強力的成功（スペシャル）！**"
                embed_color = 0x3498db
            elif total_sum <= 目標値:
                judgment_text = "✅ **成功**"
                embed_color = 0x2ecc71
            else:
                judgment_text = "❌ **失敗**"
                embed_color = 0xFFC800

        embed = discord.Embed(title="CoC 第6版 ダイスロール", color=embed_color)
        if is_ephemeral:
            embed.title += " [シークレット]"

        embed.add_field(name="ダイス", value=f"`{roll_expr}`", inline=True)
        embed.add_field(name="合計値", value=f"**{total_sum}**", inline=True)
        
        if 回数 > 1:
            embed.add_field(name="ダイス内訳", value=f"`{', '.join(map(str, rolls))}`", inline=False)
            
        if 目標値 is not None:
            special_threshold = math.floor(目標値 / 5)
            embed.add_field(name="目標値 / 判定", value=f"目標: `{目標値}` (スペシャル: {special_threshold}以下)\n結果: {judgment_text}", inline=False)
        
        embed.set_footer(text=f"実行者: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        await interaction.followup.send(embed=embed, ephemeral=is_ephemeral)

    except Exception as e:
        await interaction.followup.send(f"エラーが発生しました: {e}", ephemeral=is_ephemeral)

@bot.tree.command(
    name="settai", 
    description="【接待】必ずスペシャル以上の結果を出します。",
)
# 実行可能な場所の設定 (サーバー, 個人DM, グループDM/他人のDM)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
# インストール方法の設定 (サーバーへの導入, ユーザー自身への導入)
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.describe(
    回数="振るダイスの数",
    面数="ダイスの種類",
    目標値="成功判定に使用する目標値 (必須)",
    シークレット="1を入れると自分だけ"
)
async def settai(
    interaction: discord.Interaction, 
    目標値: int,
    回数: int = 1, 
    面数: int = 100, 
    シークレット: int = 0
):
    is_ephemeral = True if シークレット == 1 else False
    await interaction.response.defer(ephemeral=is_ephemeral)

    try:
        special_threshold = math.floor(目標値 / 5)
        total_sum = random.randint(1, max(1, special_threshold))
        
        if 回数 > 1:
            rolls = [0] * 回数
            temp_sum = total_sum
            for i in range(回数 - 1):
                val = random.randint(0, temp_sum)
                rolls[i] = val
                temp_sum -= val
            rolls[-1] = temp_sum
        else:
            rolls = [total_sum]

        if 1 <= total_sum <= 5:
            judgment_text = "✨ **決定的成功（クリティカル）！！**"
            embed_color = 0x206694
        else:
            judgment_text = "⭐ **強力的成功（スペシャル）！**"
            embed_color = 0x3498db

        embed = discord.Embed(title="CoC 第6版 ダイスロール [接待]", color=embed_color)
        if is_ephemeral: embed.title += " [シークレット]"
        
        embed.add_field(name="ダイス", value=f"`{回数}d{面数}`", inline=True)
        embed.add_field(name="合計値", value=f"**{total_sum}**", inline=True)
        if 回数 > 1:
            embed.add_field(name="ダイス内訳", value=f"`{', '.join(map(str, rolls))}`", inline=False)
        embed.add_field(name="目標値 / 判定", value=f"目標: `{目標値}` (スペシャル: {special_threshold}以下)\n結果: {judgment_text}", inline=False)
        embed.set_footer(text=f"実行者: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.followup.send(embed=embed, ephemeral=is_ephemeral)
    except Exception as e:
        await interaction.followup.send(f"エラーが発生しました: {e}", ephemeral=is_ephemeral)

@bot.tree.command(
    name="gyakutai", 
    description="【虐待】必ずファンブルの結果を出します。",
)
# 実行可能な場所の設定 (サーバー, 個人DM, グループDM/他人のDM)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
# インストール方法の設定 (サーバーへの導入, ユーザー自身への導入)
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.describe(
    回数="振るダイスの数",
    面数="ダイスの種類",
    目標値="成功判定に使用する目標値 (必須)",
    シークレット="1を入れると自分だけ"
)
async def gyakutai(
    interaction: discord.Interaction, 
    目標値: int,
    回数: int = 1, 
    面数: int = 100, 
    シークレット: int = 0
):
    is_ephemeral = True if シークレット == 1 else False
    await interaction.response.defer(ephemeral=is_ephemeral)

    try:
        total_sum = random.randint(96, 100)
        
        if 回数 > 1:
            rolls = [0] * 回数
            temp_sum = total_sum
            for i in range(回数 - 1):
                val = random.randint(1, max(1, temp_sum - (回数 - i - 1)))
                rolls[i] = val
                temp_sum -= val
            rolls[-1] = temp_sum
        else:
            rolls = [total_sum]

        judgment_text = "💀 **致命的失敗（ファンブル）！！**"
        embed_color = 0xe74c3c

        embed = discord.Embed(title="CoC 第6版 ダイスロール [虐待]", color=embed_color)
        if is_ephemeral: embed.title += " [シークレット]"
        
        embed.add_field(name="ダイス", value=f"`{回数}d{面数}`", inline=True)
        embed.add_field(name="合計値", value=f"**{total_sum}**", inline=True)
        if 回数 > 1:
            embed.add_field(name="ダイス内訳", value=f"`{', '.join(map(str, rolls))}`", inline=False)
        
        special_threshold = math.floor(目標値 / 5)
        embed.add_field(name="目標値 / 判定", value=f"目標: `{目標値}` (スペシャル: {special_threshold}以下)\n結果: {judgment_text}", inline=False)
        embed.set_footer(text=f"実行者: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.followup.send(embed=embed, ephemeral=is_ephemeral)
    except Exception as e:
        await interaction.followup.send(f"エラーが発生しました: {e}", ephemeral=is_ephemeral)

@bot.event
async def on_ready():
    print(f'{bot.user} (ID: {bot.user.id})としてログインしました。')
    try:
        # グローバルコマンドとして同期
        synced = await bot.tree.sync()
        print(f"{len(synced)} 個のコマンドを同期しました")
    except Exception as e:
        print(f"同期エラー: {e}")

if __name__ == "__main__":
    bot.run(os.getenv("BOT_TOKEN"))
