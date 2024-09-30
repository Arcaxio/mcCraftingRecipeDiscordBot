import discord
import json
import traceback

# Load JSON utility function with error handling
def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON in {file_path}.")
        return None

# Get item ID from the item name with error handling
def get_item_id(item_name):
    try:
        items_data = load_json('mc_data/json/items.json')
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

# Get recipe by item ID with error handling
def get_recipe_by_item_id(item_id):
    try:
        recipes_data = load_json('mc_data/json/recipes.json')
        if not recipes_data:
            return None
        return recipes_data.get(str(item_id))
    except Exception as e:
        print(f"Error in get_recipe_by_item_id: {e}")
        traceback.print_exc()
        return None

# Get item name by item ID with error handling
def get_item_name_by_id(item_id):
    try:
        items_data = load_json('mc_data/json/items.json')
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
def format_recipe_message_with_item_names(recipe, item_name):
    try:
        in_shape = recipe[0].get('inShape', [])
        all_items = []

        # Collect all item names for calculating the max length
        for row in in_shape:
            for item in row:
                if item is not None:
                    item_name_from_id = get_item_name_by_id(item)
                    all_items.append(item_name_from_id if item_name_from_id else "unknown_item")

        # Find the max length of the item names
        max_length = max([len(item) for item in all_items] or [0])

        formatted_shape = ""
        for row in in_shape:
            formatted_row = []
            for item in row:
                if item is not None:
                    item_name_from_id = get_item_name_by_id(item)
                    # Pad the item name so that all entries are the same length
                    padded_item = f"{item_name_from_id:{max_length}}"
                    formatted_row.append(f"[{padded_item}]")
                else:
                    # Pad the null with spaces to match the max length
                    formatted_row.append(f"[{' ' * max_length}]")
            formatted_shape += " ".join(formatted_row) + "\n"
        
        return f"Crafting recipe for {item_name}:\n{formatted_shape}"
    except Exception as e:
        print(f"Error in format_recipe_message_with_item_names: {e}")
        traceback.print_exc()
        return f"Error: Could not format the recipe for {item_name}."


# Handle the !mc command with error handling
async def handle_mc_command(message, item_name):
    try:
        item_id = get_item_id(item_name)
        if item_id is None:
            await message.channel.send(f"Item {item_name} not found.")
            return
        
        recipe = get_recipe_by_item_id(item_id)
        if recipe is None:
            await message.channel.send(f"Recipe for {item_name} not found.")
            return

        recipe_message = format_recipe_message_with_item_names(recipe, item_name)
        await message.channel.send("```" + recipe_message + "```")
    except Exception as e:
        await message.channel.send(f"An error occurred while processing {item_name}.")
        print(f"Error in handle_mc_command: {e}")
        traceback.print_exc()

# Discord bot setup with error handling
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return
    
    try:
        if message.content.startswith('!mc'):
            args = message.content[4:].strip()

            # Check if the item name contains spaces instead of underscores
            if " " in args:
                await message.channel.send("Item name should contain underscores (e.g., iron_pickaxe)")
                return

            # Process item name
            item_name = args
            await handle_mc_command(message, item_name)
    except Exception as e:
        await message.channel.send("An error occurred while processing your request.")
        print(f"Error in on_message: {e}")
        traceback.print_exc()

# Start the bot
client.run('bot_token')
