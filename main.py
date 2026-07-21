
import cv2
import numpy as np
import os

video_file = 'Lane Detection Test Video 01.mp4'

if not os.path.exists(video_file):
    exit()

cam = cv2.VideoCapture(video_file)

left_top = (0, 0)
left_bottom = (0, 0)
right_top = (0, 0)
right_bottom = (0, 0)

while True:
    ret, frame = cam.read()

    # ret (bool): Return code of the `read` operation. Did we get an image or not?
    #             (if not maybe the camera is not detected/connected etc.)

    # frame (array): The actual frame as an array.
    #                Height x Width x 3 (3 colors, BGR) if color image.
    #                Height x Width if Grayscale
    #                Each element is 0-255.
    #                You can slice it, reassign elements to change pixels, etc.

    if ret is False:
        break

    # Exercitiul 2
    height, width, _ = frame.shape
    frame = cv2.resize(frame, (width // 2, height // 2))
    height, width, _ = frame.shape

    # Exercitiul 3
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Exercitiul 4
    top_y = int(height * 0.75)
    upper_left = (int(width * 0.45), top_y)
    upper_right = (int(width * 0.55), top_y)
    lower_right = (width - 1, height - 1)
    lower_left = (0, height - 1)

    trapezoid_bounds = np.array([upper_left, upper_right, lower_right, lower_left], dtype=np.int32)
    trapezoid_points = np.zeros((height, width), dtype=np.uint8)

    cv2.fillConvexPoly(trapezoid_points, trapezoid_bounds, 1)
    road = gray_frame * trapezoid_points

    # Exercitiul 5
    frame_bounds = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype=np.float32)
    trapezoid_bounds_float = np.float32(trapezoid_bounds)
    matrix = cv2.getPerspectiveTransform(trapezoid_bounds_float, frame_bounds)
    top_down = cv2.warpPerspective(road, matrix, (width, height))

    #Exercitiul 6
    blur_frame = cv2.GaussianBlur(top_down, (5, 5), 0)

    # Exercitiul 7
    sobelV_result = cv2.Sobel(blur_frame, cv2.CV_32F, 1, 0, ksize=3)
    sobelH_result = cv2.Sobel(blur_frame, cv2.CV_32F, 0, 1, ksize=3)
    combined = cv2.magnitude(sobelV_result, sobelH_result)

    # Exercitiul 8
    sobel_abs = cv2.normalize(combined, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    _, binarized = cv2.threshold(sobel_abs, 35, 255, cv2.THRESH_BINARY)

    cv2.imshow('Binarized Version', binarized)

    # Exercitiul 9
    cleaned = binarized.copy()
    margin = int(width * 0.05)
    cleaned[:, :margin] = 0
    cleaned[:, width - margin:] = 0
    cv2.imshow('Cleaned', cleaned)

    left_half = cleaned[:, :width // 2]
    right_half = cleaned[:, width // 2:]
    
    left_points = np.argwhere(left_half > 0)
    right_points = np.argwhere(right_half > 0)
    
    left_ys = left_points[:, 0]
    left_xs = left_points[:, 1]
    right_ys = right_points[:, 0]
    right_xs = right_points[:, 1] + width // 2

    # Exercitiul 10
    def fit_lane(xs, ys):
        if len(xs) < 2:
            return None
        coeffs = np.polynomial.polynomial.polyfit(xs, ys, 1)
        b, a = coeffs[0], coeffs[1]

        if abs(a) < 0.1:
            return None
         
        return a, b
    
    left_coeffs = fit_lane(left_xs, left_ys)
    right_coeffs = fit_lane(right_xs, right_ys)
    
    def get_line_points(coeffs, height, width, prev_top, prev_bottom):
        if coeffs is None:
            return prev_top, prev_bottom
        
        a, b = coeffs
        
        y1 = 0
        y2 = height - 1
        
        x1 = int((y1 - b) / a) if a != 0 else 0
        x2 = int((y2 - b) / a) if a != 0 else 0
        
        if x1 < 0 or x1 >= width or x2 < 0 or x2 >= width:
            return prev_top, prev_bottom
        
        return (x1, y1), (x2, y2)
    
    left_top, left_bottom = get_line_points(left_coeffs, height, width, left_top, left_bottom)
    right_top, right_bottom = get_line_points(right_coeffs, height, width, right_top, right_bottom)

    # Exercitiul 11
    matrix_inverse = cv2.getPerspectiveTransform(frame_bounds, trapezoid_bounds_float)

    left_lane_frame = np.zeros((height, width), dtype=np.uint8)
    cv2.line(left_lane_frame, left_top, left_bottom, 255, 3)
    left_lane_transformed = cv2.warpPerspective(left_lane_frame, matrix_inverse, (width, height))
    left_coords = np.argwhere(left_lane_transformed > 0)

    right_lane_frame = np.zeros((height, width), dtype=np.uint8)
    cv2.line(right_lane_frame, right_top, right_bottom, 255, 3)
    right_lane_transformed = cv2.warpPerspective(right_lane_frame, matrix_inverse, (width, height))
    right_coords = np.argwhere(right_lane_transformed > 0)

    output_frame = frame.copy()
    if len(left_coords) > 0:
        output_frame[left_coords[:, 0], left_coords[:, 1]] = (50, 50, 250)
    if len(right_coords) > 0:
        output_frame[right_coords[:, 0], right_coords[:, 1]] = (50, 250, 50)

    # Exercitiul 12
    cv2.imshow('Lane Detection', output_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
