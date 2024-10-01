import discord
import json
import traceback
import aiofiles
import asyncio

# Load JSON utility function with async handling
async def load_json(file_path):
    try:
        async with aiofiles.open(file_path, 'r') as f:
            file_content = await f.read()
            return json.loads(file_content)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON in {file_path}.")
        return None

# Get item ID from the item name with async handling
async def get_item_id(item_name):
    try:
        items_data = await load_json('mc_data/json/items.json')
        if not items_data:
            return None
        for item in items_data:
            if item['name'] == item_name:
                return item['id']
        print(f"Error: Item '{item_name}' not found in items.json.")
        return None
    except Exception as e:
        print(f"Error in get_item_id: {e}")
        traceback.print_exc()
        return None

# Get recipe by item ID with async handling
async def get_recipe_by_item_id(item_id):
    try:
        recipes_data = await load_json('mc_data/json/recipes.json')
        if not recipes_data:
            return None
        return recipes_data.get(str(item_id))
    except Exception as e:
        print(f"Error in get_recipe_by_item_id: {e}")
        traceback.print_exc()
        return None

# Get item name by item ID with async handling
async def get_item_name_by_id(item_id):
    try:
        items_data = await load_json('mc_data/json/items.json')
        if not items_data:
            return None
        for item in items_data:
            if item['id'] == item_id:
                return item['name']
        print(f"Error: Item name for ID '{item_id}' not found.")
        return None
    except Exception as e:
        print(f"Error in get_item_name_by_id: {e}")
        traceback.print_exc()
        return None

# Format the recipe message by replacing item IDs with item names, with padding for alignment
async def format_recipe_message_with_item_names(recipe, item_name):
    try:
        all_recipe_variations = []
        
        for recipe_entry in recipe:
            if 'inShape' in recipe_entry:
                in_shape = recipe_entry.get('inShape', [])
                all_items = []

                # Collect all item names for calculating the max length
                for row in in_shape:
                    for item in row:
                        if item is not None:
                            item_name_from_id = await get_item_name_by_id(item)
                            all_items.append(item_name_from_id if item_name_from_id else "unknown_item")

                max_length = max([len(item) for item in all_items] or [0])

                formatted_shape = ""
                for row in in_shape:
                    formatted_row = []
                    for item in row:
                        if item is not None:
                            item_name_from_id = await get_item_name_by_id(item)
                            padded_item = f"{item_name_from_id:{max_length}}"
                            formatted_row.append(f"[{padded_item}]")
                        else:
                            formatted_row.append(f"[{' ' * max_length}]")
                    formatted_shape += " ".join(formatted_row) + "\n"

                all_recipe_variations.append(formatted_shape.strip())

            elif 'ingredients' in recipe_entry:
                ingredients = recipe_entry.get('ingredients', [])
                all_items = []

                for ingredient in ingredients:
                    if ingredient is not None:
                        item_name_from_id = await get_item_name_by_id(ingredient)
                        all_items.append(item_name_from_id if item_name_from_id else "unknown_item")

                max_length = max([len(item) for item in all_items] or [0])

                formatted_ingredients = ""
                for ingredient in ingredients:
                    if ingredient is not None:
                        item_name_from_id = await get_item_name_by_id(ingredient)
                        padded_item = f"{item_name_from_id:{max_length}}"
                        formatted_ingredients += f"[{padded_item}] "
                    else:
                        formatted_ingredients += f"[{' ' * max_length}] "

                all_recipe_variations.append(formatted_ingredients.strip())

        combined_recipes = "\nOR\n".join(all_recipe_variations)
        return f"Crafting recipe for {item_name}:\n{combined_recipes}"

    except Exception as e:
        print(f"Error in format_recipe_message_with_item_names: {e}")
        traceback.print_exc()
        return f"Error: Could not format the recipe for {item_name}."

# Handle the !mc command with async handling
async def handle_mc_command(message, item_name):
    try:
        item_id = await get_item_id(item_name)
        if item_id is None:
            await message.channel.send(f"Item {item_name} not found.")
            return
        
        recipe = await get_recipe_by_item_id(item_id)
        if recipe is None:
            await message.channel.send(f"Recipe for {item_name} not found.")
            return

        recipe_message = await format_recipe_message_with_item_names(recipe, item_name)
        await message.channel.send("```" + recipe_message + "```")
    except Exception as e:
        await message.channel.send(f"An error occurred while processing {item_name}.")
        print(f"Error in handle_mc_command: {e}")
        traceback.print_exc()

# Discord bot setup with async handling
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    try:
        if message.content.startswith('!mc'):
            args = message.content[4:].strip()

            if " " in args:
                await message.channel.send("Item name should contain underscores (e.g., iron_pickaxe)")
                return

            item_name = args
            await handle_mc_command(message, item_name)
    except Exception as e:
        await message.channel.send("An error occurred while processing your request.")
        print(f"Error in on_message: {e}")
        traceback.print_exc()

# Start the bot
client.run('YOUR_DISCORD_BOT_TOKEN')
