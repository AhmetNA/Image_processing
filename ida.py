import cv2
import numpy as np
import tkinter as tk
from tkinter import LabelFrame, messagebox
from PIL import Image, ImageTk
import threading
import time
from datetime import datetime
import pigpio
import pytesseract
## Tesseract dosyasından fonksiyonu import et
from tesseract import rakam_ve_konum_oku
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'



# Tkinter ana penceresi
master = tk.Tk()

# Başlangıç penceresi boyutları
canvas_genislik = 1000
canvas_yukseklik = 450
panel_genislik = 150
panel_yukseklik = 250
panel_margin = 10
top_margin = 20

# Tkinter ana penceresi
master.title("Kamera ve Veri Okuma Uygulamasi")

# Kanvas oluşturma
canvas = tk.Canvas(master, width=canvas_genislik, height=canvas_yukseklik)
canvas.pack()
def label_frame_olusturma(master, text, relx, rely, relwidth, relheight):
    label_frame = LabelFrame(master, text=text)
    label_frame.place(relx=relx, rely=rely, relwidth=relwidth, relheight=relheight)
    return label_frame

# Veri Paneli (Kamera görüntüsü burada olacak)
label_frame_veri = label_frame_olusturma(master, "Veri", 0.04, top_margin / canvas_yukseklik, 0.5, 0.65)

# Araç Paneli (başka bir örnek için)
label_frame_arac = label_frame_olusturma(master, "Araç", 0.6, 0.04, 0.34, 0.1)
label_arac = tk.Label(label_frame_arac, text="arac ismi icin simdilik bos birakilmistir")
label_arac.pack(padx=15, pady=5, anchor=tk.NW)

# Sonuç Paneli (veriler burada gösterilecek)
label_frame_sonuc = label_frame_olusturma(master, "Sonuç", 0.6, 0.2, 0.35, 0.5)

# Fonksiyon Paneli
label_frame_fonksiyon = label_frame_olusturma(master, "Fonksiyon", 0.6, 0.6, 0.35, 0.3)

# Kamera açma butonu
def btnCamera():
    start_video_capture()

# Diğer buton fonksiyonları
def btnBatma():
    messagebox.showinfo("Bilgi", "Batma butonuna tikandi")
def btnCikma():
    messagebox.showinfo("Bilgi", "Çıkma butonuna tıklandı")

def btnSag():
    messagebox.showinfo("Bilgi", "Sağ butonuna tıklandı")

def btnSol():
    messagebox.showinfo("Bilgi", "Sol butonuna tıklandı")

def btnIleri():
    messagebox.showinfo("Bilgi", "İleri butonuna tıklandı")

def btnGeri():
    messagebox.showinfo("Bilgi", "Geri butonuna tıklandı")

def btnReset():
    messagebox.showinfo("Bilgi", "Reset butonuna tıklandı")

def btnArm():
    messagebox.showinfo("Bilgi", "Arm butonuna tıklandı")

def btnDisarm():
    messagebox.showinfo("Bilgi", "Disarm butonuna tıklandı")

def btnStabilize():
    messagebox.showinfo("Bilgi", "Stabilize butonuna tıklandı")

def btnAuto():
    messagebox.showinfo("Bilgi", "Auto butonuna tıklandı")

# Color limit
color_limit = 123

# Butonları yerleştirme
buton_metinleri = ["Batma", "Çıkma", "Sağ", "Sol", "İleri", "Geri", "Kamera", "Reset", "Arm", "Disarm", "Stabilize", "Auto"]
buton_fonksiyonlari = [btnBatma, btnCikma, btnSag, btnSol, btnIleri, btnGeri, btnCamera, btnReset, btnArm, btnDisarm, btnStabilize, btnAuto]

for i, metin in enumerate(buton_metinleri):
    row, column = divmod(i, 2)
    buton = tk.Button(label_frame_fonksiyon, text=metin, width=10, height=1, background='White', command=buton_fonksiyonlari[i])
    buton.grid(row=row, column=column, padx=40, pady=3)

# Sonuç paneline veri yazdırmak için fonksiyon
def update_sonuc_panel(text):
    for widget in label_frame_sonuc.winfo_children():
        widget.destroy()
    label = tk.Label(label_frame_sonuc, text=text)
    label.pack()

def find_center_of_counters(mask, color, frame):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        max_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(max_contour)
        if M['m00'] != 0:
            cX = int(M['m10'] / M['m00'])
            cY = int(M['m01'] / M['m00'])
        else:
            cX, cY = 0, 0  # Default value if division by zero would occur
        max_area = cv2.contourArea(max_contour)
        x, y, w, h = cv2.boundingRect(max_contour)
        if max_area > color_limit:
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            return max_area, mask[y:y + h, x:x + w].sum() // 255, (cX, cY)
        else:
            return 0, 0, (0, 0)
    else:
        return 0, 0, (0, 0)  # Return 0 area and pixel count if no contours are found

def find_mid_way(center1, center2):
    mid_x = (center1[0] + center2[0]) // 2
    mid_y = (center1[1] + center2[1]) // 2
    return (mid_x, mid_y)

# Motorların bağlı olduğu GPIO pinleri
left_motor_pin = 17   # Sol motor ESC pini
right_motor_pin = 18  # Sağ motor ESC pini

# ESC'leri kontrol etmek için pigpio nesnesi oluştur
pi = pigpio.pi()

# PWM genişlikleri (Mikro-saniye cinsinden)
min_pulse_width = 1000  # Minimum PWM genişliği (Motor durur)
max_pulse_width = 2000  # Maksimum PWM genişliği (Motor tam hız)

step_delay = 0.01  # Kademeler arasındaki gecikme süresi (saniye)
step_size = 10  # Kademeli artış miktarı

def gradual_move(pin, target_pulse_width):
    current_pulse_width = pi.get_servo_pulsewidth(pin)
    step = step_size if target_pulse_width > current_pulse_width else -step_size

    for pulse_width in range(current_pulse_width, target_pulse_width, step):
        pi.set_servo_pulsewidth(pin, pulse_width)
        time.sleep(step_delay)
    
    pi.set_servo_pulsewidth(pin, target_pulse_width)
def turn_left():
    update_sonuc_panel("Sola dön")
    # Sol motoru yavaşlat, sağ motoru hızlandır
    gradual_move(left_motor_pin, min_pulse_width)
    gradual_move(right_motor_pin, max_pulse_width)
    time.sleep(1)
    stop_motors()
    pass

def turn_right():
    update_sonuc_panel("Sağa dön")
    # Sağ motoru yavaşlat, sol motoru hızlandır
    gradual_move(left_motor_pin, max_pulse_width)
    gradual_move(right_motor_pin, min_pulse_width)
    time.sleep(1)
    stop_motors()
    pass
def go_straight():
    update_sonuc_panel("Düz git")
    # İki motoru aynı hızda çalıştır
    gradual_move(left_motor_pin, max_pulse_width)
    gradual_move(right_motor_pin, max_pulse_width)
    time.sleep(1)
    stop_motors()
    pass

def stop_motors():
    # Motorları durdur
    gradual_move(left_motor_pin, min_pulse_width)
    gradual_move(right_motor_pin, min_pulse_width)
    

def calculate_distance(point1, point2):
    return np.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

# Video akışını başlatacak fonksiyon
def start_video_capture():
    label_veri = tk.Label(label_frame_veri)
    label_veri.pack()
    def video_thread():
        
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            messagebox.showerror("Hata", "Kamera bulunamadi veya acilamadi!")
            return

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        video_filename = f"Akriha_Control_{now}.avi"
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(video_filename, fourcc, 20.0, (frame_width, frame_height))

        while cap.isOpened():
            
            ret, frame = cap.read()
            
            if ret:
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                
                # Kırmızı renk için maske
                lower_red1 = np.array([0, 120, 70])
                upper_red1 = np.array([10, 255, 255])
                mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
                lower_red2 = np.array([170, 120, 70])
                upper_red2 = np.array([180, 255, 255])
                mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
                mask_red = mask_red1 + mask_red2

                # Yeşil renk için maske
                lower_green = np.array([36, 100, 100])
                upper_green = np.array([86, 255, 255])
                mask_green = cv2.inRange(hsv, lower_green, upper_green)

                # Sarı renk için maske
                lower_yellow = np.array([20, 100, 100])
                upper_yellow = np.array([30, 255, 255])
                mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
                
                red_output = cv2.bitwise_and(frame, frame, mask=mask_red)
                green_output = cv2.bitwise_and(frame, frame, mask=mask_green)
                yellow_output = cv2.bitwise_and(frame, frame, mask=mask_yellow)

                max_red_area, red_pixels, red_center = find_center_of_counters(mask_red, (0, 0, 255), frame)
                max_green_area, green_pixels, green_center = find_center_of_counters(mask_green, (0, 255, 0), frame)
                max_yellow_area, yellow_pixels, yellow_center = find_center_of_counters(mask_yellow, (0, 255, 255), frame)
                
                if max_red_area > color_limit:
                    color_detected = f"Kirmizi: {red_pixels} piksel"
                elif max_green_area > color_limit:
                    color_detected = f"Yesil: {green_pixels} piksel"
                elif max_yellow_area > color_limit:
                    color_detected = f"Sari: {yellow_pixels} piksel"
                else:
                    color_detected = "Renk Yok"

                # GÖRDÜĞÜ FARKLI RENKTE TOP SAYISI
                def check_balls(red_center, green_center, yellow_center, orjin):
                    orjin_x_range = range(orjin[0] - 310, orjin[0] + 310)
                    
                    red_in_range = red_center[0] in orjin_x_range
                    green_in_range = green_center[0] in orjin_x_range
                    yellow_in_range = yellow_center[0] in orjin_x_range
                    warning_txt = "Cant see"
                    ball_counter = 0
                    if red_in_range:
                        warning_txt = "kirmizi gorunuyor "
                        ball_counter += 1
                    if green_in_range:
                        warning_txt += "yesil gozukuyor "
                        ball_counter += 1
                    if yellow_in_range:
                        warning_txt += "sari gorunuyor "
                        ball_counter += 1
                    update_sonuc_panel(warning_txt)
                    return ball_counter
                
    # ORTA NOKTA BULMA VE YUVARLAK ÇİZME
                # En uzun mesafeyi bul ve orta noktaya mor yuvarlak çiz
        # KONTURLAR ARASI MESAFE
                # Sarı ile kırmızı ve sarı ile yeşil arasındaki mesafeleri hesapla
                def find_widest_distance(red_center, green_center, yellow_center):
                    if red_center != (0, 0) and yellow_center != (0, 0):
                        dist_red_yellow = calculate_distance(red_center, yellow_center)
                    else:
                        dist_red_yellow = 0
                    
                    # Yeşil ile sarı arasındaki mesafeyi hesapla
                    if green_center != (0, 0) and yellow_center != (0, 0):
                        dist_green_yellow = calculate_distance(green_center, yellow_center)
                    else:
                        dist_green_yellow = 0

                    # Yeşil ile kırmızı ve yeşil ile sarı arasındaki mesafeleri hesapla
                    if green_center != (0, 0) and red_center != (0, 0):
                        dist_green_red = calculate_distance(green_center, red_center)
                    else:
                        dist_green_red = 0
                    return dist_red_yellow, dist_green_yellow, dist_green_red
                
                dist_red_yellow, dist_green_yellow, dist_green_red = find_widest_distance(red_center, green_center, yellow_center)
                # Sari varsa
                def find_ways():
                    # EĞER İKİ TOP GÖRÜYORSA YOL ÇİZ YOKSA DÜZ GİT
                    ball_count = check_balls(red_center, green_center, yellow_center, orjin)
                    if ball_count >= 2:
                        mid_way = (0, 0)
                        if yellow_center != (0, 0) and (red_center != (0, 0) or green_center != (0, 0)):
                            if dist_red_yellow > dist_green_yellow:
                                mid_way = find_mid_way(red_center, yellow_center)
                            else:
                                mid_way = find_mid_way(green_center, yellow_center)
                        elif red_center != (0, 0) and green_center != (0, 0):
                            mid_way = find_mid_way(green_center, red_center)
                        else:
                            mid_way = (0, 0)
                        # Eğer orta nokta yoksa topları bul
                        if mid_way != (0, 0):
                            cv2.circle(frame , mid_way , 10 ,(255 ,0 ,255) , -1)
                    else :
                        mid_way = (0, 0)

    # KAMERA ORTA NOKTASI İLE DENKLEŞTİRME
                # kamera orjini
                orjin=(322,240)

                def drive_boat(mid_way, orjin):
                    cv2.circle(frame,orjin,5,(0,0,0),-1)
            
                    mid_way_x , mid_way_y = mid_way
                    
                    if mid_way_x < orjin[0]-20:
                        turn_right()
                    elif mid_way_x > orjin[0]+20:
                        turn_left()
                    else:
                        go_straight()
                
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(img)

                def update_gui():
                    label_veri.imgtk = imgtk
                    label_veri.config(image=imgtk)
                    height, width, _ = frame.shape
                    update_sonuc_panel(f"Görüntü Boyutu: {width}x{height}\n{color_detected}\n")

                master.after(0, update_gui)
                out.write(frame)

            else:
                break

            time.sleep(0.05)  # Görüntü güncellemeleri arasında küçük bir bekleme süresi

        cap.release()
        out.release()

    threading.Thread(target=video_thread, daemon=True).start()

# Tkinter ana döngüsü
master.mainloop()


#TODO:
#ilk gorev bittikten sonraki kısımda izlenecek algoritmaya baglı bu fonksiyon guncellenecek
"""def toplardansonra(gemi_görüyor_fn, orjin,red_center,öneri3_metin):
                    x_min, x_max = orjin[0] - 300, orjin[0] + 300
                    red_in_range = x_min <= red_center[0] <= x_max
                    
                    if gemi_uyarısı_metin == "üç topu da görmüyorum":
                        öneri3_metin = "80 derece sağa kır"
                    elif gemi_uyarısı_metin == "kırmızı topu görüyorum":
                        if red_center[0]+200 < orjin[0]:  # Kırmızı top geminin sağındaysa
                            öneri3_metin = "düz devam et"
                        elif red_center[0] >= orjin[0]:  # Kırmızı top geminin solundaysa
                            öneri3_metin = "sola kır"
                    else:
                        öneri3_metin = "daha parkurdan çıkmadık"
                    
                    return öneri3_metin"""