
from flask import Flask
from flask import request
from flask import render_template
from flask import send_from_directory
from io import BytesIO 
from PIL import Image, ImageSequence, GifImagePlugin
from threading import Thread

import os
import random
import time
import json
import requests
import glob
import sys
import base64
import argparse
import socket

# Constants
HUB75_WIDTH = 128
HUB75_HEIGHT = 64
# Add your upload function (to the matrix display) here
def upload_image(imagePath):
    #return
    UPLOAD_URL = "http://10.42.28.7/upload"
    UPLOAD_FORM = "data"
    with open(imagePath, "rb") as gif:
        #print(f"Trying to upload {imagePath} to {UPLOAD_URL}!")
        requests.post(UPLOAD_URL, files = {UPLOAD_FORM: gif})

# Flask app
app = Flask("pythonGIFChooser")
app.config['IMAGE_EXTS'] = [".gif"] # Only GIFs for now

# State variables
current_image = None
image_delay = 1 # in Minutes
next_image_time = 0 # Timestamp when next image should be shown
display_mode = "random" # random, sequential

def encode(x):
    return base64.b64encode(x.encode('utf-8')).decode()

def decode(x):
    return base64.b64decode(x.encode('utf-8')).decode()

GifImagePlugin.LOADING_STRATEGY = GifImagePlugin.LoadingStrategy.RGB_ALWAYS

@app.route('/', methods = ['GET'])
def home():
    root_dir = app.config['ROOT_DIR']
    image_paths = []
    for root,dirs,files in os.walk(root_dir):
        for file in files:
            if any(file.endswith(ext) for ext in app.config['IMAGE_EXTS']):
                image_paths.append(encode(os.path.join(root,file)))
    current_imageVar = encode(current_image) if current_image is not None else "None"
    return render_template('index.html', paths=image_paths, hub75width=HUB75_WIDTH, hub75height=HUB75_HEIGHT, 
        image_delay=image_delay, display_mode=display_mode, current_image=current_imageVar)


@app.route('/cdn/<path:filepath>', methods = ['GET'])
def fetch_file(filepath):
    if os.path.isfile(decode(filepath)):
        dir,filename = os.path.split(decode(filepath))
        return send_from_directory(dir, filename, as_attachment=False)
    else:
        return 404
    
@app.route('/cdn/current', methods = ['GET'])
def get_current():
    current_imageVar = encode(current_image) if current_image is not None else "None"
    return '{"status":"OK", "current_image":"'+current_imageVar+'", "image_delay_s":"'+str(int(image_delay*60))+'", "statusId":0}',200

@app.route('/cdn/upload', methods = ['POST'])
def create_file():
    imageFile = request.files['imageData']
    imageDataB64 = base64.b64encode(imageFile.read())
    if(imageDataB64 == ''):
        retVal = {"status":"Please provide an image file in \"imageData\"", "statusId":-1}
        return json.dumps(retVal),400
    try:
        im = Image.open(BytesIO(base64.b64decode(imageDataB64))) 
    except Exception as e:
        retVal = {"status":"Image could not be parsed properly!", "error":str(e), "statusId":-1}
        return json.dumps(retVal),400
    else:
        # Modify GIF here
        gif_duration = im.info['duration']
        frames = [frame.copy() for frame in ImageSequence.Iterator(im)]
        newFrames = []

        for frame in frames:
            frame.convert('RGB')
            frame.thumbnail((HUB75_WIDTH,HUB75_HEIGHT), resample=Image.LANCZOS, reducing_gap=3.0)

            newFrame = Image.new('RGB', (HUB75_WIDTH,HUB75_HEIGHT), (0,0,0))
            newFrame.info["version"] = "GIF87a"
            offset_x = int(max((HUB75_WIDTH - frame.size[0]) / 2, 0))
            offset_y = int(max((HUB75_HEIGHT - frame.size[1]) / 2, 0))
            offset_tuple = (offset_x, offset_y) #pack x and y into a tuple
            newFrame.paste(frame.convert('RGB'), offset_tuple)
            newFrames.append(newFrame)

        # Save GIF to disk
        filepath = os.path.join(app.config['ROOT_DIR'], imageFile.filename)

        newFrames[0].save(filepath, 
            save_all = True, append_images = newFrames[1:], 
            optimize = True, duration = gif_duration, loop=0,
            include_color_table=True, interlace=True, disposal=1) 
        retVal = {"statusId":0, "newFile":filepath}
        return json.dumps(retVal),200

@app.route('/cdn/config', methods = ['POST'])
def setConfig():
    global image_delay
    global display_mode 
    data = request.form
    try:
        delay = float(data['image_delay'])
        if delay < 1 or delay > 60:
            return '{"status":"Invalid image delay provided! Must be between 1 and 60!", "statusId":-1}',400
        image_delay = delay
        mode = str(data['display_mode'])  
        if mode not in ["random", "sequential"]:
            return '{"status":"Invalid display mode provided!", "statusId":-1}',400
        display_mode = mode
        return '{"status":"Set config!", "statusId":0}',200

    except Exception as e:
        return '{"status":"Invalid data provided!", "error":%s, "statusId":-1}' % str(e),400

@app.route('/cdn/show/<path:filepath>', methods = ['POST'])
def show_file(filepath):
    global current_image
    global next_image_time
    if os.path.isfile(decode(filepath)):
        current_image = decode(filepath)
        next_image_time = 0 # Force next image to be shown
        #print("Showing file: %s" % current_image)
        return '{"status":"Showing image", "current_image":"'+encode(current_image)+'", "statusId":0}',200
    else:
        return '{"status":"Image not found", "statusId":-3}',404

@app.route('/cdn/del/<path:filepath>', methods = ['POST'])
def remove_file(filepath):
    #return '{"status":"Image not found", "statusId":-5}',404
    # Disabled for now
    if os.path.isfile(decode(filepath)):
        fullpath = decode(filepath)
        #print("Deleting: %s" % fullpath)
        if fullpath.startswith(app.config['ROOT_DIR']):
            #print("Deleting file: %s" % fullpath)
            os.remove(fullpath)
            return '{"status":"Deleting Image", "statusId":0}',200
        else:
            return '{"status":"Image not found", "statusId":-4}',404
    else:
        return '{"status":"Image not found", "statusId":-5}',404

def worker_thread(root_dir):
    global current_image
    global image_delay
    global next_image_time
    global display_mode

    while True:
        if current_image is not None:
            try:
                upload_image(current_image)
            except Exception as e:
                pass # Fail silent if upload fails
        
        while(time.time() < next_image_time):
            time.sleep(2)
            if(next_image_time == 0):
                break
        if next_image_time != 0:
            # Select next image only if we are not in "show" mode
            if display_mode == "random":
                image_paths = []
                for root,dirs,files in os.walk(root_dir):
                    for file in files:
                        if any(file.endswith(ext) for ext in app.config['IMAGE_EXTS']):
                            image_paths.append(os.path.join(root,file))
                current_image = random.choice(image_paths)
                #print("Next image: %s" % current_image)
            elif display_mode == "sequential":
                image_paths = []
                for root,dirs,files in os.walk(root_dir):
                    for file in files:
                        if any(file.endswith(ext) for ext in app.config['IMAGE_EXTS']):
                            image_paths.append(os.path.join(root,file))
                if current_image is None:
                    current_image = image_paths[0]
                else:
                    current_image = image_paths[(image_paths.index(current_image)+1)%len(image_paths)]
                #print("Next image: %s" % current_image)
        next_image_time = time.time() + image_delay*60
        #time.sleep(image_delay*60)
        

if __name__=="__main__":
    parser = argparse.ArgumentParser('Usage: %prog [options]')
    parser.add_argument('root_dir', help='Gallery root directory path')
    parser.add_argument('-l', '--listen', dest='host', default='127.0.0.1', \
                                    help='address to listen on [127.0.0.1]')
    parser.add_argument('-p', '--port', metavar='PORT', dest='port', type=int, \
                                default=5000, help='port to listen on [5000]')
    args = parser.parse_args()

    # Start with random Image
    image_paths = []
    for root,dirs,files in os.walk(args.root_dir):
        for file in files:
            if any(file.endswith(ext) for ext in app.config['IMAGE_EXTS']):
                image_paths.append(os.path.join(root,file))
    current_image = random.choice(image_paths)
    next_image_time = time.time() + image_delay*60
    #print("Next image: %s" % current_image)

    workerTH = Thread(target=worker_thread,args=(args.root_dir,))
    workerTH.start()


    app.config['ROOT_DIR'] = args.root_dir
    app.run(host=args.host, port=args.port, debug=False)
