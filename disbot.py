import discord
from discord import app_commands
from discord.ext import commands
import os
import time
import platform
import random
import asyncio
import datetime
import ollama
import json
import re

#---------------------------------------| variables |-------------------------------------------------
myModel = ''
botToken = ''
#-----------------------------------------------------------------------------------------------------

intents = discord.Intents.all()
intents.message_content = True
client = commands.Bot(command_prefix=".", intents=discord.Intents.all())
chatlogDM = []
chatlogGrp = []

def export_to_json(object, filename):
    with open(filename, 'w') as f:
        json.dump(object, f)

def import_from_json(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("file not found")
        return None

#----------------------------------| bot startup and command sync |------------------------------------
@client.event
async def on_ready():
  print(f'Successfully logged in as {client.user}.')
  
  try:
    synced = await client.tree.sync()
    print(f"Synced {len(synced)} command/s.")
  except Exception as e:
    print (e)

#----------------------------------------| user info command |------------------------------------------
@client.tree.command(
  name="userinfo",
  description="prints the info of a user"
)
async def userinfo(interaction: discord.Interaction, member:discord.Member=None):
  if member == None:
    member = interaction.user
  roles = [role for role in member.roles]
  embed = discord.Embed(title="user info", description=f"here is the info i found for the user {member.mention}", color = discord.Color.green(), timestamp = datetime.datetime.now())
  embed.set_thumbnail(url = member.avatar)
  embed.add_field(name="id", value = member.id)
  embed.add_field(name="name", value = f"{member.name}#{member.discriminator}")
  embed.add_field(name="nickname", value = member.display_name)
  embed.add_field(name="status", value = member.status)
  embed.add_field(name="created", value = member.created_at.strftime("%a, %B, %#d, %Y, %I:%M %p ").lower())
  embed.add_field(name="joined", value = member.joined_at.strftime("%a, %B, %#d, %Y, %I:%M %p ").lower())
  embed.add_field(name=f"roles ({len(roles)})", value = " ".join([role.mention for role in roles]))
  await interaction.response.send_message(embed=embed)

#----------------------------------------| server info command |------------------------------------------
@client.tree.command(
  name="serverinfo",
  description="prints the info of the current server"
)
async def serverinfo(interaction: discord.Interaction):
  embed = discord.Embed(title="server info", description=f"here is the info i found for the server {interaction.guild.name}", color = discord.Color.blue(), timestamp = datetime.datetime.now())
  embed.set_thumbnail(url = interaction.guild.icon)
  embed.add_field(name="members", value = interaction.guild.member_count)
  embed.add_field(name="text channels", value = len(interaction.guild.text_channels))
  embed.add_field(name="voice channels", value = len(interaction.guild.voice_channels))
  embed.add_field(name="owner", value = interaction.guild.owner.mention)
  embed.add_field(name="description", value = interaction.guild.description)
  embed.add_field(name="created", value = interaction.guild.created_at.strftime("%a, %B, %#d, %Y, %I:%M %p ").lower())
  await interaction.response.send_message(embed=embed)

#-------------------------------------------| chat history |---------------------------------------------
@client.event
async def on_message(message):
  if message.author == client.user:
    return
  if client.user.mention in message.content.split() and not isinstance(message.channel, discord.DMChannel):
    async with message.channel.typing():
      full_string = message.content
      cut_string = re.sub('<.*?>', f'{myModel}', full_string)
      prompt_dict = {
          'role': 'user',
          'content':f'{message.author.display_name}: ' + f'{cut_string}'
        }
      chatlogGrp.append(prompt_dict)
      ai_response = ollama.chat(model=myModel, messages=chatlogGrp)
      resp = ai_response['message']['content']  
      resp_dict = {
        'role': 'assistant',
        'content': f'{resp}'
      }
      chatlogGrp.append(resp_dict)
      await message.channel.send(f'{resp}')
  else:
    if isinstance(message.channel, discord.DMChannel):
      async with message.channel.typing():
        full_string = message.content
        cut_string = re.sub('<.*?>', f'{myModel}', full_string)
        prompt_dict = {
          'role': 'user',
          'content':f'{message.author.display_name}: ' + f'{cut_string}'
        }
        chatlogDM.append(prompt_dict)
        ai_response = ollama.chat(model=myModel, messages=chatlogDM)
        resp = ai_response['message']['content']
        resp_dict = {
          'role': 'assistant',
          'content': f'{resp}'
        }
        chatlogDM.append(resp_dict)
        await message.channel.send(f'{resp}')

@client.tree.command(
    name="clear",
    description="clear my chat history",
)
async def clear(interaction):
  chatlogDM.clear()
  chatlogGrp.clear()
  await interaction.response.send_message(f"`chat logs cleared, starting fresh`")

@client.tree.command(
    name="save",
    description="save my chat history",
)
async def save(interaction):
  export_to_json(chatlogDM, f'{myModel}-log.json')
  await interaction.response.send_message(f"`my logs have been saved to the server`")
  # await interaction.response.send_message(file=discord.File('chatlog.json'))

@client.tree.command(
    name="load",
    description="load my last saved chat history",
)
async def load(interaction):
  global chatlogDM
  chatlogDM = import_from_json(f'{myModel}-log.json')
  await interaction.response.send_message(f"`my logs have been loaded from the server`")

client.run(botToken)
