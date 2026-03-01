"""
测试脚本 - 验证系统各组件
"""
import sys

def test_ollama():
    """测试 Ollama 连接"""
    import requests
    from rag.config import Config
    
    print("测试 Ollama 连接...")
    try:
        response = requests.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama 连接成功，找到 {len(models)} 个模型")
            for model in models:
                print(f"   - {model['name']}")
            return True
        else:
            print(f"❌ Ollama 返回错误：{response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama 连接失败：{e}")
        return False


def test_embedding():
    """测试嵌入模型"""
    from langchain_ollama import OllamaEmbeddings
    from rag.config import Config
    
    print("\n测试嵌入模型...")
    embedding = OllamaEmbeddings(model=Config.EMBEDDING_MODEL, base_url=Config.OLLAMA_BASE_URL)
    
    result = embedding.embed_query("测试文本")
    if result and len(result) > 0:
        print(f"✅ 嵌入模型工作正常，向量维度：{len(result)}")
        return True
    else:
        print(f"❌ 嵌入模型失败")
        return False


def test_crawler():
    """测试爬虫"""
    from dataRetrieval.paper_crawler import PaperCrawler
    from rag.config import Config
    
    print("\n测试论文爬虫...")
    crawler = PaperCrawler(Config.PAPERS_DIR)
    
    # 测试 arXiv 搜索
    papers = crawler.search_arxiv("hyperspectral", max_results=3)
    if papers:
        print(f"✅ arXiv 搜索成功，找到 {len(papers)} 篇论文")
        for p in papers[:2]:
            print(f"   - {p['title'][:50]}...")
        return True
    else:
        print("⚠️  arXiv 搜索未返回结果")
        return False


def test_llm():
    """测试 LLM"""
    import requests
    from rag.config import Config
    
    print("\n测试 LLM...")
    url = f"{Config.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": Config.LLM_MODEL,
        "prompt": "Hello",
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            print(f"✅ LLM 工作正常")
            return True
        else:
            print(f"❌ LLM 返回错误：{response.status_code}")
            print(f"   可能需要下载模型：ollama pull {Config.LLM_MODEL}")
            return False
    except Exception as e:
        print(f"❌ LLM 测试失败：{e}")
        print(f"   可能需要下载模型：ollama pull {Config.LLM_MODEL}")
        return False


def main():
    """运行所有测试"""
    print("=" * 50)
    print("RAG 系统组件测试")
    print("=" * 50)
    
    results = {
        "Ollama 连接": test_ollama(),
        "嵌入模型": test_embedding(),
        "论文爬虫": test_crawler(),
        "LLM": test_llm()
    }
    
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\n总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统可以正常使用")
    else:
        print("\n⚠️  部分测试失败，请检查配置")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
