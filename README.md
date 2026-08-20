# Kadam Foundation Website
> Young steps towards the nation

---

## 🚀 Quick Start

```bash
pip install flask
python app.py
# Open → http://localhost:5000
```

---

## 📁 Project Structure

```
kadam/
├── app.py                        ← Flask server + all routes + auth logic
├── requirements.txt
├── static/
│   ├── css/
│   │   ├── main.css              ← Public website styles
│   │   └── admin.css             ← Admin panel styles
│   └── js/
│       └── main.js               ← Public JS (animations, forms, counters)
└── templates/
    ├── base.html                 ← Public layout (nav + footer)
    ├── index.html                ← Home page (with Instagram section)
    ├── about.html
    ├── programs.html
    ├── stories.html
    ├── volunteer.html
    ├── donate.html
    └── admin/
        ├── base_admin.html       ← Admin layout (sidebar)
        ├── login.html
        ├── dashboard.html
        ├── instagram.html        ← Update 3 Instagram post URLs
        ├── stats.html            ← Edit homepage stats
        ├── volunteers.html       ← View volunteer applications
        ├── messages.html         ← View contact messages
        ├── change_password.html  ← Step 1: enter auth code
        ├── set_password.html     ← Step 2: set new password
        ├── change_authcode.html  ← Masterkey-only: change auth code
        └── login.html
```

---

## 🔐 Security System (Three-Tier)

### Tier 1 — Regular Password
- Used for: daily admin login
- Default: `kadam2024`
- How to change: Login → Change Password → Enter Auth Code → Set New Password

### Tier 2 — Auth Code
- Used for: verifying password change requests
- Default: `KADAM@auth`
- How to change: Login with Masterkey → Change Auth Code section

### Tier 3 — Masterkey (Dynamic)
- Used for: emergency access + changing auth code
- Never stored anywhere — calculated fresh each day
- Formula: `lsfs,kadam` + (sum of digits of today in DDMMYYYY × 123)

**Masterkey Examples:**
| Date       | DDMMYYYY | Digit Sum | × 123 | Masterkey              |
|------------|----------|-----------|-------|------------------------|
| 21/03/2026 | 21032026 | 16        | 1968  | `lsfs,kadam1968`       |
| 22/03/2026 | 22032026 | 17        | 2091  | `lsfs,kadam2091`       |
| 01/01/2027 | 01012027 | 13 (0+1+0+1+2+0+2+7) | 1599 | `lsfs,kadam1599` |

**Dev helper** (remove before production!):
```
GET /admin/masterkey-hint
```

---

## 📸 Instagram Setup

1. Go to Admin Panel → Instagram URLs
2. Paste your 3 latest post URLs
3. The homepage will display them with oEmbed previews
4. Clicking any post opens it on Instagram

---

## 🌐 Public Routes

| Route        | Page              |
|--------------|-------------------|
| `/`          | Home              |
| `/about`     | About Us          |
| `/programs`  | Programs          |
| `/stories`   | Stories & Impact  |
| `/volunteer` | Volunteer         |
| `/donate`    | Donate            |

## 🔧 API Endpoints

| Method | Route              | Description                     |
|--------|--------------------|---------------------------------|
| GET    | `/api/stats`       | Returns site stats as JSON      |
| GET    | `/api/instagram`   | Returns 3 Instagram post embeds |
| POST   | `/api/volunteer`   | Submit volunteer application    |
| POST   | `/api/contact`     | Submit contact message          |

## 🛡️ Admin Routes

| Route                     | Access          |
|---------------------------|-----------------|
| `/admin/login`            | Public          |
| `/admin`                  | Regular/Master  |
| `/admin/instagram`        | Regular/Master  |
| `/admin/stats`            | Regular/Master  |
| `/admin/volunteers`       | Regular/Master  |
| `/admin/messages`         | Regular/Master  |
| `/admin/change-password`  | Anyone (needs auth code) |
| `/admin/change-authcode`  | Masterkey only  |

---

## ⚠️ Before Production

1. Change `app.secret_key` in `app.py` to a long random string
2. Remove the `/admin/masterkey-hint` route
3. Replace in-memory `state` dict with a real database (SQLite / PostgreSQL)
4. Set up HTTPS (SSL certificate)
5. Change default password and auth code
