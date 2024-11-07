import discord
from discord.ext import commands
import json
import random
import re
import os

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
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# 写入本地存储的文件
def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False)

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

@bot.command(name="st")
async def set_attributes(ctx, *, args):
    user_id = str(ctx.author.id)
    if user_id not in stats:
        stats[user_id] = {}

    # 使用正则表达式匹配输入模式
    pattern = re.compile(r'([一-龥a-zA-Z]+)([+-]?(?:\d+d\d+|\d+))')
    matches = pattern.findall(args)

    if not matches:
        await ctx.send("输入格式有误，请使用正确的格式：例如 .st 力量50 或 .st hp+2d6")
        return

    updates = []
    for attr, value in matches:
        attr = attr.lower()

        # 解析数值或骰子表达式
        if 'd' in value:
            # 骰子表达式处理，例如 2d6 或 -3d4
            sign = -1 if value.startswith('-') else 1
            dice_part = value.lstrip('+-')
            num, sides = map(int, dice_part.split('d'))
            roll_result = sum(random.randint(1, sides) for _ in range(num))
            value = sign * roll_result
        else:
            # 直接数值处理，例如 +2 或 -3 或 50
            value = int(value)

        # 更新属性值
        current_value = stats[user_id].get(attr, 0)
        if value >= 0 and not ('+' in args or '-' in args):
            # 直接赋值，例如 .st 力量50
            new_value = value
        else:
            # 增量更新，例如 .st hp+2 或 .st hp-3
            new_value = current_value + value

        stats[user_id][attr] = new_value
        updates.append(f"{attr} 已更新为 {new_value}（变化：{'+' if value >= 0 else ''}{value}）")

    # 保存数据并发送更新消息
    save_data(STATS_FILE, stats)
    await ctx.send(f"属性更新：\n" + "\n".join(updates))


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