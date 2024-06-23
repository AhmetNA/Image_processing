import cv2
import numpy as np

# Kamera nesnesini başlat
cap = cv2.VideoCapture(0)

while True:
    # Kameradan bir kare al
    ret, frame = cap.read()
    
    if not ret:
        break
    
    # Görüntüyü HSV renk alanına çevir
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Renk aralıklarını belirle
    # Kırmızı renk için
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = mask_red1 + mask_red2

    # Yeşil renk için
    lower_green = np.array([36, 100, 100])
    upper_green = np.array([86, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)

    # Sarı renk için
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([30, 255, 255])
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # Maskeleri uygula
    red_output = cv2.bitwise_and(frame, frame, mask=mask_red)
    green_output = cv2.bitwise_and(frame, frame, mask=mask_green)
    yellow_output = cv2.bitwise_and(frame, frame, mask=mask_yellow)
    
    # Renk yoğunluklarını hesapla
    red_intensity = cv2.countNonZero(mask_red)
    green_intensity = cv2.countNonZero(mask_green)
    yellow_intensity = cv2.countNonZero(mask_yellow)
    
    # En büyük alanların piksel sayısını bul ve dikdörtgen içine al
    def max_contour_area_and_draw(mask, color):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            max_contour = max(contours, key=cv2.contourArea)
            max_area = cv2.contourArea(max_contour)
            x, y, w, h = cv2.boundingRect(max_contour)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            return max_area
        return 0
    
    max_red_area = max_contour_area_and_draw(mask_red, (0, 0, 255)) # Kırmızı dikdörtgen
    max_green_area = max_contour_area_and_draw(mask_green, (0, 255, 0)) # Yeşil dikdörtgen
    max_yellow_area = max_contour_area_and_draw(mask_yellow, (0, 255, 255)) # Sarı dikdörtgen
    
    # Yoğunlukları yazdır
    if max_red_area > 1000:
        print("Kirmizi")
    elif max_green_area > 1000:
        print("Yesil")
    elif max_yellow_area > 1000:
        print("Sari")
    else:
        print("Renk Yok")
    # Sonuçları göster
    cv2.imshow('Frame', frame)
    cv2.imshow('Red Mask', red_output)
    cv2.imshow('Green Mask', green_output)
    cv2.imshow('Yellow Mask', yellow_output)
    
    # Çıkmak için 'q' tuşuna basın
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Kaynakları serbest bırak
cap.release()
cv2.destroyAllWindows()
