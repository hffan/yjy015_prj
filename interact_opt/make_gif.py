import os

#from PIL import ImageGrab
import time
import imageio    
from PIL import Image


from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True


def img2gif(gif_path,imagesPath,fps):
    """ 
    Desc: 将图片合成动画
    videoPath；视频路径
    imagesPath: 图片路径
    fps:  帧率 
    """
    gif_images = []
    for id in range(len(imagesPath)):
        print (imagesPath[id])
        #im=imageio.imread(imagesPath[id])
        im=imageio.imread(imagesPath[id])
        gif_images.append(im) 
    
    imageio.mimsave(gif_path, gif_images, fps=fps) 
    
    print('Synthetic success!')
 
if __name__ == '__main__':
	# 输入图片
    path=os.getcwd()
    imgdir='img'
    images= os.listdir(imgdir)
    images.sort()
    imagesPath=[]
    for id in range(len(images)):
        imagesPath.append(os.path.join(path,imgdir,images[id]))
        print(imagesPath[-1])
    
    # 输出动画
    gif_path=imgdir+'.gif'
    isExists=os.path.exists(gif_path)
    if isExists:
        os.remove(gif_path)
        
    img2gif(gif_path,imagesPath,fps=4)
    
    
    
