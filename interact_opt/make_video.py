import os
import cv2
from PIL import Image
import shutil
  
# 输入：数据种类标识，日期，返回路径
# 输出：视频文件名

def img2video(imagesPath,videoPath,fps,resize=(1.0,1.0)):
    """ 
    Desc: 将图片合成视频
    imagesPath: 图片路径
    videoPath；视频路径
    fps:  帧率 
    """
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    im = Image.open(imagesPath[0])
    size = (int(im.size[0]*resize[0]), int(im.size[1]*resize[1]))  
    vw = cv2.VideoWriter(videoPath, fourcc, fps, size)
    
    numImage=len(imagesPath)
    if numImage==0:
        print('No images')
        return
    if  numImage>fps*3600:
        print('Too many images')
        return
    
    for id in range(numImage):
        print(imagesPath[id])
        try:
            # im = cv2.imread(imagesPath[id])
            # vm.write(im)
            im = cv2.imread(imagesPath[id])
            shrink = cv2.resize(im, size, interpolation=cv2.INTER_AREA)  
            vw.write(shrink)
        except Exception as exc:
            print(imagesPath[id], exc)
            
    vw.release()
    print('Synthetic success!')
    return

def video2img(videoPath,imagesDir):
    """ 
	Desc: 将视频转换成图片
    videoPath: 视频路径 
    imagesDir: 图片路径
	"""
    cap = cv2.VideoCapture(videoPath)
    suc = cap.isOpened()
    frame_count = 0
    imagesPath=[]
    while suc:
        frame_count += 1
        suc, frame = cap.read()
        if not suc:
            break
        imageName=str(frame_count).rjust(4,'0')+'.jpg'
        imagePath=imagesDir+imageName
        print(imagePath)
        cv2.imwrite(imagePath, frame)
        imagesPath.append(imagePath)
 
    cap.release()
    print('unlock image: ', frame_count)
    return imagesPath
	
if __name__ == '__main__':
    # 输入图片
    path=os.getcwd()
    subdir='img'
    images= os.listdir(subdir)
    images.sort()
    imagesPath=[]
    for id in range(len(images)):
        imagesPath.append(os.path.join(path,subdir,images[id]))
        print(imagesPath[-1])
    
    # 图片转视频
    videoPath='video.avi'
    isExists=os.path.exists(videoPath)
    if isExists:
        os.remove(videoPath)
        
    img2video(imagesPath,videoPath,fps=4)
	
	# 视频转图片
    unlockpath='unlock/'
    isExists=os.path.exists(unlockpath)
    if isExists:
        shutil.rmtree(unlockpath)
    os.makedirs(unlockpath) 
	
    imagesPath=video2img(videoPath,unlockpath)
