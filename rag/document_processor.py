"""
文档处理模块 - 使用 LangChain
"""
import os
import json
from typing import List, Dict
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentProcessor:
    """文档处理器 - LangChain 版本"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # 使用 LangChain 的递归字符文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )

    def load_pdf(self, pdf_path: str) -> List[Document]:
        """使用 LangChain 加载 PDF 文件"""
        try:
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            # 添加元数据
            for doc in documents:
                doc.metadata.update({
                    "source": os.path.basename(pdf_path),
                    "type": "pdf",
                    "file_path": pdf_path
                })
            return documents
        except Exception as e:
            print(f"加载 PDF 错误 {pdf_path}: {e}")
            return []

    def load_json_papers(self, json_path: str) -> List[Document]:
        """加载 JSON 格式的论文信息"""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                papers = json.load(f)

            documents = []
            for paper in papers:
                # 构建论文内容
                content = f"""标题：{paper.get('title', '')}
作者：{', '.join(paper.get('authors', [])) if isinstance(paper.get('authors'), list) else paper.get('authors', '')}
期刊：{paper.get('journal', paper.get('source', ''))}
年份：{paper.get('year', '')}
DOI: {paper.get('doi', '')}
摘要：{paper.get('abstract', paper.get('summary', ''))}"""

                doc = Document(
                    page_content=content,
                    metadata={
                        "source": paper.get('title', 'unknown'),
                        "type": "paper_metadata",
                        "doi": paper.get('doi', ''),
                        "year": paper.get('year', ''),
                        "journal": paper.get('journal', paper.get('source', ''))
                    }
                )
                documents.append(doc)

            return documents
        except Exception as e:
            print(f"加载 JSON 错误 {json_path}: {e}")
            return []

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """使用 LangChain 分割文档"""
        if not documents:
            return []

        chunks = self.text_splitter.split_documents(documents)
        return chunks

    def process_papers(self, papers_dir: str) -> List[Document]:
        """处理论文目录中的所有文档"""
        all_documents = []

        # 1. 处理 PDF 文件
        print("处理 PDF 文件...")
        pdf_files = [f for f in os.listdir(papers_dir) if f.endswith(".pdf")]

        for filename in pdf_files:
            pdf_path = os.path.join(papers_dir, filename)
            print(f"  - {filename}")

            docs = self.load_pdf(pdf_path)
            if docs:
                # 分割文档
                chunks = self.split_documents(docs)
                all_documents.extend(chunks)
                print(f"    加载 {len(docs)} 页，分割为 {len(chunks)} 块")

        # 2. 处理论文信息 JSON
        print("\n处理论文信息...")
        json_path = os.path.join(papers_dir, "papers_info.json")
        if os.path.exists(json_path):
            docs = self.load_json_papers(json_path)
            # 元数据文档通常不需要再分割
            all_documents.extend(docs)
            print(f"  加载 {len(docs)} 篇论文元数据")

        print(f"\n总计：{len(all_documents)} 个文档块")
        return all_documents

    def create_sample_documents(self, papers_dir: str) -> List[Document]:
        """如果没有 PDF，从 JSON 创建示例文档"""
        json_path = os.path.join(papers_dir, "papers_info.json")

        if not os.path.exists(json_path):
            print("未找到论文信息文件")
            return []

        with open(json_path, "r", encoding="utf-8") as f:
            papers = json.load(f)

        documents = []
        for paper in papers:
            content = f"""# {paper.get('title', 'Unknown Title')}

## 作者
{', '.join(paper.get('authors', [])) if isinstance(paper.get('authors'), list) else paper.get('authors', '')}

## 发表信息
期刊：{paper.get('journal', paper.get('source', ''))}
年份：{paper.get('year', '')}
DOI: {paper.get('doi', '')}

## 摘要
{paper.get('abstract', paper.get('summary', ''))}

## 关键词
hyperspectral, salient object detection, deep learning, remote sensing"""

            doc = Document(
                page_content=content,
                metadata={
                    "source": paper.get('title', 'unknown'),
                    "type": "paper_summary",
                    "doi": paper.get('doi', '')
                }
            )
            documents.append(doc)

        # 分割文档
        chunks = self.split_documents(documents)

        # 保存为文本文件（可选）
        for i, chunk in enumerate(chunks[:20]):
            txt_path = os.path.join(papers_dir, f"paper_{i}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(chunk.page_content)

        print(f"创建 {len(chunks)} 个示例文档块")
        return chunks


if __name__ == "__main__":
    from config import Config
    processor = DocumentProcessor(Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
    documents = processor.process_papers(Config.PAPERS_DIR)
    print(f"处理完成，共 {len(documents)} 个文档块")
