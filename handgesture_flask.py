import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
import pyttsx3
import random
import pickle
import tensorflow as tf
from skimage.transform import resize
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import load_model, Sequential
from tensorflow.keras.layers import Dense, Flatten, Conv2D, MaxPooling2D
import winsound
import time
from flask import Flask, render_template, Response, redirect, request

cap = cv2.VideoCapture(0)

##################################################### Flask ############################################

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html') 

##################################################### View Camera ######################################
@app.route('/video_feed')
def video_feed():
    return Response(camera(), mimetype='multipart/x-mixed-replace; boundary=frame')

def camera():
    
    while(True):
        ret, frame = cap.read()
        if ret == True:
            start_point = (425, 100)
            end_point = (625, 300)
            color = (0, 100, 255)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_flip = cv2.flip(gray, 1)

            img = cv2.rectangle(gray_flip, start_point, end_point,color, thickness=2, lineType=8)
            fullimg = cv2.rectangle(cv2.flip(frame, 1), start_point, end_point,color, thickness=2, lineType=8)
            
            imcrop = img[102:298, 427:623]

            (thresd, binaryimg) = cv2.threshold(imcrop, 127, 255, cv2.THRESH_BINARY)

            # cv2.imshow('fullimg',fullimg)
            # cv2.imshow('Grayimcrop',imcrop)
            # cv2.imshow('binaryimg',binaryimg)
            frame = cv2.imencode('.jpg', fullimg)[1].tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.05)

        else: 
            break

##################################################### View Camera Binary ######################################
@app.route('/video_feed_binary')
def video_feed_binary():
    return Response(camerabinary(), mimetype='multipart/x-mixed-replace; boundary=frame')

def camerabinary():
    
    while(True):
        ret, frame = cap.read()
        if ret == True:
            start_point = (425, 100)
            end_point = (625, 300)
            color = (0, 100, 255)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_flip = cv2.flip(gray, 1)

            img = cv2.rectangle(gray_flip, start_point, end_point,color, thickness=2, lineType=8)
            fullimg = cv2.rectangle(cv2.flip(frame, 1), start_point, end_point,color, thickness=2, lineType=8)
            
            imcrop = img[102:298, 427:623]

            (thresd, binaryimg) = cv2.threshold(imcrop, 127, 255, cv2.THRESH_BINARY)

            # cv2.imshow('fullimg',fullimg)
            # cv2.imshow('Grayimcrop',imcrop)
            # cv2.imshow('binaryimg',binaryimg)
            frame = cv2.imencode('.jpg', binaryimg)[1].tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.05)

        else: 
            break

##################################################### Training Data Creation #####################################################

@app.route('/create_dataset', methods=['GET', 'POST'])
def create_dataset():
    print("Called create_dataset")
    hgn = request.form.get('hgn')
    gesture_name = hgn
    print(gesture_name)

    if os.path.exists('./Dataset/') == False:
        os.mkdir('./Dataset/')

    if os.path.exists('./Dataset/' + gesture_name) == True:
        existing_class=os.path.join('./Dataset/'+gesture_name)
        listofnames=os.listdir(existing_class)
        if listofnames != []:
            lastimgno = int(os.path.splitext(listofnames[-1])[0])
            print(lastimgno)
            training_set_image_name = lastimgno+1
        else:
            training_set_image_name = 1
    else:
        os.mkdir('./Dataset/' + gesture_name)
        training_set_image_name = 1

    image_x, image_y = 64, 64

    ret, frame = cap.read()

    start_point = (425, 100)
    end_point = (625, 300)
    color = (0, 100, 255)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_flip = cv2.flip(gray, 1)

    img = cv2.rectangle(gray_flip, start_point, end_point,color, thickness=2, lineType=8)
    fullimg = cv2.rectangle(cv2.flip(frame, 1), start_point, end_point,color, thickness=2, lineType=8)
    
    imcrop = img[102:298, 427:623]

    (thresd, binaryimg) = cv2.threshold(imcrop, 127, 255, cv2.THRESH_BINARY)

    # cv2.imshow('fullimg',fullimg)
    # cv2.imshow('Grayimcrop',imcrop)
    # cv2.imshow('binaryimg',binaryimg)
    img_name = "./Dataset/" + str(gesture_name) + "/{}.png".format(training_set_image_name)
    save_img = cv2.resize(binaryimg,(image_x, image_y)) #### binaryimg or imcrop
    cv2.imwrite(img_name, save_img)
    print("{} written!".format(img_name))
    training_set_image_name += 1

    return redirect('/')
    

######################################################################## CNN Training ###########################################
@app.route('/cnn')
def cnn():
    tf.test.is_gpu_available(cuda_only=False,min_cuda_compute_capability=None)

    BASE_DIR=os.getcwd()
    dataset_dir=os.path.join(BASE_DIR,"Dataset")
    categories=os.listdir(dataset_dir)
    print(dataset_dir,"\n",categories)

    training_data = []
    IMG_SIZE = 100

    print("Please Wait it will take some time")
    for category in categories:
        path = os.path.join(dataset_dir,category)
        class_num = categories.index(category)
        for img in os.listdir(path):
            try:
                img_array = cv2.imread(os.path.join(path,img),cv2.IMREAD_GRAYSCALE)
                new_array = cv2.resize(img_array, (IMG_SIZE,IMG_SIZE))
                training_data.append([new_array,class_num])
                
            except Exception as e:
                print(e)
                pass
                
    print("\n \n Total Traning Data Length",len(training_data))

    random.shuffle(training_data)

    X = []
    y = []

    for features,labels in training_data:
        X.append(features)
        y.append(labels)
        
    X = np.array(X).reshape(-1,IMG_SIZE,IMG_SIZE,1)
    y = np.array(y)

    pickle_out = open("X.pickle","wb")
    pickle.dump(X,pickle_out)
    pickle_out.close()

    pickle_out = open("y.pickle","wb")
    pickle.dump(y,pickle_out)
    pickle_out.close()

    del X,y

    X = []
    y = []

    X = pickle.load(open("X.pickle","rb"))
    y = pickle.load(open("y.pickle","rb"))

    x_train, x_test, y_train, y_test = train_test_split(X,y,test_size=0.2)

    y_train_one_hot = to_categorical(y_train)
    y_test_one_hot = to_categorical(y_test)

    del labels,features,y_train,y_test,X,y

    x_train = x_train / 255
    x_test = x_test / 255

    begin = time.time() 

    try:
        model = Sequential()

        model.add(Conv2D(64, (3,3), input_shape = x_train.shape[1:],activation ='relu')) 
        model.add(MaxPooling2D(pool_size=(2,2)))

        model.add(Conv2D(64,3,3, activation ='relu'))
        model.add(MaxPooling2D(pool_size=(2,2)))

        model.add(Conv2D(64,3,3, activation ='relu'))
        model.add(MaxPooling2D(pool_size=(2,2)))

        model.add(Flatten())

        model.add(Dense(512,activation= 'relu'))

        model.add(Dense(512,activation= 'relu'))
        model.add(Dense(len(categories), activation='softmax'))

        model.compile(loss="mean_squared_error",optimizer='adam',metrics=['accuracy'])

        hist = model.fit(x_train, y_train_one_hot,batch_size=50, epochs=50, validation_split=0.3)
        model.save("savedmodel")


        time.sleep(1) 
        end = time.time() 
        print(f"Total runtime of the program is {end - begin}") 

        for beep in range(10):
            frequency = 1000
            duration = 100
            winsound.Beep(frequency, duration)
            time.sleep(0.5)


        model.summary()
        history_dict = hist.history
        print(history_dict.keys())
        
    except:
        for beep in range(5):
            frequency = 2500
            duration = 1000
            winsound.Beep(frequency, duration)
            time.sleep(0.5)

    return redirect('/')
##################################################### Recognisation #################################################################
@app.route('/recognisation')
def recognisation():
    sentence = " "
    pervious = " "

    BASE_DIR=os.getcwd()
    dataset_dir=os.path.join(BASE_DIR,"Dataset")
    categories=os.listdir(dataset_dir)
    print(dataset_dir,"\n",categories)

    IMG_SIZE = 100
    
    model = load_model('savedmodel')
    model.summary()
   
    while(True):
        ret, frame = cap.read()

        start_point = (425, 100)
        end_point = (625, 300)
        color = (0, 100, 255)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_flip = cv2.flip(gray, 1)

        img = cv2.rectangle(gray_flip, start_point, end_point,color, thickness=2, lineType=8)
        fullimg = cv2.rectangle(cv2.flip(frame, 1), start_point, end_point,color, thickness=2, lineType=8)
        
        imcrop = img[102:298, 427:623]

        (thresd, binaryimg) = cv2.threshold(imcrop, 127, 255, cv2.THRESH_BINARY)

        # cv2.imshow('fullimg',fullimg)
        # cv2.imshow('Grayimcrop',imcrop)
        # cv2.imshow('binaryimgcrop',binaryimg)

        my_image_resized = resize(binaryimg, (IMG_SIZE,IMG_SIZE,1)) #### binaryimg or imcrop

        probabilities = model.predict(np.array( [my_image_resized,] ))

        index = np.argsort(probabilities[0,:])
        category = categories[index[len(categories)-1]]
        probability = probabilities[0,index[len(categories)-1]]*100
        print("\n\n\n Predicted Class:", category,"\n Probability:", probability)

        if pervious != category:
            sentence += " "
            sentence += category
            pervious = category

        
        print(sentence)
        
        engine=pyttsx3.init()
        engine.say(sentence)
        engine.runAndWait()
        return render_template('index.html',sentence=sentence)