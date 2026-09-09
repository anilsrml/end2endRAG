# end2endRAG — Proje Durumu

Son güncelleme: 2026-09-09

Bu dosya oturumlar arasındaki teknik bağlamın tek doğruluk kaynağıdır. Yeni bir çalışma
oturumunda önce `AGENTS.md`, ardından bu dosya ve `README.md` okunmalıdır.

## Amaç

Windows bilgisayarda Docker Desktop üzerinde yerel olarak çalışan, CV ve portföyü
güçlendirecek uçtan uca bir hybrid RAG uygulaması geliştirmek. WSL2 yalnızca geliştirme
ortamıdır; şu aşamada canlıya alma hedefi yoktur.

## Mevcut kapsam

- FastAPI backend ve küçük chat arayüzü
- LangGraph tabanlı sorgu akışı
- PostgreSQL + pgvector semantic search
- PostgreSQL full-text keyword search
- Reciprocal Rank Fusion ile hybrid retrieval
- OpenAI embeddings
- OpenRouter üzerinden GPT/LLM erişimi
- Opsiyonel Cohere reranking ve LangSmith tracing
- Markdown ve metin tabanlı PDF yükleme
- Alembic migration, Dockerfile ve Docker Compose kurulumu

## Tamamlananlar

- MVP proje iskeleti ve temel uygulama kodu oluşturuldu.
- Veritabanı migration'ı ve `pgvector` kurulumu tanımlandı.
- Belge yükleme, parçalama, retrieval ve soru-cevap akışları eklendi.
- Basit chat arayüzü, birim testleri ve GitHub Actions workflow'u eklendi.
- `.env` Git dışında tutuldu; `.env.example` örnek yapılandırma olarak eklendi.
- Docker Compose yapılandırması `docker compose config --quiet` ile doğrulandı.
- Hedef GitHub deposu public olarak ayarlandı: `anilsrml/end2endRAG`.
- Yerel Git deposu yeniden oluşturuldu; ilk MVP commit'i `main` dalına gönderildi ve
  `origin/main` takibi yapılandırıldı.
- GitHub Actions üzerinde bağımlılık kurulumu, Ruff ve pytest kontrolleri başarıyla geçti.

## Güncel engeller ve belirsizlikler

- Codex ortamı Docker socket erişimine izin vermeyebilir. Tam image build ve container
  testi gerekirse Windows terminalinde Docker Desktop üzerinden çalıştırılmalıdır.
- WSL ortamında `uv`, `pytest` ve `ruff` komutları kalıcı olarak kurulu değil; doğrulamalar
  GitHub Actions üzerinde tamamlandı.
- Gerçek API anahtarlarıyla uçtan uca belge yükleme ve sorgu testi henüz doğrulanmadı.

## Doğrulama durumu

| Kontrol | Durum | Sonuç |
|---|---|---|
| `docker compose config --quiet` | Başarılı | 2026-09-09 |
| `uv run pytest` | Başarılı | GitHub Actions, 2026-09-09 |
| `uv run ruff check .` | Başarılı | Yerel geçici Ruff kurulumu ve GitHub Actions, 2026-09-09 |
| Docker image build | Bekliyor | Docker daemon erişimi gerekli |
| Uçtan uca RAG sorgusu | Bekliyor | API anahtarları ve çalışan container gerekli |
| GitHub push kontrolü | Başarılı | `main` dalı `anilsrml/end2endRAG` deposuna gönderildi |

## Sonraki üç adım

1. Windows Docker Desktop üzerinde `docker compose up --build` çalıştır; veritabanı,
   migration ve API health kontrollerini doğrula.
2. Örnek belgeleri yükleyip hybrid retrieval ve kaynaklı yanıt akışını uçtan uca test et.
3. Belge yükleme ve sorgu endpointleri için veritabanı destekli entegrasyon testleri ekle.

## Sabit kararlar

- Üretim veya cloud deployment bu sürümün kapsamında değildir.
- Elasticsearch, auth, OCR ve konuşma hafızası ilk MVP'ye eklenmeyecektir.
- Kişisel belgeler, gerçek API anahtarları ve `.env` public repoya gönderilmeyecektir.
- Uygulama Windows üzerinde Docker Desktop ile çalışacak; geliştirme WSL2'de yapılacaktır.
- CV değeri için çalışan demo, okunabilir mimari, testler ve dokümantasyon önceliklidir.

## Oturum kapatma kontrol listesi

- Tamamlanan işi ve yeni kararları bu dosyaya işle.
- Çalıştırılan testleri ve gerçek sonuçlarını güncelle.
- Sonraki adımları en fazla üç maddeyle somutlaştır.
- Hassas veri bulunmadığını kontrol et.
- Git kullanılabiliyorsa anlamlı bir checkpoint commit oluştur.
