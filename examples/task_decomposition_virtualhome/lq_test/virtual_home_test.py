from virtualhome.simulation import unity_simulator
import cv2

YOUR_FILE_NAME = "/home/lq/Downloads/linux_exec/linux_exec.v2.3.0.x86_64"
comm = unity_simulator.UnityCommunication()
# Start the first environment
# comm.reset(0)
# Get an image of the first camera
success, image = comm.camera_image([0])

# Check that the image exists
print(image[0].shape)
cv2.imwrite('a.png',image[0])