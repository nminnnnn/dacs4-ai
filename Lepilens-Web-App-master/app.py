import os
import time
import sys
import shutil
import warnings
import uuid
import logging
import json
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import tensorflow as tf
import os
print("Current working directory:", os.getcwd())


# Supress deprecation warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from flask import Flask, render_template, request
import modelo

debug_output=False
min_confidence = 0.05
max_results = 5
pic_number = 0

application = Flask(__name__)

model_file = application.root_path + "/model.tflite"
label_file = application.root_path + "/dict.txt"

model = modelo.Model(model_file, label_file)

speciesInfoJSON = application.root_path + "/species_info.json"
file = open("C:/Users/Lenovo/Downloads/Lepilens-Web-App-master/Lepilens-Web-App-master/species_info.json", encoding="utf-8")

data = json.load(file)

family_dict = dict()
secundary_name = dict()
iNaturalist_link = dict()
wikipedia_link = dict()

for species in data:
    family_dict[species["name"]] = species["family"]
    secundary_name[species["name"]] = species["otherName"]
    iNaturalist_link[species["name"]] = species["iNatLink"]
    wikipedia_link[species["name"]] = species["WikipediaLink"]

application.config["IMAGE_STATIC"] = application.root_path + "/static/images"
application.config["LOG_FILE"] = application.root_path + "/lepilens.log"
logging.basicConfig(level=logging.INFO,
                     format='%(asctime)s - %(levelname)s - %(message)s',
                     datefmt='%Y-%m-%d %H:%M:%S',
                     filename=application.config['LOG_FILE'])

@application.route("/")
def initHTML():
    return render_template('Model_WebPage.html',confidence_slider_initially=10)

@application.route("/classify_image", methods=["GET", "POST"])
def classify_image():

    confidence_slider = request.form["confidence_slider"]
    min_confidence = float(confidence_slider) / 100
    if debug_output:
      print(min_confidence)

    dictionary = {}

    if request.method == "POST":
        if request.files:
            images = request.files.getlist("image_to_classify")
            if len(images) > 1 or images[0].filename != '':
              for image in images:
                print("%s / %s" % (image.filename, image.mimetype), file=sys.stderr)
                if image.mimetype != 'image/png' and image.mimetype != 'image/jpeg':
                  logging.error('\'%s\' - invalid MIME type \'%s\'' % (image.filename, image.mimetype))
                  continue
                _, extension = os.path.splitext(image.filename)
                unique_filename = str(uuid.uuid4()) +  extension
                path_to_image = os.path.join(application.config["IMAGE_STATIC"], unique_filename)
                image.save(path_to_image)
                logging.info('\'%s\' - saved onto \'%s\'' % (image.filename,unique_filename))
                t = time.time()
                res_list = model.classify(path_to_image, max_results, min_confidence)
                t = time.time() - t
                logging.info('\'%s\' - %d results in %d milliseconds for min confidence level %f' % (image.filename,len(res_list), int(t * 1e+03), min_confidence))
                dictionary[unique_filename] = res_list
                for elem in res_list:
                    logging.info('\'%s\' - %s' % (image.filename, elem))
                
    return render_template('Model_WebPage.html', confidence_slider_initially=confidence_slider,species_list=dictionary, family_dict=family_dict,
    secundary_name=secundary_name, iNaturalist_link=iNaturalist_link, wikipedia_link=wikipedia_link)

if __name__ == "__main__":
    application.run(debug=True)
