from illuminate import main

if __name__ == "__main__":
    try:
        main('dev/wifi/EC:FA:BC:8A:43:D9/switch', '23:30')
    except KeyboardInterrupt:
        pass
