
import hashlib
import json
from time import time
from textwrap import dedent
from uuid import uuid4
import requests
from urllib.parse import urlparse
from flask import Flask, jsonify, request

class Blockchain(object):
	def __init__(self):
		self.current_transactions = []
		self.chain = []
		# Use a 'set' to avoid the duplicate node easily
		self.nodes = set()

		# Create the genesis block # 创始块
		self.new_block(previous_hash='1', proof=100)

	def register_node(self, address):
		"""
		Add a new node to the list of nodes
		:param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
		:return: None
		"""
		parsed_url = urlparse(address)
		self.nodes.add(parsed_url.netloc)

	def new_block(self, proof, previous_hash=None):
		block = {
			'index': len(self.chain)+1,
			'timestamp': time(),
			'transactions': self.current_transactions,
			'proof': proof,
			'previous_hash': previous_hash or self.hash(self.chain[-1]),
		}

		# Reset the current list of transactions
		self.current_transactions = []
		self.chain.append(block)

		return block

	def new_transaction(self, sender, recipient, amount):
		"""
		生成新交易信息，信息将加入到下一个待挖的区块中
		:param sender: <str> Address of the Sender
		:param recipient: <str> Address of the Recipient
		:param amount: <int> Amount
		:return: <int> The index of the Block thar will hold this transaction	
		"""
		self.current_transactions.append({
			'sender': sender,
			'recipient': recipient,
			'amount': amount,
		})

		return self.last_block['index'] + 1

	@property
	def last_block(self):
		return self.chain[-1]

	@staticmethod
	def hash(block):
		"""
		生成块的 SHA-256 hash值
		:param block: <dict> Block
		:return: <str>
		"""	

		# We must make sure thar the Dictionary is Ordered, or we'll have inconsistent hashes
		block_string = json.dumps(block, sort_keys=True).encode()
		return hashlib.sha256(block_string).hexdigest()

	def proof_of_work(self, last_proof):
		"""
		简单的工作量证明：
		- 查找一个p' 使得hask(pp')以4个0开头
		- p 是上一个块的证明， p'是当前的证明
		:param last_proof: <int>
		:return: <int>
		"""
		proof = 0;
		while self.valid_proof(last_proof, proof) is False:
			proof += 1

		return proof

	def valid_chain(self, chain):
		"""
		Determine if a given blockchain is valid
		:param chain: <list> A blockchain
		:return: <bool> True if valid, False if not
		"""
		last_block = chain[0]
		current_index = 1

		while current_index < len(chain):
			block = chain[current_index]
			print(f'{last_block}')
			print(f'{block}')
			print('\n----------\n')
			# Check that the hash of the block is correct
			if block['previous_hash'] != self.hash(last_block):
				return False

			# Check that the Proof of work is correct
			if not self.valid_proof(last_block['proof'], block['proof']):
				return False

			last_block = block
			current_index += 1

		return True

	def resolve_conflicts(self):
		"""
		共识算法解决冲突
		使用网络中最长的链
		:return: <bool> True if the chain be repaced, else False
		"""
		neighbours = self.nodes
		new_chain = None

		# We're only looking for chains longer than ours
		max_length = len(self.chain)
		
		# Grab and veriry the chains from all the nodes in our network
		for node in neighbours:
			response = requests.get(f'http://{node}/chain')	

			if response.status_code == 200:
				length = response.json()['length']
				chain = response.json()['chain']

				# Check if the length is longer and the chain is valid
				if length > max_length and self.valid_chain(chain):
					max_length = length
					new_chain = chain

		# Replace our chain if we discoverd a new, valid chain longer than ours
		if new_chain:
			self.chain = new_chain
			return True

		return False


	@staticmethod
	def valid_proof(last_proof, proof):
		"""
		验证证明：是否hash(last_proof, proof)以4个0开头?
		:param: last_proof: <int> Previous Proof
		:param: proof: <int> Current Proof
		:return: <bool> True if correct, False if not	
		"""
		guess = f'{last_proof}{proof}'.encode()
		guess_hash = hashlib.sha256(guess).hexdigest()
		return guess_hash[:4] == "0000"


# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
	# We run the proof of work algorithm to get the next proof...
	last_block = blockchain.last_block
	last_proof = last_block['proof']
	proof = blockchain.proof_of_work(last_proof)

	# 给工作量证明的节点提供奖励
	# 发送者为“0”表明是新挖出的币
	blockchain.new_transaction(
		sender="0",
		recipient = node_identifier,
		amount = 1,
	)

	# Forge the new Block by adding it to the chain
	block = blockchain.new_block(proof)

	response = {
		'message': "New Block Forged",
		'index': block['index'],
		'transactions': block['transactions'],
		'proof': block['proof'],
		'previous_hash': block['previous_hash'],
	}
	return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
	values = request.get_json()
	
	# Check that the required fields are in the POST'ed data
	required = ['sender', 'recipient', 'amount']
	if not all(k in values for k in required):
		return 'Missing values', 400

	# Create a new Transaction
	index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

	response = {'message': f'Transaction will be added to Block {index}'}
	return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
	response = {
		'chain': blockchain.chain,
		'length': len(blockchain.chain),
	}
	return jsonify(response), 200

@app.route('/nodes', methods=['GET'])
def full_nodes():
	response = {
		'nodes': list(blockchain.nodes),
		'length': len(blockchain.nodes),
	}
	return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
	values = request.get_json()
	
	nodes = values.get('nodes')
	if nodes is None:
		return "Error: Please supply a valid list of nodes", 400

	for node in nodes:
		blockchain.register_node(node)
	
	response = {
		'message': 'New nodes have been added',
		'total_nodes': list(blockchain.nodes),
	}

	return jsonify(response), 201

# 解决冲突的路由
@app.route('/nodes/resolve', methods=['GET'])
def consensus():
	replaced = blockchain.resolve_conflicts()
	
	if replaced:
		response = {
			'message': 'Our chain was replaced',
			'new_chain': blockchain.chain
		}
	else:
		response = {
			'message': 'Our chain is authoritative',
			'chain': blockchain.chain
		}

	return jsonify(response), 200



if __name__ == '__main__':
	from argparse import ArgumentParser

	parser = ArgumentParser()
	parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
	args = parser.parse_args()
	port = args.port

	app.run(host='0.0.0.0', port=port, debug=True)






