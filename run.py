import os
from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Default to port 5050 to avoid MacOS AirPlay receiver conflict on 5000
    port = int(os.environ.get('PORT', 5050))
    print(f"🚀 Server Tin học 11 (Ứng dụng) đang chạy tại: http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
