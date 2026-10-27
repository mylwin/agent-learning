import collections
import re


def get_stats(vocab):
    """统计词元对频率"""
    pairs = collections.defaultdict(int)
    # 遍历词表
    for word, freq in vocab.items():
        # 将词拆分为字符列表
        symbols = word.split()
        # 遍历词元对，统计频率
        for i in range(len(symbols) - 1):
            pairs[symbols[i], symbols[i + 1]] += freq
    # 打印方便查看
    print(f"词元对频率: {dict(pairs)}")
    return pairs


def merge_vocab(pair, v_in):
    """合并词元对"""
    v_out = {}
    # escape()函数将正则表达式的字符串序列或字符序列转换成特殊字符
    bigram = re.escape(" ".join(pair))
    p = re.compile(r"(?<!\S)" + bigram + r"(?!\S)")
    for word in v_in:
        # sub()方法将正则表达式匹配的字符串替换为第二个参数
        w_out = p.sub("".join(pair), word)
        v_out[w_out] = v_in[word]
    return v_out


# 准备语料库，每个词末尾加上</w>表示结束，并切分好字符
vocab = {"h u g </w>": 1, "p u g </w>": 1, "p u n </w>": 1, "b u n </w>": 1}
num_merges = 4  # 设置合并次数

for i in range(num_merges):
    pairs = get_stats(vocab)
    if not pairs:
        break
    best = max(pairs, key=lambda pair: pairs[pair])
    vocab = merge_vocab(best, vocab)
    print(f"第{i + 1}次合并: {best} -> {''.join(best)}")
    print(f"新词表（部分）: {list(vocab.keys())}")
    print("-" * 20)
