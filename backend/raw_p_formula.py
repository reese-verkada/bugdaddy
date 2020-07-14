class Raw_P_Formula:

	def __init__(self,formula):
		self.operators = {'+':float.__add__, '*':float.__mul__}
		self.operands = set()

		self.tokenized = self.tokenizer(formula)

	def stringFormula(self):
		return " ".join(self.tokenized)

	def isNumeric(self,string):
		try:
			float(string)
			return True
		except ValueError:
			return False

	def tokenizer(self,formula):
		tokenized = formula.split(" ")
		if len(tokenized) % 2 == 0:
			raise Exception("Formula should have an odd number of elements")

		operands = tokenized[0::2]
		operators = tokenized[1::2]

		for operand in operands:
			if operand in self.operators:
				raise Exception("Operator being used as an operand")
			else:
				if not self.isNumeric(operand):
					self.operands.add(operand)

		for operator in operators:
			if operator not in self.operators:
				raise Exception("Operand being used as an operator")

		return tokenized


	def evaluate(self,operands):
		tokenized = self.tokenized.copy()
		result = 0.0
		if set(operands) != self.operands:
			raise Exception("Too many or too few operands supplied")
		if len(tokenized) == 1:
			if self.isNumeric(tokenized[0]):
				result = float(tokenized[0])
			else:
				result = operands[tokenized[0]]
		while tokenized.count("*"):
			print(tokenized)
			loc = tokenized.index("*")

			if tokenized[loc - 1] in self.operands:
				op_a = operands[tokenized[loc - 1]]
			elif self.isNumeric(tokenized[loc - 1]):
				op_a = float(tokenized[loc - 1])
			else:
				raise Exception("Could not evaluate left operand for *")

			if tokenized[loc + 1] in self.operands:
				op_b = operands[tokenized[loc + 1]]
			elif self.isNumeric(tokenized[loc + 1]):
				op_b = float(tokenized[loc + 1])
			else:
				raise Exception("Could not evaluate right operand for *")

			result = self.operators['*'](float(op_a),float(op_b))
			tokenized[loc] = result
			tokenized[loc - 1] = " "
			tokenized[loc + 1] = " "
			while tokenized.count(" "):
				tokenized.remove(" ")

		while tokenized.count("+"):
			print(tokenized)
			loc = tokenized.index("+")

			if tokenized[loc - 1] in self.operands:
				op_a = operands[tokenized[loc - 1]]
			elif self.isNumeric(tokenized[loc - 1]):
				op_a = float(tokenized[loc - 1])
			else:
				raise Exception("Could not evaluate left operand for +")

			if tokenized[loc + 1] in self.operands:
				op_b = operands[tokenized[loc + 1]]
			elif self.isNumeric(tokenized[loc + 1]):
				op_b = float(tokenized[loc + 1])
			else:
				raise Exception("Could not evaluate right operand for +")

			result = self.operators["+"](float(op_a),float(op_b))
			tokenized[loc] = result
			tokenized[loc - 1] = " "
			tokenized[loc + 1] = " "
			while tokenized.count(" "):
				tokenized.remove(" ")

		return result




