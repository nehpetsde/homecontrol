from illuminate import main

if __name__ == "__main__":
    try:
        main('dev/wifi/5C:CF:7F:7A:90:24/switch', '23:50')
    except KeyboardInterrupt:
        pass
