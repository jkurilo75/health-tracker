# health-tracker
personal project to track my sugar and blood pressure from phone hosted on pythonanywhere

Main page look (demo.bmp)

Database storage (SQLite)
Backend API (Flask routes)
Data entry forms (HTML)
Analytics (averages)
Data visualization (Chart.js from https://cdn.jsdelivr.net/npm/chart.js)
Mobile UI (Bootstrap from https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css)

create .env file and put your secret keys there (either google email or http://resend.com/ service api key) :
EMAIL_ADDRESS="sender@gmail.com"
EMAIL_PASSWORD="sender app password for sending emails via smtp"
RESEND_API_KEY="resend service api key"