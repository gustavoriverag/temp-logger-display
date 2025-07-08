#!/usr/bin/python3

import socket
import threading
from datetime import datetime
import sqlite3
import time

HOST = '0.0.0.0'
PORT = "1234"


def run_server(db_path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, int(PORT)))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.listen(1)
        print(f"Server listening on {HOST}:{PORT}")

        while True:
            try:
                print("Waiting for a connection...")
                conn, addr = s.accept()
                conn.settimeout(5)  # Set a timeout for the connection
                print(f"Connection established with {addr}")
                try:
                    with conn.makefile('rb') as f:
                        command = f.readline()
                        try:
                            command = command.decode('utf-8').strip() 
                            temp, humidity = map(float, command.split(','))
                            print(f"Received temperature: {temp}, humidity: {humidity}")
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            try: 
                                with sqlite3.connect(db_path) as db:
                                    cursor = db.cursor()
                                    cursor.execute("CREATE TABLE IF NOT EXISTS temps (id INTEGER PRIMARY KEY, timestamp DATETIME DEFAULT (datetime('now')), temperature REAL, humidity REAL)")
                                    cursor.execute("INSERT INTO temps (timestamp, temperature, humidity) VALUES (?, ?, ?)", (timestamp, temp, humidity))
                                    db.commit()
                                    print("Data inserted into database successfully")
                            except sqlite3.Error as e:
                                print("Database error:", e)
                                
                        except ValueError:
                            print("Invalid command received:", command)
                except ConnectionResetError:
                    print("Connection reset by peer")
                except socket.timeout:
                    print("Socket timeout occurred")
                except Exception as e:
                    print("An unexpected error occurred:", e)
                finally:
                    conn.close()
            except socket.timeout:
                print("Socket timeout occurred while accepting connection")
                continue
            except Exception as e:
                print("An unexpected error occurred while accepting connection:", e)
                time.sleep(1)

def run_server_in_background(db_path):
    server_thread = threading.Thread(target=run_server, args=(db_path,))
    server_thread.daemon = True  # Allow the thread to exit when the main program exits
    server_thread.start()
    return server_thread