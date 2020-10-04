from PIL import Image,ImageDraw,ImageFont
from io import BytesIO
from flask import send_file


def sign(line1, line2, line3, line4):
    # load the font, image and create a draw area
    W = 242
    font = ImageFont.truetype("assets/Minecraftia-Regular.ttf", 20)
    img = Image.open("assets/sign.png")
    draw = ImageDraw.Draw(img)

    # add all the lines of text
    if line1:
        w, h = draw.textsize(line1, font=font)
        draw.text(((W-w)/2,0), line1, font=font)
    if line2:
        w, h = draw.textsize(line2, font=font)
        draw.text(((W-w)/2,30), line2, font=font)
    if line3:
        w, h = draw.textsize(line3, font=font)
        draw.text(((W-w)/2,60), line3, font=font)
    if line4:
        w, h = draw.textsize(line4, font=font)
        draw.text(((W-w)/2,90), line4, font=font)
    
    # save the image in a buffer so we can send it
    img_io = BytesIO()
    img.save(img_io, 'PNG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

def advancement(item, title, text):
    
    # load font, image and create an area to draw on
    font = ImageFont.truetype("assets/Minecraftia-Regular.ttf", 14)
    img = Image.open("assets/advancement.png")
    draw = ImageDraw.Draw(img)

    # Title
    draw.text((60, 11),title,(222, 250, 60),font=font) # Yellow
    #draw.text((60, 11),title,(255, 124, 256),font=font) # Magenta

    # Message
    draw.text((60, 36),text,"white",font=font)

    # Item
    item = Image.open(f"items/{item}.png").convert("RGBA").resize((32, 32), Image.NEAREST)

    # make the black around it fully opaque
    pixdata = item.load()
    width, height = item.size
    for y in range(height):
        for x in range(width):
            if pixdata[x, y] == (0, 0, 0, 255):
                pixdata[x, y] = (0, 0, 0, 0)
    
    # paste item onto image keeping transparency
    img.paste(item, (20, 14), item)

    # save image in buffer so we can send
    img_io = BytesIO()
    img.save(img_io, 'PNG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')