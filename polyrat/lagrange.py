import numpy as np
from .basis import PolynomialBasis



def lagrange_roots(nodes, weights, coef, deflation = True):
	r""" Compute the roots of a Lagrange polynomial

	This implements the deflation algorithm from LC14

	"""
	n = len(nodes)
	assert (n == len(weights)) and  (n == len(coef)), "Dimensions of nodes, weights, and coef should be the same"

	
	# Build the RHS of the generalized eigenvalue problem
	C0 = np.zeros((n+1, n+1), dtype=np.complex)
	C0[1:n+1,1:n+1] = np.diag(nodes)

	# LHS for generalized eigenvalue problem	
	C1 = np.eye(n+1, dtype=np.complex)
	C1[0, 0] = 0

	# scaling
	coef = coef / np.linalg.norm(coef)
	weights = weights / np.linalg.norm(weights)

	C0[0,1:n+1] = coef
	C0[1:n+1,0] = weights


	# balancing [LC14, eq. 29]
	coef0 = np.copy(coef)
	weights0 = np.copy(weights)
	s = np.array([1.]+[np.sqrt(np.abs(wj/aj)) if np.abs(aj) > 0 else 1 for (wj, aj) in zip(weights, coef)])
	C0 = np.diag(1/s) @ C0 @ np.diag(s)

	# Apply a rotation to make the first weight real
	angle = np.angle(C0[1,0])
	if np.isfinite(angle):
		C0[1:,0] *= np.exp(-1j*angle)
	else:
		print("Rotation failed", angle)
		deflation = False

	if deflation:
		#C0[1,0] must be real for Householder to reflect correctly
		assert np.abs(C0[1,0].imag) < 1e-10, "C0[1,0]: %g + I %g" % (C0[1,0].real, C0[1,0].imag)
		#Householder Reflector
		u = np.copy(C0[1:,0]) # = w scaled
		u[0] += np.linalg.norm(C0[1:,0]) # (w) scaled
		H = np.eye(n, dtype=complex) - 2 * np.outer(u,u.conjugate())/(np.linalg.norm(u)**2)
		G2 = np.zeros((n+1, n+1), dtype=complex)
		G2[0,0] = 1
		G2[1:,1:] = H
		C0 = G2 @ C0 @ G2
		C1 = G2 @ C1 @ G2
		H1, P1 = hessenberg(C0[1:,1:], calc_q=True, overwrite_a = False)
		G3 = np.zeros((n+1, n+1), dtype=complex)
		G3[0,0] = 1
		G3[1:,1:] = P1.T.conjugate()
		G4 = np.eye(n+1, dtype=complex)
		G4[0:2,0:2] = [[0,1],[1,0]]
		H1 = G4.dot(G3.dot(C0.dot(G3.T.conjugate())))[1:,1:]
		B1 = G4.dot(G3.dot(C1.dot(G3.T.conjugate())))[1:,1:]

		# Givens Rotation
		G5 = np.eye(n, dtype=complex)
		a = H1[0,0]
		b = H1[1,0]
		c = a / np.sqrt(a**2 + b**2)
		s = b / np.sqrt(a**2 + b**2)
		G5[0:2,0:2] = [[c.conjugate(), s.conjugate()],[-s,c]]

		H2 = G5.dot(H1)[1:,1:]
		B2 = G5.dot(B1)[1:,1:]
		try:
			return eigvals(H2, B2)
		except np.linalg.linalg.LinAlgError as e:
			raise e 
	else:
		# Compute the eigenvalues
		# As this eigenvalue problem has a double root at infinity, we ignore the division by zero warning
		with warnings.catch_warnings():
			warnings.filterwarnings("ignore", message='divide by zero encountered in true_divide',
									category=RuntimeWarning)
			ew = eigvals(C0, C1, overwrite_a=False)
		ew = ew[np.isfinite(ew).flatten()]
		assert len(ew) == len(coef) - 1, "Error: too many infinite eigenvalues encountered"

		return ew


class LagrangePolynomialBasis(PolynomialBasis):
	r""" Constructs a Lagrange polynomial basis in barycentric form

	See: BT04
	"""
	def __init__(self, nodes):
		self.nodes = np.array(nodes).flatten()
		assert len(nodes) == len(self.nodes), "Input must be one-dimensional"

		# BT 04, eq. (3.2)
		# w[j] = prod_{j\ne k} 1./(node[j] - node[k])
		self.weights = 1./np.array([
			np.prod(self.nodes[k] - self.nodes[0:k]) * np.prod(self.nodes[k] - self.nodes[k+1:]) for k in range(len(self.nodes))
			])

	def vandermonde(self, X):
		x = X.flatten()
		assert len(x) == len(X), "Input must be one dimensional"

		with np.errstate(divide = 'ignore', invalid = 'ignore'):
			# The columns of the Vandermonde matrix 
			V = np.hstack([w/(x - n) for n, w in zip(self.nodes, self.weights)])
			for row in np.argwhere(~np.all(np.isfinite(V), axis = 1)):
				V[row] = 0
				V[row, np.argmin(np.abs(x[row] - self.nodes)).flatten()] = 1.
		
		return V

	def roots(self, coef, deflation = True):
		r"""
		"""
		return lagrange_roots(self.nodes, self.weights, coef, deflation = deflation)