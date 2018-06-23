# 用Python从零开始创建区块链
该学习代码来自博客[用Python从零开始创建区块链](https://learnblockchain.cn/2017/10/27/build_blockchain_by_python/)
源码参考：https://github.com/xilibi2003/blockchain

## 环境准备

1. 安装python3.6
2. 安装pipenv
3. 创建virtual env
```
$ pipenv --python=python3.6
```
4. 安装依赖
```
$ pipenv install
```
> 主要是：
> flask = "==0.12.2"
> requests = "==2.18.4"

5. 在不同的中终端运行各自节点
```
$ pipenv run python blockchain.py
$ pipenv run python blockchain.py -p 5001
```

## 部分交互效果
以下使用curl命令进行交互，也可以使用Postman软件。

查看整个区块链
```
$ curl "http://localhost:5000/chain"
{
  "chain": [
    {
      "index": 1, 
      "previous_hash": "1", 
      "proof": 100, 
      "timestamp": 1528444452.7936225, 
      "transactions": []
    }
  ], 
  "length": 1
}
```

创建并提交一个新的交易
```
$ curl -X POST -H "Content-Type: application/json" -d '{
>  "sender": "threezhang",
>  "recipient": "fourli",
>  "amount": 5
> }' "http://localhost:5000/transactions/new"
{
  "message": "Transaction will be added to Block 2"
}
```

创建新的区块
```
$ curl "http://localhost:5000/mine" 
{
  "index": 2, 
  "message": "New Block Forged", 
  "previous_hash": "1de4e34d78c2a5736365b7a4530247e4a1d1aa14d58ba179435f19f669aea10c", 
  "proof": 35293, 
  "transactions": [
    {
      "amount": 5, 
      "recipient": "fourli", 
      "sender": "threezhang"
    }, 
    {
      "amount": 1, 
      "recipient": "755c55a96b6f48ec909ddf888a57c889", 
      "sender": "0"
    }
  ]
}
```
