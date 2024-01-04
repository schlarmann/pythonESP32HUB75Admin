
# Python GIF Chooser

A Flask application to upload, organize and select GIFs to display on a ESP32 based LED matrix display. (or similar)

Allows changing some settings like delay between the GIFs and order (random or sequential).

### Run application
The preferred way to use is by Docker. If you have docker installed and you wish to view images on say `/home/piyush/Pictures` directory, you can issue following command and then browse `localhost:6006`. Change this to your preferred directory path.
```
docker run -it -p 0.0.0.0:6006:5000/tcp -v /home/piyush/Pictures:/imgdir:ro piyush01123/flaskig python app.py /imgdir -l 0.0.0.0 -p 5000
```


2nd way is to clone this repo, install `flask` and run `app.py`:
```
python app.py /path/to/your/root/directory/containing/images
```
Make sure you have write permissions to the directory as the application will save uploaded GIFs in the directory.


If you wish to run it on a server and view the gallery on your own system then you might want to [port forward](https://www.ssh.com/ssh/tunneling/example) to your local system's IP or you might use a tunnelling service like [ngrok](https://ngrok.com) or [pagekite](https://pagekite.net/).
