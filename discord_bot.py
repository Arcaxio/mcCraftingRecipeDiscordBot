import discord
import json
import traceback
import aiofiles
import asyncio
from PIL import Image
from io import BytesIO
import os
import base64


# Function to retrieve texture path based on item name
# Function to retrieve texture data (base64) based on item name
async def get_texture_data(item_name):
    try:
        texture_content = await load_json('mc_data/textures/texture_content.json')
        
        # Search for the item in texture_content.json
        for entry in texture_content:
            if entry['name'] == item_name:
                # Return the base64 texture content
                return entry.get('texture').split(',')[1]
        
        return None
    except Exception as e:
        print(f"Error retrieving texture for {item_name}: {e}")
        traceback.print_exc()
        return None

# Function to generate the final crafting grid image
async def generate_crafting_image(in_shape):
    try:
        grid_size = 32
        grid_image = Image.new("RGBA", (grid_size * 3, grid_size * 3), (255, 255, 255, 0))

        for row_idx, row in enumerate(in_shape):
            for col_idx, item_id in enumerate(row):
                if item_id is not None:
                    item_name = await get_item_name_by_id(item_id)
                    texture_base64 = await get_texture_data(item_name)

                    if texture_base64:
                        # Decode the base64 texture
                        texture_data = base64.b64decode(texture_base64)
                        item_image = Image.open(BytesIO(texture_data)).resize((grid_size-2, grid_size-2)).convert("RGBA")

                        # Paste the image into the grid
                        grid_image.paste(item_image, (col_idx * grid_size, row_idx * grid_size), item_image)

        return grid_image
    except Exception as e:
        print(f"Error in generate_crafting_image: {e}")
        traceback.print_exc()
        return None
    
async def generate_crafting_image_ingredients(ingredients):
    try:
        # Define grid size (width and height of each cell)
        grid_size = 32
        
        # Calculate the number of ingredients
        num_ingredients = len(ingredients)
        
        # Dynamically set rows and cols based on number of ingredients
        if num_ingredients == 1:
            rows, cols = 1, 1  # 1x1 grid
        elif num_ingredients == 2:
            rows, cols = 1, 2  # 2x1 grid
        elif num_ingredients == 3:
            rows, cols = 1, 3  # 3x1 grid
        else:
            rows, cols = 3, 3  # 3x3 grid for 4 or more items

        # Create a new blank image (transparent background)
        grid_image = Image.new("RGBA", (grid_size * cols, grid_size * rows), (255, 255, 255, 0))

        # Loop over the ingredients and place them in the grid
        for idx, item_id in enumerate(ingredients):
            if item_id is not None:
                item_name = await get_item_name_by_id(item_id)
                texture_base64 = await get_texture_data(item_name)

                if texture_base64:
                    # Decode the base64 texture
                    texture_data = base64.b64decode(texture_base64)
                    item_image = Image.open(BytesIO(texture_data)).resize((grid_size-2, grid_size-2)).convert("RGBA")

                    # Calculate the column and row positions based on index
                    col_idx = idx % cols  # Column position
                    row_idx = idx // cols  # Row position

                    # Paste the image into the correct position in the grid
                    grid_image.paste(item_image, (col_idx * grid_size, row_idx * grid_size), item_image)

        return grid_image
    except Exception as e:
        print(f"Error in generate_crafting_image: {e}")
        traceback.print_exc()
        return None

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

# Get item ID from the item name
async def get_item_id(item_name):
    try:
        items_data = await load_json('mc_data/json/items.json')
        if not items_data:
            return None
        for item in items_data:
            if item['name'] == item_name:
                return item['id']
        return None
    except Exception as e:
        print(f"Error in get_item_id: {e}")
        traceback.print_exc()
        return None

# Get recipe by item ID
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

# Get item name by item ID
async def get_item_name_by_id(item_id):
    try:
        items_data = await load_json('mc_data/json/items.json')
        if not items_data:
            return None
        for item in items_data:
            if item['id'] == item_id:
                return item['name']
        return None
    except Exception as e:
        print(f"Error in get_item_name_by_id: {e}")
        traceback.print_exc()
        return None

# Format the recipe and image array for sending
async def format_recipe_with_images(recipe, item_name):
    try:
        recipes_text = []
        images_to_send = []

        for recipe_entry in recipe:
            formatted_recipe = ""

            # Handle inShape if it exists
            if 'inShape' in recipe_entry:
                in_shape = recipe_entry.get('inShape', [])
                all_items = []

                # Collect all item names for calculating the max length
                for row in in_shape:
                    for item in row:
                        if item is not None:
                            item_name_from_id = await get_item_name_by_id(item)
                            all_items.append(item_name_from_id if item_name_from_id else "unknown_item")

                # Calculate max item name length for padding
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

                formatted_recipe += f"{formatted_shape.strip()}"

                # Generate image for this inShape
                crafting_image = await generate_crafting_image(in_shape)
                if crafting_image:
                    image_path = f'/{item_name}_crafting_{len(images_to_send)}.png'
                    crafting_image.save(image_path)
                    images_to_send.append(image_path)

            # Handle ingredients if it exists
            elif 'ingredients' in recipe_entry:
                ingredients = recipe_entry.get('ingredients', [])
                formatted_ingredients = []

                # Collect and format ingredients
                for ingredient in ingredients:
                    if ingredient is not None:
                        ingredient_name = await get_item_name_by_id(ingredient)
                        formatted_ingredients.append(ingredient_name if ingredient_name else "unknown_item")

                # Format ingredients into a grid (2x2 or 3x3 grid)
                grid_size = 3  # We assume a max grid size of 3x3 (adjust if needed)
                formatted_ingredients_grid = ""

                # Arrange ingredients into rows
                for i in range(0, len(formatted_ingredients), grid_size):
                    row = formatted_ingredients[i:i + grid_size]
                    padded_row = [f"[{ingredient.ljust(max([len(ing) for ing in formatted_ingredients]))}]" for ingredient in row]
                    formatted_ingredients_grid += " ".join(padded_row) + "\n"

                formatted_recipe += f"{formatted_ingredients_grid.strip()}"

                # Generate image for this ingredients
                crafting_image = await generate_crafting_image_ingredients(ingredients)
                if crafting_image:
                    image_path = f'/{item_name}_crafting_{len(images_to_send)}.png'
                    crafting_image.save(image_path)
                    images_to_send.append(image_path)

            # Add formatted recipe text to the list
            recipes_text.append(formatted_recipe.strip())

        return recipes_text, images_to_send
    except Exception as e:
        print(f"Error in format_recipe_with_images: {e}")
        traceback.print_exc()
        return [], []

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

        # Format the recipe into text and images
        recipes_text, images_to_send = await format_recipe_with_images(recipe, item_name)

        # Send the text-based crafting recipe with all variations
        formatted_message = f"Crafting recipe for {item_name}:" + "OR\n".join([f"```{text}```" for text in recipes_text])
        await message.channel.send(formatted_message)

        # Limit the number of images sent to 10
        if images_to_send:
            limited_images = images_to_send[:10]  # Only take the first 10 images
            image_files = [discord.File(img_path) for img_path in limited_images]
            await message.channel.send(files=image_files)

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
client.run('Token')
