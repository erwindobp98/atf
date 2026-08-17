# 🚀 ATF Mining Bot

Bot otomatis untuk ATF Mining menggunakan Telegram WebApp.

## ✨ Fitur

- 🔐 Login Telegram menggunakan Telethon
- 💾 Auto-save Telegram session
- 🔑 Auto mengambil WebApp Query
- 💾 Query disimpan di `queries.txt`
- 🔄 Auto refresh query jika invalid
- ⛏️ Auto start mining
- 💰 Auto claim mining
- ⚡ Auto boost mining
- 🎯 One-Time Task
- 🔁 Repeatable Task
- 🌐 Website Visit
- ▶️ YouTube Like/Comment
- 𝕏 Twitter Retweet
- 🔥 Telegram React Latest Post
- 📢 Telegram Join Channel
- 💵 Auto refresh balance
- 🔄 Auto cycle
- 👥 Multi-account
- 📊 Live terminal dashboard
- 💾 State setiap account disimpan otomatis

# ▶️ Cara Menjalankan ATF Bot

Struktur folder final :

```text
atf/
├── atf.py
├── config.json
├── queries.txt
├── sessions/
└── data/
```

## 1. Clone folder
```
git clone https://github.com/erwindobp98/atf.git
```

## 2. Install Dependency
```
pip install telethon httpx rich
```
## 3. Jalankan Bot
```
python atf.py
```

## 4. Pertama Kali Menjalankan

Jika `config.json` belum ada, bot akan membuatnya otomatis.

Isi bagian Telegram:

```json
"telegram": {
    "api_id": 12345678,
    "api_hash": "ISI_API_HASH_TELEGRAM"
}
```

dengan **API ID** dan **API HASH Telegram** milikmu.

Kemudian jalankan kembali:

```bash
python atf.py
```

## 5. Login Telegram

Pada login pertama akan muncul:

```text
Nomor Telegram untuk acc_001:
```

Masukkan nomor Telegram:

```text
+628xxxxxxxxxx
```

Kemudian:

```text
Kode OTP Telegram:
```

Masukkan kode OTP.

Jika akun menggunakan 2FA:

```text
Password 2FA Telegram:
```

Masukkan password 2FA.

Setelah berhasil, session otomatis tersimpan di:

```text
sessions/acc_001.session
```

Jadi login Telegram **tidak perlu diulang setiap menjalankan bot**.

## 6. Query WebApp

Setelah session aktif, bot akan mengambil **query WebApp Telegram** secara otomatis.

Query disimpan di:

```text
queries.txt
```

Formatnya:

```text
acc_001|query Telegram WebApp...
```

Pada run berikutnya bot akan mencoba menggunakan query yang tersimpan terlebih dahulu.

## 7. Menambah Akun

Session Telegram akan berada di:

```text
sessions/
```

Contoh:

```text
sessions/
├── acc_001.session
├── acc_002.session
└── acc_003.session
```

Bot otomatis membaca akun:

```text
acc_001
acc_002
acc_003
```

## 8. Output Bot

Dashboard akan berjalan **bergulir di tempat**, bukan mencetak dashboard baru terus-menerus.

Contohnya:

```text
🚀 ATF MINING BOT
Telegram WebApp • Repeatable Tasks • Live Dashboard

┌────────────┬──────────────────┬──────────┬─────────────────────────────┐
│ ACCOUNT    │ ACTIVITY         │ STATUS   │ DETAIL                      │
├────────────┼──────────────────┼──────────┼─────────────────────────────┤
│ acc_001    │ TELEGRAM SESSION │ OK       │ Session aktif               │
│ acc_001    │ LOGIN            │ SUCCESS  │ Query lama valid             │
│ acc_001    │ MINING           │ SUCCESS  │ +0.1234 ATF                  │
│ acc_001    │ BOOST            │ SUCCESS  │ 2x | Target=YES              │
│ acc_001    │ ONE-TIME TASK    │ SUCCESS  │ youtube_subscribe             │
│ acc_001    │ REPEAT TASK      │ SUCCESS  │ Visit website                │
│ acc_001    │ REPEAT TASK      │ SUCCESS  │ YouTube like/comment         │
│ acc_001    │ REPEAT TASK      │ SUCCESS  │ Twitter retweet              │
│ acc_001    │ REPEAT TASK      │ SUCCESS  │ React to latest post         │
│ acc_001    │ BALANCE          │ SUCCESS  │ 10.0000 -> 10.2500 ATF       │
│ acc_001    │ NEXT CYCLE       │ WAIT     │ Cycle berikutnya 59:42       │
└────────────┴──────────────────┴──────────┴─────────────────────────────┘
```

Setiap **REPEAT TASK memiliki baris sendiri**, sehingga tidak saling menimpa.

## ⚡ Perintah Paling Sederhana

Kalau `config.json` sudah benar:

```bash
pip install telethon httpx rich
python atf.py
```

Selesai. 🚀
