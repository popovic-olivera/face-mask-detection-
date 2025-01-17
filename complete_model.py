from facenet_pytorch import MTCNN
import time
import cv2
import numpy as np
import torch
import torchvision
import matplotlib.pyplot as plt


detector = MTCNN(min_face_size=20)
model = torch.load('models/mobilenet_80_20_epochs20_acc0992274.pt', map_location=torch.device('cpu'))


def draw_box(image, resized, faces, labels, probabilities, class_names, video):
    im_height, im_width, _ = image.shape
    res_height, res_width, _ = resized.shape

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # plot all boxes
    for i in range(len(faces)):
        x, y, x_right, y_bottom = faces[i].round().astype('int32')

        x = round(im_width * x / res_width)
        y = round(im_height * y / res_height)
        x_right = round(im_width * x_right / res_width)
        y_bottom = round(im_height * y_bottom / res_height)

        if video:
            color = (0, 255, 0) if labels[i] else (0, 0, 255)
        else:
            color = (0, 255, 0) if labels[i] else (255, 0, 0)

        cv2.putText(image, f'{class_names[labels[i]]}: {probabilities[i][1]:.2f}', (x, y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
        cv2.rectangle(image, (x, y), (x_right, y_bottom), color, 2)
        
    return image


def complete_model(image, video=False):
    start_time = time.time()

    height, width, _ = image.shape

    scale_percent = 50
    width = int(width * scale_percent / 100)
    height = int(height * scale_percent / 100)
    resized = cv2.resize(image, (width, height), interpolation = cv2.INTER_AREA)
    
    faces, _, landmarks = detector.detect(resized, landmarks=True)

    if faces is None:
        return image

    # time_elapsed = time.time() - start_time
    # print(f'Time spent: {time_elapsed}')
    # start_time = time.time()
    
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    transform = torchvision.transforms.Compose([torchvision.transforms.ToTensor(),
                                                torchvision.transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

    batch_images = []

    for face, landmark in zip(faces, landmarks):
        vec = landmark[1] - landmark[0]
        vec_norm = vec / np.linalg.norm(vec)
        angle = np.degrees(np.arccos(np.dot(vec_norm, np.array([1, 0]))))

        rot_mat = cv2.getRotationMatrix2D(tuple(landmark[0]), -angle if vec[1] <= 0 else angle, 1.0)
        result = cv2.warpAffine(resized, rot_mat, resized.shape[1::-1], flags=cv2.INTER_LINEAR)

        startX, startY, endX, endY = face.round().astype('int32')
        
        (startX, startY) = (max(0, startX), max(0, startY))
        (endX, endY) = (min(width - 1, endX), min(height - 1, endY))

        cropped_face = result[startY:endY, startX:endX]
        # cv2.imwrite(f'rotated {face[0]}.png', cv2.cvtColor(cropped_face, cv2.COLOR_RGB2BGR))
        # cv2.imwrite(f'original {face[0]}.png', cv2.cvtColor(resized[startY:endY, startX:endX], cv2.COLOR_RGB2BGR))
        
        cropped_face = cv2.resize(cropped_face, (224, 224))

        cropped_face = transform(cropped_face)

        batch_images.append(cropped_face)

    batch_torch = torch.stack(batch_images)
    output = model(batch_torch)
    
    probabilities = torch.softmax(output, dim=1)

    # _, predicted = torch.max(output, 1)

    predicted = torch.tensor([1 if p[1] > 0.55 else 0 for p in probabilities])

    # time_elapsed = time.time() - start_time    # print(f'Time spent: {time_elapsed}')

    return draw_box(image, resized, faces, predicted, probabilities, ['WITHOUT MASK', 'WITH MASK'], video)


def on_image(image_name):
    image = plt.imread(image_name)
    cv2.imshow('Model output', cv2.cvtColor(complete_model(image), cv2.COLOR_RGB2BGR))


def on_video(video_name='', output_filename='', live=False):
    if live:
        cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(video_name)

    if (cap.isOpened()== False): 
        print("Error opening video stream or file")

    if not live:
        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        out = cv2.VideoWriter(output_filename + '.avi', cv2.VideoWriter_fourcc('M','J','P','G'), 30, (frame_width, frame_height))

    # Read until video is completed
    while cap.isOpened():
        ret, frame = cap.read()

        if ret == True:
            frame = cv2.flip(frame, 1)
            new_frame = complete_model(frame, True)

            if not live:
                out.write(new_frame)
            else:
                cv2.imshow('Output', new_frame)
                key = cv2.waitKey(10) & 0xFF

                # Press Q on keyboard to  exit
                if key == ord('q'):
                    break
            
        else: 
            break


    cap.release()

    if not live:
        out.release()
        
    cv2.destroyAllWindows()
