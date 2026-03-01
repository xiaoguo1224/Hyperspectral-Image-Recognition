#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAG 系统测试脚本
测试所有 API 接口的功能
"""
import os
import sys
import json
import requests
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# API 基础 URL
BASE_URL = "http://localhost:5000/api/rag"

# 测试颜色
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def test_health():
    """测试健康检查"""
    print_header("测试 1: 健康检查")
    
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"健康检查通过")
            print_info(f"响应：{json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print_error(f"健康检查失败：{response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"请求失败：{e}")
        print_info("请确保 Flask 应用已启动：python gradio.py")
        return False

def test_stream_query():
    """测试流式查询"""
    print_header("测试 3: 流式查询 (SSE)")
    
    test_question = "神经网络的基本结构是什么？"
    print_info(f"问题：{test_question}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/query/stream",
            json={
                "question": test_question,
                "k": 5,
                "use_history": True
            },
            stream=True,
            timeout=60
        )
        
        if response.status_code == 200:
            print_success("流式查询成功")
            print_info("接收流式响应：\n")
            
            answer = ""
            sources = []
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            msg_type = data.get('type')
                            
                            if msg_type == 'answer':
                                chunk = data.get('content', '')
                                answer += chunk
                                print(chunk, end='', flush=True)
                            elif msg_type == 'sources':
                                sources = data.get('content', [])
                            elif msg_type == 'done':
                                print("\n")
                                print_info(f"完整答案长度：{len(answer)}")
                                print_info(f"来源：{sources}")
                                break
                            elif msg_type == 'error':
                                print_error(f"流式查询错误：{data.get('content')}")
                                return False
                        except json.JSONDecodeError:
                            pass
            
            return True
        else:
            print_error(f"HTTP 错误：{response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"请求失败：{e}")
        return False


def test_search():
    """测试相似性搜索"""
    print_header("测试 4: 相似性搜索")
    
    test_query = "卷积神经网络"
    print_info(f"搜索：{test_query}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/search",
            json={
                "query": test_query,
                "k": 3
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                print_success("搜索成功")
                results = data.get("data", {}).get("results", [])
                print_info(f"找到 {len(results)} 个结果")
                
                for i, result in enumerate(results[:2], 1):
                    print_info(f"\n结果 {i}:")
                    print_info(f"来源：{result.get('metadata', {}).get('source')}")
                    print_info(f"内容：{result.get('content', '')[:150]}...")
                
                return True
            else:
                print_error(f"搜索失败：{data.get('error')}")
                return False
        else:
            print_error(f"HTTP 错误：{response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"请求失败：{e}")
        return False


def test_memory():
    """测试记忆管理"""
    print_header("测试 5: 记忆管理")
    
    try:
        # 获取记忆统计
        response = requests.get(f"{BASE_URL}/memory/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success("获取记忆统计成功")
            print_info(f"统计：{json.dumps(data.get('data', {}), indent=2, ensure_ascii=False)}")
        else:
            print_error(f"获取记忆统计失败：{response.status_code}")
        
        # 获取对话历史
        response = requests.get(f"{BASE_URL}/memory/history", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success("获取对话历史成功")
            history = data.get("data", {}).get("history", "")
            if history:
                print_info(f"历史对话：\n{history[:300]}...")
            else:
                print_info("暂无历史对话")
        else:
            print_error(f"获取对话历史失败：{response.status_code}")
        
        return True
        
    except Exception as e:
        print_error(f"请求失败：{e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print_header("RAG 系统功能测试")
    
    results = []
    
    # 测试 1: 健康检查
    results.append(("健康检查", test_health()))
    
    # 等待一下
    time.sleep(1)

    
    # 等待一下
    time.sleep(1)
    
    # 测试 3: 流式查询
    results.append(("流式查询", test_stream_query()))
    
    # 等待一下
    time.sleep(1)
    
    # 测试 4: 相似性搜索
    results.append(("相似性搜索", test_search()))
    
    # 等待一下
    time.sleep(1)
    
    # 测试 5: 记忆管理
    results.append(("记忆管理", test_memory()))
    
    # 等待一下
    time.sleep(1)

    
    # 汇总结果
    print_header("测试结果汇总")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.OKGREEN}通过{Colors.ENDC}" if result else f"{Colors.FAIL}失败{Colors.ENDC}"
        print(f"  {name}: {status}")
    
    print(f"\n总计：{passed}/{total} 测试通过")
    
    if passed == total:
        print_success("所有测试通过！✓")
        return True
    else:
        print_error(f"有 {total - passed} 个测试失败")
        return False


def main():
    """主函数"""
    print_info("RAG 系统测试脚本")
    print_info(f"API 地址：{BASE_URL}")
    print_info("请确保 Flask 应用已启动：python gradio.py\n")
    
    # 询问是否运行所有测试
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"测试异常：{e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
