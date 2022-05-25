from website import create_app, io

app = create_app()

if __name__ == '__main__':
    io.run(app, debug=True)       #wraps around the typical run(app) method
