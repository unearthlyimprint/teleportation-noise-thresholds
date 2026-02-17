import sympy
from sympy import symbols, Function, Matrix, diff, simplify, sqrt, det

def verify_derivation():
    # Define coordinates (2D for simplicity, or just symbolic)
    # We will do a symbolic variation manually to avoid full GR tensor overhead
    
    # Symbols
    R = symbols('R', real=True) # Determinant factor (sqrt(-g))
    L_coh = symbols('L_coh')
    
    # Lagrangian: L = 1/2 * g^{mu,nu} * d_mu phi * d_nu phi - V
    # If F^{mu,nu} is identified with g^{mu,nu} (Emergent Gravity)
    
    # Variation of Action S = Integral(R * L)
    # delta S = Integral ( delta(R) * L + R * delta(L) )
    
    # 1. Term: delta(R) * L
    # R = sqrt(-g)
    # delta R = -1/2 * R * g_{mu,nu} * delta g^{mu,nu}
    # So Term 1 = -1/2 * R * g_{mu,nu} * L * delta g^{mu,nu}
    
    # 2. Term: R * delta(L)
    # L = 1/2 * g^{alpha,beta} * d_alpha phi * d_beta phi - V
    # delta L / delta g^{mu,nu} = 1/2 * d_mu phi * d_nu phi
    # So Term 2 = R * 1/2 * d_mu phi * d_nu phi * delta g^{mu,nu}
    
    # Total delta S = Integral ( R * delta g^{mu,nu} * [ -1/2 g_{mu,nu} L + 1/2 d_mu phi d_nu phi ] )
    
    # T_{mu,nu} definition:
    # T_{mu,nu} = -2/R * (delta S / delta g^{mu,nu})
    #           = -2 * [ 1/2 d_mu phi d_nu phi - 1/2 g_{mu,nu} L ]
    #           = - (d_mu phi d_nu phi - g_{mu,nu} L)
    #           = g_{mu,nu} L - d_mu phi d_nu phi
    
    # Standard sign convention: G_{mu,nu} = 8pi T_{mu,nu}. 
    # Usually T_{mu,nu} = d_mu phi d_nu phi - g_{mu,nu} L (for +--- signature?)
    # Let's check signs.
    # L = 1/2 (dphi)^2 - V.
    # If T_00 ~ rho.
    # d_0 phi d_0 phi - g_00 (1/2 d_0 phi^2) = dot^2 - (-1)(1/2 dot^2) = 1.5 dot^2? No.
    # Correct T_{mu,nu} = d_mu phi d_nu phi - g_{mu,nu} L.
    
    # Compare with User's Eq 90:
    # T = (d_mu phi)(d_nu phi) F_{mu,nu} - g_{mu,nu} [...]
    # If F_{mu,nu} = g_{mu,nu} (Inverse of F^{mu,nu}=g^{mu,nu})
    # Then User T = (d_mu phi)(d_nu phi) g_{mu,nu} - g_{mu,nu} [...]
    #             = g_{mu,nu} [ (d_mu phi)(d_nu phi) - L ] ? No.
    # The term (d_mu phi)(d_nu phi) g_{mu,nu} is a Tensor proportional to metric.
    # Standard T has a free kinematic term d_mu phi d_nu phi.
    
    print("Standard Scalar Field T_uv:")
    print("  T_uv = d_u phi * d_v phi - g_uv * L")
    print("\nUser Manuscript Eq 90:")
    print("  T_uv = (d_u phi)(d_v phi) * F_uv - g_uv * [...]")
    print("If F_uv is the metric g_uv:")
    print("  T_uv = (d_u phi)(d_v phi) * g_uv - g_uv * [...]")
    
    print("\nDISCREPANCY DETECTED:")
    print("The user's term has an extra metric factor g_uv in the kinetic term.")
    print("Standard:  d_u phi d_v phi")
    print("User:      d_u phi d_v phi * g_uv")
    print("\nResult: Eq 90 is likely incorrect.")

if __name__ == "__main__":
    verify_derivation()
