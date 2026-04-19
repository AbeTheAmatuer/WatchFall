import argparse
import serial
import sys
import time

try:
    import cv2
    import numpy as np
except ImportError:
    print("This viewer requires opencv-python and numpy. Install with: pip install opencv-python numpy pyserial")
    sys.exit(1)

FRAME_WIDTH = 96
FRAME_HEIGHT = 96
FRAME_SIZE = FRAME_WIDTH * FRAME_HEIGHT
FRAME_MAGIC = b"\xAA\x55"


def find_port():
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    if len(ports) == 1:
        return ports[0].device

    for port in ports:
        desc = port.description.lower()
        hwid = port.hwid.lower() if port.hwid else ""
        if any(keyword in desc for keyword in ["pico", "rp2040", "usbserial", "usb serial", "serial device"]) or \
                any(keyword in hwid for keyword in ["2e8a", "pico"]):
            return port.device
    return None


def print_ports():
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports were found on this system.")
        return
    print("Available serial ports:")
    for port in ports:
        print(f"  {port.device}: {port.description} [{port.hwid}]")


def draw_status(text, subtext=None):
    blank = np.zeros((FRAME_HEIGHT * 3, FRAME_WIDTH * 3, 3), dtype=np.uint8)
    cv2.putText(blank, "WatchFall Viewer", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(blank, text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    if subtext:
        cv2.putText(blank, subtext, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.imshow("WatchFall Camera", blank)
    cv2.waitKey(1)


def init_window():
    cv2.namedWindow("WatchFall Camera", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("WatchFall Camera", FRAME_WIDTH * 3, FRAME_HEIGHT * 3)
    draw_status("Waiting for camera stream...", "Press q to exit.")


def main():
    parser = argparse.ArgumentParser(description="WatchFall Pico camera stream viewer")
    parser.add_argument("port", nargs="?", help="Serial port for the Pico (e.g. COM4)")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate")
    args = parser.parse_args()

    init_window()

    port = args.port or find_port()
    if not port:
        print("Could not automatically find the Pico USB serial port. Specify it as an argument.")
        print_ports()
        print("The blank window is open for verification. Press q in the window to exit.")
        while True:
            if cv2.waitKey(100) & 0xFF == ord("q"):
                break
        return

    print(f"Opening {port} @ {args.baud}...")
    try:
        ser = serial.Serial(port, args.baud, timeout=1)
    except serial.SerialException as e:
        print(f"Could not open serial port {port}: {e}")
        return

    sync = False
    frame_buffer = bytearray()
    total_bytes = 0
    last_data_time = time.time()
    data_received = False

    while True:
        data = ser.read(1024)
        if data:
            total_bytes += len(data)
            last_data_time = time.time()
            data_received = True
            print(f"Received {len(data)} bytes, total {total_bytes}")
            draw_status("Data received from serial.", f"Total bytes: {total_bytes}")
            frame_buffer.extend(data)
        else:
            if not data_received:
                draw_status("Waiting for serial data...", "No camera frames received yet.")
            else:
                draw_status("Connected. Waiting for next frame...", f"Total bytes: {total_bytes}")

        while True:
            if not sync:
                idx = frame_buffer.find(FRAME_MAGIC)
                if idx == -1:
                    # keep buffer if it might contain partial header
                    if len(frame_buffer) > 4 * FRAME_SIZE:
                        frame_buffer = frame_buffer[-4:]
                    break
                del frame_buffer[:idx]
                if len(frame_buffer) < 2:
                    break
                del frame_buffer[:2]
                sync = True

            if sync and len(frame_buffer) >= FRAME_SIZE:
                frame_data = bytes(frame_buffer[:FRAME_SIZE])
                del frame_buffer[:FRAME_SIZE]
                sync = False

                frame = np.frombuffer(frame_data, dtype=np.uint8).reshape((FRAME_HEIGHT, FRAME_WIDTH))
                frame = cv2.resize(frame, (FRAME_WIDTH * 3, FRAME_HEIGHT * 3), interpolation=cv2.INTER_NEAREST)
                cv2.imshow("WatchFall Camera", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    ser.close()
                    return
            else:
                break

        if cv2.waitKey(1) & 0xFF == ord("q"):
            ser.close()
            return

        if time.time() - last_data_time > 5 and data_received:
            draw_status("Connected but no frame boundary found.", f"Total bytes: {total_bytes}")


if __name__ == "__main__":
    main()
