# fingerSpark.py
# Connor Goggins
# Working with my partner, I developed a computer vision system in Python that is capable of recognizing various user gestures.

def forgeMask(image,boundary):
    #boundary: 2-tuple/3-list in BGR order
    lower = np.array(boundary[0], dtype='uint8')
    upper = np.array(boundary[1], dtype='uint8')
    return cv2.inRange(image,lower,upper)

def bound_(x,limits):
    return max(limits[0],min(limits[1],x))

def array_size(array):
    return [len(array[0]),len(array)]

def overlap(image,template,edges):
    y1=bound_(int(edges[0]),[0,639])
    y2=bound_(int(edges[1]),[1,640])
    x1=bound_(int(edges[2]),[0,479])
    x2=bound_(int(edges[3]),[1,480])
    #bound all values to their correct ranges and make them integers
    try:
        template=cv2.resize(template,(x2-x1,y2-y1),interpolation=cv2.INTER_LINEAR)
        #shrink the template to FXxFY size, which is always smaller than the original
        dTemplate=[len(template[0]),len(template)]
        dImage=[len(image[0]),len(image)]
        #find the dimensions of both the resized template and the image
        I_t=np.count_nonzero(image)
        T_t=np.count_nonzero(template)
        #establish the total number of white pixels in both images before cropping
        xbound=[max(0,x1),min(dTemplate[0]+x1,dImage[0])]
        ybound=[max(0,y1),min(dTemplate[1]+y1,dImage[1])]
        #establish the "area of overlap" between the two differently-sized images
        rImage=image[ybound[0]:ybound[1],xbound[0]:xbound[1]]
        rTemplate=template[ybound[0]-y1:ybound[1]-y1,xbound[0]-x1:xbound[1]-x1]
        #crop both images so they incorporate the offset and have identical size
        count=np.count_nonzero(cv2.bitwise_and(rImage,rTemplate))
        #find the raw number of pixels that overlap post-cropping and resizing
        par=(count**2)*1.0/(I_t*T_t)
        im_out=np.hstack([rImage,rTemplate,cv2.bitwise_and(rImage,rTemplate)])
        cv2.imwrite('/home/pi/Desktop/rimage.png',rImage)
        return [par,im_out]
    except:
        return [0,image]

import cv2, os, time, numpy as np
[vid_loc,vid_len,vid_fps]=['/home/pi/Desktop/v2a.h264','5000','90']
if raw_input('Record a new video? (say no)').lower()[0]=='y':
    time.sleep(3)
    os.system('sudo rm '+vid_loc)
    stem='raspivid -w 640 -h 480 -fps '
    os.system(stem+vid_fps+' -t '+vid_len+' -o '+vid_loc)
print 'Video Loaded'
cap = cv2.VideoCapture(vid_loc)
frame_jump=3
#red dot: bound=([0,100,100], [10,255,255])
#blue dot: bound=([85,100,25],[125,255,255])
bound=([85,100,25],[125,255,255])
frame_bound=int(.0009*eval(vid_fps)*eval(vid_len))
#assuming that the high-speed video misses 1/10 of the frames
while True:
    flag, frame = cap.read()
    if not flag:
        print 'Failed to read frame'
        #this indicates that there was a reading error while processing the frame
        #so skip this frame and move on to the next one
    else:
        pos_frame = cap.get(cv2.cv.CV_CAP_PROP_POS_FRAMES)
        if pos_frame%frame_jump==0:
            hsv_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
            if pos_frame==frame_jump:
                Image=forgeMask(hsv_frame,bound)
            else:
                Image=cv2.bitwise_or(Image,forgeMask(hsv_frame,bound))
    if cap.get(cv2.cv.CV_CAP_PROP_POS_FRAMES)>frame_bound:
        break

print 'Mask Generated'
cap.release()
cv2.imwrite('/home/pi/Desktop/newmask.png',Image)
templates=['horizontal2','vertical2','circle2']
for tmp in templates:
    Template=cv2.imread('/home/pi/Desktop/images/'+tmp+'.png')
    Template=forgeMask(Template,([1,1,1],[255,255,255]))
    [a,b,c,d]=[0,480,0,640]
    total=np.count_nonzero(Image)*1.0
    while True:
        cImage=Image[a:480,0:640]
        if np.count_nonzero(cImage)/total<.95:
            break
        else:
            a+=3
    while True:
        cImage=Image[0:b,0:640]
        if np.count_nonzero(cImage)/total<.95:
            break
        else:
            b-=3
    while True:
        cImage=Image[0:480,c:640]
        if np.count_nonzero(cImage)/total<.95:
            break
        else:
            c+=3
    while True:
        cImage=Image[0:480,0:d]
        if np.count_nonzero(cImage)/total<.95:
            cv2.imwrite('init_crop.png',Image[a:b,c:d])
            break
        else:
            d-=3

    overall_best=[0]
    for i in xrange(5,40,5):
        point = [a,b,c,d]
        [epsilon,delta,omega] = [.49,i*1.0,50]
        best = overlap(Image,Template,point)[0]
        cv2.imwrite('start.png',overlap(Image,Template,point)[1])
        n = 1
        while True:
            if (n > omega):
                #max iterations reached
                break
            if (delta < epsilon):
                #result converged
                break
            mylist = []
            for i in range(4):
                newpoint = [x for x in point]
                newpoint[i] += delta
                mylist.append([overlap(Image,Template,newpoint)[0],newpoint])
                newpoint[i] -= 2*delta
                mylist.append([overlap(Image,Template,newpoint)[0],newpoint])
            if best==0 and max(mylist)[0]==0:
                pass
                #all zeroes
            if max(mylist)[0] > best:
                point = max(mylist)[1]
                best=max(mylist)[0]
                if best>max(overall_best):
                    cv2.imwrite('/home/pi/Desktop/image_storage/'+str(best)+'.png',overlap(Image,Template,point)[1])
            else:
                delta = delta*.5
                #reduce delta by a factor of 2
            n+=1
        overall_best.append(best)
    print '\n'+tmp,max(overall_best)
