from app import app
import sys

def main():
    try:
        # Make the server accessible from other devices on the network
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
