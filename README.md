# 🚀 ATF Mining Bot

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

```
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
cd atf
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

Jika inging mengganti bagian Telegram:

```json
"telegram": {
    "api_id": 224069,
    "api_hash": "f2ddfd53867f28a3b6b98e80fa010e9d"
}
```

dengan **API ID** dan **API HASH Telegram** milikmu.

# Cara Mendapatkan Telegram `API_ID` dan `API_HASH`

Panduan langkah demi langkah untuk mendapatkan kredensial Telegram API (`api_id` dan `api_hash`) yang diperlukan untuk pengembangan bot, userbot, atau aplikasi pihak ketiga.

---

## 📋 Langkah-langkah Pengambilan Kredensial

1. **Buka Portal Pengembang Telegram**  
   Buka peramban (browser) Anda dan kunjungi halaman resmi: [https://my.telegram.org](https://my.telegram.org)

2. **Masuk ke Akun Telegram**  
   * Masukkan **Nomor Telepon** Anda yang terhubung dengan akun Telegram (gunakan format internasional, contoh: `+6281234xxxxxx`).
   * Klik tombol **Next**.

3. **Verifikasi Kode Keamanan**  
   * Buka aplikasi Telegram di HP atau Desktop Anda.
   * Salin kode verifikasi/konfirmasi yang dikirimkan langsung oleh sistem Telegram.
   * Tempelkan kode tersebut pada kolom **Confirmation code** di situs web, lalu klik **Sign In**.

4. **Akses Menu Aplikasi**  
   * Setelah berhasil masuk, pilih menu **API development tools**.

5. **Buat Aplikasi Baru**  
   Isi formulir pembuatan aplikasi dengan ketentuan sebagai berikut:
   * **App title:** Nama aplikasi Anda (bebas, contoh: `Aplikasi Saya`).
   * **Short name:** Nama pendek tanpa spasi (contoh: `aplikasisaya`).
   * **URL:** (Opsional) Boleh dikosongkan atau diisi dengan link bebas (contoh: `https://mywebsite.com`).
   * **Platform:** Pilih platform yang sesuai (contoh: `Android`, `iOS`, atau `Desktop`).
   * **Description:** Deskripsi singkat aplikasi Anda (bebas).

6. **Simpan Kredensial**  
   * Klik tombol **Create application**.
   * Setelah berhasil, Anda akan melihat halaman rincian yang menampilkan **App api_id** dan **App api_hash**.
   * Salin dan simpan nilai `api_id` (berupa angka) serta `api_hash` (berupa deretan karakter acak) ke tempat yang aman.

---

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

```                                                         
                                                          📊 ATF MINING BOT DASHBOARD
╭─────────────┬────────────────────┬──────────────┬──────────────────────────────────────╮
│ ACCOUNT     │ ACTIVITY           │ STATUS       │ DETAIL                               │
├─────────────┼────────────────────┼──────────────┼──────────────────────────────────────┤
│ acc_001     │ ACCOUNT            │ READY        │ Bal=296.1587 ATF | Lvl=44            │
├─────────────┼────────────────────┼──────────────┼──────────────────────────────────────┤
│             │ MINING             │ SKIP         │ Mining aktif | Pend=0.0621 ATF       │
├─────────────┼────────────────────┼──────────────┼──────────────────────────────────────┤
│             │ NEXT CYCLE         │ WAIT         │ Cycle berikutnya dalam 58:41         │
├─────────────┼────────────────────┼──────────────┼──────────────────────────────────────┤
│ acc_002     │ ACCOUNT            │ READY        │ Bal=76.1265 ATF | Lvl=1              │
├─────────────┼────────────────────┼──────────────┼──────────────────────────────────────┤
│             │ MINING             │ SKIP         │ Mining aktif | Pend=0.0259 ATF       │
├─────────────┼────────────────────┼──────────────┼──────────────────────────────────────┤
│             │ NEXT CYCLE         │ WAIT         │ Cycle berikutnya dalam 59:15         │
╰─────────────┴────────────────────┴──────────────┴──────────────────────────────────────╯
```

Setiap **REPEAT TASK memiliki baris sendiri**, sehingga tidak saling menimpa.


# 🛑 Stop Bot

Tekan:

```text
CTRL + C
```

Bot akan menghentikan proses yang sedang berjalan.

---

## ⭐ Support

Jika project ini bermanfaat, silakan ⭐ repository.

## Buy Me a Coffee
EVM: 
```
0x4b05cad2a8e10dfde15d0ec4239bcb94e107ccbc
```
SOL:
```
Gj5FcTN93KLMQBmB6NbYMYe5kMZH5hgW8wjsg8dk8gse
```

**Happy Testing! 🚀**
