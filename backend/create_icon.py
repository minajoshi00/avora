from PIL import Image, ImageDraw, ImageFont

# Create a 256x256 icon with the AVORA logo
size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw a rounded rectangle background
margin = 20
bg = Image.new('RGBA', (size - margin*2, size - margin*2), (0, 0, 0, 0))
bg_draw = ImageDraw.Draw(bg)
radius = 40
bg_draw.rounded_rectangle(
    [0, 0, bg.width, bg.height],
    radius=radius,
    fill=(139, 122, 255, 255)  # #8B7AFF
)

# Paste background
img.paste(bg, (margin, margin), bg)

# Draw the star symbol (✦) or text "A"
try:
    font = ImageFont.truetype('arial.ttf', 140)
except:
    font = ImageFont.load_default()

# Get text bounding box
bbox = draw.textbbox((0, 0), 'A', font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]

x = (size - text_width) // 2
y = (size - text_height) // 2 - 10

draw.text((x, y), 'A', font=font, fill=(255, 255, 255, 255))

# Save as ICO with multiple sizes
icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
img.save('avora.ico', format='ICO', sizes=icon_sizes)
print('Created avora.ico successfully')