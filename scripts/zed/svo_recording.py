########################################################################
#
# Copyright (c) 2022, STEREOLABS.
#
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
########################################################################

import sys
import pyzed.sl as sl
from signal import signal, SIGINT
import argparse 
import os 

cam = sl.Camera()

#Handler to deal with CTRL+C properly
def handler(signal_received, frame):
    cam.disable_recording()
    cam.close()
    sys.exit(0)

signal(SIGINT, handler)

def get_whole_camera_params(calibration_params: sl.CalibrationParameters, init: sl.InitParameters):
    baseline = calibration_params.get_camera_baseline()
    unit = init.coordinate_units
    print(f"Baseline: {baseline} {unit}")
    print("--------------------------------")
    print("left eye")
    get_eye_params(calibration_params.left_cam)
    print("--------------------------------")
    print("right eye")
    get_eye_params(calibration_params.right_cam)


def get_eye_params(eye_params: sl.CameraParameters):
    fx = eye_params.fx
    fy = eye_params.fy
    cx = eye_params.cx
    cy = eye_params.cy
    disto = eye_params.disto
    v_fov = eye_params.v_fov
    h_fov = eye_params.h_fov
    d_fov = eye_params.d_fov
    image_size = eye_params.image_size
    width, height = image_size.width, image_size.height
    focal_length = eye_params.focal_length_metric  # in millimeters
    print(f"fx: {fx}")
    print(f"fy: {fy}")
    print(f"cx: {cx}")
    print(f"cy: {cy}")
    print(f"disto: {disto}")
    print(f"v_fov: {v_fov}")
    print(f"h_fov: {h_fov}")
    print(f"d_fov: {d_fov}")
    print(f"image_size (w, h): {width}, {height}")
    print(f"focal_length: {focal_length} mm")

def main(opt):

    init = sl.InitParameters()
    init.depth_mode = sl.DEPTH_MODE.NONE # Set configuration parameters for the ZED
    init.camera_resolution = sl.RESOLUTION.HD1080 # Set resolution to HD1080
    init.camera_fps = 30 # Set FPS to 30
    init.async_image_retrieval = False; # This parameter can be used to record SVO in camera FPS even if the grab loop is running at a lower FPS (due to compute for ex.)

    status = cam.open(init) 
    if status != sl.ERROR_CODE.SUCCESS: 
        print("Camera Open", status, "Exit program.")
        exit(1)

    # Get the camera information
    camera_info = cam.get_camera_information().camera_configuration
    resolution = camera_info.resolution
    fps = camera_info.fps
    calibration_params = camera_info.calibration_parameters
    firmware_version = camera_info.firmware_version
    print(f"Resolution: {resolution}")
    print(f"FPS: {fps}")
    print(f"Firmware Version: {firmware_version}")

    get_whole_camera_params(calibration_params, init)
        
    recording_param = sl.RecordingParameters(opt.output_svo_file, sl.SVO_COMPRESSION_MODE.H264) # Enable recording with the filename specified in argument
    err = cam.enable_recording(recording_param)
    if err != sl.ERROR_CODE.SUCCESS:
        print("Recording ZED : ", err)
        exit(1)

    runtime = sl.RuntimeParameters()
    print("SVO is Recording, use Ctrl-C to stop.") # Start recording SVO, stop with Ctrl-C command
    frames_recorded = 0

    while True:
        if cam.grab(runtime) == sl.ERROR_CODE.SUCCESS : # Check that a new image is successfully acquired
            frames_recorded += 1
            print("Frame count: " + str(frames_recorded), end="\r")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_svo_file', type=str, help='Path to the SVO file that will be written', required= True)
    opt = parser.parse_args()
    if not opt.output_svo_file.endswith(".svo") and not opt.output_svo_file.endswith(".svo2"): 
        print("--output_svo_file parameter should be a .svo file but is not : ",opt.output_svo_file,"Exit program.")
        exit()
    main(opt)