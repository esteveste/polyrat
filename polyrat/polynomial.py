import numpy as np
from .basis import *
from copy import deepcopy


class Polynomial:
	def __init__(self, basis, coef):
		self.basis = deepcopy(basis)
		self.coef = np.copy(coef)

	def __call__(self, X):
		return self.basis.vandermonde(X) @ self.coef

	def eval(self, X):
		return self.basis.vandermonde(X) @ self.coef

class PolynomialApproximation:
	def __init__(self, degree, basis = None, mode = None):
		pass

	def fit(self, X, y):
		pass
		