from ultralytics import YOLO
import cv2
import math
from datetime import datetime
import mysql.connector

def draw_dashed_line(image, start, end, color, thickness, dash_length=20):
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    angle = math.atan2(dy, dx)
    total_length = math.sqrt(dx**2 + dy**2)
    dash_count = int(total_length / dash_length)

    for i in range(dash_count):
        if i % 2 == 0:
            xa = int(x1 + i * dash_length * math.cos(angle))
            ya = int(y1 + i * dash_length * math.sin(angle))
            xb = int(x1 + (i + 1) * dash_length * math.cos(angle))
            yb = int(y1 + (i + 1) * dash_length * math.sin(angle))
            cv2.line(image, (xa, ya), (xb, yb), color, thickness)

def calculate_overlap(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    overlap_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
    overlap_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))

    overlap_area = overlap_x * overlap_y
    area1 = w1 * h1
    area2 = w2 * h2

    iou = overlap_area / (area1 + area2 - overlap_area)
    return iou

# Define your MySQL database connection parameters
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'houssamMRD007',
    'database': 'AI',
}

def initialize_database():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Create a table if it doesn't exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS passenger_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME,
        passengers_entering INT,
        passengers_sorting INT
    );
    """
    cursor.execute(create_table_query)

    connection.commit()
    connection.close()

def insert_data_into_database(timestamp, passengers_entering, passengers_sorting):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Insert data into the database
    insert_query = "INSERT INTO passenger_data (timestamp, passengers_entering, passengers_sorting) VALUES (%s, %s, %s);"
    cursor.execute(insert_query, (timestamp, passengers_entering, passengers_sorting))

    connection.commit()
    connection.close()

def video_detection(path_x):
    initialize_database()
    video_capture = path_x
    cap = cv2.VideoCapture(video_capture)
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))

    # Set a larger size for the video
    new_frame_width = 2000
    new_frame_height = 1000
    cap.set(3, new_frame_width)
    cap.set(4, new_frame_height)

    model = YOLO('yolov8n.pt')
    classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
                  "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
                  "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
                  "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
                  "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
                  "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
                  "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
                  "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
                  "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
                  "teddy bear", "hair drier", "toothbrush", "safety mask", "face shield", "hand sanitizer", "glasses",
                  ]

    persons_entering = {}
    persons_sorting = {}

    # Define the blue and red lines
    blue_line_start = (0, frame_height // 3)
    blue_line_end = (new_frame_width, frame_height // 3)
    red_line_start = (0, 2 * frame_height // 3)
    red_line_end = (new_frame_width, 2 * frame_height // 3)
    line_thickness = 5

    while True:
        success, img = cap.read()
        results = model(img, stream=True)

        # Draw blue and red lines
        draw_dashed_line(img, blue_line_start, blue_line_end, (255, 0, 0), line_thickness, dash_length=30)
        draw_dashed_line(img, red_line_start, red_line_end, (0, 0, 255), line_thickness, dash_length=30)

        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # Add a border around detected objects
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

                cls = int(box.cls[0])
                class_name = classNames[cls]

                # Check if the detected object is a person
                if class_name == "person":
                    person_id = (x1, y1, x2, y2)

                    # Check if the person crosses the blue line and not already counted
                    if y1 <= blue_line_start[1] <= y2 and person_id not in persons_entering:
                        persons_entering[person_id] = cap.get(cv2.CAP_PROP_POS_FRAMES)

                        # Optionally, draw a yellow rectangle for persons entering
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 255), 3)
                        cv2.putText(img, f' Entering ', (x1, y1 - 2), 0, 0.5, [69, 247, 78], thickness=1,
                                    lineType=cv2.LINE_AA)

                    # Check if the person crosses the red line and not already counted
                    elif y1 <= red_line_start[1] <= y2 and person_id not in persons_sorting:
                        persons_sorting[person_id] = cap.get(cv2.CAP_PROP_POS_FRAMES)

                        # Optionally, draw a red rectangle for persons sorting
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)
                        cv2.putText(img, f' Sorting ', (x1, y1 - 2), 0, 0.5, [0, 0, 255], thickness=1,
                                    lineType=cv2.LINE_AA)

        # Remove persons from the entering dictionary if they haven't crossed the blue line in the last few frames
        frames_to_keep_entering = 10
        current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
        persons_to_remove_entering = [person_id for person_id, last_frame in persons_entering.items()
                                       if current_frame - last_frame > frames_to_keep_entering]
        for person_id in persons_to_remove_entering:
            persons_entering.pop(person_id, None)

        # Remove persons from the sorting dictionary if they haven't crossed the red line in the last few frames
        frames_to_keep_sorting = 10
        persons_to_remove_sorting = [person_id for person_id, last_frame in persons_sorting.items()
                                     if current_frame - last_frame > frames_to_keep_sorting]
        for person_id in persons_to_remove_sorting:
            persons_sorting.pop(person_id, None)

        # Display the current date and time with a gray background
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        passengers_entering = len(persons_entering)
        passengers_sorting = len(persons_sorting)

        # Insert data into the MySQL database
        insert_data_into_database(current_time, passengers_entering, passengers_sorting)

        display_text = f'{current_time} | Entering: {passengers_entering} | Sorting: {passengers_sorting}'

        # Customized text properties with a gray background
        text_bg_color = (169, 169, 169)  # Gray background color
        font_size = 0.5  # Smaller font size
        line_thickness = 1  # Adjust the line thickness as needed
        text_size = cv2.getTextSize(display_text, cv2.FONT_HERSHEY_SIMPLEX, font_size, line_thickness)[0]
        cv2.rectangle(img, (10, 10), (10 + text_size[0], 30 + text_size[1]), text_bg_color, cv2.FILLED)
        font_type = cv2.FONT_HERSHEY_SIMPLEX

        # Display text
        cv2.putText(img, display_text, (20, 25), font_type, font_size, (255, 255, 255), line_thickness)

        # Optionally, you can add more icons or styling as needed

        # Show result in console
        print(f'{current_time} | Entering: {passengers_entering} | Sorting: {passengers_sorting}')

        yield img

    # Release the video capture when the program ends
    cv2.destroyAllWindows()

