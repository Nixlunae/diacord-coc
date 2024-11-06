import discord
from discord.ext import commands
import json
import random
import re

# 机器人设置
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)

# 文件路径
NICKNAME_FILE = 'nicknames.json'
STATS_FILE = 'stats.json'

# 读取本地存储的文件
def load_data(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# 写入本地存储的文件
def save_data(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file)

nicknames = load_data(NICKNAME_FILE)
stats = load_data(STATS_FILE)

@bot.command()
async def nn(ctx, nickname):
    user_id = str(ctx.author.id)
    if user_id in nicknames:
        await ctx.send(f"你已有昵称：{nicknames[user_id]}。是否更改为 {nickname}? (Y/N)")

        def check(msg):
            return msg.author == ctx.author and msg.content.lower() in ['y', 'n', '是', '不用', 'yes', 'no']

        try:
            response = await bot.wait_for("message", check=check, timeout=30)
            if response.content.lower() in ['y', '是', 'yes']:
                nicknames[user_id] = nickname
                save_data(NICKNAME_FILE, nicknames)
                await ctx.send(f"昵称已更新为：{nickname}")
            else:
                await ctx.send("已取消更改。")
        except:
            await ctx.send("响应超时，未更新昵称。")
    else:
        nicknames[user_id] = nickname
        save_data(NICKNAME_FILE, nicknames)
        await ctx.send(f"昵称已设置为：{nickname}")
@bot.command()
async def st(ctx, *args):
    user_id = str(ctx.author.id)
    if user_id not in stats:
        stats[user_id] = {}

    message = "属性更新：\n"
    for arg in args:
        match = re.match(r"(\D+)([+-]?\d+)", arg)
        if match:
            attr, value = match.groups()
            value = int(value)
            if attr in stats[user_id]:
                original_value = stats[user_id][attr]
                if "+" in arg or "-" in arg:
                    stats[user_id][attr] += value
                    message += f"{attr}: {original_value} -> {stats[user_id][attr]}\n"
                else:
                    stats[user_id][attr] = value
                    message += f"{attr} 已更新为 {value}\n"
            else:
                if "+" in arg or "-" in arg:
                    await ctx.send(f"属性 {attr} 尚未设定初始值。请先设定。")
                    continue
                stats[user_id][attr] = value
                message += f"{attr} 已设定为 {value}\n"

    save_data(STATS_FILE, stats)
    await ctx.send(message)
@bot.command()
async def ra(ctx, *args):
    user_id = str(ctx.author.id)
    if user_id not in stats:
        await ctx.send("尚未录入任何属性。请先使用 .st 指令录入属性。")
        return

    if len(args) == 2:
        level, attr = args
    elif len(args) == 1:
        level, attr = "普通", args[0]
    else:
        await ctx.send("输入格式错误。")
        return

    if attr not in stats[user_id]:
        await ctx.send(f"未找到属性 {attr}，请先使用 .st 录入。")
        return

    target = stats[user_id][attr]
    roll = random.randint(1, 100)
    result_message = f"{attr}检定结果: {roll}，目标值: {target}"

    if level == "困难":
        target = target // 2
    elif level == "极难":
        target = target // 5

    if roll == 1:
        result_message += " - 大成功！"
    elif roll <= target:
        if roll <= target // 5:
            result_message += " - 极难成功"
        elif roll <= target // 2:
            result_message += " - 困难成功"
        else:
            result_message += " - 成功"
    elif roll == 100:
        result_message += " - 大失败！"
    else:
        result_message += " - 失败"

    await ctx.send(result_message)
@bot.command()
async def r(ctx, *args):
    results = []
    for arg in args:
        if arg.lower() in ["adv", "dis"]:
            continue
        match = re.match(r"(\d*)d(\d+)([+-]\d+)?", arg)
        if match:
            dice_count, dice_type, modifier = match.groups()
            dice_count = int(dice_count) if dice_count else 1
            dice_type = int(dice_type)
            modifier = int(modifier) if modifier else 0

            rolls = [random.randint(1, dice_type) for _ in range(dice_count)]
            result = sum(rolls) + modifier
            results.append(f"{arg}: {' + '.join(map(str, rolls))} {'+' if modifier >= 0 else ''}{modifier} = {result}")

    if not results:
        roll = random.randint(1, 100)
        await ctx.send(f"默认投掷 1d100 结果：{roll}")
    else:
        await ctx.send("\n".join(results))
# 运行机器人，替换 'YOUR_BOT_TOKEN' 为你的真实 Token
bot.run(os.getenv("DISCORD_TOKEN"))
