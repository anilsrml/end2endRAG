# end2endRAG çalışma notları

- Türkçe iletişim kur.
- WSL2 yalnız geliştirme ortamıdır; hedef çalışma ortamı Windows üzerindeki Docker Desktop'tır.
- Önce çalışan, küçük MVP'yi koru; cloud deployment, auth, Elasticsearch, OCR ve konuşma hafızasını kullanıcı istemeden ekleme.
- Gerçek API anahtarlarını, kişisel belgeleri ve `.env` dosyasını repoya ekleme.
- Değişiklikleri test et; public arayüz ve README davranışla birlikte güncel kalsın.

## Kalıcı bağlam protokolü

- Her yeni oturumda işe başlamadan önce sırasıyla `PROJECT_STATE.md`, `README.md` ve `git status` çıktısını incele.
- `PROJECT_STATE.md` uygulamanın mevcut durumuyla ilgili tek doğruluk kaynağıdır; sohbet geçmişine güvenme.
- Anlamlı bir geliştirme, teknik karar, doğrulama sonucu veya engel oluştuğunda `PROJECT_STATE.md` dosyasını aynı oturumda güncelle.
- Oturum sonunda tamamlanan işi, doğrulama sonuçlarını ve sonraki en fazla üç somut adımı kaydet.
- Kararlı kullanıcı özellikleri ve kurulum adımları değişirse `README.md` dosyasını da güncelle.
- Kişisel hedefler ve üst seviye proje bağlamı Obsidian'daki `🏰 300-Projects/end2endRAG.md` notunda tutulur; uygulama durumu için önce repo dosyasını esas al.
