# backend/tools/faq_tool.py
"""
SSS (Sıkça Sorulan Sorular) için embedding ve semantik arama tool'u
RAG-lite implementasyonu: Local embedding + FAISS arama
"""

import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Tuple
import os
import logging

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FAQTool:
    """SSS embedding ve semantik arama sınıfı"""
    
    def __init__(self, faq_file_path: str = None):
        """
        FAQTool başlatıcı
        
        Args:
            faq_file_path: SSS JSON dosyasının yolu
        """
        # Varsayılan path
        if faq_file_path is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            faq_file_path = os.path.join(base_dir, "data", "faq.json")
        
        self.faq_file_path = faq_file_path
        
        # Türkçe için optimize edilmiş multilingual model
        # Bu model Türkçe'yi de destekler ve hafif bir modeldir
        logger.info("Model yükleniyor...")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # SSS verilerini sakla
        self.faq_data = []
        self.questions = []
        self.answers = []
        self.embeddings = None
        self.index = None
        
        # SSS'leri yükle ve index'le
        self._load_and_index_faq()
        
    def _load_and_index_faq(self):
        """SSS verilerini yükle ve FAISS index oluştur"""
        try:
            # JSON dosyasını oku
            logger.info(f"SSS dosyası yükleniyor: {self.faq_file_path}")
            with open(self.faq_file_path, 'r', encoding='utf-8') as f:
                self.faq_data = json.load(f)
            
            # Soru ve cevapları ayır
            self.questions = [item['question'] for item in self.faq_data]
            self.answers = [item['answer'] for item in self.faq_data]
            
            logger.info(f"{len(self.questions)} adet SSS yüklendi")
            
            # Soruları embedding'e çevir
            logger.info("Embedding'ler oluşturuluyor...")
            self.embeddings = self.model.encode(
                self.questions,
                convert_to_numpy=True,
                show_progress_bar=True
            )
            
            # FAISS index oluştur
            dimension = self.embeddings.shape[1]
            
            # L2 mesafe ile index (daha hassas sonuçlar için)
            self.index = faiss.IndexFlatL2(dimension)
            
            # Normalizasyon ekle (cosine similarity için)
            faiss.normalize_L2(self.embeddings)
            
            # Embedding'leri index'e ekle
            self.index.add(self.embeddings.astype('float32'))
            
            logger.info(f"FAISS index oluşturuldu. Boyut: {dimension}")
            
        except FileNotFoundError:
            logger.error(f"SSS dosyası bulunamadı: {self.faq_file_path}")
            raise
        except json.JSONDecodeError:
            logger.error("SSS dosyası geçerli bir JSON değil")
            raise
        except Exception as e:
            logger.error(f"SSS yüklenirken hata: {str(e)}")
            raise
    
    def search(self, query: str, top_k: int = 3, threshold: float = 0.7) -> List[Dict]:
        """
        Kullanıcı sorusuna en yakın SSS'leri bul
        
        Args:
            query: Kullanıcının sorusu
            top_k: Döndürülecek maksimum sonuç sayısı
            threshold: Minimum benzerlik skoru (0-1 arası)
            
        Returns:
            En yakın SSS kayıtlarının listesi
        """
        try:
            # Query'yi embedding'e çevir
            query_embedding = self.model.encode([query], convert_to_numpy=True)
            
            # Normalize et
            faiss.normalize_L2(query_embedding)
            
            # FAISS ile arama yap
            distances, indices = self.index.search(
                query_embedding.astype('float32'), 
                min(top_k, len(self.questions))
            )
            
            # Sonuçları hazırla
            results = []
            
            for idx, distance in zip(indices[0], distances[0]):
                # L2 mesafeyi benzerlik skoruna çevir
                # Normalized vektörler için: similarity = 1 - (distance^2 / 2)
                similarity_score = 1 - (distance / 2)
                
                # Threshold kontrolü
                if similarity_score >= threshold:
                    result = {
                        'question': self.questions[idx],
                        'answer': self.answers[idx],
                        'similarity_score': float(similarity_score),
                        'confidence': self._get_confidence_level(similarity_score)
                    }
                    
                    # Orijinal veri'de category varsa ekle
                    if 'category' in self.faq_data[idx]:
                        result['category'] = self.faq_data[idx]['category']
                    
                    results.append(result)
            
            # Skor'a göre sırala (yüksekten düşüğe)
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info(f"Sorgu: '{query[:50]}...' için {len(results)} sonuç bulundu")
            
            return results
            
        except Exception as e:
            logger.error(f"Arama sırasında hata: {str(e)}")
            return []
    
    def _get_confidence_level(self, score: float) -> str:
        """
        Benzerlik skoruna göre güven seviyesi belirle
        
        Args:
            score: Benzerlik skoru (0-1)
            
        Returns:
            Güven seviyesi (high/medium/low)
        """
        if score >= 0.9:
            return "high"
        elif score >= 0.8:
            return "medium"
        else:
            return "low"
    
    def add_faq(self, question: str, answer: str, category: Optional[str] = None) -> bool:
        """
        Yeni SSS ekle ve index'i güncelle
        
        Args:
            question: Soru
            answer: Cevap
            category: Kategori (opsiyonel)
            
        Returns:
            Başarılı ise True
        """
        try:
            # Yeni SSS'i veri listesine ekle
            new_faq = {"question": question, "answer": answer}
            if category:
                new_faq["category"] = category
            
            self.faq_data.append(new_faq)
            self.questions.append(question)
            self.answers.append(answer)
            
            # Yeni soru için embedding oluştur
            new_embedding = self.model.encode([question], convert_to_numpy=True)
            faiss.normalize_L2(new_embedding)
            
            # Index'e ekle
            self.index.add(new_embedding.astype('float32'))
            
            # Embedding listesini güncelle
            if self.embeddings is not None:
                self.embeddings = np.vstack([self.embeddings, new_embedding])
            
            # JSON dosyasını güncelle
            with open(self.faq_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.faq_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Yeni SSS eklendi: {question[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"SSS eklenirken hata: {str(e)}")
            return False
    
    def get_stats(self) -> Dict:
        """SSS istatistiklerini döndür"""
        return {
            "total_faqs": len(self.questions),
            "embedding_dimension": self.embeddings.shape[1] if self.embeddings is not None else 0,
            "index_size": self.index.ntotal if self.index else 0,
            "model_name": "paraphrase-multilingual-MiniLM-L12-v2"
        }


# Singleton pattern için global instance
_faq_tool_instance: Optional[FAQTool] = None

def get_faq_tool() -> FAQTool:
    """
    FAQTool singleton instance'ını döndür
    
    Returns:
        FAQTool instance
    """
    global _faq_tool_instance
    
    if _faq_tool_instance is None:
        _faq_tool_instance = FAQTool()
    
    return _faq_tool_instance


# Tool catalog'a eklemek için fonksiyon
def search_faq(query: str, top_k: int = 3) -> Dict:
    """
    SSS'de arama yap (Tool catalog için wrapper)
    
    Args:
        query: Kullanıcı sorusu
        top_k: Maksimum sonuç sayısı
        
    Returns:
        Arama sonuçları
    """
    tool = get_faq_tool()
    results = tool.search(query, top_k=top_k)
    
    if results:
        return {
            "success": True,
            "results": results,
            "query": query
        }
    else:
        return {
            "success": False,
            "message": "İlgili SSS bulunamadı",
            "query": query
        }


# Test için main fonksiyon
if __name__ == "__main__":
    # Tool'u başlat
    faq = get_faq_tool()
    
    # İstatistikleri göster
    print("\n=== SSS Tool İstatistikleri ===")
    stats = faq.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Test sorguları
    test_queries = [
        "Mobil bankacılık şifremi nasıl alabilirim?",
        "Şifremi unuttum ne yapmalıyım?",
        "Para transferi nasıl yapılır?",
        "Kredi başvurusu yapabilir miyim?",
        "Hesap bakiyemi nasıl görürüm?",
        "Güvenlik için ne yapmalıyım?"
    ]
    
    print("\n=== Test Sorguları ===")
    for query in test_queries:
        print(f"\nSorgu: {query}")
        results = faq.search(query, top_k=2, threshold=0.6)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"  {i}. Benzerlik: {result['similarity_score']:.2%} ({result['confidence']})")
                print(f"     Soru: {result['question'][:60]}...")
                print(f"     Cevap: {result['answer'][:80]}...")
        else:
            print("  Sonuç bulunamadı")