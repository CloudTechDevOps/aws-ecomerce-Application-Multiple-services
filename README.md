# Smart eCommerce Platform1
<img src="ops.png" width="1700"/>

## AWS Deployment Order

Deploy in this order:

1. Create Amazon RDS MySQL database.
2. Deploy the Flask backend on one Amazon Linux EC2 instance.
3. Deploy the frontend with Nginx on another Amazon Linux EC2 instance.

```

## 1. Create RDS MySQL

In AWS Console:

- Open **RDS**.
- Create database.
- Engine: **MySQL**.
- Template: **Free tier** for practice.
- DB name: `cloud`
- Master username: example `admin`
- Save the password.
- Public access: choose based on your setup. If backend runs from EC2 in same VPC, public access can be **No**.
- Security group inbound rule: allow MySQL port `3306` from your EC2 security group.

After RDS is ready, copy the RDS endpoint, for example:

```bash
your-rds-endpoint.xxxxxx.ap-south-1.rds.amazonaws.com
```

## 2. Connect To Backend EC2


Update Amazon Linux and install packages:


For Amazon Linux 2, use:

```bash
sudo yum update -y
sudo yum install -y git  python3-pip  mariadb105-server
```

Clone your project:

```bash
sudo su -
git clone YOUR_GITHUB_REPO_URL aws-ecommerce-otp-authentication
cd aws-ecommerce-otp-authentication/backend
```

## 3. Import Database Schema To RDS

Test RDS connection:

```bash
mysql -h your-rds-endpoint -u admin -p < test.sql
```

Import the schema:

```bash
mysql -h your-rds-endpoint -u admin -pCloud123 < test.sql
```

## 4. Deploy Backend On EC2

Create Python virtual environment:

```bash
cd aws-ecommerce-otp-authentication/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create backend environment file:

```bash
vi .env
```

Add these values:

```bash
PORT=5000
FLASK_DEBUG=false
DB_HOST=your-rds-endpoint
DB_USER=admin
DB_PASSWORD=your-rds-password
DB_NAME=cloud
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
```

Test backend manually:

```bash
source venv/bin/activate
python3 app.py
```

Open another SSH terminal and test:

```bash
curl http://127.0.0.1:5000/api
```

You should see:

```json
{"message":"API is running successfully"}
```


## 5. Connect To Frontend EC2


Install packages:

For Amazon Linux 2:

```bash
sudo yum update -y
sudo yum install -y git nginx
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl status nginx
```

Clone project on frontend EC2:

```bash
sudo su -
git clone YOUR_GITHUB_REPO_URL aws-ecommerce-otp-authentication
cd aws-ecommerce-otp-authentication/frontend
```

## 6. Deploy Frontend With Nginx

Copy frontend files to Nginx web root:

```bash
sudo cp -r * /usr/share/nginx/html/
sudo cp -r main/* /usr/share/nginx/html/
```

Create Nginx config:

```bash
sudo vi /etc/nginx/conf.d/google-store.conf
```

Paste:

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location = /api {
        proxy_pass http://BACKEND_PRIVATE_IP:5000/api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://BACKEND_PRIVATE_IP:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Replace `BACKEND_PRIVATE_IP` with the backend EC2 private IP. Example:

```nginx
proxy_pass http://172.31.10.25:5000/api;
proxy_pass http://172.31.10.25:5000/api/;
```

Remove default config if it exists:

```bash
sudo rm -f /etc/nginx/conf.d/default.conf
```

Test and start Nginx:

```bash
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
sudo systemctl status nginx
```
