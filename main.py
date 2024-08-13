import discord
from discord import app_commands
from discord.ext import commands
import csv
import os
import getpass

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command()
@commands.has_permissions(administrator=True)
async def update_members(ctx):
    if not os.path.exists('members.csv'):
        await ctx.send("Error: members.csv 파일을 찾을 수 없습니다.")
        return
    
    # 4학년 학회원 이월 기능
    await promote_seniors(ctx)

    # CSV 파일 읽기
    members = []
    with open('members.csv', 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            members.append(row)

    guild = ctx.guild
    updated_member = []
    not_joined_member = []
    
    # 모든 멤버 순회
    for csv_member in members:
        member = guild.get_member_named(f"{csv_member['이름']}({csv_member['백준 아이디']})")
        
        if member:
            # 역할 부여
            await assign_roles(member, csv_member)
            updated_member.append(csv_member)
        else:
            # 아직 서버에 들어오지 않은 멤버
            not_joined_member.append(csv_member)

    # 서버에 있지만 CSV에 없는 멤버 처리
    for member in guild.members:
        name, baekjoon_id = parse_nickname(member.nick)
        if not any(m['이름'] == name and m['백준 아이디'] == baekjoon_id for m in members):
            await remove_all_roles(member)

    # 아직 서버에 들어오지 않은 멤버 CSV 저장
    if not_joined_member:
        with open('not_joined.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=members[0].keys())
            writer.writeheader()
            writer.writerows(not_joined_member)
        await ctx.send("서버에 들어오지 않은 멤버 목록을 not_joined.csv 파일로 저장했습니다.")

    await ctx.send("멤버 업데이트가 완료되었습니다.")

@bot.command()
@commands.has_permissions(administrator=True)
async def promote_seniors(ctx):
    response = await ctx.send("4학년 학회원을 OB로 이월하시겠습니까? (y/n)")
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['y', 'n']

    msg = await bot.wait_for('message', check=check)
    
    if msg.content.lower() == 'y':
        guild = ctx.guild
        senior_role = discord.utils.get(guild.roles, name="4학년")
        ob_role = discord.utils.get(guild.roles, name="OB")
        
        if senior_role and ob_role:
            for member in senior_role.members:
                await member.remove_roles(senior_role)
                await member.add_roles(ob_role)
            await ctx.send("4학년 학회원들을 OB로 이월했습니다.")
        else:
            await ctx.send("Error: 4학년 또는 OB 역할을 찾을 수 없습니다.")
    else:
        await ctx.send("작업을 취소했습니다.")

async def assign_roles(member, csv_member):
    guild = member.guild
    roles_to_assign = ["학회원"]
    
    if csv_member['학년'] == '휴학 중 및 예정':
        roles_to_assign.append("휴학생")
    else:
        roles_to_assign.append(f"{csv_member['학년']}학년")
    
    for role_name in roles_to_assign:
        role = discord.utils.get(guild.roles, name=role_name)
        if role and role not in member.roles:
            await member.add_roles(role)

async def remove_all_roles(member):
    roles_to_keep = ["@everyone"]  # 기본 역할은 유지
    roles_to_remove = [role for role in member.roles if role.name not in roles_to_keep]
    await member.remove_roles(*roles_to_remove)

def parse_nickname(nickname):
    if nickname:
        parts = nickname.split('(')
        if len(parts) == 2:
            name = parts[0].strip()
            baekjoon_id = parts[1].strip(')')
            return name, baekjoon_id
    return None, None

if __name__ == "__main__":
    token = getpass.getpass("봇 토큰을 입력하세요: ")
    bot.run(token)