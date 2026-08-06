# FactBite Otomasyonu

Bu klasör, FactBite Instagram sayfası için günlük carousel gönderilerini
otomatik üretip yayınlayan botu içerir.

## Nasıl çalışıyor

Her gün (varsayılan: 08:00 İstanbul saati) GitHub Actions otomatik olarak:
1. Claude API'den TR/EN/ES/AR dillerinde bir "günün bilgisi" ister
2. 4 slaytlık görseli marka şablonuyla oluşturur (`posts/<tarih>/slide_1..4.png`)
3. Görselleri repoya commit'leyip push'lar (Instagram Graph API görsele
   herkese açık bir URL istediği için görselleri repodan servis ediyoruz)
4. Instagram Graph API üzerinden carousel'i yayınlar

## Kurulum

### 1. Bu klasörü bir GitHub reposuna yükle
Yeni bir repo oluştur (public repo olması gerekiyor, çünkü Graph API'nin
görsellere erişebilmesi için raw.githubusercontent.com linkleri public
olmalı), bu klasördeki her şeyi push'la.

### 2. Repo Secrets ekle
GitHub reposunda: **Settings → Secrets and variables → Actions → New repository secret**

Üç secret ekle:
- `ANTHROPIC_API_KEY` — console.anthropic.com üzerinden alınan API anahtarın
- `IG_ACCESS_TOKEN` — Meta Developer panelinden aldığın uzun ömürlü Instagram access token
- `IG_USER_ID` — Instagram business hesabının ID'si (sende: `17841437422396013`)

### 3. Workflow'u test et
Repo'da **Actions** sekmesine git → "Daily FactBite Post" → **Run workflow**
ile elle bir kere tetikleyip her şeyin çalıştığını doğrula.

### 4. Token yenileme
Instagram access token'ı ~60 günde bir sona eriyor. Süresi dolmadan
Meta Developer panelinden yeni bir token alıp `IG_ACCESS_TOKEN` secret'ını
güncellemen gerekecek (bunu da otomatikleştirmek mümkün, istersen ekleriz).

## Yerelde test etmek istersen

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python scripts/generate_content.py
python scripts/render_slides.py
# posts/<bugünün tarihi>/ klasöründeki slaytları kontrol et
```

(`publish_instagram.py` sadece GitHub Actions içinde, görseller repoya
push'landıktan sonra çalıştırılmalı — yerelde görseller public URL'de
olmadığı için Instagram tarafı hata verir.)

## Saati değiştirmek

`.github/workflows/daily-post.yml` içindeki cron satırını düzenle:
```
- cron: "0 5 * * *"   # UTC saatinde — 05:00 UTC = 08:00 İstanbul (yaz saati)
```
