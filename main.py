from website import create_app, io

#psycopg2==2.9.3

app = create_app()

if __name__ == '__main__':
    io.run(app, debug=True)       #wraps around the typical run(app) method
